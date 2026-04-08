from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0007_team_headtohead_stat"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamFormStat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team", models.CharField(max_length=16)),
                ("last_n", models.PositiveIntegerField(default=5)),
                ("form", models.CharField(max_length=16)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="teamformstat",
            constraint=models.UniqueConstraint(fields=("team", "last_n"), name="uniq_team_form_lastn"),
        ),
    ]

