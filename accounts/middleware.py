from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from .models import RegistrationStatus


class ApprovalMiddleware:
    """Block authenticated users who are not approved (except auth/admin routes)."""

    ALLOWED_PREFIXES = (
        "/accounts/login",
        "/accounts/logout",
        "/accounts/register",
        "/accounts/pending",
        "/admin/",
        "/static/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            path = request.path
            if not any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                profile = getattr(user, "profile", None)
                if profile is None or profile.registration_status != RegistrationStatus.APPROVED:
                    logout(request)
                    messages.warning(
                        request,
                        "Your account is not approved yet. Please wait for approval.",
                    )
                    return redirect(reverse("login"))
        return self.get_response(request)
