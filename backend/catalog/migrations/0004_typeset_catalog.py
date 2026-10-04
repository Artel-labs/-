from django.db import migrations

from catalog.typesetting import typeset_program


def typeset_existing(apps, schema_editor):
    for program in apps.get_model("catalog", "Program").objects.all():
        typeset_program(program)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_catalog_position")]

    operations = [migrations.RunPython(typeset_existing, migrations.RunPython.noop)]
