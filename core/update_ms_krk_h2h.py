import os

import django


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    from matches.models import TeamHeadToHeadStat  # noqa: WPS433

    TeamHeadToHeadStat.objects.update_or_create(
        team_a="KRK",
        team_b="MS",
        scope="overall",
        defaults=dict(played=10, won_a=4, won_b=6),
    )
    print("ok")


if __name__ == "__main__":
    main()

