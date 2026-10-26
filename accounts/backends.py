from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Lets people sign in with either their username or their email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by("id").first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
