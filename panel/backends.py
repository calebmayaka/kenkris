from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    """Sign in with the username in any letter case ("caleb", "Caleb", "CALEB")."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User._default_manager.get(**{f"{User.USERNAME_FIELD}__iexact": username})
        except User.DoesNotExist:
            User().set_password(password)  # same timing as a real check, to avoid username probing
            return None
        except User.MultipleObjectsReturned:
            # Only possible for accounts created outside the panel; fall back to exact match.
            return super().authenticate(request, username=username, password=password, **kwargs)
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
