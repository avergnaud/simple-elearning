"""Authentication views for OAuth 2.0 login via Microsoft Entra ID."""
from django.conf import settings
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from authlib.integrations.django_client import OAuth

from apps.accounts.models import User

# Initialise the Authlib OAuth registry and register the Microsoft provider.
_oauth = OAuth()
_oauth.register(
    name="microsoft",
    client_id=settings.ENTRA_CLIENT_ID,
    client_secret=settings.ENTRA_CLIENT_SECRET,
    server_metadata_url=(
        f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}"
        "/v2.0/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid profile email"},
)


class LoginView(TemplateView):
    """Render the login page with a 'Sign in with Microsoft' button.

    This view does not require authentication. If the user is already
    authenticated they are immediately redirected to the quiz catalogue.
    """

    template_name = "accounts/login.html"

    def get(self, request, *args, **kwargs):
        """Redirect already-authenticated users; otherwise show the login page."""
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)


class OAuthRedirectView(View):
    """Redirect the user to Microsoft's Entra ID authorisation endpoint."""

    def get(self, request, *args, **kwargs):
        """Build the redirect URI and send the user to Microsoft."""
        redirect_uri = request.build_absolute_uri("/accounts/callback/")
        return _oauth.microsoft.authorize_redirect(request, redirect_uri)


class OAuthCallbackView(View):
    """Handle the OAuth 2.0 callback from Microsoft Entra ID.

    Exchanges the authorisation code for tokens, extracts user claims from the
    id_token, upserts the local User record, and creates a Django session.
    """

    def get(self, request, *args, **kwargs):
        """Process the callback, upsert the user, and log them in."""
        token = _oauth.microsoft.authorize_access_token(request)
        user_info = token.get("userinfo") or {}

        oid = user_info.get("oid") or user_info.get("sub", "")
        email = (
            user_info.get("email")
            or user_info.get("preferred_username")
            or ""
        )
        display_name = user_info.get("name") or email

        if not oid:
            return redirect(settings.LOGIN_URL)

        user, _created = User.objects.update_or_create(
            entra_oid=oid,
            defaults={
                "email": email,
                "display_name": display_name,
            },
        )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        next_url = request.session.pop("next", settings.LOGIN_REDIRECT_URL)
        return redirect(next_url)


class LogoutView(View):
    """Log the user out of the Django session."""

    def post(self, request, *args, **kwargs):
        """Terminate the session and redirect to the login page."""
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)
