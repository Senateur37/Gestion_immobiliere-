# apps/payments/models.py
from django.db import models
from django.conf import settings
from Locations.models import Lease

class Payment(models.Model):
    """Paiement de loyer"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('partial', 'Partiel'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulé'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('online', 'Paiement en ligne'),
    ]
    
    lease = models.ForeignKey(
        Lease, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    payment_number = models.CharField(max_length=50, unique=True, verbose_name="Référence paiement")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(verbose_name="Date d'échéance")
    paid_date = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    notes = models.TextField(blank=True)
    receipt = models.FileField(upload_to='payments/receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_payment'
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['lease', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['paid_date']),
        ]
    
    def __str__(self):
        return f"Paiement {self.payment_number} - {self.lease.lease_number}"


class PaymentRecord(models.Model):
    """Historique des transactions (pour paiements fractionnés)"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='records')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments_paymentrecord'
        ordering = ['-recorded_at']


class Deposit(models.Model):
    """Dépôt de garantie"""
    STATUS_CHOICES = [
        ('held', 'Conservé'),
        ('partial_refund', 'Remboursement partiel'),
        ('fully_refunded', 'Entièrement remboursé'),
        ('deducted', 'Déduit'),
    ]
    
    lease = models.OneToOneField(Lease, on_delete=models.CASCADE, related_name='deposit')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='held')
    refund_date = models.DateField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deductions = models.TextField(blank=True, help_text="Motif des déductions")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_deposit'