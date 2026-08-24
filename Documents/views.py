from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import DocumentForm
from .models import Document


@login_required
def document_list(request):
	documents = Document.objects.filter(owner=request.user)
	category = request.GET.get('category', '').strip()
	if category:
		documents = documents.filter(category=category)
	return render(request, 'documents/document_list.html', {
		'documents': documents,
		'category': category,
		'category_choices': Document.CATEGORY_CHOICES,
	})


@login_required
def document_create(request):
	form = DocumentForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		uploaded_file = form.cleaned_data['file']
		document = form.save(commit=False)
		document.owner = request.user
		document.file_size = uploaded_file.size
		document.mime_type = uploaded_file.content_type or 'application/octet-stream'
		document.save()
		messages.success(request, 'Le document a été ajouté à votre bibliothèque.')
		return redirect('document_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Ajouter un document', 'back_url': 'document_list', 'has_file': True})


@login_required
def document_update(request, pk):
	document = get_object_or_404(Document, pk=pk, owner=request.user)
	form = DocumentForm(request.POST or None, request.FILES or None, instance=document)
	if request.method == 'POST' and form.is_valid():
		document = form.save(commit=False)
		uploaded_file = request.FILES.get('file')
		if uploaded_file:
			document.file_size = uploaded_file.size
			document.mime_type = uploaded_file.content_type or 'application/octet-stream'
		document.save()
		messages.success(request, 'Le document a été mis à jour.')
		return redirect('document_list')
	return render(request, 'shared_form.html', {'form': form, 'page_title': 'Modifier le document', 'back_url': 'document_list', 'has_file': True})


@login_required
def document_delete(request, pk):
	document = get_object_or_404(Document, pk=pk, owner=request.user)
	if request.method == 'POST':
		document.delete()
		messages.success(request, 'Le document a été supprimé.')
		return redirect('document_list')
	return render(request, 'confirm_delete.html', {
		'object_label': f'le document « {document.title} »',
		'delete_message': f'Le document « {document.title} » sera définitivement supprimé.',
		'cancel_url': reverse('document_list'),
	})

# Create your views here.
