from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from accounts.roles import STAFF_GROUP


def give_staff_role(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    group_model = apps.get_model("auth", "Group")
    user_model = apps.get_model("auth", "User")
    group, _ = group_model.objects.get_or_create(name=STAFF_GROUP)
    for user in user_model.objects.filter(is_staff=True, is_superuser=False):
        user.groups.add(group)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(give_staff_role, migrations.RunPython.noop)]
