from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0004_add_scorecard_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamComparisonStat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team_a", models.CharField(max_length=16)),
                ("team_b", models.CharField(max_length=16)),
                (
                    "scope",
                    models.CharField(
                        choices=[("overall", "Overall"), ("on_venue", "On Venue")],
                        default="overall",
                        max_length=16,
                    ),
                ),
                ("last_n", models.PositiveIntegerField(default=10)),
                ("matches_played_a", models.PositiveIntegerField(default=0)),
                ("matches_played_b", models.PositiveIntegerField(default=0)),
                ("win_pct_a", models.PositiveIntegerField(default=0)),
                ("win_pct_b", models.PositiveIntegerField(default=0)),
                ("avg_score_a", models.PositiveIntegerField(default=0)),
                ("avg_score_b", models.PositiveIntegerField(default=0)),
                ("highest_score_a", models.PositiveIntegerField(default=0)),
                ("highest_score_b", models.PositiveIntegerField(default=0)),
                ("lowest_score_a", models.PositiveIntegerField(default=0)),
                ("lowest_score_b", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="teamcomparisonstat",
            constraint=models.UniqueConstraint(fields=("team_a", "team_b", "scope"), name="uniq_teamcomp_pair_scope"),
        ),
    ]

