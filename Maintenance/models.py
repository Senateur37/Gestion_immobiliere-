# apps/maintenance/models.py
from django.db import models
from django.conf import settings
from Proprietes.models import Unit

class MaintenanceRequest(models.Model):
    """Demande de maintenance"""
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Soumise'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ]
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests'
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='maintenance_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    category = models.CharField(
        max_length=100,
        choices=[
            ('plumbing', 'Plomberie'),
            ('electrical', 'Électricité'),
            ('heating', 'Chauffage'),
            ('appliances', 'Électroménager'),
            ('structural', 'Structurel'),
            ('other', 'Autre'),
        ],
        default='other'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_maintenance',
        limit_choices_to={'role': 'agent'}
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'maintenance_maintenancerequest'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['unit', 'status']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f"Demande #{self.id} - {self.title}"


class MaintenanceAttachment(models.Model):
    """Photos/documents joints aux demandes"""
    request = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='maintenance/attachments/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'maintenance_maintenanceattachment'