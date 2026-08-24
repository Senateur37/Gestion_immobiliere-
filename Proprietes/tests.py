from django.test import TestCase
from django.urls import reverse

from Comptes.models import User

from .models import Property


class PropertyFrontendTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username='owner', password='password', role='owner')
		self.other_owner = User.objects.create_user(username='other', password='password', role='owner')
		self.client.force_login(self.owner)

	def property_data(self, name='Residence Premium'):
		return {
			'name': name,
			'address': '12 rue des Lilas',
			'city': 'Lyon',
			'postal_code': '69001',
			'country': 'France',
			'property_type': 'apartment',
			'total_area': '85.50',
			'year_built': '2020',
			'description': 'Fiche premium',
			'is_active': 'on',
		}

	def test_create_assigns_logged_in_owner(self):
		response = self.client.post(reverse('property_create'), self.property_data())

		self.assertRedirects(response, reverse('property_list'))
		property = Property.objects.get(name='Residence Premium')
		self.assertEqual(property.owner, self.owner)

	def test_other_owner_cannot_edit_property(self):
		property = Property.objects.create(owner=self.other_owner, **{
			key: value for key, value in self.property_data('Private Property').items()
			if key != 'is_active'
		})

		response = self.client.get(reverse('property_update', args=[property.pk]))

		self.assertEqual(response.status_code, 404)

	def test_list_search_filters_owned_properties(self):
		Property.objects.create(owner=self.owner, **{
			key: value for key, value in self.property_data().items()
			if key != 'is_active'
		})
		Property.objects.create(owner=self.other_owner, **{
			key: value for key, value in self.property_data('Other Residence').items()
			if key != 'is_active'
		})

		response = self.client.get(reverse('property_list'), {'q': 'Lyon'})

		self.assertContains(response, 'Residence Premium')
		self.assertNotContains(response, 'Other Residence')

	def test_unit_creation_only_offers_owned_properties(self):
		Property.objects.create(owner=self.owner, **{
			key: value for key, value in self.property_data().items()
			if key != 'is_active'
		})
		other_property = Property.objects.create(owner=self.other_owner, **{
			key: value for key, value in self.property_data('Other Residence').items()
			if key != 'is_active'
		})

		response = self.client.get(reverse('unit_create'))

		self.assertContains(response, 'Residence Premium')
		self.assertNotContains(response, f'value="{other_property.pk}"')
