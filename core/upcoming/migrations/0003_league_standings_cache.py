from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("upcoming", "0002_team_squad_cache"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeagueStandingsCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("league", models.CharField(max_length=16, unique=True)),
                ("series_id", models.CharField(blank=True, default="", max_length=32)),
                ("data", models.JSONField(default=dict)),
                ("fetched_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
