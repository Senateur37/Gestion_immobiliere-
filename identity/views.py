"""Vues API d'authentification et de profil."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.middleware import activate_organization
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from organizations.selectors import memberships_for_user

from .serializers import CurrentUserSerializer, ImmoPilotTokenSerializer, MembershipSerializer


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — echange identifiants contre un couple de jetons."""

    serializer_class = ImmoPilotTokenSerializer


class CurrentUserView(APIView):
    """GET /api/v1/auth/me/ — qui suis-je, et ou puis-je travailler."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class MyOrganizationsView(APIView):
    """GET /api/v1/auth/organizations/ — organisations accessibles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Resolution explicite : cette vue n'exige pas d'organisation (un
        # utilisateur fraichement invite n'en a aucune), mais elle doit
        # savoir laquelle est active pour le dire au front.
        activate_organization(request)
        memberships = memberships_for_user(request.user)
        return Response({
            'active': request.organization.slug if request.organization else None,
            'results': MembershipSerializer(memberships, many=True).data,
        })
