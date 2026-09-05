"""Operations metier du domaine financier.

Les vues et l'API appellent ces fonctions : elles ne manipulent pas les
modeles directement. Chaque operation est atomique et leve DomainError
plutot que de renvoyer None, pour que l'appelant ne puisse pas ignorer un
echec par megarde.
"""
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Sum

from core.events import publish
from core.exceptions import DomainError

from .events import (
    PaymentAllocated,
    PaymentRecorded,
    RentChargeSettled,
    RentScheduleGenerated,
)
from .models import Payment, PaymentAllocation, RentCharge

# Duree d'une periode selon la frequence de paiement du bail.
MOIS_PAR_FREQUENCE = {
    'monthly': 1,
    'quarterly': 3,
    'yearly': 12,
}


def _echeance_de_periode(debut, jour_de_paiement):
    """Date d'echeance dans le mois de debut de periode.

    Un bail peut demander le 31 dans un mois de 30 jours : on retombe
    alors sur le dernier jour du mois plutot que de refuser la date.
    """
    dernier_jour = (debut + relativedelta(day=31)).day
    return debut.replace(day=min(jour_de_paiement, dernier_jour))


@transaction.atomic
def generate_rent_schedule(*, lease, until=None):
    """Produit les echeances de loyer d'un bail.

    Rejouable : les periodes deja facturees sont ignorees, grace a
    l'unicite (bail, nature, debut de periode). On peut donc relancer la
    generation apres avoir prolonge un bail sans creer de doublons.
    """
    if lease.status == 'draft':
        raise DomainError(
            "Un bail en brouillon n'a pas d'echeancier. Activez-le d'abord.",
            code='lease_not_active',
        )

    pas = MOIS_PAR_FREQUENCE.get(lease.payment_frequency)
    if pas is None:
        raise DomainError(
            f"Frequence de paiement inconnue : {lease.payment_frequency}.",
            code='unknown_frequency',
        )

    fin = min(until or lease.end_date, lease.end_date)
    if fin < lease.start_date:
        raise DomainError(
            "La date demandee precede le debut du bail.",
            code='invalid_period',
        )

    deja_faites = set(
        RentCharge.objects.filter(lease=lease, kind='rent').values_list('period_start', flat=True)
    )

    creees = []
    debut_periode = lease.start_date
    while debut_periode <= fin:
        fin_periode = debut_periode + relativedelta(months=pas, days=-1)
        # La derniere periode s'arrete a la fin du bail, pas au-dela.
        if fin_periode > lease.end_date:
            fin_periode = lease.end_date

        if debut_periode not in deja_faites:
            creees.append(
                RentCharge(
                    organization_id=lease.organization_id,
                    lease=lease,
                    kind='rent',
                    label=f'Loyer du {debut_periode} au {fin_periode}',
                    period_start=debut_periode,
                    period_end=fin_periode,
                    due_date=_echeance_de_periode(debut_periode, lease.payment_day),
                    amount_due=lease.rent_amount,
                )
            )

        debut_periode = debut_periode + relativedelta(months=pas)

    RentCharge.objects.bulk_create(creees)

    if creees:
        publish(RentScheduleGenerated(
            lease_id=lease.pk,
            organization_id=lease.organization_id,
            charge_ids=[charge.pk for charge in creees],
        ))
    return creees


def _rafraichir_statut(rent_charge):
    """Recalcule le statut d'une echeance depuis ses imputations."""
    if rent_charge.status == RentCharge.STATUS_CANCELLED:
        return rent_charge

    impute = rent_charge.amount_allocated
    if impute <= 0:
        nouveau = RentCharge.STATUS_PENDING
    elif impute < rent_charge.amount_due:
        nouveau = RentCharge.STATUS_PARTIAL
    else:
        nouveau = RentCharge.STATUS_PAID

    if nouveau != rent_charge.status:
        rent_charge.status = nouveau
        rent_charge.save(update_fields=['status', 'updated_at'])
    return rent_charge


@transaction.atomic
def allocate_payment(*, payment, rent_charge, amount):
    """Impute une part d'encaissement sur une echeance.

    Deux garde-fous : on ne peut pas imputer plus que ce qui reste sur
    l'encaissement, ni plus que ce qui reste du sur l'echeance. Sans eux,
    le solde d'un locataire deviendrait une fiction.
    """
    amount = Decimal(amount)
    if amount <= 0:
        raise DomainError("Le montant impute doit etre positif.", code='invalid_amount')

    if payment.organization_id != rent_charge.organization_id:
        raise DomainError(
            "Encaissement et echeance appartiennent a des organisations differentes.",
            code='organization_mismatch',
        )

    if payment.lease_id != rent_charge.lease_id:
        raise DomainError(
            "L'encaissement et l'echeance ne portent pas sur le meme bail.",
            code='lease_mismatch',
        )

    if rent_charge.status == RentCharge.STATUS_CANCELLED:
        raise DomainError("Cette echeance est annulee.", code='charge_cancelled')

    disponible = payment.amount_unallocated
    if amount > disponible:
        raise DomainError(
            f"Cet encaissement ne dispose que de {disponible} a imputer.",
            code='insufficient_payment',
        )

    reste_du = rent_charge.amount_outstanding
    if amount > reste_du:
        raise DomainError(
            f"Cette echeance ne reclame plus que {reste_du}.",
            code='overpaying_charge',
        )

    # Une seconde imputation du meme encaissement sur la meme echeance
    # s'ajoute a la premiere plutot que de la dupliquer.
    allocation = PaymentAllocation.objects.filter(payment=payment, rent_charge=rent_charge).first()
    if allocation is None:
        allocation = PaymentAllocation.objects.create(
            organization_id=payment.organization_id,
            payment=payment,
            rent_charge=rent_charge,
            amount=amount,
        )
    else:
        allocation.amount = allocation.amount + amount
        allocation.save(update_fields=['amount', 'updated_at'])

    _rafraichir_statut(rent_charge)

    publish(PaymentAllocated(
        payment_id=payment.pk,
        rent_charge_id=rent_charge.pk,
        organization_id=payment.organization_id,
        amount=amount,
    ))

    rent_charge.refresh_from_db()
    if rent_charge.status == RentCharge.STATUS_PAID:
        publish(RentChargeSettled(
            rent_charge_id=rent_charge.pk,
            organization_id=rent_charge.organization_id,
            amount=rent_charge.amount_due,
        ))

    return allocation


def _porter_au_compte(payment, user=None):
    """Porte l'encaissement sur le compte financier reel.

    C'est ce mouvement qui declenche, par le signal `mouvement_valide` de
    django-comptes, l'ecriture comptable SYSCOHADA correspondante. La
    finance ne connait donc pas la comptabilite : elle alimente la
    tresorerie, et la comptabilite en decoule.

    La cle d'idempotence est la reference de l'encaissement : rejouer
    l'operation ne peut pas crediter le compte deux fois.
    """
    if payment.compte_id is None:
        return None

    from comptes.services.mouvement_service import MouvementCompteService

    return MouvementCompteService.encaisser(
        compte=payment.compte,
        montant=payment.amount,
        libelle=f'Loyer {payment.lease.lease_number} — {payment.reference}',
        user=user,
        reference=payment.reference,
        idempotency_key=f'finance.payment:{payment.pk}',
    )


@transaction.atomic
def record_payment(*, lease, amount, payment_date, method, reference=None,
                   external_reference='', notes='', auto_allocate=True,
                   compte=None, user=None):
    """Enregistre un encaissement et l'impute sur les echeances les plus anciennes.

    L'imputation automatique suit l'ordre des echeances : un locataire qui
    verse une somme solde d'abord ce qu'il doit depuis le plus longtemps.
    Le reliquat demeure non impute — c'est une avance, pas une anomalie.
    """
    amount = Decimal(amount)
    if amount <= 0:
        raise DomainError("Le montant recu doit etre positif.", code='invalid_amount')

    reference = reference or _reference_suivante(lease.organization_id, payment_date)

    if Payment.objects.filter(reference=reference).exists():
        raise DomainError(
            f"La reference {reference} est deja utilisee.",
            code='duplicate_reference',
        )

    payment = Payment.objects.create(
        organization_id=lease.organization_id,
        lease=lease,
        reference=reference,
        amount=amount,
        payment_date=payment_date,
        method=method,
        external_reference=external_reference,
        notes=notes,
        compte=compte,
    )

    # Le mouvement de tresorerie est dans la meme transaction que
    # l'encaissement : on ne veut pas d'un loyer enregistre dont l'argent
    # n'apparait dans aucun compte.
    _porter_au_compte(payment, user=user)

    publish(PaymentRecorded(
        payment_id=payment.pk,
        organization_id=payment.organization_id,
        amount=amount,
        method=method,
    ))

    if auto_allocate:
        echeances = (
            RentCharge.objects
            .filter(lease=lease)
            .exclude(status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED])
            .order_by('due_date', 'pk')
        )
        for echeance in echeances:
            reste = payment.amount_unallocated
            if reste <= 0:
                break
            a_imputer = min(reste, echeance.amount_outstanding)
            if a_imputer > 0:
                allocate_payment(payment=payment, rent_charge=echeance, amount=a_imputer)

    payment.refresh_from_db()
    return payment


def _reference_suivante(organization_id, payment_date):
    """Reference lisible, unique dans l'organisation : PAY-AAAAMM-0001."""
    prefixe = f'PAY-{payment_date:%Y%m}'
    derniere = (
        Payment.all_objects
        .filter(organization_id=organization_id, reference__startswith=prefixe)
        .order_by('-reference')
        .values_list('reference', flat=True)
        .first()
    )
    rang = int(derniere.rsplit('-', 1)[1]) + 1 if derniere else 1
    return f'{prefixe}-{rang:04d}'


@transaction.atomic
def cancel_rent_charge(*, rent_charge, reason=''):
    """Annule une echeance qui n'aurait pas du etre emise."""
    if rent_charge.allocations.exists():
        raise DomainError(
            "Cette echeance a deja recu des paiements et ne peut pas etre annulee.",
            code='charge_has_allocations',
        )
    rent_charge.status = RentCharge.STATUS_CANCELLED
    if reason:
        rent_charge.label = f'{rent_charge.label} (annulee : {reason})'.strip()
    rent_charge.save(update_fields=['status', 'label', 'updated_at'])
    return rent_charge


def lease_balance(lease):
    """Solde d'un bail : ce qui reste du, toutes echeances confondues."""
    du = RentCharge.objects.filter(lease=lease).exclude(
        status=RentCharge.STATUS_CANCELLED
    ).aggregate(total=Sum('amount_due'))['total'] or Decimal('0')

    impute = PaymentAllocation.objects.filter(
        rent_charge__lease=lease
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return du - impute


def overdue_charges(organization=None, today=None):
    """Echeances en retard, du plus ancien au plus recent."""
    today = today or date.today()
    queryset = RentCharge.objects.filter(due_date__lt=today).exclude(
        status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED]
    )
    if organization is not None:
        queryset = queryset.for_organization(organization)
    return queryset.select_related('lease', 'lease__unit').order_by('due_date')
