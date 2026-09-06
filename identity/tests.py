"""Tests de l'API d'authentification."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from organizations.services import create_organization

User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='motdepasse123')
        self.bob = User.objects.create_user('bob', password='motdepasse123')
        self.agence_a = create_organization(name='Agence A', owner=self.alice)
        self.agence_b = create_organization(name='Agence B', owner=self.bob)

    def _login(self, username='alice', password='motdepasse123'):
        response = self.client.post(
            reverse('api-v1:login'),
            {'username': username, 'password': password},
            format='json',
        )
        return response

    def test_connexion_renvoie_les_deux_jetons_et_le_profil(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'alice')

    def test_mauvais_mot_de_passe_refuse(self):
        response = self._login(password='faux')
        self.assertEqual(response.status_code, 401)

    def test_profil_inaccessible_sans_jeton(self):
        response = self.client.get(reverse('api-v1:me'))
        self.assertEqual(response.status_code, 401)

    def test_profil_liste_les_organisations_du_membre(self):
        token = self._login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('api-v1:me'))
        self.assertEqual(response.status_code, 200)
        slugs = [m['organization']['slug'] for m in response.data['memberships']]
        self.assertEqual(slugs, ['agence-a'])

    def test_organisation_active_resolue_pour_une_requete_api(self):
        """Regression : le middleware s'execute avant l'authentification DRF.

        La resolution doit donc etre refaite dans la vue, sans quoi
        l'organisation active est systematiquement nulle en API.
        """
        token = self._login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('api-v1:organizations'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['active'], 'agence-a')

    def test_en_tete_vers_une_organisation_non_autorisee_ne_donne_aucun_perimetre(self):
        """Alice reclame l'agence de Bob : refus, sans repli silencieux."""
        token = self._login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('api-v1:organizations'), HTTP_X_ORGANIZATION='agence-b')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['active'])

    def test_le_jeton_porte_l_organisation_et_le_role(self):
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken(self._login().data['access'])
        self.assertEqual(token['organization_slug'], 'agence-a')
        self.assertEqual(token['role'], 'owner')

    def test_rafraichissement_du_jeton(self):
        refresh = self._login().data['refresh']
        response = self.client.post(reverse('api-v1:refresh'), {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
