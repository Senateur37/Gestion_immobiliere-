"""Serialiseurs de l'API v1.

Volontairement decouples des modeles : ils decrivent ce que le front
recoit, non la structure des tables. Un renommage de colonne ne casse donc
pas le contrat d'API, et aucun champ n'est expose par inadvertance.
"""
from decimal import Decimal

from rest_framework import serializers


# --- Patrimoine ---------------------------------------------------------

class PropertySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    postal_code = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    property_type = serializers.CharField()
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    total_area = serializers.DecimalField(max_digits=8, decimal_places=2)
    is_active = serializers.BooleanField(required=False, default=True)
    units_count = serializers.SerializerMethodField()

    def get_units_count(self, bien):
        return bien.units.count()


class UnitSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    property = serializers.IntegerField(source='property_id')
    property_name = serializers.CharField(source='property.name', read_only=True)
    unit_number = serializers.CharField()
    area = serializers.DecimalField(max_digits=6, decimal_places=2)
    rooms = serializers.IntegerField(required=False, default=0)
    bedrooms = serializers.IntegerField(required=False, default=0)
    rent_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField(required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)


# --- Location -----------------------------------------------------------

class LeaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    lease_number = serializers.CharField()
    unit = serializers.IntegerField(source='unit_id')
    unit_label = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    rent_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_unit_label(self, bail):
        return f'{bail.unit.property.name} - {bail.unit.unit_number}'

    def get_tenant_name(self, bail):
        return bail.tenant.get_full_name() or bail.tenant.username


# --- Finance ------------------------------------------------------------

class RentChargeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    lease = serializers.IntegerField(source='lease_id', read_only=True)
    lease_number = serializers.CharField(source='lease.lease_number', read_only=True)
    tenant_name = serializers.SerializerMethodField()
    unit_label = serializers.SerializerMethodField()
    kind = serializers.CharField(read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    period_start = serializers.DateField(read_only=True)
    period_end = serializers.DateField(read_only=True)
    due_date = serializers.DateField(read_only=True)
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_tenant_name(self, charge):
        locataire = charge.lease.tenant
        return locataire.get_full_name() or locataire.username

    def get_unit_label(self, charge):
        unite = charge.lease.unit
        return f'{unite.property.name} - {unite.unit_number}'


class PaymentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    reference = serializers.CharField(read_only=True)
    lease = serializers.IntegerField(source='lease_id', read_only=True)
    lease_number = serializers.CharField(source='lease.lease_number', read_only=True)
    tenant_name = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_allocated = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_unallocated = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_date = serializers.DateField(read_only=True)
    method = serializers.CharField(read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    external_reference = serializers.CharField(read_only=True)

    def get_tenant_name(self, paiement):
        locataire = paiement.lease.tenant
        return locataire.get_full_name() or locataire.username


class RecordPaymentSerializer(serializers.Serializer):
    """Entree de l'enregistrement d'un encaissement.

    Ne porte que ce que l'agent saisit. L'imputation sur les echeances est
    calculee par le service : le client ne la transmet pas, il ne pourrait
    donc pas la fausser.
    """

    lease = serializers.IntegerField()
    compte = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_date = serializers.DateField()
    method = serializers.CharField()
    external_reference = serializers.CharField(required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class CompteSerializer(serializers.Serializer):
    """Compte financier, pour le choix a l'encaissement."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    nom = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    solde_actuel = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)


# --- Locataires ---------------------------------------------------------

class LocataireSerializer(serializers.Serializer):
    """Locataire vu depuis son bail : le CRM affiche des personnes, pas des comptes."""

    id = serializers.IntegerField(read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    leases_count = serializers.IntegerField(read_only=True)
    active_lease = serializers.SerializerMethodField()
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def get_full_name(self, personne):
        return personne.get_full_name() or personne.username

    def get_active_lease(self, personne):
        bail = getattr(personne, 'bail_actif', None)
        return bail.lease_number if bail else None


# --- Maintenance --------------------------------------------------------

class MaintenanceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    unit_label = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    def get_unit_label(self, demande):
        unite = demande.unit
        return f'{unite.property.name} - {unite.unit_number}'


# --- Documents ----------------------------------------------------------

class DocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    mime_type = serializers.CharField(read_only=True)
    is_signed = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


# --- Comptabilite -------------------------------------------------------

class EcritureSerializer(serializers.Serializer):
    """Ecriture comptable, avec ses lignes."""

    id = serializers.IntegerField(read_only=True)
    reference = serializers.CharField(read_only=True)
    date_ecriture = serializers.DateField(read_only=True)
    libelle = serializers.CharField(read_only=True)
    journal = serializers.CharField(source='journal.code', read_only=True)
    total_debit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    est_equilibree = serializers.BooleanField(read_only=True)
    lignes = serializers.SerializerMethodField()

    def get_lignes(self, ecriture):
        return [
            {
                'compte': ligne.compte.code,
                'intitule': ligne.compte.libelle,
                'debit': str(ligne.debit),
                'credit': str(ligne.credit),
            }
            for ligne in ecriture.lignes.select_related('compte')
        ]


# --- Membres ------------------------------------------------------------

class MembreSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    def get_full_name(self, membre):
        return membre.user.get_full_name() or membre.user.username
