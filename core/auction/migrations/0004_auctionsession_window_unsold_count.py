# Unsold tracking per 30-player auction window

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0003_budget_50cr"),
    ]

    operations = [
        migrations.AddField(
            model_name="auctionsession",
            name="window_unsold_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
