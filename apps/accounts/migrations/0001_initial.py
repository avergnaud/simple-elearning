"""Initial migration for the accounts app — creates the User table."""
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import apps.accounts.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "entra_oid",
                    models.CharField(
                        help_text="The 'oid' claim from the Microsoft Entra ID JWT.",
                        max_length=36,
                        unique=True,
                        verbose_name="Entra OID",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email address")),
                ("display_name", models.CharField(max_length=200, verbose_name="display name")),
                (
                    "role",
                    models.CharField(
                        choices=[("student", "Student"), ("admin", "Admin")],
                        default="student",
                        max_length=10,
                        verbose_name="role",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Grants access to the Django built-in admin site.",
                        verbose_name="staff status",
                    ),
                ),
                ("date_joined", models.DateTimeField(auto_now_add=True, verbose_name="date joined")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "ordering": ["display_name"],
            },
            managers=[
                ("objects", apps.accounts.managers.UserManager()),
            ],
        ),
    ]
