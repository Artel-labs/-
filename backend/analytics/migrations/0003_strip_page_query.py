from django.db import migrations

from analytics.sanitize import page_path

BATCH = 1000


def strip_page_query(apps, schema_editor):
    Event = apps.get_model("analytics", "Event")
    changed = []
    for event in Event.objects.filter(path__contains="?").only("pk", "path").iterator(chunk_size=BATCH):
        event.path = page_path(event.path)
        changed.append(event)
    Event.objects.bulk_update(changed, ["path"], batch_size=BATCH)


class Migration(migrations.Migration):
    dependencies = [("analytics", "0002_purge_schedule")]

    operations = [migrations.RunPython(strip_page_query, migrations.RunPython.noop)]
