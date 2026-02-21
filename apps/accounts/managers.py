"""Custom user manager for the accounts app."""
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for the custom User model.

    Provides create_user and create_superuser helpers compatible with
    Django's management commands and admin interface.
    """

    def create_user(self, email: str, display_name: str, password: str = None, **extra_fields):
        """Create and return a regular user with the given email and display name."""
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, display_name=display_name, **extra_fields)
        user.set_unusable_password()
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, display_name: str, password: str = None, **extra_fields):
        """Create and return a superuser with is_staff and is_superuser set."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, display_name, password, **extra_fields)
