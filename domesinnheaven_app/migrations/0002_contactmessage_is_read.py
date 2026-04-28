from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("domesinnheaven_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="is_read",
            field=models.BooleanField(default=False),
        ),
    ]
