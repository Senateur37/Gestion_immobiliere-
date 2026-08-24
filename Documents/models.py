# apps/documents/models.py
from django.db import models
from django.conf import settings

class Document(models.Model):
    """Document générique (contrats, diagnostics, assurances, etc.)"""
    CATEGORY_CHOICES = [
        ('lease', 'Contrat de location'),
        ('inspection', 'État des lieux'),
        ('receipt', 'Quittance'),
        ('diagnostic', 'Diagnostic'),
        ('insurance', 'Assurance'),
        ('legal', 'Document légal'),
        ('other', 'Autre'),
    ]
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.IntegerField(help_text="Taille en octets")
    mime_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents_document'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'category']),
            models.Index(fields=['expires_at']),
        ]