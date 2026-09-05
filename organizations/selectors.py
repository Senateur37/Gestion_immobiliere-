"""Lectures sur les organisations.

Les selectors repondent aux questions ("quelles organisations pour cet
utilisateur ?"), les services agissent ("cree cette organisation").
Separer les deux evite le fourre-tout qu'etait Comptabilite/views.py.
"""
from .models import Membership


def memberships_for_user(user):
    """Memberships actifs d'un utilisateur, organisation prechargee."""
    if not user or not user.is_authenticated:
        return Membership.objects.none()
    return (
        Membership.objects
        .filter(user=user, is_active=True, organization__is_active=True)
        .select_related('organization')
        .order_by('-is_default', 'organization__name')
    )


def default_membership_for_user(user):
    """Membership a ouvrir par defaut, ou None."""
    return memberships_for_user(user).first()


def resolve_membership_for_request(request):
    """Determine le membership actif pour une requete.

    Si le client demande une organisation precise, on ne la lui accorde
    que s'il en est reellement membre : l'en-tete est une preference, pas
    une autorisation.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return None

    memberships = memberships_for_user(user)
    requested = request.META.get('HTTP_X_ORGANIZATION')
    if requested:
        membership = memberships.filter(organization__slug=requested).first()
        if membership is not None:
            return membership
        # Organisation demandee mais non autorisee : on ne bascule pas
        # silencieusement sur une autre, on refuse le perimetre.
        return None

    return memberships.first()
