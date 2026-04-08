from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0005_team_comparison_stat"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamLastNStat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team", models.CharField(max_length=16)),
                (
                    "scope",
                    models.CharField(
                        choices=[("overall", "Overall"), ("on_venue", "On Venue")],
                        default="overall",
                        max_length=16,
                    ),
                ),
                ("last_n", models.PositiveIntegerField(default=10)),
                ("matches_played", models.PositiveIntegerField(default=0)),
                ("win_pct", models.PositiveIntegerField(default=0)),
                ("avg_score", models.PositiveIntegerField(default=0)),
                ("highest_score", models.PositiveIntegerField(default=0)),
                ("lowest_score", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="teamlastnstat",
            constraint=models.UniqueConstraint(fields=("team", "scope"), name="uniq_team_lastn_scope"),
        ),
    ]

