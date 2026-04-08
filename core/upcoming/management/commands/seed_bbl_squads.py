from django.core.management.base import BaseCommand

from upcoming.models import TeamSquadCache


def _payload(batters: list[str], allrounders: list[str], bowlers: list[str]) -> dict:
    """
    Match Cricbuzz-like squad payload shape already parsed in the frontend.

    Frontend parsing logic:
    - It iterates `data["player"]`.
    - Items with no `id` are treated as section headers (BATSMEN/ALL ROUNDER/BOWLER).
    - Items with `id` go into whichever section header is currently active.
    """
    image_id = 174146  # dummy image id; UI will try to load from Cricbuzz

    out: list[dict] = []
    out.append({"name": "BATSMEN", "imageId": image_id})
    for p in batters:
        out.append({"id": p, "name": p, "imageId": image_id})

    out.append({"name": "ALL ROUNDER", "imageId": image_id})
    for p in allrounders:
        out.append({"id": p, "name": p, "imageId": image_id})

    out.append({"name": "BOWLER", "imageId": image_id})
    for p in bowlers:
        out.append({"id": p, "name": p, "imageId": image_id})

    return {"player": out}


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        nx = (x or "").strip()
        if not nx:
            continue
        if nx in seen:
            continue
        seen.add(nx)
        out.append(nx)
    return out


def _prioritize_roles(
    batters: list[str],
    allrounders: list[str],
    bowlers: list[str],
):
    """
    Avoid duplicates across sections.

    Priority:
    - Bowlers first
    - Then all-rounders
    - Then batters
    """
    bowl_set = set(_dedupe_preserve_order(bowlers))
    all_dedup = _dedupe_preserve_order(allrounders)
    bat_dedup = _dedupe_preserve_order(batters)

    all_final = [p for p in all_dedup if p not in bowl_set]
    bat_final = [p for p in bat_dedup if p not in bowl_set and p not in set(all_final)]
    return bat_final, _dedupe_preserve_order(all_final), _dedupe_preserve_order(bowlers)


class Command(BaseCommand):
    help = "Seed BBL (Big Bash League) squads into TeamSquadCache for squad display."

    def handle(self, *args, **options):
        # Team keys match frontend `getInitials()` / `getTeamCodeDisplay()` for BBL:
        #   PS=Perth Scorchers, SS=Sydney Sixers, HH=Hobart Hurricanes, MR=Melbourne Renegades,
        #   BH=Brisbane Heat, AS=Adelaide Strikers, MS=Melbourne Stars, ST=Sydney Thunder
        #
        # Source: web-compiled 2025-26 squad lists (batsmen/all-rounders/wicketkeepers/bowlers).
        squads: dict[str, dict] = {
            "PS": _payload(
                *_prioritize_roles(
                    batters=[
                        "Nick Hobson",
                        "Zak Crawley",
                        "Laurie Evans",
                        "Finn Allen",
                        "Sam Fanning",
                        # wicket-keepers (treated as batters in UI)
                        "Josh Inglis",
                        "Joel Curtis",
                    ],
                    allrounders=[
                        "Ashton Agar",
                        "Aaron Hardie",
                        "Cooper Connolly",
                        "Mitchell Marsh",
                    ],
                    bowlers=[
                        "Jason Behrendorff",
                        "Matthew Kelly",
                        "Hamish McKenzie",
                        "Lance Morris",
                        "Jhye Richardson",
                        "Andrew Tye",
                        "Mahli Beardman",
                        "Bryce Jackson",
                        "David Payne",
                    ],
                )
            ),
            "SS": _payload(
                *_prioritize_roles(
                    batters=[
                        "Babar Azam",
                        "Daniel Hughes",
                        "Jack Edwards",
                        "Joel Davies",
                        "Jordan Silk",
                        "Steve Smith",
                        "Harjas Singh",
                        "Lachlan Shaw",
                        # wicket-keepers
                        "Josh Philippe",
                    ],
                    allrounders=[
                        "Moises Henriques",
                        "Sean Abbott",
                        "Hayden Kerr",
                        "Sam Curran",
                    ],
                    bowlers=[
                        "Ben Dwarshuis",
                        "Todd Murphy",
                        "Mitch Perry",
                        "Kane Richardson",
                        "Ben Manenti",
                        "Jafer Chohan",
                        # Abbott is listed as both all-rounder and bowler in sources; role priority keeps him in bowler.
                        "Sean Abbott",
                    ],
                )
            ),
            "BH": _payload(
                *_prioritize_roles(
                    batters=[
                        "Usman Khawaja",
                        "Colin Munro",
                        "Matt Renshaw",
                        "Marnus Labuschagne",
                        "Max Bryant",
                        "Lachlan Hearne",
                        "Hugh Weibgen",
                        # wicket-keepers
                        "Jimmy Peirson",
                        "Tom Alsop",
                    ],
                    allrounders=[
                        "Michael Neser",
                        "Jack Wildermuth",
                        "Nathan McSweeney",
                        "Thomas Balkin",
                    ],
                    bowlers=[
                        "Matthew Kuhnemann",
                        "Xavier Bartlett",
                        "Spencer Johnson",
                        "Jack Wood",
                        "Zaman Khan",
                        "Patrick Dooley",
                        "Callum Vidler",
                        "Liam Haskett",
                        "Shaheen Afridi",
                    ],
                )
            ),
            "MR": _payload(
                *_prioritize_roles(
                    batters=[
                        "Josh Brown",
                        "Harry Dixon",
                        "Jake Fraser-McGurk",
                        "Caleb Jewell",
                        "Oliver Peake",
                        # wicket-keepers
                        "Mohammad Rizwan",
                        "Tim Seifert",
                    ],
                    allrounders=[
                        "Will Sutherland",
                        "Hassan Khan",
                    ],
                    bowlers=[
                        "Adam Zampa",
                        "Jason Behrendorff",
                        "Tom Rogers",
                        "Brendan Doggett",
                        "Fergus O'Neill",
                        "Nathan Lyon",
                    ],
                )
            ),
            "HH": _payload(
                *_prioritize_roles(
                    batters=[
                        "Jake Weatherald",
                        "Mac Wright",
                        # wicket-keepers
                        "Matthew Wade",
                        "Ben McDermott",
                    ],
                    allrounders=[
                        "Tim David",
                        "Beau Webster",
                        "Rehan Ahmed",
                        "Rishad Hossain",
                        "Nikhil Chaudhary",
                        "Mitch Owen",
                    ],
                    bowlers=[
                        "Nathan Ellis",
                        "Riley Meredith",
                        "Billy Stanlake",
                        "Chris Jordan",
                        "Iain Carlisle",
                    ],
                )
            ),
            "AS": _payload(
                *_prioritize_roles(
                    batters=[
                        "Matt Short",
                        "Chris Lynn",
                        "Mackenzie Harvey",
                        "Thomas Kelly",
                        "Alex Ross",
                        "Jason Sangha",
                        "Travis Head",
                        "D'Arcy Short",
                        "Jake Weatherald",
                        # wicket-keepers
                        "Alex Carey",
                        "Harry Nielsen",
                    ],
                    allrounders=[
                        "Matt Short",
                        "Jamie Overton",
                        "Liam Scott",
                        "Harry Manenti",
                        "James Bazley",
                    ],
                    bowlers=[
                        "Hasan Ali",
                        "Cameron Boyce",
                        "Jordan Buckingham",
                        "Lloyd Pope",
                        "Henry Thornton",
                        "Luke Wood",
                    ],
                )
            ),
            "MS": _payload(
                *_prioritize_roles(
                    batters=[
                        "Hilton Cartwright",
                        "Campbell Kellaway",
                        "Tom Rogers",
                        "Sam Hain",
                        "Blake Macdonald",
                        # wicket-keepers
                        "Sam Harper",
                        "Joe Clarke",
                    ],
                    allrounders=[
                        "Marcus Stoinis",
                        "Glenn Maxwell",
                        "Tom Curran",
                        "Jonathan Merlo",
                        "Austin Anlezark",
                        "Aryan Sharma",
                    ],
                    bowlers=[
                        "Scott Boland",
                        "Liam Hatcher",
                        "Hamish McKenzie",
                        "Haris Rauf",
                        "Peter Siddle",
                        "Mark Steketee",
                        "Mitchell Swepson",
                        "Tom Whitney",
                        # appears in bowlers list on sources
                        "Austin Anlezark",
                    ],
                )
            ),
            "ST": _payload(
                *_prioritize_roles(
                    batters=[
                        "David Warner",
                        "Cameron Bancroft",
                        "Sam Billings",
                        "Oliver Davies",
                        "Sam Konstas",
                        "Nic Maddinson",
                        "Blake Nikitaras",
                        # wicket-keepers
                        "Matthew Gilkes",
                    ],
                    allrounders=[
                        "Tom Andrews",
                        "Chris Green",
                        "Shadab Khan",
                        "Nathan McAndrew",
                        "Daniel Sams",
                        "Ravichandran Ashwin",
                    ],
                    bowlers=[
                        "Wes Agar",
                        "Lockie Ferguson",
                        "Ryan Hadley",
                        "Tanveer Sangha",
                    ],
                )
            ),
        }

        upserted = 0
        for team_id, payload in squads.items():
            TeamSquadCache.objects.update_or_create(
                team_id=team_id,
                defaults={"data": payload},
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} BBL squads into cache."))

