"""Tests du patrimoine, desormais cloisonne par organisation.

L'intention des tests d'origine est conservee — un tiers ne doit voir ni
modifier le patrimoine d'autrui — mais le cloisonnement ne passe plus par
le proprietaire : il passe par l'organisation.
"""
from django.test import TestCase
from django.urls import reverse

from Comptes.models import User
from core.tenancy import organization_context
from organizations.services import create_organization

from .models import Property, Unit


class PatrimoineTestCase(TestCase):
    """Deux organisations distinctes, chacune avec son bien."""

    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password', role='owner')
        self.bob = User.objects.create_user(username='bob', password='password', role='owner')

        self.agence_a = create_organization(name='Agence A', owner=self.alice)
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

        self.client.force_login(self.alice)

    def property_data(self, name='Residence Premium', city='Bamako'):
        return {
            'name': name,
            'address': '12 rue des Lilas',
            'city': city,
            'postal_code': '69001',
            'country': 'Mali',
            'property_type': 'apartment',
            'total_area': '85.50',
            'year_built': '2020',
            'description': 'Fiche premium',
            'is_active': 'on',
        }

    def creer_bien(self, organization, name='Residence Premium', city='Bamako', owner=None):
        """Cree un bien dans une organisation donnee."""
        champs = {k: v for k, v in self.property_data(name, city).items() if k != 'is_active'}
        with organization_context(organization):
            return Property.objects.create(owner=owner, **champs)


class PropertyViewTests(PatrimoineTestCase):
    def test_creation_rattache_le_bien_a_l_organisation_active(self):
        response = self.client.post(reverse('property_create'), self.property_data())

        self.assertRedirects(response, reverse('property_list'))
        bien = Property.all_objects.get(name='Residence Premium')
        self.assertEqual(bien.organization, self.agence_a)
        self.assertEqual(bien.owner, self.alice)

    def test_une_autre_organisation_ne_peut_pas_modifier_le_bien(self):
        bien = self.creer_bien(self.agence_b, name='Bien prive', owner=self.bob)

        response = self.client.get(reverse('property_update', args=[bien.pk]))

        self.assertEqual(response.status_code, 404)

    def test_une_autre_organisation_ne_peut_pas_supprimer_le_bien(self):
        bien = self.creer_bien(self.agence_b, name='Bien prive', owner=self.bob)

        response = self.client.post(reverse('property_delete', args=[bien.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Property.all_objects.filter(pk=bien.pk).exists())

    def test_la_liste_ne_montre_que_le_patrimoine_de_l_organisation(self):
        self.creer_bien(self.agence_a, name='Residence Premium')
        self.creer_bien(self.agence_b, name='Residence Voisine')

        response = self.client.get(reverse('property_list'))

        self.assertContains(response, 'Residence Premium')
        self.assertNotContains(response, 'Residence Voisine')

    def test_la_recherche_reste_cloisonnee(self):
        self.creer_bien(self.agence_a, name='Residence Premium', city='Bamako')
        self.creer_bien(self.agence_b, name='Residence Voisine', city='Bamako')

        response = self.client.get(reverse('property_list'), {'q': 'Bamako'})

        self.assertContains(response, 'Residence Premium')
        self.assertNotContains(response, 'Residence Voisine')


class UnitFormTests(PatrimoineTestCase):
    def test_le_formulaire_d_unite_n_offre_que_les_biens_de_l_organisation(self):
        self.creer_bien(self.agence_a, name='Residence Premium')
        bien_voisin = self.creer_bien(self.agence_b, name='Residence Voisine')

        response = self.client.get(reverse('unit_create'))

        self.assertContains(response, 'Residence Premium')
        self.assertNotContains(response, f'value="{bien_voisin.pk}"')

    def test_l_unite_herite_de_l_organisation_de_la_requete(self):
        bien = self.creer_bien(self.agence_a)

        response = self.client.post(reverse('unit_create'), {
            'property': bien.pk,
            'unit_number': 'A-101',
            'floor': '1',
            'rooms': '3',
            'bedrooms': '2',
            'bathrooms': '1',
            'area': '65.00',
            'rent_amount': '150000',
            'deposit_amount': '300000',
            'status': 'available',
            'description': '',
        })

        self.assertRedirects(response, reverse('unit_list'))
        unite = Unit.all_objects.get(unit_number='A-101')
        self.assertEqual(unite.organization, self.agence_a)


class IsolationDuPatrimoineTests(PatrimoineTestCase):
    """Verifications au niveau de l'ORM, independamment des vues."""

    def test_chaque_organisation_ne_voit_que_ses_biens(self):
        self.creer_bien(self.agence_a, name='Bien de A')
        self.creer_bien(self.agence_b, name='Bien de B')

        with organization_context(self.agence_a):
            self.assertEqual([p.name for p in Property.objects.all()], ['Bien de A'])
        with organization_context(self.agence_b):
            self.assertEqual([p.name for p in Property.objects.all()], ['Bien de B'])

    def test_un_identifiant_devine_ne_donne_pas_acces(self):
        bien_de_b = self.creer_bien(self.agence_b, name='Bien de B')

        with organization_context(self.agence_a):
            with self.assertRaises(Property.DoesNotExist):
                Property.objects.get(pk=bien_de_b.pk)

    def test_owner_ne_cloisonne_plus(self):
        """Alice possede un bien range dans l'organisation de Bob.

        Elle ne doit pas y acceder depuis son organisation : c'est
        l'organisation qui decide, plus le proprietaire.
        """
        bien = self.creer_bien(self.agence_b, name='Bien de Bob', owner=self.alice)

        with organization_context(self.agence_a):
            self.assertFalse(Property.objects.filter(pk=bien.pk).exists())
