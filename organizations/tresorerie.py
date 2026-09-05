"""Passerelle entre les roles d'organisation et les permissions de django-comptes.

Le module `comptes` protege ses services par des permissions Django. Sans
correspondance, un gestionnaire parfaitement legitime se voit refuser
l'encaissement d'un loyer.

On traduit donc le role porte par le Membership en permissions concretes,
au moment ou le membre est ajoute ou change de role. Le principe reste
celui du moindre privilege : un agent encaisse, il ne cloture pas.
"""
from django.contrib.auth.models import Permission

from .models import Membership

# Ce que chaque role peut faire sur les comptes financiers.
PERMISSIONS_PAR_ROLE = {
    Membership.ROLE_OWNER: ['encaisser', 'decaisser', 'transferer', 'annuler', 'cloturer', 'rapprocher'],
    Membership.ROLE_MANAGER: ['encaisser', 'decaisser', 'transferer', 'rapprocher'],
    Membership.ROLE_ACCOUNTANT: ['encaisser', 'decaisser', 'rapprocher', 'cloturer'],
    Membership.ROLE_AGENT: ['encaisser'],
}


def synchroniser_permissions_tresorerie(membership):
    """Aligne les permissions de tresorerie d'un membre sur son role.

    Sans effet si django-comptes n'est pas installe : le projet doit
    rester demontable.
    """
    codenames = PERMISSIONS_PAR_ROLE.get(membership.role, [])
    if not codenames:
        return []

    try:
        permissions = list(
            Permission.objects.filter(
                codename__in=codenames,
                content_type__app_label='comptes',
            )
        )
    except Exception:
        return []

    if permissions:
        membership.user.user_permissions.add(*permissions)
    return permissions
