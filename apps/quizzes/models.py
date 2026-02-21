"""Quiz, Question, and Answer models."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Quiz(models.Model):
    """A quiz consisting of a pool of questions from which a subset is shown per attempt.

    Once a student enrols, the quiz is considered locked (``is_locked=True``) and
    no further questions may be added. Quizzes are never deleted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name=_("title"))
    description = models.TextField(blank=True, default="", verbose_name=_("description"))
    questions_shown = models.PositiveIntegerField(
        verbose_name=_("questions shown per attempt"),
        help_text=_("How many questions are randomly selected and shown per attempt."),
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,
        verbose_name=_("passing score (%)"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_quizzes",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    is_locked = models.BooleanField(
        default=False,
        verbose_name=_("locked"),
        help_text=_("Set to True automatically when the first student enrols."),
    )

    class Meta:
        verbose_name = _("quiz")
        verbose_name_plural = _("quizzes")
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    @property
    def question_count(self) -> int:
        """Return the total number of questions in the pool."""
        return self.questions.count()


class Question(models.Model):
    """A question belonging to a quiz, written in Markdown.

    Questions have a ``question_type`` of either 'single' (one correct answer,
    rendered as radio buttons) or 'multiple' (two or more correct answers,
    rendered as checkboxes).
    """

    TYPE_SINGLE = "single"
    TYPE_MULTIPLE = "multiple"
    TYPE_CHOICES = [
        (TYPE_SINGLE, _("Single choice")),
        (TYPE_MULTIPLE, _("Multiple choice")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.PROTECT,
        related_name="questions",
        verbose_name=_("quiz"),
    )
    text = models.TextField(verbose_name=_("question text (Markdown)"))
    question_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name=_("question type"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("order"),
        help_text=_("Display order in admin; randomised for students."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"Q{self.order}: {self.text[:80]}"


class Answer(models.Model):
    """One of four possible answers for a question.

    At least one answer must have ``is_correct=True``. For single-choice questions
    exactly one answer is correct; for multiple-choice at least two.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("question"),
    )
    text = models.CharField(max_length=500, verbose_name=_("answer text"))
    is_correct = models.BooleanField(default=False, verbose_name=_("is correct"))
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("order"),
        help_text=_("Admin display order; randomised per attempt for students."),
    )

    class Meta:
        verbose_name = _("answer")
        verbose_name_plural = _("answers")
        ordering = ["order"]

    def __str__(self) -> str:
        correct_marker = " ✓" if self.is_correct else ""
        return f"{self.text[:60]}{correct_marker}"
