from django.db import models
from django.conf import settings

class Plan(models.Model):
    """
    Définition des plans d'abonnement (Gratuit, Premium, Entreprise).
    """
    name = models.CharField(max_length=50, verbose_name="Nom du plan")
    stripe_price_id = models.CharField(max_length=150, blank=True, null=True, verbose_name="ID du prix Stripe")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (EUR)")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    features = models.JSONField(default=dict, blank=True, verbose_name="Fonctionnalités incluses")

    class Meta:
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"

    def __str__(self):
        return f"{self.name} - {self.price}€"

class UserSubscription(models.Model):
    """
    Liaison entre un utilisateur et son abonnement.
    """
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('past_due', 'En retard de paiement'),
        ('canceled', 'Annulé'),
        ('unpaid', 'Non payé'),
        ('trialing', 'En période d\'essai'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    stripe_customer_id = models.CharField(max_length=150, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='trialing')
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Abonnement utilisateur"
        verbose_name_plural = "Abonnements utilisateurs"

    def __str__(self):
        return f"Abonnement de {self.user.email} - {self.status}"
