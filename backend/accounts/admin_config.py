from django.contrib.admin.apps import AdminConfig


class DpoAdminConfig(AdminConfig):
    default_site = "accounts.sites.DpoAdminSite"
