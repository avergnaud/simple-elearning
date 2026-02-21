"""Initial migration for the quizzes app — creates Quiz, Question, and Answer tables."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Quiz",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="title")),
                ("description", models.TextField(blank=True, default="", verbose_name="description")),
                (
                    "questions_shown",
                    models.PositiveIntegerField(
                        help_text="How many questions are randomly selected and shown per attempt.",
                        verbose_name="questions shown per attempt",
                    ),
                ),
                (
                    "passing_score",
                    models.DecimalField(
                        decimal_places=2, default=70.0, max_digits=5, verbose_name="passing score (%)"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "is_locked",
                    models.BooleanField(
                        default=False,
                        help_text="Set to True automatically when the first student enrols.",
                        verbose_name="locked",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_quizzes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
            ],
            options={
                "verbose_name": "quiz",
                "verbose_name_plural": "quizzes",
                "ordering": ["title"],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("text", models.TextField(verbose_name="question text (Markdown)")),
                (
                    "question_type",
                    models.CharField(
                        choices=[("single", "Single choice"), ("multiple", "Multiple choice")],
                        max_length=10,
                        verbose_name="question type",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order in admin; randomised for students.",
                        verbose_name="order",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="questions",
                        to="quizzes.quiz",
                        verbose_name="quiz",
                    ),
                ),
            ],
            options={
                "verbose_name": "question",
                "verbose_name_plural": "questions",
                "ordering": ["order", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("text", models.CharField(max_length=500, verbose_name="answer text")),
                ("is_correct", models.BooleanField(default=False, verbose_name="is correct")),
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Admin display order; randomised per attempt for students.",
                        verbose_name="order",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="quizzes.question",
                        verbose_name="question",
                    ),
                ),
            ],
            options={
                "verbose_name": "answer",
                "verbose_name_plural": "answers",
                "ordering": ["order"],
            },
        ),
    ]
