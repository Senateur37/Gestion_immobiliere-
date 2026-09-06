"""Adaptation des erreurs metier a l'API."""
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import DomainError, NoActiveOrganization


def exception_handler(exc, context):
    """Traduit les exceptions du socle en reponses HTTP lisibles.

    Sans cela, une DomainError remonterait en 500 alors qu'il s'agit
    d'une regle metier que le client peut corriger.
    """
    if isinstance(exc, NoActiveOrganization):
        return Response(
            {'detail': str(exc), 'code': 'no_active_organization'},
            status=409,
        )

    if isinstance(exc, DomainError):
        return Response(
            {'detail': exc.message, 'code': exc.code},
            status=400,
        )

    return drf_exception_handler(exc, context)
