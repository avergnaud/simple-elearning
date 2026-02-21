"""Access-control mixins for the accounts app."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin that restricts access to users with role == 'admin'.

    Unauthenticated users are redirected to the login page (via LoginRequiredMixin).
    Authenticated users without the admin role receive a 403 Forbidden response.
    Never relies on Django's ``is_staff`` flag for this check.
    """

    def dispatch(self, request, *args, **kwargs):
        """Enforce admin role check before dispatching the request."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != "admin":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
