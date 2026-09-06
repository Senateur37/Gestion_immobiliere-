"""Permissions DRF adossees au membership."""
from rest_framework.permissions import BasePermission

from organizations.models import Membership

from .middleware import activate_organization


class IsOrganizationMember(BasePermission):
    """Exige un membership actif sur l'organisation resolue.

    C'est ici que le perimetre est reellement installe pour l'API : a ce
    stade DRF a authentifie le jeton, ce qui n'etait pas le cas quand le
    middleware s'est execute.
    """

    message = "Vous devez appartenir a une organisation pour acceder a cette ressource."

    def has_permission(self, request, view):
        return activate_organization(request) is not None


class HasOrganizationRole(IsOrganizationMember):
    """Exige un role minimum, selon la hierarchie definie par Membership.

    S'utilise en fixant `required_role` sur la vue.
    """

    message = "Votre role dans cette organisation ne permet pas cette action."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        required = getattr(view, 'required_role', None)
        if required is None:
            return True
        return request.membership.has_at_least(required)


class IsOrganizationOwner(IsOrganizationMember):
    """Reserve aux proprietaires de l'organisation."""

    message = "Cette action est reservee aux proprietaires de l'organisation."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.membership.has_at_least(Membership.ROLE_OWNER)
