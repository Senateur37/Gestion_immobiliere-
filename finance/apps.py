from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'
    verbose_name = 'Finance'

    def ready(self):
        # Enregistre les abonnements aux evenements du domaine.
        from . import handlers  # noqa: F401
