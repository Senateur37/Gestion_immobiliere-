"""
URL configuration for Immobiliere project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from Comptabilite.views import (
    business_report,
    dashboard,
    payment_delete,
    payment_list,
    payment_update,
    transaction_create,
    transaction_delete,
    transaction_list,
    transaction_update,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('rapports/', business_report, name='business_report'),
    path('biens/', include('Proprietes.urls')),
    path('paiements/', payment_list, name='payment_list'),
    path('paiements/<int:pk>/modifier/', payment_update, name='payment_update'),
    path('paiements/<int:pk>/supprimer/', payment_delete, name='payment_delete'),
    path('baux/', include('Locations.urls')),
    path('maintenance/', include('Maintenance.urls')),
    path('documents/', include('Documents.urls')),
    path('comptabilite/', transaction_list, name='transaction_list'),
    path('comptabilite/ajouter/', transaction_create, name='transaction_create'),
    path('comptabilite/<int:pk>/modifier/', transaction_update, name='transaction_update'),
    path('comptabilite/<int:pk>/supprimer/', transaction_delete, name='transaction_delete'),
    path('comptes/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
