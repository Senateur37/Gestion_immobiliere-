# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Utilisateur personnalisé avec rôles"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('owner', 'Propriétaire'),
        ('tenant', 'Locataire'),
        ('agent', 'Agent immobilier'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounts_user'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class SiteSettings(models.Model):
    """Configuration globale de l'application (Singleton)"""
    app_name = models.CharField(max_length=100, default='ImmoPilot', verbose_name='Nom de l\'application')
    logo = models.ImageField(upload_to='settings/', null=True, blank=True, verbose_name='Logo de l\'application')
    primary_color = models.CharField(max_length=20, default='#0ea5e9', verbose_name='Couleur principale')

    class Meta:
        verbose_name = 'Paramètre du site'
        verbose_name_plural = 'Paramètres du site'

    def __str__(self):
        return self.app_name

    def save(self, *args, **kwargs):
        # Assurer qu'une seule instance existe (Singleton)
        if not self.pk and SiteSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj