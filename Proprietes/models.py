# apps/properties/models.py
from django.db import models
from django.conf import settings

class Property(models.Model):
    """Bien immobilier (immeuble, maison, etc.)"""
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Appartement'),
        ('house', 'Maison'),
        ('commercial', 'Commercial'),
        ('parking', 'Parking'),
        ('land', 'Terrain'),
    ]
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='properties'
    )
    name = models.CharField(max_length=200, verbose_name="Nom du bien")
    address = models.CharField(max_length=255, verbose_name="Adresse")
    city = models.CharField(max_length=100, verbose_name="Ville")
    postal_code = models.CharField(max_length=20, verbose_name="Code postal")
    country = models.CharField(max_length=100, default='France', verbose_name="Pays")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, verbose_name="Type de bien")
    total_area = models.DecimalField(max_digits=8, decimal_places=2, help_text="Surface totale en m²", verbose_name="Surface totale")
    year_built = models.IntegerField(null=True, blank=True, verbose_name="Année de construction")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        db_table = 'properties_property'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'postal_code']),
            models.Index(fields=['owner', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class Unit(models.Model):
    """Unité locative (appartement, bureau, etc.)"""
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('occupied', 'Occupé'),
        ('maintenance', 'En maintenance'),
        ('reserved', 'Réservé'),
    ]
    
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='units'
    )
    unit_number = models.CharField(max_length=20, verbose_name="Numéro/Reference")
    floor = models.IntegerField(null=True, blank=True, verbose_name="Étage")
    rooms = models.IntegerField(default=0, verbose_name="Pièces")
    bedrooms = models.IntegerField(default=0, verbose_name="Chambres")
    bathrooms = models.IntegerField(default=0, verbose_name="Salles de bain")
    area = models.DecimalField(max_digits=6, decimal_places=2, help_text="Surface en m²", verbose_name="Surface")
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Loyer mensuel")
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Dépôt de garantie")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Statut")
    available_from = models.DateField(null=True, blank=True, verbose_name="Disponible à partir de")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        db_table = 'properties_unit'
        unique_together = [['property', 'unit_number']]
        indexes = [
            models.Index(fields=['property', 'status']),
            models.Index(fields=['status', 'available_from']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - Unité {self.unit_number}"


class PropertyImage(models.Model):
    """Photos des biens et unités"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='properties/images/', verbose_name="Image")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Légende")
    display_order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    is_primary = models.BooleanField(default=False, verbose_name="Image principale")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        db_table = 'properties_propertyimage'
        ordering = ['display_order']