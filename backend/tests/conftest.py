import pytest

PLAIN_STATIC = "django.contrib.staticfiles.storage.StaticFilesStorage"


@pytest.fixture(autouse=True)
def plain_static_files(settings):
    settings.STORAGES = {**settings.STORAGES, "staticfiles": {"BACKEND": PLAIN_STATIC}}
