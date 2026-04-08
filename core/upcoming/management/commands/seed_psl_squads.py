from django.core.management.base import BaseCommand

from upcoming.models import TeamSquadCache


def _payload(batters, allrounders, bowlers):
    # Match Cricbuzz API shape we already parse in frontend
    out = []
    out.append({"name": "BATSMEN", "imageId": 174146})
    out.extend(batters)
    out.append({"name": "ALL ROUNDER", "imageId": 174146})
    out.extend(allrounders)
    out.append({"name": "BOWLER", "imageId": 174146})
    out.extend(bowlers)
    return {"player": out}


def _p(name: str):
    return {"id": name, "name": name, "imageId": 174146}


class Command(BaseCommand):
    help = "Seed PSL squads (manual, categorized) into TeamSquadCache."

    def handle(self, *args, **options):
        # Source: ProPakistani PSL 11 squads (Feb 11, 2026).
        # Roles are best-effort manual categorization.
        squads = {
            # Quetta Gladiators -> QTG
            "psl-QTG": _payload(
                batters=[
                    _p("Rilee Rossouw"),
                    _p("Saud Shakeel"),
                    _p("Hasan Nawaz"),
                    _p("Shamyl Hussain"),
                    _p("Sam Harper"),
                    _p("Ben McDermott"),
                    _p("Bevon Jacobs"),
                    _p("Bismillah Khan"),
                    _p("Khan Zaib"),
                ],
                allrounders=[
                    _p("Tom Curran"),
                    _p("Arafat Minhas"),
                    _p("Brett Hampton"),
                    _p("Jahandad Khan"),
                ],
                bowlers=[
                    _p("Abrar Ahmed"),
                    _p("Usman Tariq"),
                    _p("Spencer Johnson"),
                    _p("Faisal Akram"),
                    _p("Waseem Akram Jr."),
                    _p("Saqib Khan"),
                ],
            ),
            # Karachi Kings -> KRK
            "psl-KRK": _payload(
                batters=[
                    _p("David Warner"),
                    _p("Salman Ali Agha"),
                    _p("Azam Khan"),
                    _p("Johnson Charles"),
                    _p("Saad Baig"),
                    _p("Hamza Sohail"),
                ],
                allrounders=[
                    _p("Moeen Ali"),
                    _p("Khushdil Shah"),
                    _p("Aqib Ilyas"),
                    _p("Muhammad Waseem"),
                ],
                bowlers=[
                    _p("Hasan Ali"),
                    _p("Abbas Afridi"),
                    _p("Adam Zampa"),
                    _p("Mir Hamza"),
                    _p("Shahid Aziz"),
                    _p("Ihsanullah"),
                    _p("Rizwanullah"),
                ],
            ),
            # Islamabad United -> ISU
            "psl-ISU": _payload(
                batters=[
                    _p("Devon Conway"),
                    _p("Andries Gous"),
                    _p("Max Bryant"),
                    _p("Mark Chapman"),
                    _p("Sameer Minhas"),
                    _p("Haider Ali"),
                ],
                allrounders=[
                    _p("Shadab Khan"),
                    _p("Faheem Ashraf"),
                    _p("Imad Wasim"),
                    _p("Dipendra Singh Airee"),
                ],
                bowlers=[
                    _p("Salman Irshad"),
                    _p("Mohammad Wasim Jr."),
                    _p("Mehran Mumtaz"),
                    _p("Shamar Joseph"),
                    _p("Sameen Gul"),
                    _p("Mir Hamza Sajjad"),
                    _p("Richard Gleeson"),
                    _p("Mohammad Hasnain"),
                ],
            ),
            # Lahore Qalandars -> LHQ
            "psl-LHQ": _payload(
                batters=[
                    _p("Fakhar Zaman"),
                    _p("Abdullah Shafique"),
                    _p("Muhammad Naeem"),
                    _p("Asif Ali"),
                    _p("Parvez Hossain Emon"),
                    _p("Tayyab Tahir"),
                    _p("Haseebullah Khan"),
                ],
                allrounders=[
                    _p("Sikandar Raza"),
                    _p("Dasun Shanaka"),
                ],
                bowlers=[
                    _p("Shaheen Afridi"),
                    _p("Haris Rauf"),
                    _p("Usama Mir"),
                    _p("Ubaid Shah"),
                    _p("Mustafizur Rahman"),
                    _p("Gudakesh Motie"),
                    _p("Mohammad Farooq"),
                ],
            ),
            # Multan Sultans -> MS
            "psl-MS": _payload(
                batters=[
                    _p("Steve Smith"),
                    _p("Sahibzada Farhan"),
                    _p("Ashton Turner"),
                    _p("Shan Masood"),
                    _p("Josh Philippe"),
                ],
                allrounders=[
                    _p("Mohammad Nawaz"),
                    _p("Delano Potgieter"),
                ],
                bowlers=[
                    _p("Salman Mirza"),
                    _p("Ahmed Daniyal"),
                    _p("Peter Siddle"),
                    _p("Tabraiz Shamsi"),
                    _p("Arshad Iqbal"),
                    _p("Nisar Khan"),
                ],
            ),
            # Peshawar Zalmi -> PSZ
            "psl-PSZ": _payload(
                batters=[
                    _p("Babar Azam"),
                    _p("Abdul Samad"),
                    _p("Mohammad Haris"),
                    _p("James Vince"),
                    _p("Kusal Mendis"),
                ],
                allrounders=[
                    _p("Aaron Hardie"),
                    _p("Aamer Jamal"),
                    _p("Iftikhar Ahmed"),
                    _p("Michael Bracewell"),
                ],
                bowlers=[
                    _p("Sufiyan Muqeem"),
                    _p("Ali Raza"),
                    _p("Khurram Shahzad"),
                    _p("Khalid Usman"),
                    _p("Nahid Rana"),
                    _p("Kashif Ali"),
                ],
            ),
            # Hyderabad Kingsmen -> HKS
            "psl-HKS": _payload(
                batters=[
                    _p("Saim Ayub"),
                    _p("Maaz Sadaqat"),
                    _p("Usman Khan"),
                    _p("Marnus Labuschagne"),
                    _p("Kusal Perera"),
                    _p("Irfan Khan Niazi"),
                    _p("Shayan Jahangir"),
                    _p("Sharjeel Khan"),
                    _p("Tayyab Arif"),
                    _p("Ahmed Hussain"),
                    _p("Saad Ali"),
                ],
                allrounders=[
                    _p("Hassan Khan"),
                    _p("Hammad Azam"),
                ],
                bowlers=[
                    _p("Akif Javed"),
                    _p("Mohammad Ali"),
                    _p("Ottneil Baartman"),
                    _p("Hunain Shah"),
                    _p("Riley Meredith"),
                    _p("Asif Mehmood"),
                    _p("Rizwan Mehmood"),
                ],
            ),
            # Pindiz -> PND
            "psl-PND": _payload(
                batters=[
                    _p("Mohammad Rizwan"),
                    _p("Sam Billings"),
                    _p("Jake Fraser-McGurk"),
                    _p("Daryl Mitchell"),
                    _p("Kamran Ghulam"),
                    _p("Yasir Khan"),
                    _p("Laurie Evans"),
                    _p("Shahzaib Khan"),
                    _p("Abdullah Fazal"),
                ],
                allrounders=[
                    _p("Amad Butt"),
                    _p("Asif Afridi"),
                    _p("Rishad Hosain"),
                ],
                bowlers=[
                    _p("Naseem Shah"),
                    _p("Mohammad Amir"),
                    _p("Zaman Khan"),
                    _p("Mohammad Amir Khan"),
                ],
            ),
        }

        upserted = 0
        for team_id, data in squads.items():
            TeamSquadCache.objects.update_or_create(
                team_id=team_id,
                defaults={"data": data},
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} PSL squads into cache."))

