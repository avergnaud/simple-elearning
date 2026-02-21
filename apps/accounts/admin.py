"""Django admin registration for the accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""

    list_display = ("email", "display_name", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "display_name", "entra_oid")
    ordering = ("display_name",)
    readonly_fields = ("id", "entra_oid", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("id", "email", "display_name", "entra_oid")}),
        ("Role & permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("date_joined", "last_login")}),
    )

    # No password creation via admin — auth is delegated to Entra ID
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "display_name", "role", "is_active", "is_staff"),
        }),
    )
