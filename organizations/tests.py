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
