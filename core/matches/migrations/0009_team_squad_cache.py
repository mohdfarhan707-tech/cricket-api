from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0008_team_form_stat"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamSquadCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team_id", models.PositiveIntegerField(unique=True)),
                ("team_code", models.CharField(max_length=16)),
                ("raw", models.JSONField()),
                ("fetched_at", models.DateTimeField(auto_now=True)),
            ],
            options={},
        ),
    ]

