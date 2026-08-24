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