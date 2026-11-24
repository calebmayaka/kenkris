from django.conf import settings
from django.db import models


class PanelAccount(models.Model):
    """Per-user panel flags, kept out of the auth User model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="panel_account")
    must_change_password = models.BooleanField(
        default=False,
        help_text="Set when an administrator chooses this user's password; cleared once they pick their own.",
    )

    def __str__(self):
        return f"Panel account for {self.user}"


def require_password_change(user, required=True):
    PanelAccount.objects.update_or_create(user=user, defaults={"must_change_password": required})


def must_change_password(user):
    return PanelAccount.objects.filter(user=user, must_change_password=True).exists()
