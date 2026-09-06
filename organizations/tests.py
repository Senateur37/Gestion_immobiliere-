"""Tests de la fondation multi-tenant.

Ces tests ne verifient pas que le code "marche" : ils tentent activement
de faire fuiter des donnees entre deux organisations.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase

from core.exceptions import DomainError, NoActiveOrganization
from core.tenancy import get_current_organization_id, organization_context, unscoped

from .models import Membership, Organization
from .selectors import memberships_for_user, resolve_membership_for_request
from .services import add_member, create_organization, remove_member, set_member_role

User = get_user_model()


class OrganizationServiceTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')

    def test_creation_installe_le_createur_comme_proprietaire(self):
        org = create_organization(name='Agence Bamako', owner=self.alice)
        membership = Membership.objects.get(organization=org, user=self.alice)
        self.assertEqual(membership.role, Membership.ROLE_OWNER)
        self.assertTrue(membership.is_default)

    def test_le_slug_est_derive_du_nom(self):
        org = create_organization(name='Agence du Fleuve', owner=self.alice)
        self.assertEqual(org.slug, 'agence-du-fleuve')

    def test_nom_vide_refuse(self):
        with self.assertRaises(DomainError):
            create_organization(name='   ', owner=self.alice)

    def test_double_adhesion_refusee(self):
        org = create_organization(name='Agence A', owner=self.alice)
        with self.assertRaises(DomainError):
            add_member(organization=org, user=self.alice)

    def test_le_dernier_proprietaire_ne_peut_pas_etre_retrograde(self):
        org = create_organization(name='Agence A', owner=self.alice)
        membership = Membership.objects.get(organization=org, user=self.alice)
        with self.assertRaises(DomainError):
            set_member_role(membership=membership, role=Membership.ROLE_AGENT)

    def test_le_dernier_proprietaire_ne_peut_pas_etre_retire(self):
        org = create_organization(name='Agence A', owner=self.alice)
        membership = Membership.objects.get(organization=org, user=self.alice)
        with self.assertRaises(DomainError):
            remove_member(membership=membership)

    def test_retrogradation_possible_s_il_reste_un_proprietaire(self):
        org = create_organization(name='Agence A', owner=self.alice)
        add_member(organization=org, user=self.bob, role=Membership.ROLE_OWNER)
        membership = Membership.objects.get(organization=org, user=self.alice)
        set_member_role(membership=membership, role=Membership.ROLE_MANAGER)
        membership.refresh_from_db()
        self.assertEqual(membership.role, Membership.ROLE_MANAGER)

    def test_un_utilisateur_peut_avoir_deux_roles_dans_deux_organisations(self):
        """Ce que User.role rendait impossible."""
        agence = create_organization(name='Agence A', owner=self.alice)
        regie = create_organization(name='Regie B', owner=self.bob)
        add_member(organization=regie, user=self.alice, role=Membership.ROLE_ACCOUNTANT)

        roles = {m.organization_id: m.role for m in memberships_for_user(self.alice)}
        self.assertEqual(roles[agence.pk], Membership.ROLE_OWNER)
        self.assertEqual(roles[regie.pk], Membership.ROLE_ACCOUNTANT)


class RoleHierarchyTests(TestCase):
    def test_hierarchie_des_roles(self):
        user = User.objects.create_user('carla', password='x')
        org = create_organization(name='Agence A', owner=user)
        membership = Membership.objects.get(organization=org, user=user)

        self.assertTrue(membership.has_at_least(Membership.ROLE_AGENT))
        self.assertTrue(membership.has_at_least(Membership.ROLE_OWNER))

        membership.role = Membership.ROLE_AGENT
        self.assertFalse(membership.has_at_least(Membership.ROLE_MANAGER))
        self.assertTrue(membership.has_at_least(Membership.ROLE_AGENT))


class TenancyContextTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.org = create_organization(name='Agence A', owner=self.alice)

    def test_le_contexte_est_pose_et_restaure(self):
        self.assertIsNone(get_current_organization_id())
        with organization_context(self.org):
            self.assertEqual(get_current_organization_id(), self.org.pk)
        self.assertIsNone(get_current_organization_id())

    def test_le_contexte_est_restaure_meme_en_cas_d_erreur(self):
        with self.assertRaises(ValueError):
            with organization_context(self.org):
                raise ValueError('boom')
        self.assertIsNone(get_current_organization_id())

    def test_contextes_imbriques(self):
        autre = create_organization(name='Agence B', owner=self.alice)
        with organization_context(self.org):
            with organization_context(autre):
                self.assertEqual(get_current_organization_id(), autre.pk)
            self.assertEqual(get_current_organization_id(), self.org.pk)


class MembershipResolutionTests(TestCase):
    """L'en-tete X-Organization est une preference, jamais une autorisation."""

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')
        self.agence_a = create_organization(name='Agence A', owner=self.alice)
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

    def _request(self, user, organization_slug=None):
        class FakeRequest:
            pass

        request = FakeRequest()
        request.user = user
        request.META = {}
        if organization_slug:
            request.META['HTTP_X_ORGANIZATION'] = organization_slug
        return request

    def test_organisation_par_defaut_sans_en_tete(self):
        membership = resolve_membership_for_request(self._request(self.alice))
        self.assertEqual(membership.organization, self.agence_a)

    def test_en_tete_vers_une_organisation_non_autorisee_refuse_le_perimetre(self):
        """Alice demande l'agence de Bob : elle n'obtient aucun perimetre."""
        membership = resolve_membership_for_request(
            self._request(self.alice, organization_slug='agence-b')
        )
        self.assertIsNone(membership)

    def test_utilisateur_anonyme_sans_perimetre(self):
        class Anonymous:
            is_authenticated = False

        membership = resolve_membership_for_request(self._request(Anonymous()))
        self.assertIsNone(membership)


class RattachementDesModulesTests(TestCase):
    """Les lignes des modules metier portent leur organisation des leur creation.

    Sans cela, le passage au multi-entreprises obligerait a repasser sur
    toutes les lignes existantes pour deviner a qui elles appartiennent.
    """

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')
        self.agence_a = create_organization(name='Agence A', owner=self.alice)
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

    def _creer_compte(self, code):
        from decimal import Decimal

        from comptes.models import Compte

        return Compte.objects.create(
            code=code, nom=f'Caisse {code}', type='CAISSE',
            solde_initial=Decimal('0'), solde_actuel=Decimal('0'),
        )

    def test_une_ligne_creee_porte_l_organisation_active(self):
        with organization_context(self.agence_a):
            compte = self._creer_compte('C-A')

        self.assertEqual(compte.entreprise_id, str(self.agence_a.uid))

    def test_deux_organisations_produisent_deux_rattachements(self):
        with organization_context(self.agence_a):
            a = self._creer_compte('C-1')
        with organization_context(self.agence_b):
            b = self._creer_compte('C-2')

        self.assertEqual(a.entreprise_id, str(self.agence_a.uid))
        self.assertEqual(b.entreprise_id, str(self.agence_b.uid))
        self.assertNotEqual(a.entreprise_id, b.entreprise_id)

    def test_un_rattachement_existant_n_est_jamais_recrit(self):
        """Une ligne appartient a l'organisation qui l'a creee."""
        with organization_context(self.agence_a):
            compte = self._creer_compte('C-STABLE')

        with organization_context(self.agence_b):
            compte.nom = 'Renomme depuis B'
            compte.save()

        compte.refresh_from_db()
        self.assertEqual(compte.entreprise_id, str(self.agence_a.uid))

    def test_hors_contexte_la_ligne_reste_sans_rattachement(self):
        """Une commande d'administration ne doit pas echouer."""
        compte = self._creer_compte('C-ADMIN')
        self.assertEqual(compte.entreprise_id, '')

    def test_tous_les_modeles_concernes_sont_branches(self):
        from .rattachement import modeles_rattachables

        labels = {modele._meta.label for modele in modeles_rattachables()}
        attendus = {
            'comptes.Compte',
            'comptabilite_ohada.CompteComptable',
            'comptabilite_ohada.EcritureComptable',
            'rh.Employee',
        }
        self.assertTrue(attendus.issubset(labels), f'manquants : {attendus - labels}')


class FiltrageParEntrepriseTests(TestCase):
    """Le filtrage est ecrit et teste, mais volontairement inactif."""

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.agence = create_organization(name='Agence A', owner=self.alice)

    def test_le_filtrage_est_inactif_par_defaut(self):
        from . import entreprise

        self.assertFalse(entreprise.FILTRER_PAR_ENTREPRISE)

    def test_inactif_le_filtre_ne_retire_rien(self):
        from decimal import Decimal

        from comptes.models import Compte

        from .entreprise import filtrer_par_entreprise

        with organization_context(self.agence):
            Compte.objects.create(code='C-1', nom='Caisse', type='CAISSE',
                                  solde_initial=Decimal('0'), solde_actuel=Decimal('0'))

        self.assertEqual(filtrer_par_entreprise(Compte.objects.all()).count(), 1)

    def test_actif_le_filtre_restreint_a_l_organisation(self):
        """Simulation de la bascule, sans la declencher pour de bon."""
        from decimal import Decimal
        from unittest.mock import patch

        from comptes.models import Compte

        from . import entreprise

        autre = create_organization(name='Agence B', owner=User.objects.create_user('bob', password='x'))

        with organization_context(self.agence):
            Compte.objects.create(code='C-A', nom='Caisse A', type='CAISSE',
                                  solde_initial=Decimal('0'), solde_actuel=Decimal('0'))
        with organization_context(autre):
            Compte.objects.create(code='C-B', nom='Caisse B', type='CAISSE',
                                  solde_initial=Decimal('0'), solde_actuel=Decimal('0'))

        with patch.object(entreprise, 'FILTRER_PAR_ENTREPRISE', True):
            with organization_context(self.agence):
                visibles = entreprise.filtrer_par_entreprise(Compte.objects.all())
                self.assertEqual([c.code for c in visibles], ['C-A'])

    def test_actif_hors_contexte_rien_n_est_visible(self):
        """Fail closed : sans organisation, on ne montre rien."""
        from decimal import Decimal
        from unittest.mock import patch

        from comptes.models import Compte

        from . import entreprise

        with organization_context(self.agence):
            Compte.objects.create(code='C-A', nom='Caisse A', type='CAISSE',
                                  solde_initial=Decimal('0'), solde_actuel=Decimal('0'))

        with patch.object(entreprise, 'FILTRER_PAR_ENTREPRISE', True):
            self.assertEqual(entreprise.filtrer_par_entreprise(Compte.objects.all()).count(), 0)


class UidDesOrganisationsTests(TestCase):
    """L'UID est ce que les modules stockent : il doit etre fiable."""

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')

    def test_chaque_organisation_recoit_un_uid_unique(self):
        a = create_organization(name='Agence A', owner=self.alice)
        b = create_organization(name='Agence B', owner=User.objects.create_user('bob', password='x'))

        self.assertIsNotNone(a.uid)
        self.assertNotEqual(a.uid, b.uid)

    def test_l_uid_ne_change_pas_quand_l_organisation_est_renommee(self):
        """C'est tout l'interet : le nom bouge, l'identifiant non."""
        organisation = create_organization(name='Ancien nom', owner=self.alice)
        uid_initial = organisation.uid

        organisation.name = 'Nouveau nom'
        organisation.slug = 'nouveau-nom'
        organisation.save()
        organisation.refresh_from_db()

        self.assertEqual(organisation.uid, uid_initial)

    def test_entreprise_id_courant_renvoie_l_uid_et_non_la_cle(self):
        from .entreprise import entreprise_id_courant

        organisation = create_organization(name='Agence A', owner=self.alice)
        with organization_context(organisation):
            valeur = entreprise_id_courant()

        self.assertEqual(valeur, str(organisation.uid))
        self.assertNotEqual(valeur, str(organisation.pk))

    def test_hors_contexte_l_identifiant_est_vide(self):
        from .entreprise import entreprise_id_courant

        self.assertEqual(entreprise_id_courant(), '')

    def test_une_organisation_disparue_ne_fait_pas_echouer(self):
        """Mieux vaut une ligne sans rattachement qu'une exception."""
        from .entreprise import uid_de

        self.assertEqual(uid_de(999999), '')

    def test_deux_organisations_ne_sont_jamais_confondues(self):
        """Regression : un cache cle primaire -> UID les melangeait."""
        from .entreprise import entreprise_id_courant

        a = create_organization(name='Agence A', owner=self.alice)
        b = create_organization(name='Agence B', owner=User.objects.create_user('bob', password='x'))

        with organization_context(a):
            vu_a = entreprise_id_courant()
        with organization_context(b):
            vu_b = entreprise_id_courant()
        with organization_context(a):
            vu_a_encore = entreprise_id_courant()

        self.assertEqual(vu_a, str(a.uid))
        self.assertEqual(vu_b, str(b.uid))
        self.assertEqual(vu_a_encore, str(a.uid))
