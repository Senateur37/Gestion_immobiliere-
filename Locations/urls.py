from django.urls import path

from .views import lease_create, lease_delete, lease_list, lease_update, tenant_crm

urlpatterns = [
    path('', lease_list, name='lease_list'),
    path('crm/', tenant_crm, name='tenant_crm'),
    path('ajouter/', lease_create, name='lease_create'),
    path('<int:pk>/modifier/', lease_update, name='lease_update'),
    path('<int:pk>/supprimer/', lease_delete, name='lease_delete'),
]