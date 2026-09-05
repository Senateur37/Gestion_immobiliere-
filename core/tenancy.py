"""Contexte d'organisation courant.

Le peril d'un SaaS multi-tenant, c'est la requete qui oublie de filtrer.
On ne compte donc pas sur la discipline de l'appelant : l'organisation
active est portee par le contexte d'execution, et les managers de
core.managers s'en servent pour filtrer d'office.

Un ContextVar (et non une variable globale) parce qu'il est isole par
thread ET par tache asynchrone : deux requetes simultanees ne peuvent pas
se voler leur organisation.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from .exceptions import NoActiveOrganization

_current_organization_id: ContextVar = ContextVar('current_organization_id', default=None)

# Sortie de secours explicite, pour les taches d'administration qui doivent
# legitimement voir toutes les organisations (commandes de gestion, cron).
# Nommee sans ambiguite : on doit pouvoir la reperer en relisant un diff.
_tenancy_disabled: ContextVar = ContextVar('tenancy_disabled', default=False)


def set_current_organization(organization):
    """Definit l'organisation active. Accepte une instance ou un identifiant."""
    org_id = getattr(organization, 'pk', organization)
    return _current_organization_id.set(org_id)


def get_current_organization_id():
    """Identifiant de l'organisation active, ou None."""
    return _current_organization_id.get()


def require_current_organization_id():
    """Identifiant de l'organisation active, ou lever une erreur.

    Utilise par les managers : mieux vaut une exception bruyante qu'une
    requete qui retourne silencieusement les donnees de tout le monde.
    """
    org_id = _current_organization_id.get()
    if org_id is None:
        raise NoActiveOrganization(
            "Aucune organisation active. Utilisez organization_context(...) ou "
            "unscoped() si l'acces inter-organisations est intentionnel."
        )
    return org_id


def is_tenancy_disabled():
    return _tenancy_disabled.get()


@contextmanager
def organization_context(organization):
    """Execute un bloc dans le perimetre d'une organisation."""
    token = set_current_organization(organization)
    try:
        yield
    finally:
        _current_organization_id.reset(token)


@contextmanager
def request_scope():
    """Isole le contexte d'organisation d'une requete.

    Sans cette remise a zero, l'organisation posee par une requete
    resterait visible pour la suivante servie par le meme worker ou le
    meme thread : une requete sans organisation heriterait du perimetre
    de la precedente. C'est une fuite inter-tenant, pas seulement une
    impurete de test.
    """
    token = _current_organization_id.set(None)
    try:
        yield
    finally:
        _current_organization_id.reset(token)


@contextmanager
def unscoped():
    """Desactive le filtrage par organisation pour un bloc.

    A n'utiliser que pour l'administration et les taches systeme. Tout
    appel a ce gestionnaire dans du code de vue doit etre considere
    comme un bug.
    """
    token = _tenancy_disabled.set(True)
    try:
        yield
    finally:
        _tenancy_disabled.reset(token)
