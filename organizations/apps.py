from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
    verbose_name = 'Organisations'

    def ready(self):
        # Les modeles des modules metier se rattachent a l'organisation
        # active des leur enregistrement, sans reprise ulterieure.
        from .rattachement import connecter
        connecter()
