from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import TransactionForm
from .models import Transaction
from Locations.models import Lease
from Maintenance.models import MaintenanceRequest
from finance.models import RentCharge
from Proprietes.models import Property, Unit


@login_required
def dashboard(request):
	properties = Property.objects.all()
	units = Unit.objects.all()
	leases = Lease.objects.all()
	charges = RentCharge.objects.all()
	maintenance = MaintenanceRequest.objects.filter(unit__in=Unit.objects.all())
	active_leases = leases.filter(status='active')
	pending_charges = charges.exclude(status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED])
	open_maintenance = maintenance.filter(status__in=['submitted', 'in_progress'])
	month_labels, month_income = [], []
	today = timezone.now().date()
	transactions = request.user.transactions.all()
	for offset in range(5, -1, -1):
		month_index = today.month - 1 - offset
		month_start = date(today.year + month_index // 12, month_index % 12 + 1, 1)
		month_end = date(month_start.year + (1 if month_start.month == 12 else 0), 1 if month_start.month == 12 else month_start.month + 1, 1)
		month_transactions = transactions.filter(transaction_date__gte=month_start, transaction_date__lt=month_end)
		month_labels.append(month_start.strftime('%m/%Y'))
		month_income.append(float(month_transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0))

	context = {
		'property_count': properties.count(),
		'unit_count': units.count(),
		'occupied_units': units.filter(status='occupied').count(),
		'active_leases': active_leases.count(),
		'pending_payments': pending_charges.count(),
		'open_maintenance': open_maintenance.count(),
		'pending_amount': sum((charge.amount_outstanding for charge in pending_charges), start=0),
		'monthly_revenue': active_leases.aggregate(total=Sum('rent_amount'))['total'] or 0,
		'recent_properties': properties[:6],
		'month_labels': month_labels,
		'month_income': month_income,
	}
	return render(request, 'dashboard.html', context)






@login_required
def transaction_list(request):
	transactions = request.user.transactions.all()
	transaction_type = request.GET.get('type', '').strip()
	if transaction_type:
		transactions = transactions.filter(transaction_type=transaction_type)
	income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
	expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
	return render(request, 'accounting/transaction_list.html', {
		'transactions': transactions,
		'transaction_type': transaction_type,
		'income': income,
		'expense': expense,
		'net': income - expense,
	})


@login_required
def transaction_create(request):
	form = TransactionForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		transaction = form.save(commit=False)
		transaction.owner = request.user
		transaction.save()
		return redirect('transaction_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Nouvelle écriture', 'back_url': 'transaction_list'})


@login_required
def transaction_update(request, pk):
	transaction = get_object_or_404(Transaction, pk=pk, owner=request.user)
	form = TransactionForm(request.POST or None, instance=transaction)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'L’écriture a été mise à jour.')
		return redirect('transaction_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Modifier l’écriture', 'back_url': 'transaction_list'})


@login_required
def transaction_delete(request, pk):
	transaction = get_object_or_404(Transaction, pk=pk, owner=request.user)
	if request.method == 'POST':
		transaction.delete()
		messages.success(request, 'L’écriture a été supprimée.')
		return redirect('transaction_list')
	return render(request, 'confirm_delete.html', {
		'object_label': f'l’écriture « {transaction.label} »',
		'delete_message': f'L’écriture « {transaction.label} » sera définitivement supprimée.',
		'cancel_url': reverse('transaction_list'),
	})


@login_required
def business_report(request):
	properties = Property.objects.all()
	units = Unit.objects.all()
	active_leases = Lease.objects.filter(status='active').select_related('unit', 'unit__property')
	pending_payments = RentCharge.objects.exclude(
		status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED],
	).select_related('lease', 'lease__unit', 'lease__unit__property', 'lease__tenant')
	open_maintenance = MaintenanceRequest.objects.filter(
		unit__in=Unit.objects.all(),
		status__in=['submitted', 'in_progress'],
	).select_related('unit', 'unit__property', 'tenant')
	transactions = request.user.transactions.all()
	income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
	expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
	occupied_units = units.filter(status='occupied').count()
	unit_count = units.count()
	occupancy_rate = round((occupied_units / unit_count) * 100) if unit_count else 0
	total_rent = active_leases.aggregate(total=Sum('rent_amount'))['total'] or 0
	average_rent = total_rent / active_leases.count() if active_leases.count() else 0
	# Le reste a payer se calcule echeance par echeance : une somme SQL sur
	# les montants dus ignorerait les versements deja recus.
	pending_amount = sum((charge.amount_outstanding for charge in pending_payments), start=0)
	due_soon = RentCharge.objects.filter(
		status=RentCharge.STATUS_PENDING,
		due_date__lte=timezone.now().date() + timedelta(days=30),
	).count()

	unit_status_counts = {value: 0 for value, _ in Unit.STATUS_CHOICES}
	for row in units.values('status').annotate(total=Count('id')):
		unit_status_counts[row['status']] = row['total']

	all_payments = RentCharge.objects.all()
	payment_status_counts = {value: 0 for value, _ in RentCharge.STATUS_CHOICES}
	for row in all_payments.values('status').annotate(total=Count('id')):
		payment_status_counts[row['status']] = row['total']

	all_maintenance = MaintenanceRequest.objects.filter(unit__in=Unit.objects.all())
	priority_counts = {value: 0 for value, _ in MaintenanceRequest.PRIORITY_CHOICES}
	for row in all_maintenance.values('priority').annotate(total=Count('id')):
		priority_counts[row['priority']] = row['total']

	month_labels, month_income, month_expense = [], [], []
	today = timezone.now().date()
	for offset in range(5, -1, -1):
		month_index = today.month - 1 - offset
		month_start = date(today.year + month_index // 12, month_index % 12 + 1, 1)
		month_end = date(month_start.year + (1 if month_start.month == 12 else 0), 1 if month_start.month == 12 else month_start.month + 1, 1)
		month_transactions = transactions.filter(transaction_date__gte=month_start, transaction_date__lt=month_end)
		month_labels.append(month_start.strftime('%m/%Y'))
		month_income.append(float(month_transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0))
		month_expense.append(float(month_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0))

	return render(request, 'reports/business_report.html', {
		'property_count': properties.count(),
		'unit_count': unit_count,
		'occupied_units': occupied_units,
		'occupancy_rate': occupancy_rate,
		'active_leases': active_leases.count(),
		'total_rent': total_rent,
		'average_rent': average_rent,
		'pending_amount': pending_amount,
		'due_soon': due_soon,
		'pending_payments': pending_payments.count(),
		'open_maintenance': open_maintenance.count(),
		'unit_status_labels': [label for _, label in Unit.STATUS_CHOICES],
		'unit_status_data': [unit_status_counts[value] for value, _ in Unit.STATUS_CHOICES],
		'payment_status_labels': [label for _, label in RentCharge.STATUS_CHOICES],
		'payment_status_data': [payment_status_counts[value] for value, _ in RentCharge.STATUS_CHOICES],
		'priority_labels': [label for _, label in MaintenanceRequest.PRIORITY_CHOICES],
		'priority_data': [priority_counts[value] for value, _ in MaintenanceRequest.PRIORITY_CHOICES],
		'month_labels': month_labels,
		'month_income': month_income,
		'month_expense': month_expense,
		'income': income,
		'expense': expense,
		'net': income - expense,
		'recent_payments': pending_payments.order_by('-due_date')[:5],
		'recent_maintenance': open_maintenance.order_by('-submitted_at')[:5],
	})
