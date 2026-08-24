from django.urls import path

from .views import maintenance_create, maintenance_delete, maintenance_list, maintenance_update

urlpatterns = [
    path('', maintenance_list, name='maintenance_list'),
    path('ajouter/', maintenance_create, name='maintenance_create'),
    path('<int:pk>/modifier/', maintenance_update, name='maintenance_update'),
    path('<int:pk>/supprimer/', maintenance_delete, name='maintenance_delete'),
]