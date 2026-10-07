from django.db import migrations, models

from accounts.secret_box import is_sealed, seal, unseal


def seal_secrets(apps, schema_editor):
    TwoFactor = apps.get_model("accounts", "TwoFactor")
    for device in TwoFactor.objects.all():
        if not is_sealed(device.sealed_secret):
            device.sealed_secret = seal(device.sealed_secret)
            device.save(update_fields=["sealed_secret"])


def unseal_secrets(apps, schema_editor):
    TwoFactor = apps.get_model("accounts", "TwoFactor")
    for device in TwoFactor.objects.all():
        if is_sealed(device.sealed_secret):
            device.sealed_secret = unseal(device.sealed_secret)
            device.save(update_fields=["sealed_secret"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_staff_role")]

    operations = [
        migrations.RenameField("twofactor", "secret", "sealed_secret"),
        migrations.AlterField(
            model_name="twofactor",
            name="sealed_secret",
            field=models.CharField(max_length=255, verbose_name="Секрет (зашифрован)"),
        ),
        migrations.RunPython(seal_secrets, unseal_secrets),
    ]
