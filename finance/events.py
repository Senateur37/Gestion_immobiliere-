"""Evenements du domaine financier."""
from core.events import DomainEvent


class RentScheduleGenerated(DomainEvent):
    """Un echeancier de loyer vient d'etre produit pour un bail."""

    def __init__(self, lease_id, organization_id, charge_ids):
        self.lease_id = lease_id
        self.organization_id = organization_id
        self.charge_ids = charge_ids


class PaymentRecorded(DomainEvent):
    """Un encaissement a ete enregistre."""

    def __init__(self, payment_id, organization_id, amount, method):
        self.payment_id = payment_id
        self.organization_id = organization_id
        self.amount = amount
        self.method = method


class PaymentAllocated(DomainEvent):
    """Un encaissement a ete impute sur une echeance."""

    def __init__(self, payment_id, rent_charge_id, organization_id, amount):
        self.payment_id = payment_id
        self.rent_charge_id = rent_charge_id
        self.organization_id = organization_id
        self.amount = amount


class RentChargeSettled(DomainEvent):
    """Une echeance vient d'etre soldee."""

    def __init__(self, rent_charge_id, organization_id, amount):
        self.rent_charge_id = rent_charge_id
        self.organization_id = organization_id
        self.amount = amount
