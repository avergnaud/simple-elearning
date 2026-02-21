"""App configuration for the enrolments app."""
from django.apps import AppConfig


class EnrolmentsConfig(AppConfig):
    """Configuration for the enrolments application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.enrolments"
    verbose_name = "Enrolments"
