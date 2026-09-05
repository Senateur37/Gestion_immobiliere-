"""L'organisation est le tenant du SaaS.

Le projet reposait sur `Property.owner = User` : un utilisateur possedait
des biens. Ce modele ne sait pas representer une agence dont plusieurs
employes gerent le portefeuille de plusieurs proprietaires. L'organisation
prend donc la place du tenant, et l'utilisateur y accede par un membership.
"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class Organization(TimeStampedModel):
    """Une agence, une regie, ou un proprietaire exploitant en direct."""

    KIND_CHOICES = [
        ('agency', 'Agence immobiliere'),
        ('owner', 'Proprietaire independant'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Identifiant")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='agency', verbose_name="Type")

    # Reglages qui appartenaient au singleton SiteSettings : dans un SaaS,
    # chaque organisation a sa marque.
    logo = models.ImageField(upload_to='organizations/logos/', null=True, blank=True, verbose_name="Logo")
    primary_color = models.CharField(max_length=20, default='#0ea5e9', verbose_name="Couleur principale")

    # Le projet affichait des FCFA tout en fixant "France" par defaut.
    # La devise et le pays deviennent des choix de l'organisation.
    currency = models.CharField(max_length=3, default='XOF', verbose_name="Devise")
    country = models.CharField(max_length=100, default='Mali', verbose_name="Pays")

    is_active = models.BooleanField(default=True, verbose_name="Active")

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        related_name='organizations',
        verbose_name="Membres",
    )

    class Meta:
        db_table = 'organizations_organization'
        ordering = ['name']
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:220]
        return super().save(*args, **kwargs)


class Membership(TimeStampedModel):
    """Rattachement d'un utilisateur a une organisation, avec son role.

    Remplace `User.role`, qui n'autorisait qu'un seul role global : une
    personne peut desormais etre comptable dans une agence et
    proprietaire dans une autre.
    """

    ROLE_OWNER = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_AGENT = 'agent'
    ROLE_ACCOUNTANT = 'accountant'

    ROLE_CHOICES = [
        (ROLE_OWNER, 'Proprietaire'),
        (ROLE_MANAGER, 'Gestionnaire'),
        (ROLE_AGENT, 'Agent'),
        (ROLE_ACCOUNTANT, 'Comptable'),
    ]

    # Hierarchie utilisee par les permissions : un role donne accede a tout
    # ce qu'autorisent les roles de rang inferieur.
    ROLE_RANK = {
        ROLE_OWNER: 40,
        ROLE_MANAGER: 30,
        ROLE_ACCOUNTANT: 20,
        ROLE_AGENT: 10,
    }

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Organisation",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Utilisateur",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_AGENT, verbose_name="Role")
    is_default = models.BooleanField(
        default=False,
        verbose_name="Organisation par defaut",
        help_text="Organisation ouverte a la connexion si l'utilisateur en a plusieurs.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'organizations_membership'
        unique_together = [['organization', 'user']]
        ordering = ['organization__name', 'user__username']
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user} — {self.get_role_display()} chez {self.organization}'

    @property
    def rank(self):
        return self.ROLE_RANK.get(self.role, 0)

    def has_at_least(self, role):
        """Vrai si ce membership vaut au moins le role demande."""
        return self.rank >= self.ROLE_RANK.get(role, 0)
