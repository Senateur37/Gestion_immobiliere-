"""Tests du domaine financier.

On y verifie surtout ce que l'ancien modele ne savait pas representer :
paiement partiel, versement couvrant plusieurs echeances, avance, et
refus des situations qui fausseraient un solde.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from Comptes.models import User
from core.events import clear_subscribers, publish, subscribe
from core.exceptions import DomainError
from core.tenancy import organization_context
from Locations.models import Lease
from organizations.services import create_organization
from Proprietes.models import Property, Unit

from .events import PaymentRecorded, RentChargeSettled
from .models import Payment, PaymentAllocation, RentCharge
from .services import (
    allocate_payment,
    cancel_rent_charge,
    generate_rent_schedule,
    lease_balance,
    overdue_charges,
    record_payment,
)


class FinanceTestCase(TestCase):
    """Un bail d'un an a 100 000 par mois, dans une organisation."""

    def setUp(self):
        self.proprietaire = User.objects.create_user('alice', password='x', role='owner')
        self.locataire = User.objects.create_user('moussa', password='x', role='tenant')
        self.organisation = create_organization(name='Agence A', owner=self.proprietaire)

        contexte = organization_context(self.organisation)
        contexte.__enter__()
        self.addCleanup(contexte.__exit__, None, None, None)

        bien = Property.objects.create(
            name='Residence du Fleuve',
            address='1 rue du Fleuve',
            city='Bamako',
            postal_code='0000',
            property_type='apartment',
            total_area=200,
        )
        self.unite = Unit.objects.create(
            property=bien,
            unit_number='A-101',
            area=60,
            rent_amount=Decimal('100000'),
            deposit_amount=Decimal('200000'),
        )
        self.bail = Lease.objects.create(
            unit=self.unite,
            tenant=self.locataire,
            lease_number='BAIL-001',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            rent_amount=Decimal('100000'),
            deposit_amount=Decimal('200000'),
            payment_frequency='monthly',
            payment_day=1,
            status='active',
        )


class EcheancierTests(FinanceTestCase):
    def test_un_bail_mensuel_d_un_an_produit_douze_echeances(self):
        echeances = generate_rent_schedule(lease=self.bail)

        self.assertEqual(len(echeances), 12)
        self.assertEqual(RentCharge.objects.count(), 12)
        self.assertEqual(RentCharge.objects.first().amount_due, Decimal('100000'))

    def test_la_generation_est_rejouable_sans_doublon(self):
        """Relancer la generation ne doit pas refacturer les memes mois."""
        generate_rent_schedule(lease=self.bail)
        nouvelles = generate_rent_schedule(lease=self.bail)

        self.assertEqual(nouvelles, [])
        self.assertEqual(RentCharge.objects.count(), 12)

    def test_un_bail_trimestriel_produit_quatre_echeances(self):
        self.bail.payment_frequency = 'quarterly'
        self.bail.save()

        echeances = generate_rent_schedule(lease=self.bail)

        self.assertEqual(len(echeances), 4)

    def test_la_derniere_periode_s_arrete_a_la_fin_du_bail(self):
        echeances = generate_rent_schedule(lease=self.bail)

        self.assertEqual(echeances[-1].period_end, self.bail.end_date)

    def test_un_jour_de_paiement_absent_du_mois_retombe_sur_le_dernier(self):
        """Le 31 demande, fevrier ne l'a pas."""
        self.bail.payment_day = 31
        self.bail.save()

        generate_rent_schedule(lease=self.bail)
        fevrier = RentCharge.objects.get(period_start=date(2026, 2, 1))

        self.assertEqual(fevrier.due_date, date(2026, 2, 28))

    def test_un_bail_en_brouillon_n_a_pas_d_echeancier(self):
        self.bail.status = 'draft'
        self.bail.save()

        with self.assertRaises(DomainError) as erreur:
            generate_rent_schedule(lease=self.bail)
        self.assertEqual(erreur.exception.code, 'lease_not_active')


class PaiementPartielTests(FinanceTestCase):
    """Ce que l'ancien modele ne savait pas faire."""

    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)
        self.janvier = RentCharge.objects.get(period_start=date(2026, 1, 1))

    def test_un_versement_partiel_laisse_l_echeance_partiellement_payee(self):
        record_payment(
            lease=self.bail,
            amount=Decimal('60000'),
            payment_date=date(2026, 1, 5),
            method=Payment.METHOD_ORANGE_MONEY,
        )

        self.janvier.refresh_from_db()
        self.assertEqual(self.janvier.status, RentCharge.STATUS_PARTIAL)
        self.assertEqual(self.janvier.amount_outstanding, Decimal('40000'))

    def test_le_complement_solde_l_echeance(self):
        record_payment(
            lease=self.bail, amount=Decimal('60000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )
        record_payment(
            lease=self.bail, amount=Decimal('40000'),
            payment_date=date(2026, 1, 20), method=Payment.METHOD_CASH,
        )

        self.janvier.refresh_from_db()
        self.assertEqual(self.janvier.status, RentCharge.STATUS_PAID)
        self.assertEqual(self.janvier.amount_outstanding, Decimal('0'))

    def test_un_versement_couvrant_deux_mois_solde_les_deux(self):
        record_payment(
            lease=self.bail, amount=Decimal('200000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_BANK,
        )

        fevrier = RentCharge.objects.get(period_start=date(2026, 2, 1))
        self.janvier.refresh_from_db()
        self.assertEqual(self.janvier.status, RentCharge.STATUS_PAID)
        self.assertEqual(fevrier.status, RentCharge.STATUS_PAID)

    def test_l_imputation_commence_par_l_echeance_la_plus_ancienne(self):
        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 3, 1), method=Payment.METHOD_CASH,
        )

        self.janvier.refresh_from_db()
        fevrier = RentCharge.objects.get(period_start=date(2026, 2, 1))
        self.assertEqual(self.janvier.status, RentCharge.STATUS_PAID)
        self.assertEqual(fevrier.status, RentCharge.STATUS_PENDING)

    def test_le_surplus_reste_en_avance_non_imputee(self):
        """Un locataire verse plus que tout ce qu'il doit sur l'annee."""
        paiement = record_payment(
            lease=self.bail, amount=Decimal('1300000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_BANK,
        )

        self.assertEqual(paiement.amount_allocated, Decimal('1200000'))
        self.assertEqual(paiement.amount_unallocated, Decimal('100000'))
        self.assertEqual(
            RentCharge.objects.filter(status=RentCharge.STATUS_PAID).count(), 12
        )

    def test_sans_imputation_automatique_rien_n_est_impute(self):
        paiement = record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
            auto_allocate=False,
        )

        self.assertEqual(paiement.amount_allocated, Decimal('0'))
        self.janvier.refresh_from_db()
        self.assertEqual(self.janvier.status, RentCharge.STATUS_PENDING)


class GardeFousDeLImputationTests(FinanceTestCase):
    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)
        self.janvier = RentCharge.objects.get(period_start=date(2026, 1, 1))
        self.paiement = record_payment(
            lease=self.bail, amount=Decimal('50000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
            auto_allocate=False,
        )

    def test_on_ne_peut_pas_imputer_plus_que_l_encaissement(self):
        with self.assertRaises(DomainError) as erreur:
            allocate_payment(payment=self.paiement, rent_charge=self.janvier, amount=Decimal('80000'))
        self.assertEqual(erreur.exception.code, 'insufficient_payment')

    def test_on_ne_peut_pas_imputer_plus_que_le_du(self):
        gros_paiement = record_payment(
            lease=self.bail, amount=Decimal('500000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
            auto_allocate=False,
        )
        with self.assertRaises(DomainError) as erreur:
            allocate_payment(payment=gros_paiement, rent_charge=self.janvier, amount=Decimal('150000'))
        self.assertEqual(erreur.exception.code, 'overpaying_charge')

    def test_un_montant_negatif_est_refuse(self):
        with self.assertRaises(DomainError) as erreur:
            allocate_payment(payment=self.paiement, rent_charge=self.janvier, amount=Decimal('-10'))
        self.assertEqual(erreur.exception.code, 'invalid_amount')

    def test_deux_imputations_sur_la_meme_echeance_se_cumulent(self):
        allocate_payment(payment=self.paiement, rent_charge=self.janvier, amount=Decimal('20000'))
        allocate_payment(payment=self.paiement, rent_charge=self.janvier, amount=Decimal('30000'))

        self.assertEqual(
            PaymentAllocation.objects.filter(payment=self.paiement, rent_charge=self.janvier).count(), 1
        )
        self.janvier.refresh_from_db()
        self.assertEqual(self.janvier.amount_allocated, Decimal('50000'))

    def test_une_echeance_annulee_n_accepte_pas_d_imputation(self):
        fevrier = RentCharge.objects.get(period_start=date(2026, 2, 1))
        cancel_rent_charge(rent_charge=fevrier, reason='erreur de saisie')

        with self.assertRaises(DomainError) as erreur:
            allocate_payment(payment=self.paiement, rent_charge=fevrier, amount=Decimal('10000'))
        self.assertEqual(erreur.exception.code, 'charge_cancelled')

    def test_une_echeance_deja_payee_ne_peut_pas_etre_annulee(self):
        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )
        self.janvier.refresh_from_db()

        with self.assertRaises(DomainError) as erreur:
            cancel_rent_charge(rent_charge=self.janvier)
        self.assertEqual(erreur.exception.code, 'charge_has_allocations')


class SoldeEtRetardsTests(FinanceTestCase):
    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)

    def test_le_solde_vaut_le_total_du_au_depart(self):
        self.assertEqual(lease_balance(self.bail), Decimal('1200000'))

    def test_le_solde_diminue_des_versements(self):
        record_payment(
            lease=self.bail, amount=Decimal('250000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_MOOV_MONEY,
        )
        self.assertEqual(lease_balance(self.bail), Decimal('950000'))

    def test_une_echeance_annulee_sort_du_solde(self):
        decembre = RentCharge.objects.get(period_start=date(2026, 12, 1))
        cancel_rent_charge(rent_charge=decembre)

        self.assertEqual(lease_balance(self.bail), Decimal('1100000'))

    def test_les_retards_sont_les_echeances_depassees_non_soldees(self):
        retards = overdue_charges(organization=self.organisation, today=date(2026, 3, 15))

        # Janvier, fevrier et mars sont echues au 15 mars.
        self.assertEqual(retards.count(), 3)

    def test_une_echeance_payee_n_est_plus_en_retard(self):
        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )
        retards = overdue_charges(organization=self.organisation, today=date(2026, 3, 15))

        self.assertEqual(retards.count(), 2)


class ReferenceTests(FinanceTestCase):
    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)

    def test_les_references_se_suivent_dans_le_mois(self):
        premier = record_payment(
            lease=self.bail, amount=Decimal('10000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )
        second = record_payment(
            lease=self.bail, amount=Decimal('10000'),
            payment_date=date(2026, 1, 6), method=Payment.METHOD_CASH,
        )

        self.assertEqual(premier.reference, 'PAY-202601-0001')
        self.assertEqual(second.reference, 'PAY-202601-0002')

    def test_une_reference_deja_prise_est_refusee(self):
        record_payment(
            lease=self.bail, amount=Decimal('10000'), payment_date=date(2026, 1, 5),
            method=Payment.METHOD_CASH, reference='RECU-1',
        )
        with self.assertRaises(DomainError) as erreur:
            record_payment(
                lease=self.bail, amount=Decimal('10000'), payment_date=date(2026, 1, 6),
                method=Payment.METHOD_CASH, reference='RECU-1',
            )
        self.assertEqual(erreur.exception.code, 'duplicate_reference')


class IsolationFinanceTests(FinanceTestCase):
    """Le cloisonnement s'applique aussi a l'argent."""

    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)

        self.bob = User.objects.create_user('bob', password='x', role='owner')
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

    def test_une_autre_organisation_ne_voit_pas_les_echeances(self):
        with organization_context(self.agence_b):
            self.assertEqual(RentCharge.objects.count(), 0)

    def test_une_autre_organisation_ne_voit_pas_les_encaissements(self):
        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )
        with organization_context(self.agence_b):
            self.assertEqual(Payment.objects.count(), 0)


class EvenementsTests(FinanceTestCase):
    """Les evenements sont bien publies, et un abonne defaillant n'annule rien."""

    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)
        self.addCleanup(self._restaurer_abonnes)
        self.recus = []

    def _restaurer_abonnes(self):
        clear_subscribers()
        import finance.handlers  # noqa: F401  reinstalle les abonnements du domaine
        import importlib
        importlib.reload(finance.handlers)

    def test_un_encaissement_publie_son_evenement(self):
        subscribe(PaymentRecorded, self.recus.append)

        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )

        self.assertEqual(len(self.recus), 1)
        self.assertEqual(self.recus[0].amount, Decimal('100000'))

    def test_solder_une_echeance_publie_son_evenement(self):
        subscribe(RentChargeSettled, self.recus.append)

        record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )

        self.assertEqual(len(self.recus), 1)

    def test_un_abonne_defaillant_n_annule_pas_l_encaissement(self):
        """L'argent recu reste recu, meme si une notification echoue."""
        def abonne_casse(event):
            raise RuntimeError('service de notification indisponible')

        subscribe(PaymentRecorded, abonne_casse)

        paiement = record_payment(
            lease=self.bail, amount=Decimal('100000'),
            payment_date=date(2026, 1, 5), method=Payment.METHOD_CASH,
        )

        self.assertIsNotNone(paiement.pk)
        self.assertTrue(Payment.objects.filter(pk=paiement.pk).exists())


class PontComptableTests(FinanceTestCase):
    """L'encaissement alimente la tresorerie, qui alimente la comptabilite.

    C'est le chainon qui manquait : le modele d'origine n'avait aucun lien
    entre un paiement et une ecriture, si bien que la comptabilite etait
    entierement ressaisie a la main.
    """

    def setUp(self):
        super().setUp()
        generate_rent_schedule(lease=self.bail)

        from comptabilite_ohada.services.initialisation_service import InitialisationService
        from comptes.models import Compte

        InitialisationService.charger_plan_comptable()
        InitialisationService.initialiser_journaux()

        from comptabilite_ohada.models import ExerciceComptable

        ExerciceComptable.objects.get_or_create(
            date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31)
        )

        self.caisse = Compte.objects.create(
            code='CAISSE-TEST',
            nom='Caisse de test',
            type='CAISSE',
            solde_initial=Decimal('0'),
            solde_actuel=Decimal('0'),
            compte_comptable_code='571',
        )

    def test_un_encaissement_credite_le_compte(self):
        record_payment(
            lease=self.bail, amount=Decimal('100000'), payment_date=date(2026, 1, 5),
            method=Payment.METHOD_CASH, compte=self.caisse, user=self.proprietaire,
        )

        self.caisse.refresh_from_db()
        self.assertEqual(self.caisse.solde_actuel, Decimal('100000'))

    def test_un_encaissement_produit_une_ecriture_equilibree(self):
        """L'ecriture nait du signal `mouvement_valide`, emis apres commit.

        captureOnCommitCallbacks est donc indispensable : dans un TestCase,
        la transaction n'est jamais validee et les callbacks on_commit ne
        s'executeraient pas.
        """
        from comptabilite_ohada.models import EcritureComptable

        avant = EcritureComptable.objects.count()
        with self.captureOnCommitCallbacks(execute=True):
            record_payment(
                lease=self.bail, amount=Decimal('100000'), payment_date=date(2026, 1, 5),
                method=Payment.METHOD_CASH, compte=self.caisse, user=self.proprietaire,
            )

        self.assertEqual(EcritureComptable.objects.count(), avant + 1)
        ecriture = EcritureComptable.objects.order_by('-id').first()
        self.assertTrue(ecriture.est_equilibree)
        self.assertEqual(ecriture.total_debit, Decimal('100000'))

    def test_l_ecriture_mouvemente_la_caisse_et_le_produit(self):
        from comptabilite_ohada.models import EcritureComptable

        with self.captureOnCommitCallbacks(execute=True):
            record_payment(
                lease=self.bail, amount=Decimal('100000'), payment_date=date(2026, 1, 5),
                method=Payment.METHOD_CASH, compte=self.caisse, user=self.proprietaire,
            )

        ecriture = EcritureComptable.objects.order_by('-id').first()
        mouvements = {ligne.compte.code: (ligne.debit, ligne.credit) for ligne in ecriture.lignes.all()}
        self.assertEqual(mouvements['571'], (Decimal('100000'), Decimal('0')))
        self.assertEqual(mouvements['706'], (Decimal('0'), Decimal('100000')))

    def test_un_encaissement_sans_compte_reste_possible(self):
        """La saisie sans compte ne doit pas bloquer, le temps de la reprise."""
        paiement = record_payment(
            lease=self.bail, amount=Decimal('100000'), payment_date=date(2026, 1, 5),
            method=Payment.METHOD_CASH,
        )
        self.assertIsNone(paiement.compte_id)


class EquilibreComptableTests(FinanceTestCase):
    """Le module OHADA acceptait des ecritures fausses : verification."""

    def setUp(self):
        super().setUp()
        from comptabilite_ohada.services.initialisation_service import InitialisationService

        InitialisationService.charger_plan_comptable()
        InitialisationService.initialiser_journaux()

    def test_une_ecriture_desequilibree_est_refusee(self):
        from django.core.exceptions import ValidationError

        from comptabilite_ohada.models import (
            CompteComptable, EcritureComptable, ExerciceComptable, JournalComptable,
        )
        from comptabilite_ohada.services.ecriture_service import EcritureService

        exercice = ExerciceComptable.objects.create(
            date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31)
        )
        with self.assertRaises(ValidationError):
            EcritureService.creer_ecriture(
                reference='TEST-DESEQUILIBRE',
                date_ecriture=date(2026, 6, 1),
                libelle='Ecriture fausse',
                journal=JournalComptable.objects.first(),
                exercice=exercice,
                lignes=[
                    {'compte': CompteComptable.objects.get(code='571'), 'debit': Decimal('100')},
                    {'compte': CompteComptable.objects.get(code='706'), 'credit': Decimal('40')},
                ],
            )

        # Et rien ne doit subsister en base.
        self.assertFalse(
            EcritureComptable.objects.filter(reference='TEST-DESEQUILIBRE').exists()
        )
