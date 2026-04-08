# Generated manually — mini auction default purse ₹50 Cr

from django.db import migrations, models


def forwards_budget(apps, schema_editor):
    AuctionTeam = apps.get_model("auction", "AuctionTeam")
    AuctionTeam.objects.filter(budget_lakhs=6000).update(budget_lakhs=5000)


def backwards_budget(apps, schema_editor):
    AuctionTeam = apps.get_model("auction", "AuctionTeam")
    AuctionTeam.objects.filter(budget_lakhs=5000).update(budget_lakhs=6000)


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0002_session_status_paused"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auctionteam",
            name="budget_lakhs",
            field=models.IntegerField(default=5000),
        ),
        migrations.RunPython(forwards_budget, backwards_budget),
    ]
