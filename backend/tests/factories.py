from django.contrib.auth.models import User

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "Надёжный-пароль-2026"


def make_admin() -> User:
    return User.objects.create_superuser(ADMIN_LOGIN, "admin@example.com", ADMIN_PASSWORD)
