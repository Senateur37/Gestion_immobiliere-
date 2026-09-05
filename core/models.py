"""Modeles abstraits du socle."""
from django.db import models

from .managers import AllObjectsManager, TenantManager
from .tenancy import get_current_organization_id


class TimeStampedModel(models.Model):
    """Horodatage de creation et de mise a jour."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Cree le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Mis a jour le')

    class Meta:
        abstract = True


class TenantOwnedModel(TimeStampedModel):
    """Modele appartenant a une organisation.

    Tout modele metier du SaaS herite de celui-ci. Il apporte trois choses :
    la cle etrangere vers l'organisation, le manager filtrant, et le
    remplissage automatique de l'organisation a la creation.
    """

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name='Organisation',
    )

    # L'ordre compte : le premier manager declare devient le manager par
    # defaut, celui qu'utilisent les relations et l'administration.
    objects = TenantManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Une creation depuis une vue n'a pas a repeter l'organisation :
        # on la prend dans le contexte. Un objet cree sans contexte et
        # sans organisation explicite echouera a la validation de la base,
        # ce qui est le comportement souhaite.
        if self.organization_id is None:
            org_id = get_current_organization_id()
            if org_id is not None:
                self.organization_id = org_id
        return super().save(*args, **kwargs)
