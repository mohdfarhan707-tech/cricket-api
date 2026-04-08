from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0006_team_lastn_stat"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamHeadToHeadStat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team_a", models.CharField(max_length=16)),
                ("team_b", models.CharField(max_length=16)),
                ("scope", models.CharField(choices=[("overall", "Overall")], default="overall", max_length=16)),
                ("played", models.PositiveIntegerField(default=0)),
                ("won_a", models.PositiveIntegerField(default=0)),
                ("won_b", models.PositiveIntegerField(default=0)),
                ("highest_total_a", models.PositiveIntegerField(default=0)),
                ("highest_total_b", models.PositiveIntegerField(default=0)),
                ("lowest_total_a", models.PositiveIntegerField(default=0)),
                ("lowest_total_b", models.PositiveIntegerField(default=0)),
                ("tosses_won_a", models.PositiveIntegerField(default=0)),
                ("tosses_won_b", models.PositiveIntegerField(default=0)),
                ("elected_to_bat_a", models.PositiveIntegerField(default=0)),
                ("elected_to_bat_b", models.PositiveIntegerField(default=0)),
                ("elected_to_field_a", models.PositiveIntegerField(default=0)),
                ("elected_to_field_b", models.PositiveIntegerField(default=0)),
                ("won_toss_and_match_a", models.PositiveIntegerField(default=0)),
                ("won_toss_and_match_b", models.PositiveIntegerField(default=0)),
                ("toss_won_bat_first_match_won_a", models.PositiveIntegerField(default=0)),
                ("toss_won_bat_first_match_won_b", models.PositiveIntegerField(default=0)),
                ("toss_won_bowl_first_match_won_a", models.PositiveIntegerField(default=0)),
                ("toss_won_bowl_first_match_won_b", models.PositiveIntegerField(default=0)),
                ("avg_runs_a", models.FloatField(default=0.0)),
                ("avg_runs_b", models.FloatField(default=0.0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="teamheadtoheadstat",
            constraint=models.UniqueConstraint(fields=("team_a", "team_b", "scope"), name="uniq_h2h_pair_scope"),
        ),
    ]

