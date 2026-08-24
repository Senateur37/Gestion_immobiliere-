from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PropertyForm, UnitForm
from .models import Property, Unit


@login_required
def property_list(request):
	properties = Property.objects.filter(owner=request.user)
	search = request.GET.get('q', '').strip()
	if search:
		properties = properties.filter(name__icontains=search) | properties.filter(city__icontains=search)
	return render(request, 'properties/property_list.html', {
		'properties': properties,
		'search': search,
		'property_count': properties.count(),
	})


@login_required
def property_create(request):
	form = PropertyForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		property = form.save(commit=False)
		property.owner = request.user
		property.save()
		messages.success(request, 'Le bien a ete ajoute a votre portefeuille.')
		return redirect('property_list')
	return render(request, 'properties/property_form.html', {'form': form, 'page_title': 'Ajouter un bien'})


@login_required
def property_update(request, pk):
	property = get_object_or_404(Property, pk=pk, owner=request.user)
	form = PropertyForm(request.POST or None, instance=property)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Les informations du bien ont ete mises a jour.')
		return redirect('property_list')
	return render(request, 'properties/property_form.html', {'form': form, 'page_title': 'Modifier le bien', 'property': property})


@login_required
def property_delete(request, pk):
	property = get_object_or_404(Property, pk=pk, owner=request.user)
	if request.method == 'POST':
		property.delete()
		messages.success(request, 'Le bien a ete supprime.')
		return redirect('property_list')
	return render(request, 'properties/property_confirm_delete.html', {'property': property})


@login_required
def unit_list(request):
	units = Unit.objects.filter(property__owner=request.user).select_related('property')
	status = request.GET.get('status', '').strip()
	if status:
		units = units.filter(status=status)
	return render(request, 'properties/unit_list.html', {
		'units': units,
		'status': status,
		'status_choices': Unit.STATUS_CHOICES,
	})


@login_required
def unit_create(request):
	form = UnitForm(request.POST or None, owner=request.user)
	if request.method == 'POST' and form.is_valid():
		unit = form.save(commit=False)
		unit.property = form.cleaned_data['property']
		unit.save()
		messages.success(request, 'L’unité locative a été ajoutée.')
		return redirect('unit_list')
	return render(request, 'properties/unit_form.html', {'form': form, 'property': form['property'].value(), 'page_title': 'Ajouter une unité'})


@login_required
def unit_update(request, pk):
	unit = get_object_or_404(Unit, pk=pk, property__owner=request.user)
	form = UnitForm(request.POST or None, instance=unit, owner=request.user)
	if request.method == 'POST' and form.is_valid():
		unit = form.save(commit=False)
		unit.property = form.cleaned_data['property']
		unit.save()
		messages.success(request, 'L’unité locative a été mise à jour.')
		return redirect('unit_list')
	return render(request, 'properties/unit_form.html', {'form': form, 'property': unit.property, 'page_title': 'Modifier une unité', 'unit': unit})


@login_required
def unit_delete(request, pk):
	unit = get_object_or_404(Unit, pk=pk, property__owner=request.user)
	if request.method == 'POST':
		unit.delete()
		messages.success(request, 'L’unité locative a été supprimée.')
		return redirect('unit_list')
	return render(request, 'confirm_delete.html', {
		'object_label': f'l’unité {unit.unit_number}',
		'delete_message': f'L’unité « {unit.unit_number} » sera définitivement supprimée.',
		'cancel_url': reverse('unit_list'),
	})
