from django.db import migrations

HIDDEN_ON_LANDING = ("Духовная Татьяна Сергеевна",)


def hide_on_landing(apps, schema_editor):
    apps.get_model("catalog", "Teacher").objects.filter(name__in=HIDDEN_ON_LANDING).update(hidden_on_landing=True)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_teacher_hidden_on_landing")]

    operations = [migrations.RunPython(hide_on_landing, migrations.RunPython.noop)]
