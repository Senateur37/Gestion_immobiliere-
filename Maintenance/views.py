from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import MaintenanceRequestForm
from .models import MaintenanceRequest


@login_required
def maintenance_list(request):
	requests = MaintenanceRequest.objects.filter(
		unit__property__owner=request.user,
	).select_related('unit', 'unit__property', 'tenant', 'assigned_to')
	status = request.GET.get('status', '').strip()
	if status:
		requests = requests.filter(status=status)
	return render(request, 'maintenance/maintenance_list.html', {
		'requests': requests,
		'status': status,
		'status_choices': MaintenanceRequest.STATUS_CHOICES,
	})


@login_required
def maintenance_create(request):
	form = MaintenanceRequestForm(request.user, request.POST or None)
	if request.method == 'POST' and form.is_valid():
		item = form.save(commit=False)
		item.tenant = request.user if request.user.role == 'tenant' else None
		item.save()
		messages.success(request, 'La demande de maintenance a été enregistrée.')
		return redirect('maintenance_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Nouvelle demande', 'back_url': 'maintenance_list'})


@login_required
def maintenance_update(request, pk):
	item = get_object_or_404(MaintenanceRequest, pk=pk, unit__property__owner=request.user)
	form = MaintenanceRequestForm(request.user, request.POST or None, instance=item)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'La demande de maintenance a été mise à jour.')
		return redirect('maintenance_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Modifier la demande', 'back_url': 'maintenance_list'})


@login_required
def maintenance_delete(request, pk):
	item = get_object_or_404(MaintenanceRequest, pk=pk, unit__property__owner=request.user)
	if request.method == 'POST':
		item.delete()
		messages.success(request, 'La demande de maintenance a été supprimée.')
		return redirect('maintenance_list')
	return render(request, 'confirm_delete.html', {
		'object_label': f'la demande « {item.title} »',
		'delete_message': f'La demande « {item.title} » sera définitivement supprimée.',
		'cancel_url': reverse('maintenance_list'),
	})

# Create your views here.
