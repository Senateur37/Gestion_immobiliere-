from django.urls import path

from .views import document_create, document_delete, document_list, document_update

urlpatterns = [
    path('', document_list, name='document_list'),
    path('ajouter/', document_create, name='document_create'),
    path('<int:pk>/modifier/', document_update, name='document_update'),
    path('<int:pk>/supprimer/', document_delete, name='document_delete'),
]