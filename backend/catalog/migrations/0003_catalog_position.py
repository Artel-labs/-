from django.db import migrations, models


def number_by_import_order(apps, schema_editor):
    program = apps.get_model("catalog", "Program")
    for position, item in enumerate(program.objects.order_by("pk")):
        item.catalog_position = position
        item.save(update_fields=["catalog_position"])


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_sync_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="program",
            name="catalog_position",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Как в списке на hse.ru; программы, добавленные вручную, идут после",
                verbose_name="Порядок в каталоге",
            ),
        ),
        migrations.RunPython(number_by_import_order, migrations.RunPython.noop),
    ]
