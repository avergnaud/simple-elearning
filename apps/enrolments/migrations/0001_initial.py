"""Initial migration for the enrolments app."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("quizzes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Attempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True, verbose_name="started at")),
                (
                    "submitted_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="submitted at"),
                ),
                (
                    "score_percent",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True, verbose_name="score (%)"
                    ),
                ),
                ("passed", models.BooleanField(blank=True, null=True, verbose_name="passed")),
            ],
            options={
                "verbose_name": "attempt",
                "verbose_name_plural": "attempts",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="Enrolment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("enrolled_at", models.DateTimeField(auto_now_add=True, verbose_name="enrolled at")),
                ("has_passed", models.BooleanField(default=False, verbose_name="has passed")),
                (
                    "certificate_code",
                    models.UUIDField(
                        blank=True,
                        help_text="Generated once when the student first passes; stable forever.",
                        null=True,
                        unique=True,
                        verbose_name="certificate code",
                    ),
                ),
                (
                    "passing_attempt",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="passing_enrolments",
                        to="enrolments.attempt",
                        verbose_name="passing attempt",
                    ),
                ),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="enrolments",
                        to="quizzes.quiz",
                        verbose_name="quiz",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="enrolments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="student",
                    ),
                ),
            ],
            options={
                "verbose_name": "enrolment",
                "verbose_name_plural": "enrolments",
                "ordering": ["-enrolled_at"],
            },
        ),
        migrations.AddField(
            model_name="attempt",
            name="enrolment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                to="enrolments.enrolment",
                verbose_name="enrolment",
            ),
        ),
        migrations.CreateModel(
            name="AttemptQuestion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("display_order", models.PositiveIntegerField(verbose_name="display order")),
                (
                    "attempt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempt_questions",
                        to="enrolments.attempt",
                        verbose_name="attempt",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="attempt_questions",
                        to="quizzes.question",
                        verbose_name="question",
                    ),
                ),
            ],
            options={
                "verbose_name": "attempt question",
                "verbose_name_plural": "attempt questions",
                "ordering": ["display_order"],
            },
        ),
        migrations.CreateModel(
            name="AttemptAnswer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("is_selected", models.BooleanField(default=False, verbose_name="is selected")),
                ("display_order", models.PositiveIntegerField(verbose_name="display order")),
                (
                    "answer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="attempt_answers",
                        to="quizzes.answer",
                        verbose_name="answer",
                    ),
                ),
                (
                    "attempt_question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempt_answers",
                        to="enrolments.attemptquestion",
                        verbose_name="attempt question",
                    ),
                ),
            ],
            options={
                "verbose_name": "attempt answer",
                "verbose_name_plural": "attempt answers",
                "ordering": ["display_order"],
            },
        ),
        migrations.AddConstraint(
            model_name="enrolment",
            constraint=models.UniqueConstraint(
                fields=["student", "quiz"], name="unique_student_quiz_enrolment"
            ),
        ),
    ]
