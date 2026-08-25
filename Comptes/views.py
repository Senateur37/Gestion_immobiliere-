from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import User
from .forms import UserCreationForm, UserUpdateForm
# from abonnements.decorators import premium_required # Optionnel si on veut bloquer au niveau des méthodes

class AdminOwnerRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux admins et propriétaires."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['admin', 'owner']

class UserListView(LoginRequiredMixin, AdminOwnerRequiredMixin, ListView):
    model = User
    template_name = 'comptes/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        """Un propriétaire ne voit que les locataires et agents, l'admin voit tout le monde."""
        if self.request.user.role == 'owner':
            return User.objects.filter(role__in=['tenant', 'agent']).order_by('-created_at')
        return User.objects.all().order_by('-created_at')

class UserCreateView(LoginRequiredMixin, AdminOwnerRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Ajouter un utilisateur"
        return context

class UserUpdateView(LoginRequiredMixin, AdminOwnerRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modifier l'utilisateur"
        return context

class UserDeleteView(LoginRequiredMixin, AdminOwnerRequiredMixin, DeleteView):
    model = User
    template_name = 'comptes/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

from .models import SiteSettings
from .forms import SiteSettingsForm

class SiteSettingsUpdateView(LoginRequiredMixin, AdminOwnerRequiredMixin, UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'comptes/site_settings.html'
    success_url = reverse_lazy('site_settings')

    def get_object(self, queryset=None):
        return SiteSettings.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Paramètres de l'application"
        return context
