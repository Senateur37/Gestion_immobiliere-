"""Routage de l'API v1.

Une version dans l'URL des le premier jour : le front et le mobile
evolueront a leur rythme, et une v2 doit pouvoir coexister.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from identity.views import CurrentUserView, LoginView, MyOrganizationsView

app_name = 'api-v1'

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='verify'),
    path('auth/me/', CurrentUserView.as_view(), name='me'),
    path('auth/organizations/', MyOrganizationsView.as_view(), name='organizations'),
]
