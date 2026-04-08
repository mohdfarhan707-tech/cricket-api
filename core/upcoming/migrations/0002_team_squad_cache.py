from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("upcoming", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamSquadCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team_id", models.CharField(max_length=32, unique=True)),
                ("fetched_at", models.DateTimeField(auto_now=True)),
                ("data", models.JSONField(blank=True, null=True)),
            ],
            options={},
        ),
    ]

