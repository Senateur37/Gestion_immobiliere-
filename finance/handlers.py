"""Abonnements du domaine financier aux evenements metier.

Ce module est le point ou la finance previendra la comptabilite, la
generation de quittance et les notifications. Il est volontairement vide
de traitements pour l'instant : le pont comptable arrive avec le domaine
Accounting, et l'ecrire ici avant ce domaine reviendrait a le placer au
mauvais endroit.

Les evenements sont deja publies par les services, donc brancher un
abonne ne demandera pas de modifier finance/services.py.
"""
import logging

from core.events import subscribe

from .events import PaymentRecorded, RentChargeSettled

logger = logging.getLogger(__name__)


def journaliser_encaissement(event):
    """Trace un encaissement, en attendant le pont comptable."""
    logger.info(
        'Encaissement %s : %s par %s (organisation %s)',
        event.payment_id, event.amount, event.method, event.organization_id,
    )


def journaliser_echeance_soldee(event):
    logger.info(
        'Echeance %s soldee pour %s (organisation %s)',
        event.rent_charge_id, event.amount, event.organization_id,
    )


subscribe(PaymentRecorded, journaliser_encaissement)
subscribe(RentChargeSettled, journaliser_echeance_soldee)
