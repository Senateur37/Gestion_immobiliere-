"""Ecrans du domaine financier.

Les vues restent minces : elles valident une saisie, appellent un service
et rendent un gabarit. Les regles — ordre d'imputation, plafonds, statuts
— vivent dans finance.services.
"""
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from core.exceptions import DomainError
from Locations.models import Lease

from .forms import PaymentForm
from .models import Payment, RentCharge
from .services import generate_rent_schedule, record_payment


@login_required
def charge_list(request):
    """Echeances de l'organisation, avec leur reste a payer."""
    charges = RentCharge.objects.select_related(
        'lease', 'lease__unit', 'lease__unit__property', 'lease__tenant'
    )

    statut = request.GET.get('status', '').strip()
    aujourdhui = date.today()

    if statut == 'overdue':
        charges = charges.filter(due_date__lt=aujourdhui).exclude(
            status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED]
        )
    elif statut:
        charges = charges.filter(status=statut)

    total_du = charges.aggregate(total=Sum('amount_due'))['total'] or 0
    # Le reste a payer se calcule echeance par echeance : une somme SQL
    # sur les imputations fausserait le total en presence de trop-percus.
    total_restant = sum((charge.amount_outstanding for charge in charges), start=0)

    return render(request, 'payments/charge_list.html', {
        'charges': charges,
        'status': statut,
        'status_choices': RentCharge.STATUS_CHOICES,
        'today': aujourdhui,
        'total_du': total_du,
        'total_restant': total_restant,
    })


@login_required
def payment_create(request):
    """Enregistre un encaissement et l'impute automatiquement."""
    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            paiement = record_payment(
                lease=form.cleaned_data['lease'],
                amount=form.cleaned_data['amount'],
                payment_date=form.cleaned_data['payment_date'],
                method=form.cleaned_data['method'],
                external_reference=form.cleaned_data['external_reference'],
                notes=form.cleaned_data['notes'],
                compte=form.cleaned_data.get('compte'),
                user=request.user,
            )
        except DomainError as erreur:
            messages.error(request, erreur.message)
        else:
            reste = paiement.amount_unallocated
            if reste > 0:
                messages.success(
                    request,
                    f'Encaissement {paiement.reference} enregistre. '
                    f'{reste:.0f} FCFA restent en avance, non imputes.',
                )
            else:
                messages.success(
                    request, f'Encaissement {paiement.reference} enregistre et impute.'
                )
            return redirect('payment_list')

    return render(request, 'shared_form.html', {
        'form': form,
        'page_title': 'Enregistrer un encaissement',
        'back_url': 'payment_list',
    })


@login_required
def payment_history(request):
    """Encaissements recus, du plus recent au plus ancien."""
    paiements = Payment.objects.select_related(
        'lease', 'lease__unit', 'lease__unit__property', 'lease__tenant'
    )
    return render(request, 'payments/payment_history.html', {
        'payments': paiements,
        'total': paiements.aggregate(total=Sum('amount'))['total'] or 0,
    })


@login_required
def payment_receipt(request, pk):
    """Quittance d'un encaissement."""
    paiement = get_object_or_404(
        Payment.objects.select_related('lease', 'lease__unit', 'lease__unit__property', 'lease__tenant'),
        pk=pk,
    )
    return render(request, 'payments/receipt_pdf.html', {
        'payment': paiement,
        'allocations': paiement.allocations.select_related('rent_charge'),
    })


@login_required
def lease_schedule(request, pk):
    """Produit l'echeancier d'un bail."""
    bail = get_object_or_404(Lease, pk=pk)
    if request.method == 'POST':
        try:
            creees = generate_rent_schedule(lease=bail)
        except DomainError as erreur:
            messages.error(request, erreur.message)
        else:
            if creees:
                messages.success(request, f'{len(creees)} echeances generees pour {bail.lease_number}.')
            else:
                messages.info(request, f'L echeancier de {bail.lease_number} etait deja complet.')
        return redirect('payment_list')

    return render(request, 'confirm_delete.html', {
        'object_label': f'l echeancier du bail {bail.lease_number}',
        'delete_message': (
            f'Les echeances de loyer du bail {bail.lease_number} seront generees '
            f'du {bail.start_date} au {bail.end_date}. Les periodes deja facturees '
            f'sont ignorees.'
        ),
        'cancel_url': '/paiements/',
        'submit_label': 'Generer',
    })
