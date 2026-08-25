from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView, UserDeleteView, SiteSettingsUpdateView

urlpatterns = [
    path('parametres/', SiteSettingsUpdateView.as_view(), name='site_settings'),
    path('', UserListView.as_view(), name='user_list'),
    path('nouveau/', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/modifier/', UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/supprimer/', UserDeleteView.as_view(), name='user_delete'),
]
