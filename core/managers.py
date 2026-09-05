"""Managers filtrant d'office sur l'organisation active."""
from django.db import models

from .tenancy import get_current_organization_id, is_tenancy_disabled, require_current_organization_id


class TenantQuerySet(models.QuerySet):
    """QuerySet conscient de l'organisation active."""

    def for_organization(self, organization):
        org_id = getattr(organization, 'pk', organization)
        return self.filter(organization_id=org_id)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """Manager par defaut des modeles rattaches a une organisation.

    get_queryset() applique le filtre systematiquement. Une vue qui
    oublie de filtrer ne fuit donc pas : elle ne voit que l'organisation
    active, ou leve NoActiveOrganization s'il n'y en a pas.

    C'est le point central de l'isolation : elle ne depend plus de ce que
    chaque developpeur pense a ecrire dans chaque vue.
    """

    # Django utilise ce manager pour les relations inverses et les
    # operations internes ; le filtrage doit s'y appliquer aussi.
    use_for_related_fields = True

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_tenancy_disabled():
            return queryset
        return queryset.filter(organization_id=require_current_organization_id())


class AllObjectsManager(models.Manager.from_queryset(TenantQuerySet)):
    """Manager non filtre, expose sous le nom `all_objects`.

    Reserve a l'administration, aux migrations et aux taches systeme.
    Son nom est volontairement explicite pour qu'un appel a
    `Model.all_objects` saute aux yeux en relecture de code.
    """

    def get_queryset(self):
        return super().get_queryset()
