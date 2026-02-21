"""Enrolment, Attempt, AttemptQuestion, and AttemptAnswer models."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.quizzes.models import Answer, Question, Quiz


class Enrolment(models.Model):
    """Records a student's enrolment in a quiz.

    One enrolment per student/quiz pair. ``has_passed`` is set to True the
    first time the student submits a passing attempt and is never reverted.
    The ``certificate_code`` UUID is generated at that same moment and is
    stable forever.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="enrolments",
        verbose_name=_("student"),
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.PROTECT,
        related_name="enrolments",
        verbose_name=_("quiz"),
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name=_("enrolled at"))
    has_passed = models.BooleanField(default=False, verbose_name=_("has passed"))
    passing_attempt = models.ForeignKey(
        "Attempt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="passing_enrolments",
        verbose_name=_("passing attempt"),
    )
    certificate_code = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("certificate code"),
        help_text=_("Generated once when the student first passes; stable forever."),
    )

    class Meta:
        verbose_name = _("enrolment")
        verbose_name_plural = _("enrolments")
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "quiz"], name="unique_student_quiz_enrolment")
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.quiz}"


class Attempt(models.Model):
    """A single attempt at a quiz by an enrolled student.

    An attempt is created when the student starts, and scored when they submit.
    ``submitted_at``, ``score_percent``, and ``passed`` are all null until submission.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrolment = models.ForeignKey(
        Enrolment,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("enrolment"),
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("started at"))
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("submitted at"))
    score_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("score (%)"),
    )
    passed = models.BooleanField(null=True, blank=True, verbose_name=_("passed"))

    class Meta:
        verbose_name = _("attempt")
        verbose_name_plural = _("attempts")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Attempt by {self.enrolment.student} on {self.enrolment.quiz} at {self.started_at:%Y-%m-%d %H:%M}"


class AttemptQuestion(models.Model):
    """Records which question was shown and in which position for an attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="attempt_questions",
        verbose_name=_("attempt"),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="attempt_questions",
        verbose_name=_("question"),
    )
    display_order = models.PositiveIntegerField(verbose_name=_("display order"))

    class Meta:
        verbose_name = _("attempt question")
        verbose_name_plural = _("attempt questions")
        ordering = ["display_order"]

    def __str__(self) -> str:
        return f"{self.attempt} — Q{self.display_order}"


class AttemptAnswer(models.Model):
    """Records one answer option for a question shown in an attempt.

    All four answer options are stored with ``is_selected=False`` when the attempt
    is created. On submission, ``is_selected`` is set to True for the chosen answers.
    ``display_order`` preserves the randomised answer order shown to the student.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_question = models.ForeignKey(
        AttemptQuestion,
        on_delete=models.CASCADE,
        related_name="attempt_answers",
        verbose_name=_("attempt question"),
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.PROTECT,
        related_name="attempt_answers",
        verbose_name=_("answer"),
    )
    is_selected = models.BooleanField(default=False, verbose_name=_("is selected"))
    display_order = models.PositiveIntegerField(verbose_name=_("display order"))

    class Meta:
        verbose_name = _("attempt answer")
        verbose_name_plural = _("attempt answers")
        ordering = ["display_order"]

    def __str__(self) -> str:
        selected = " [selected]" if self.is_selected else ""
        return f"{self.answer.text[:40]}{selected}"
