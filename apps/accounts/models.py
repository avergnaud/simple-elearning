"""User model for the accounts app."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model authenticated via Microsoft Entra ID (OAuth).

    Users are identified by their Entra OID. Passwords are never set — all
    authentication is delegated to Microsoft. The ``role`` field controls access
    to the admin panel; Django's ``is_staff`` flag is used only for the built-in
    Django admin interface.
    """

    ROLE_STUDENT = "student"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_STUDENT, _("Student")),
        (ROLE_ADMIN, _("Admin")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entra_oid = models.CharField(
        max_length=36,
        unique=True,
        verbose_name=_("Entra OID"),
        help_text=_("The 'oid' claim from the Microsoft Entra ID JWT."),
    )
    email = models.EmailField(unique=True, verbose_name=_("email address"))
    display_name = models.CharField(max_length=200, verbose_name=_("display name"))
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        verbose_name=_("role"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("active"))
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("staff status"),
        help_text=_("Grants access to the Django built-in admin site."),
    )
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name=_("date joined"))

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["display_name"]

    def __str__(self) -> str:
        return f"{self.display_name} <{self.email}>"

    @property
    def is_admin(self) -> bool:
        """Return True if this user has the admin role."""
        return self.role == self.ROLE_ADMIN
