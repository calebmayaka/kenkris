from django.shortcuts import redirect
from django.urls import reverse

from .models import must_change_password

# Panel pages a user may still visit while a password change is pending.
ALLOWED_URL_NAMES = {"password_change", "logout", "login"}


class ForcePasswordChangeMiddleware:
    """Send panel users with a temporary password to the change-password page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if not match or match.app_name != "panel" or match.url_name in ALLOWED_URL_NAMES:
            return None
        user = request.user
        if user.is_authenticated and user.is_staff and must_change_password(user):
            return redirect(reverse("panel:password_change"))
        return None
