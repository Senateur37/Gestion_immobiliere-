from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from Paiements.models import Payment
from .forms import LeaseForm
from .models import Lease


@login_required
def lease_list(request):
	leases = Lease.objects.filter(
		unit__property__owner=request.user,
	).select_related('unit', 'unit__property', 'tenant')
	status = request.GET.get('status', '').strip()
	if status:
		leases = leases.filter(status=status)
	return render(request, 'leases/lease_list.html', {
		'leases': leases,
		'status': status,
		'status_choices': Lease.STATUS_CHOICES,
	})


@login_required
def tenant_crm(request):
	leases = Lease.objects.filter(unit__property__owner=request.user).select_related('unit', 'unit__property', 'tenant')
	status = request.GET.get('status', '').strip()
	if status:
		leases = leases.filter(status=status)
	active_leases = leases.filter(status='active')
	payments = Payment.objects.filter(lease__unit__property__owner=request.user).select_related('lease', 'lease__tenant', 'lease__unit', 'lease__unit__property')
	pending_payments = payments.filter(status__in=['pending', 'overdue'])
	return render(request, 'leases/tenant_crm.html', {
		'leases': leases,
		'status': status,
		'status_choices': Lease.STATUS_CHOICES,
		'active_leases': active_leases.count(),
		'tenant_count': leases.values('tenant').distinct().count(),
		'monthly_rent': active_leases.aggregate(total=Sum('rent_amount'))['total'] or 0,
		'pending_amount': pending_payments.aggregate(total=Sum('amount'))['total'] or 0,
		'overdue_count': pending_payments.filter(status='overdue').count(),
	})


@login_required
def lease_create(request):
	form = LeaseForm(request.user, request.POST or None)
	if request.method == 'POST' and form.is_valid():
		lease = form.save()
		messages.success(request, f'Le bail {lease.lease_number} a été créé.')
		return redirect('lease_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Nouveau bail', 'back_url': 'lease_list'})


@login_required
def lease_update(request, pk):
	lease = get_object_or_404(Lease, pk=pk, unit__property__owner=request.user)
	form = LeaseForm(request.user, request.POST or None, instance=lease)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, f'Le bail {lease.lease_number} a été mis à jour.')
		return redirect('lease_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Modifier le bail', 'back_url': 'lease_list'})


@login_required
def lease_delete(request, pk):
	lease = get_object_or_404(Lease, pk=pk, unit__property__owner=request.user)
	if request.method == 'POST':
		lease.delete()
		messages.success(request, f'Le bail {lease.lease_number} a été supprimé.')
		return redirect('lease_list')
	return render(request, 'confirm_delete.html', {
		'object_label': f'le bail {lease.lease_number}',
		'delete_message': f'Le bail « {lease.lease_number} » sera définitivement supprimé.',
		'cancel_url': reverse('lease_list'),
	})

