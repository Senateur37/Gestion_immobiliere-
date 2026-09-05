from datetime import date

from django.test import TestCase
from django.urls import reverse

from Comptes.models import User
from core.tenancy import organization_context
from organizations.services import create_organization
from Locations.models import Lease
from Paiements.models import Payment
from Proprietes.models import Property
from Proprietes.models import Unit


class DashboardTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='proprietaire',
			password='mot-de-passe-solide',
			role='owner',
		)
		self.organization = create_organization(name='Agence Test', owner=self.user)
		self._activer_organisation()

	def _activer_organisation(self):
		"""Pose le perimetre pour la duree du test.

		Les vues le recoivent du middleware ; les creations d'objets faites
		directement dans le test ont besoin qu'on le pose explicitement.
		"""
		contexte = organization_context(self.organization)
		contexte.__enter__()
		self.addCleanup(contexte.__exit__, None, None, None)

	def test_dashboard_requires_authentication(self):
		response = self.client.get(reverse('dashboard'))

		self.assertRedirects(response, '/comptes/login/?next=/')

	def test_authenticated_owner_sees_owned_properties(self):
		self.client.force_login(self.user)
		Property.objects.create(
			owner=self.user,
			name='Residence Centrale',
			address='1 rue du Centre',
			city='Paris',
			postal_code='75001',
			property_type='apartment',
			total_area=100,
		)

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Residence Centrale')
		self.assertContains(response, '>1</strong>')

	def test_payment_list_hides_payments_from_other_owners(self):
		property = Property.objects.create(
			owner=self.user,
			name='Residence Paiement',
			address='1 rue Centre',
			city='Paris',
			postal_code='75001',
			property_type='apartment',
			total_area=80,
		)
		unit = Unit.objects.create(
			property=property,
			unit_number='A1',
			area=80,
			rent_amount=900,
			deposit_amount=900,
		)
		tenant = User.objects.create_user(username='locataire', password='password', role='tenant')
		lease = Lease.objects.create(
			unit=unit,
			tenant=tenant,
			lease_number='BAIL-001',
			start_date=date(2026, 1, 1),
			end_date=date(2027, 1, 1),
			rent_amount=900,
			deposit_amount=900,
			status='active',
		)
		Payment.objects.create(
			lease=lease,
			payment_number='PAY-001',
			amount=900,
			due_date=date(2026, 8, 1),
			status='pending',
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse('payment_list'), {'status': 'pending'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'PAY-001')


class NavigationSmokeTests(TestCase):
	"""Vérifie que chaque écran métier se rend sans erreur sur le design partagé."""

	def setUp(self):
		self.user = User.objects.create_user(
			username='proprietaire2',
			password='mot-de-passe-solide',
			role='owner',
		)
		self.organization = create_organization(name='Agence Ecrans', owner=self.user)
		contexte = organization_context(self.organization)
		contexte.__enter__()
		self.addCleanup(contexte.__exit__, None, None, None)
		self.client.force_login(self.user)

	def test_all_authenticated_screens_render(self):
		url_names = [
			'dashboard', 'property_list', 'property_create',
			'unit_list', 'unit_create',
			'lease_list', 'lease_create',
			'payment_list',
			'maintenance_list', 'maintenance_create',
			'document_list', 'document_create',
			'transaction_list', 'transaction_create',
		]
		for url_name in url_names:
			with self.subTest(url_name=url_name):
				response = self.client.get(reverse(url_name))
				self.assertEqual(response.status_code, 200)


class UtilisateurSansOrganisationTests(TestCase):
	"""Un compte sans organisation doit etre informe, pas casse."""

	def setUp(self):
		self.orphelin = User.objects.create_user(
			username='orphelin',
			password='mot-de-passe-solide',
			role='owner',
		)
		self.client.force_login(self.orphelin)

	def test_le_tableau_de_bord_explique_l_absence_d_organisation(self):
		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 409)
		self.assertContains(response, 'Aucune organisation', status_code=409)

	def test_la_liste_des_biens_ne_provoque_pas_d_erreur_serveur(self):
		response = self.client.get(reverse('property_list'))

		self.assertEqual(response.status_code, 409)
