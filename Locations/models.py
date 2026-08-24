# apps/leases/models.py
from django.db import models
from django.conf import settings
from Proprietes.models import Unit

class Lease(models.Model):
    """Contrat de location (bail)"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('terminated', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='leases'
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='leases',
        limit_choices_to={'role': 'tenant'}
    )
    lease_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de bail")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    notice_period_days = models.IntegerField(default=90, help_text="Délai de préavis en jours", verbose_name="Délai de préavis (jours)")
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du loyer")
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du dépôt")
    payment_frequency = models.CharField(
        max_length=20, 
        choices=[('monthly', 'Mensuel'), ('quarterly', 'Trimestriel'), ('yearly', 'Annuel')],
        default='monthly',
        verbose_name="Fréquence de paiement"
    )
    payment_day = models.IntegerField(default=1, help_text="Jour de paiement du loyer (1-31)", verbose_name="Jour de paiement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    document = models.FileField(upload_to='leases/documents/', null=True, blank=True, verbose_name="Document")
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name="Signé le")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        db_table = 'leases_lease'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['unit', 'status']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"Bail {self.lease_number} - {self.unit}"


class LeaseTenant(models.Model):
    """Table de jointure pour baux avec plusieurs locataires"""
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='lease_tenants')
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'leases_leasetenant'
        unique_together = [['lease', 'tenant']]


class Inspection(models.Model):
    """État des lieux (entrée/sortie)"""
    TYPE_CHOICES = [
        ('move_in', 'État des lieux d\'entrée'),
        ('move_out', 'État des lieux de sortie'),
        ('periodic', 'État des lieux périodique'),
    ]
    
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='inspections')
    inspection_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    inspection_date = models.DateField()
    notes = models.TextField(blank=True)
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='inspections_conducted'
    )
    document = models.FileField(upload_to='inspections/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'leases_inspection'
        ordering = ['-inspection_date']