"""
PSL player pool — names and roles aligned with `seed_psl_squads.py` squad data.
"""
from __future__ import annotations

from .auction_engine import ALLOWED_BASE_PRICE_LAKHS
from .models import AuctionPlayer as P


def resolve_psl_base_price_lakhs(name: str) -> int:
    """Deterministic base from name (same slabs as IPL auction)."""
    tiers = ALLOWED_BASE_PRICE_LAKHS
    return tiers[sum(ord(c) for c in name) % len(tiers)]


def get_psl_player_rows() -> list[dict[str, str]]:
    raw: list[tuple[str, str]] = [
        # Quetta Gladiators
        ("Rilee Rossouw", P.CAT_BAT),
        ("Saud Shakeel", P.CAT_BAT),
        ("Hasan Nawaz", P.CAT_BAT),
        ("Shamyl Hussain", P.CAT_BAT),
        ("Sam Harper", P.CAT_WK),
        ("Ben McDermott", P.CAT_BAT),
        ("Bevon Jacobs", P.CAT_BAT),
        ("Bismillah Khan", P.CAT_WK),
        ("Khan Zaib", P.CAT_BAT),
        ("Tom Curran", P.CAT_AR),
        ("Arafat Minhas", P.CAT_AR),
        ("Brett Hampton", P.CAT_AR),
        ("Jahandad Khan", P.CAT_AR),
        ("Abrar Ahmed", P.CAT_BOWL),
        ("Usman Tariq", P.CAT_BOWL),
        ("Spencer Johnson", P.CAT_BOWL),
        ("Faisal Akram", P.CAT_BOWL),
        ("Waseem Akram Jr.", P.CAT_BOWL),
        ("Saqib Khan", P.CAT_BOWL),
        # Karachi Kings
        ("David Warner", P.CAT_BAT),
        ("Salman Ali Agha", P.CAT_BAT),
        ("Azam Khan", P.CAT_WK),
        ("Johnson Charles", P.CAT_BAT),
        ("Saad Baig", P.CAT_WK),
        ("Hamza Sohail", P.CAT_BAT),
        ("Moeen Ali", P.CAT_AR),
        ("Khushdil Shah", P.CAT_AR),
        ("Aqib Ilyas", P.CAT_AR),
        ("Muhammad Waseem", P.CAT_AR),
        ("Hasan Ali", P.CAT_BOWL),
        ("Abbas Afridi", P.CAT_BOWL),
        ("Adam Zampa", P.CAT_BOWL),
        ("Mir Hamza", P.CAT_BOWL),
        ("Shahid Aziz", P.CAT_BOWL),
        ("Ihsanullah", P.CAT_BOWL),
        ("Rizwanullah", P.CAT_BOWL),
        # Islamabad United
        ("Devon Conway", P.CAT_BAT),
        ("Andries Gous", P.CAT_WK),
        ("Max Bryant", P.CAT_BAT),
        ("Mark Chapman", P.CAT_BAT),
        ("Sameer Minhas", P.CAT_BAT),
        ("Haider Ali", P.CAT_BAT),
        ("Shadab Khan", P.CAT_AR),
        ("Faheem Ashraf", P.CAT_AR),
        ("Imad Wasim", P.CAT_AR),
        ("Dipendra Singh Airee", P.CAT_AR),
        ("Salman Irshad", P.CAT_BOWL),
        ("Mohammad Wasim Jr.", P.CAT_BOWL),
        ("Mehran Mumtaz", P.CAT_BOWL),
        ("Shamar Joseph", P.CAT_BOWL),
        ("Sameen Gul", P.CAT_BOWL),
        ("Mir Hamza Sajjad", P.CAT_BOWL),
        ("Richard Gleeson", P.CAT_BOWL),
        ("Mohammad Hasnain", P.CAT_BOWL),
        # Lahore Qalandars
        ("Fakhar Zaman", P.CAT_BAT),
        ("Abdullah Shafique", P.CAT_BAT),
        ("Muhammad Naeem", P.CAT_BAT),
        ("Asif Ali", P.CAT_BAT),
        ("Parvez Hossain Emon", P.CAT_BAT),
        ("Tayyab Tahir", P.CAT_BAT),
        ("Haseebullah Khan", P.CAT_WK),
        ("Sikandar Raza", P.CAT_AR),
        ("Dasun Shanaka", P.CAT_AR),
        ("Shaheen Afridi", P.CAT_BOWL),
        ("Haris Rauf", P.CAT_BOWL),
        ("Usama Mir", P.CAT_BOWL),
        ("Ubaid Shah", P.CAT_BOWL),
        ("Mustafizur Rahman", P.CAT_BOWL),
        ("Gudakesh Motie", P.CAT_BOWL),
        ("Mohammad Farooq", P.CAT_BOWL),
        # Multan Sultans
        ("Steve Smith", P.CAT_BAT),
        ("Sahibzada Farhan", P.CAT_BAT),
        ("Ashton Turner", P.CAT_BAT),
        ("Shan Masood", P.CAT_BAT),
        ("Josh Philippe", P.CAT_WK),
        ("Mohammad Nawaz", P.CAT_AR),
        ("Delano Potgieter", P.CAT_AR),
        ("Salman Mirza", P.CAT_BOWL),
        ("Ahmed Daniyal", P.CAT_BOWL),
        ("Peter Siddle", P.CAT_BOWL),
        ("Tabraiz Shamsi", P.CAT_BOWL),
        ("Arshad Iqbal", P.CAT_BOWL),
        ("Nisar Khan", P.CAT_BOWL),
        # Peshawar Zalmi
        ("Babar Azam", P.CAT_BAT),
        ("Abdul Samad", P.CAT_BAT),
        ("Mohammad Haris", P.CAT_WK),
        ("James Vince", P.CAT_BAT),
        ("Kusal Mendis", P.CAT_WK),
        ("Aaron Hardie", P.CAT_AR),
        ("Aamer Jamal", P.CAT_AR),
        ("Iftikhar Ahmed", P.CAT_AR),
        ("Michael Bracewell", P.CAT_AR),
        ("Sufiyan Muqeem", P.CAT_BOWL),
        ("Ali Raza", P.CAT_BOWL),
        ("Khurram Shahzad", P.CAT_BOWL),
        ("Khalid Usman", P.CAT_BOWL),
        ("Nahid Rana", P.CAT_BOWL),
        ("Kashif Ali", P.CAT_BOWL),
        # Hyderabad Kingsmen
        ("Saim Ayub", P.CAT_BAT),
        ("Maaz Sadaqat", P.CAT_BAT),
        ("Usman Khan", P.CAT_BAT),
        ("Marnus Labuschagne", P.CAT_BAT),
        ("Kusal Perera", P.CAT_WK),
        ("Irfan Khan Niazi", P.CAT_BAT),
        ("Shayan Jahangir", P.CAT_BAT),
        ("Sharjeel Khan", P.CAT_BAT),
        ("Tayyab Arif", P.CAT_BAT),
        ("Ahmed Hussain", P.CAT_BAT),
        ("Saad Ali", P.CAT_BAT),
        ("Hassan Khan", P.CAT_AR),
        ("Hammad Azam", P.CAT_AR),
        ("Akif Javed", P.CAT_BOWL),
        ("Mohammad Ali", P.CAT_BOWL),
        ("Ottneil Baartman", P.CAT_BOWL),
        ("Hunain Shah", P.CAT_BOWL),
        ("Riley Meredith", P.CAT_BOWL),
        ("Asif Mehmood", P.CAT_BOWL),
        ("Rizwan Mehmood", P.CAT_BOWL),
        # Pindiz
        ("Mohammad Rizwan", P.CAT_BAT),
        ("Sam Billings", P.CAT_WK),
        ("Jake Fraser-McGurk", P.CAT_BAT),
        ("Daryl Mitchell", P.CAT_AR),
        ("Kamran Ghulam", P.CAT_BAT),
        ("Yasir Khan", P.CAT_BAT),
        ("Laurie Evans", P.CAT_BAT),
        ("Shahzaib Khan", P.CAT_BAT),
        ("Abdullah Fazal", P.CAT_BAT),
        ("Amad Butt", P.CAT_AR),
        ("Asif Afridi", P.CAT_AR),
        ("Rishad Hosain", P.CAT_AR),
        ("Naseem Shah", P.CAT_BOWL),
        ("Mohammad Amir", P.CAT_BOWL),
        ("Zaman Khan", P.CAT_BOWL),
        ("Mohammad Amir Khan", P.CAT_BOWL),
    ]

    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for name, cat in raw:
        if name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "category": cat})
    return out
