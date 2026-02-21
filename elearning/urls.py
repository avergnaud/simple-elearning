"""Root URL configuration for the elearning project."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Home → redirect to quiz catalogue (login required there)
    path("", RedirectView.as_view(url="/quizzes/", permanent=False), name="home"),
    # Authentication (login, OAuth callback, logout)
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    # Student-facing quiz pages
    path("quizzes/", include("apps.quizzes.urls", namespace="quizzes")),
    # Admin panel (quiz management + reporting)
    path("admin-panel/", include("apps.quizzes.admin_urls", namespace="admin-panel")),
    # Django built-in admin (superuser DB management only)
    path("admin/", admin.site.urls),
]
