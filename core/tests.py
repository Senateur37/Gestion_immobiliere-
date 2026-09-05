"""Tests du mecanisme d'isolation.

L'isolation est la promesse centrale de la refonte : on la verifie sur un
modele reel, en essayant de la contourner.
"""
from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TestCase, TransactionTestCase
from django.test.utils import isolate_apps

from organizations.models import Organization

from .exceptions import NoActiveOrganization
from .models import TenantOwnedModel
from .tenancy import organization_context, unscoped

User = get_user_model()


@isolate_apps('core')
class TenantManagerTests(TransactionTestCase):
    """Verifie que le filtrage par organisation ne peut pas etre oublie.

    On declare un modele concret heritant de TenantOwnedModel et on cree
    sa table : c'est le comportement reel de l'ORM qui est teste, pas une
    simulation.
    """

    # TransactionTestCase : SQLite refuse de modifier le schema a
    # l'interieur de la transaction qu'ouvrirait un TestCase classique.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class Widget(TenantOwnedModel):
            label = models.CharField(max_length=50)

            class Meta:
                app_label = 'core'

        cls.Widget = Widget

    def setUp(self):
        with connection.schema_editor() as editor:
            editor.create_model(self.Widget)
        self.addCleanup(self._drop_table)
        self.org_a = Organization.objects.create(name='Agence A', slug='agence-a')
        self.org_b = Organization.objects.create(name='Agence B', slug='agence-b')
        self.Widget.all_objects.create(organization=self.org_a, label='bien de A')
        self.Widget.all_objects.create(organization=self.org_b, label='bien de B')

    def _drop_table(self):
        with connection.schema_editor() as editor:
            editor.delete_model(self.Widget)

    def test_sans_contexte_la_requete_echoue_bruyamment(self):
        """Le pire scenario serait de tout retourner : on leve une erreur."""
        with self.assertRaises(NoActiveOrganization):
            list(self.Widget.objects.all())

    def test_le_contexte_limite_a_son_organisation(self):
        with organization_context(self.org_a):
            labels = [w.label for w in self.Widget.objects.all()]
        self.assertEqual(labels, ['bien de A'])

    def test_une_organisation_ne_voit_pas_les_objets_de_l_autre(self):
        with organization_context(self.org_b):
            self.assertEqual(self.Widget.objects.count(), 1)
            self.assertFalse(self.Widget.objects.filter(label='bien de A').exists())

    def test_acces_direct_par_identifiant_bloque(self):
        """Deviner un identifiant ne doit pas suffire a lire l'objet."""
        widget_de_a = self.Widget.all_objects.get(label='bien de A')
        with organization_context(self.org_b):
            with self.assertRaises(self.Widget.DoesNotExist):
                self.Widget.objects.get(pk=widget_de_a.pk)

    def test_organisation_remplie_automatiquement_a_la_creation(self):
        with organization_context(self.org_a):
            widget = self.Widget.objects.create(label='nouveau')
        self.assertEqual(widget.organization_id, self.org_a.pk)

    def test_all_objects_traverse_les_organisations(self):
        self.assertEqual(self.Widget.all_objects.count(), 2)

    def test_unscoped_leve_le_filtre_explicitement(self):
        with unscoped():
            self.assertEqual(self.Widget.objects.count(), 2)

    def test_le_filtre_revient_apres_unscoped(self):
        with unscoped():
            pass
        with self.assertRaises(NoActiveOrganization):
            list(self.Widget.objects.all())

    def test_le_filtre_survit_a_un_filter_explicite(self):
        """Meme en filtrant sur autre chose, le perimetre reste applique."""
        with organization_context(self.org_a):
            resultats = self.Widget.objects.filter(label__icontains='bien')
            self.assertEqual([w.label for w in resultats], ['bien de A'])


class RequestScopeTests(TestCase):
    """Le perimetre d'une requete ne doit pas survivre a sa reponse."""

    def setUp(self):
        self.org = Organization.objects.create(name='Agence A', slug='agence-a')
        self.user = User.objects.create_user('alice', password='x')

    def test_le_contexte_ne_fuit_pas_d_une_requete_a_la_suivante(self):
        from core.middleware import OrganizationMiddleware
        from core.tenancy import get_current_organization_id
        from organizations.services import add_member

        add_member(organization=self.org, user=self.user)

        vu = {}

        def vue(request):
            vu['organisation'] = get_current_organization_id()
            return 'ok'

        middleware = OrganizationMiddleware(vue)

        class FausseRequete:
            pass

        premiere = FausseRequete()
        premiere.user = self.user
        premiere.META = {}
        middleware(premiere)
        self.assertEqual(vu['organisation'], self.org.pk)

        # Deuxieme requete, utilisateur anonyme : elle ne doit rien
        # heriter de la premiere.
        class Anonyme:
            is_authenticated = False

        seconde = FausseRequete()
        seconde.user = Anonyme()
        seconde.META = {}
        middleware(seconde)
        self.assertIsNone(vu['organisation'])

    def test_le_contexte_est_vide_apres_la_reponse(self):
        from core.middleware import OrganizationMiddleware
        from core.tenancy import get_current_organization_id
        from organizations.services import add_member

        add_member(organization=self.org, user=self.user)
        middleware = OrganizationMiddleware(lambda request: 'ok')

        class FausseRequete:
            pass

        requete = FausseRequete()
        requete.user = self.user
        requete.META = {}
        middleware(requete)

        self.assertIsNone(get_current_organization_id())


class FormulairesTenantTests(TestCase):
    """Aucun formulaire ne doit laisser choisir son organisation.

    On verifie le contrat plutot qu'une liste de formulaires connus : les
    formulaires ecrits demain sont couverts aussi.
    """

    def test_tout_formulaire_sur_un_modele_tenant_herite_de_TenantModelForm(self):
        import importlib
        import inspect

        from django.apps import apps as django_apps
        from django.forms import ModelForm

        from .forms import TenantModelForm
        from .models import TenantOwnedModel

        fautifs = []
        for config in django_apps.get_app_configs():
            try:
                module = importlib.import_module(f'{config.name}.forms')
            except ModuleNotFoundError:
                continue

            for _, objet in inspect.getmembers(module, inspect.isclass):
                if not issubclass(objet, ModelForm) or objet in (ModelForm, TenantModelForm):
                    continue
                if objet.__module__ != module.__name__:
                    continue
                modele = getattr(getattr(objet, '_meta', None), 'model', None)
                if modele is None or not issubclass(modele, TenantOwnedModel):
                    continue
                expose = 'organization' in (objet._meta.fields or []) or (
                    objet._meta.exclude is not None
                    and 'organization' not in objet._meta.exclude
                    and not issubclass(objet, TenantModelForm)
                )
                if expose:
                    fautifs.append(f'{module.__name__}.{objet.__name__}')

        self.assertEqual(
            fautifs, [],
            "Ces formulaires peuvent exposer le champ organisation : "
            "faites-les heriter de core.forms.TenantModelForm.",
        )
