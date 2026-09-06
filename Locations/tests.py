"""Tests des baux, cloisonnes par organisation."""
from datetime import date

from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from Comptes.models import User
from core.tenancy import organization_context
from organizations.services import create_organization
from Proprietes.models import Property, Unit

from .forms import LeaseForm
from .models import Lease


class BailTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='password', role='owner')
        self.bob = User.objects.create_user('bob', password='password', role='owner')
        self.locataire_a = User.objects.create_user('locataire_a', password='password', role='tenant')
        self.locataire_b = User.objects.create_user('locataire_b', password='password', role='tenant')

        self.agence_a = create_organization(name='Agence A', owner=self.alice)
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

        self.unite_a = self.creer_unite(self.agence_a, 'A-101')
        self.unite_b = self.creer_unite(self.agence_b, 'B-201')

        self.client.force_login(self.alice)

    def creer_unite(self, organization, numero):
        with organization_context(organization):
            bien = Property.objects.create(
                name=f'Residence {numero}',
                address='1 rue du Fleuve',
                city='Bamako',
                postal_code='0000',
                property_type='apartment',
                total_area=100,
            )
            return Unit.objects.create(
                property=bien,
                unit_number=numero,
                area=60,
                rent_amount=150000,
                deposit_amount=300000,
            )

    def creer_bail(self, organization, unite, locataire, numero='BAIL-001'):
        with organization_context(organization):
            return Lease.objects.create(
                unit=unite,
                tenant=locataire,
                lease_number=numero,
                start_date=date(2026, 1, 1),
                end_date=date(2027, 1, 1),
                rent_amount=150000,
                deposit_amount=300000,
                status='active',
            )


class IsolationDesBauxTests(BailTestCase):
    def test_chaque_organisation_ne_voit_que_ses_baux(self):
        self.creer_bail(self.agence_a, self.unite_a, self.locataire_a, 'BAIL-A')
        self.creer_bail(self.agence_b, self.unite_b, self.locataire_b, 'BAIL-B')

        with organization_context(self.agence_a):
            self.assertEqual([b.lease_number for b in Lease.objects.all()], ['BAIL-A'])
        with organization_context(self.agence_b):
            self.assertEqual([b.lease_number for b in Lease.objects.all()], ['BAIL-B'])

    def test_un_identifiant_devine_ne_donne_pas_acces(self):
        bail_de_b = self.creer_bail(self.agence_b, self.unite_b, self.locataire_b)

        with organization_context(self.agence_a):
            with self.assertRaises(Lease.DoesNotExist):
                Lease.objects.get(pk=bail_de_b.pk)

    def test_la_liste_ne_montre_pas_les_baux_voisins(self):
        self.creer_bail(self.agence_a, self.unite_a, self.locataire_a, 'BAIL-A')
        self.creer_bail(self.agence_b, self.unite_b, self.locataire_b, 'BAIL-B')

        response = self.client.get(reverse('lease_list'))

        self.assertContains(response, 'BAIL-A')
        self.assertNotContains(response, 'BAIL-B')

    def test_modifier_un_bail_voisin_renvoie_404(self):
        bail_de_b = self.creer_bail(self.agence_b, self.unite_b, self.locataire_b)

        response = self.client.get(reverse('lease_update', args=[bail_de_b.pk]))

        self.assertEqual(response.status_code, 404)


class NumeroDeBailTests(BailTestCase):
    def test_deux_organisations_peuvent_avoir_le_meme_numero(self):
        """Le numero etait unique pour toute la base : c'etait un blocage.

        Une agence ne pouvait pas nommer son bail BAIL-001 si une autre
        l'avait deja fait, alors que les deux ne se connaissent pas.
        """
        self.creer_bail(self.agence_a, self.unite_a, self.locataire_a, 'BAIL-001')
        self.creer_bail(self.agence_b, self.unite_b, self.locataire_b, 'BAIL-001')

        self.assertEqual(Lease.all_objects.filter(lease_number='BAIL-001').count(), 2)

    def test_le_numero_reste_unique_dans_une_meme_organisation(self):
        self.creer_bail(self.agence_a, self.unite_a, self.locataire_a, 'BAIL-001')

        with self.assertRaises(IntegrityError):
            self.creer_bail(self.agence_a, self.unite_a, self.locataire_a, 'BAIL-001')


class FormulaireDeBailTests(BailTestCase):
    def test_le_formulaire_n_offre_que_les_unites_de_l_organisation(self):
        with organization_context(self.agence_a):
            formulaire = LeaseForm(self.alice)
            unites = list(formulaire.fields['unit'].queryset)

        self.assertEqual(unites, [self.unite_a])

    def test_le_formulaire_n_expose_pas_les_locataires_des_voisins(self):
        """Le locataire de B est deja engage ailleurs : A ne doit pas le voir."""
        self.creer_bail(self.agence_b, self.unite_b, self.locataire_b)

        with organization_context(self.agence_a):
            formulaire = LeaseForm(self.alice)
            locataires = list(formulaire.fields['tenant'].queryset)

        self.assertNotIn(self.locataire_b, locataires)
        # Un locataire encore libre reste proposable, sans quoi aucun
        # premier bail ne pourrait etre cree.
        self.assertIn(self.locataire_a, locataires)
