"""Operations metier sur les organisations.

Une regle par fonction, une transaction par fonction. Les vues et les
vues API appellent ces services : elles ne manipulent pas les modeles
directement.
"""
from django.db import transaction

from core.exceptions import DomainError

from .models import Membership, Organization
from .tresorerie import synchroniser_permissions_tresorerie


@transaction.atomic
def create_organization(*, name, owner, kind='agency', **fields):
    """Cree une organisation et y installe son premier membre comme proprietaire.

    Une organisation sans membre serait inaccessible : la creation du
    membership fait partie de l'operation, pas de la responsabilite de
    l'appelant.
    """
    if not name or not name.strip():
        raise DomainError("Le nom de l'organisation est obligatoire.", code='name_required')

    organization = Organization.objects.create(name=name.strip(), kind=kind, **fields)
    add_member(
        organization=organization,
        user=owner,
        role=Membership.ROLE_OWNER,
        is_default=not owner.memberships.exists(),
    )
    return organization


@transaction.atomic
def add_member(*, organization, user, role=Membership.ROLE_AGENT, is_default=False):
    """Rattache un utilisateur a une organisation."""
    if Membership.objects.filter(organization=organization, user=user).exists():
        raise DomainError(
            f"{user} est deja membre de {organization}.",
            code='already_member',
        )

    if is_default:
        Membership.objects.filter(user=user, is_default=True).update(is_default=False)

    membership = Membership.objects.create(
        organization=organization,
        user=user,
        role=role,
        is_default=is_default,
    )
    # Un membre doit pouvoir travailler des son arrivee : ses permissions
    # de tresorerie decoulent de son role.
    synchroniser_permissions_tresorerie(membership)
    return membership


@transaction.atomic
def set_member_role(*, membership, role):
    """Change le role d'un membre.

    Une organisation doit garder au moins un proprietaire, sinon plus
    personne ne peut administrer ni facturer.
    """
    valid_roles = dict(Membership.ROLE_CHOICES)
    if role not in valid_roles:
        raise DomainError(f"Role inconnu : {role}.", code='invalid_role')

    if membership.role == Membership.ROLE_OWNER and role != Membership.ROLE_OWNER:
        remaining_owners = Membership.objects.filter(
            organization=membership.organization,
            role=Membership.ROLE_OWNER,
            is_active=True,
        ).exclude(pk=membership.pk).count()
        if remaining_owners == 0:
            raise DomainError(
                "Cette organisation doit conserver au moins un proprietaire.",
                code='last_owner',
            )

    membership.role = role
    membership.save(update_fields=['role', 'updated_at'])
    synchroniser_permissions_tresorerie(membership)
    return membership


@transaction.atomic
def remove_member(*, membership):
    """Retire un membre, en preservant la meme regle du dernier proprietaire."""
    if membership.role == Membership.ROLE_OWNER:
        remaining_owners = Membership.objects.filter(
            organization=membership.organization,
            role=Membership.ROLE_OWNER,
            is_active=True,
        ).exclude(pk=membership.pk).count()
        if remaining_owners == 0:
            raise DomainError(
                "Cette organisation doit conserver au moins un proprietaire.",
                code='last_owner',
            )
    membership.delete()
