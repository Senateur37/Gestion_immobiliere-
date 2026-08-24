from django.urls import path

from . import views

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('ajouter/', views.property_create, name='property_create'),
    path('<int:pk>/modifier/', views.property_update, name='property_update'),
    path('<int:pk>/supprimer/', views.property_delete, name='property_delete'),
    path('unites/', views.unit_list, name='unit_list'),
    path('unites/ajouter/', views.unit_create, name='unit_create'),
    path('unites/<int:pk>/modifier/', views.unit_update, name='unit_update'),
    path('unites/<int:pk>/supprimer/', views.unit_delete, name='unit_delete'),
]