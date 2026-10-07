from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Concat

APPLICATION_REPR = "Заявка № "


def history_without_names(apps, schema_editor):
    content_types = apps.get_model("contenttypes", "ContentType").objects
    application_type = content_types.filter(app_label="applications", model="application").first()
    if application_type is None:
        return
    entries = apps.get_model("admin", "LogEntry").objects.filter(content_type=application_type)
    entries.update(object_repr=Concat(Value(APPLICATION_REPR), "object_id"))


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0012_closed_at"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(history_without_names, migrations.RunPython.noop)]
