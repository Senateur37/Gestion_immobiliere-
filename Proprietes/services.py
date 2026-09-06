"""Operations metier du patrimoine.

Les vues et l'API passent par ici. L'organisation vient du contexte : elle
n'est jamais un parametre, pour qu'aucun appelant ne puisse la choisir.
"""
from django.db import transaction

from core.exceptions import DomainError

from .models import Property, Unit


@transaction.atomic
def create_property(*, name, address, city, postal_code, property_type,
                    total_area, owner=None, **champs):
    """Enregistre un bien dans l'organisation active."""
    if not name or not name.strip():
        raise DomainError("Le nom du bien est obligatoire.", code='name_required')
    if total_area is not None and total_area <= 0:
        raise DomainError("La surface doit etre positive.", code='invalid_area')

    return Property.objects.create(
        name=name.strip(),
        address=address,
        city=city,
        postal_code=postal_code,
        property_type=property_type,
        total_area=total_area,
        owner=owner,
        **champs,
    )


@transaction.atomic
def create_unit(*, property, unit_number, area, rent_amount, deposit_amount, **champs):
    """Ajoute une unite locative a un bien.

    Le bien est resolu par le manager filtre : une unite ne peut donc pas
    etre rattachee au bien d'une autre organisation.
    """
    if not unit_number or not unit_number.strip():
        raise DomainError("Le numero d'unite est obligatoire.", code='unit_number_required')
    if rent_amount is None or rent_amount < 0:
        raise DomainError("Le loyer doit etre positif.", code='invalid_rent')

    if Unit.objects.filter(property=property, unit_number=unit_number).exists():
        raise DomainError(
            f"L'unite {unit_number} existe deja dans {property.name}.",
            code='duplicate_unit',
        )

    return Unit.objects.create(
        property=property,
        unit_number=unit_number.strip(),
        area=area,
        rent_amount=rent_amount,
        deposit_amount=deposit_amount,
        **champs,
    )


def portfolio_summary():
    """Chiffres du patrimoine de l'organisation active."""
    unites = Unit.objects.all()
    total = unites.count()
    occupees = unites.filter(status='occupied').count()
    return {
        'properties': Property.objects.count(),
        'units': total,
        'occupied_units': occupees,
        'occupancy_rate': round(occupees / total * 100) if total else 0,
    }
