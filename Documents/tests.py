from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from Comptes.models import User

from .models import Document


class DocumentFrontendTests(TestCase):
	def test_upload_stores_file_metadata(self):
		user = User.objects.create_user(username='owner', password='password', role='owner')
		self.client.force_login(user)
		uploaded_file = SimpleUploadedFile('bail.txt', b'contenu du bail', content_type='text/plain')

		response = self.client.post(reverse('document_create'), {
			'title': 'Bail signe',
			'category': 'lease',
			'file': uploaded_file,
			'description': 'Contrat principal',
			'is_signed': 'on',
		})

		self.assertRedirects(response, reverse('document_list'))
		document = Document.objects.get(title='Bail signe')
		self.assertEqual(document.owner, user)
		self.assertEqual(document.file_size, len(b'contenu du bail'))
		self.assertEqual(document.mime_type, 'text/plain')
