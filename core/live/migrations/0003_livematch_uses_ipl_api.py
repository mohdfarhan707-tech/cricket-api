from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("live", "0002_livematch_is_finished"),
    ]

    operations = [
        migrations.AddField(
            model_name="livematch",
            name="uses_ipl_api",
            field=models.BooleanField(default=False),
        ),
    ]
