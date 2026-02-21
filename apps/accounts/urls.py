"""URL configuration for the accounts app."""
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("oauth/redirect/", views.OAuthRedirectView.as_view(), name="oauth-redirect"),
    path("callback/", views.OAuthCallbackView.as_view(), name="callback"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
