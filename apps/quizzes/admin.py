"""Django admin registration for the quizzes app."""
from django.contrib import admin

from apps.quizzes.models import Answer, Question, Quiz


class AnswerInline(admin.TabularInline):
    """Inline editor for answers within the question admin."""

    model = Answer
    extra = 4
    max_num = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for questions."""

    list_display = ("quiz", "order", "question_type", "text_preview", "created_at")
    list_filter = ("quiz", "question_type")
    search_fields = ("text",)
    inlines = [AnswerInline]

    def text_preview(self, obj):
        """Return the first 80 characters of the question text."""
        return obj.text[:80]

    text_preview.short_description = "Text preview"


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for quizzes."""

    list_display = ("title", "questions_shown", "passing_score", "is_locked", "created_at")
    list_filter = ("is_locked",)
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "is_locked")
