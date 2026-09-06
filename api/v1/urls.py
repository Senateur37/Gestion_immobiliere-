"""Routage de l'API v1.

Une version dans l'URL des le premier jour : le front et le mobile
evolueront a leur rythme, et une v2 doit pouvoir coexister.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from identity.views import CurrentUserView, LoginView, MyOrganizationsView

from .views import (
    ComptesListView,
    GenerateScheduleView,
    LeaseListView,
    PaymentListView,
    PropertyDetailView,
    PropertyListCreateView,
    RecordPaymentView,
    RentChargeListView,
    UnitListCreateView,
    dashboard,
)

app_name = 'api-v1'

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='verify'),
    path('auth/me/', CurrentUserView.as_view(), name='me'),
    path('auth/organizations/', MyOrganizationsView.as_view(), name='organizations'),

    path('dashboard/', dashboard, name='dashboard'),

    path('properties/', PropertyListCreateView.as_view(), name='property-list'),
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path('units/', UnitListCreateView.as_view(), name='unit-list'),

    path('leases/', LeaseListView.as_view(), name='lease-list'),
    path('leases/<int:pk>/schedule/', GenerateScheduleView.as_view(), name='lease-schedule'),

    path('rent-charges/', RentChargeListView.as_view(), name='rentcharge-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('payments/record/', RecordPaymentView.as_view(), name='payment-record'),

    path('accounts/', ComptesListView.as_view(), name='account-list'),
]
