"""Django admin registration for the enrolments app."""
from django.contrib import admin

from apps.enrolments.models import Attempt, AttemptAnswer, AttemptQuestion, Enrolment


class AttemptInline(admin.TabularInline):
    """Inline view of attempts within an enrolment."""

    model = Attempt
    extra = 0
    readonly_fields = ("started_at", "submitted_at", "score_percent", "passed")
    can_delete = False


@admin.register(Enrolment)
class EnrolmentAdmin(admin.ModelAdmin):
    """Admin interface for enrolments."""

    list_display = ("student", "quiz", "enrolled_at", "has_passed", "certificate_code")
    list_filter = ("has_passed", "quiz")
    search_fields = ("student__email", "student__display_name", "quiz__title")
    readonly_fields = ("id", "enrolled_at", "certificate_code")
    inlines = [AttemptInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Admin interface for attempts."""

    list_display = ("enrolment", "started_at", "submitted_at", "score_percent", "passed")
    list_filter = ("passed",)
    readonly_fields = ("id", "started_at", "submitted_at", "score_percent", "passed")
