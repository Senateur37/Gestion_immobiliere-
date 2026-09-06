"""Serialiseurs d'identite et d'authentification."""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from organizations.selectors import memberships_for_user

User = get_user_model()


class OrganizationSummarySerializer(serializers.Serializer):
    """Organisation telle que la voit un membre."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    kind = serializers.CharField(read_only=True)
    currency = serializers.CharField(read_only=True)
    primary_color = serializers.CharField(read_only=True)


class MembershipSerializer(serializers.Serializer):
    """Appartenance a une organisation, avec le role."""

    organization = OrganizationSummarySerializer(read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_default = serializers.BooleanField(read_only=True)


class CurrentUserSerializer(serializers.ModelSerializer):
    """Profil renvoye par /api/v1/auth/me/.

    Le front a besoin, en une requete, de savoir qui est connecte et sur
    quelles organisations il peut travailler.
    """

    memberships = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'memberships']
        read_only_fields = fields

    def get_full_name(self, user):
        return user.get_full_name() or user.username

    def get_memberships(self, user):
        return MembershipSerializer(memberships_for_user(user), many=True).data


class ImmoPilotTokenSerializer(TokenObtainPairSerializer):
    """Jeton JWT portant l'organisation par defaut.

    Sans cela, le front devrait faire un second appel avant de pouvoir
    afficher quoi que ce soit.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        membership = memberships_for_user(user).first()
        if membership is not None:
            token['organization_id'] = membership.organization_id
            token['organization_slug'] = membership.organization.slug
            token['role'] = membership.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = CurrentUserSerializer(self.user).data
        return data
