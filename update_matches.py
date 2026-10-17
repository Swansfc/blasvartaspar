import json
from datetime import datetime

# Lista över alla spelare i Lånespåret och Utlandsspåret som matchas mot datan
TRACK_PLAYERS = [
    # --- LÅNESPÅRET (Utlånade FRÅN Sirius) ---
    {"id": "1215994", "name": "Andreas Pyndt", "team": "FC Fredericia (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "1379389", "name": "Saba Mamatsashvili", "team": "Žalgiris Vilnius (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "1441735", "name": "Isaac Yawe Höök", "team": "IF Karlstad (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "1612928", "name": "Hugo Andersson Mella", "team": "IFK Värnamo (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "900559", "name": "Bogdan Milovanov", "team": "IF Gnistan (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "1782169", "name": "Finlay Neat", "team": "Norrby IF (lån)", "track": "lane", "trackName": "Lånespåret"},
    {"id": "1127365", "name": "Noel Milleskog", "team": "Degerfors IF (lån)", "track": "lane", "trackName": "Lånespåret"},

    # --- UTLANDSSPÅRET ---
    {"id": "1242516", "name": "Michael Martin", "team": "SGV Freiberg", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1399218", "name": "Robbie Ure", "team": "Sevilla", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1157905", "name": "Johan Karlsson", "team": "Vejle Boldklub", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "493159", "name": "Stefano Holmquist Vecchia", "team": "Aalesund", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1177212", "name": "Herman Sjögrell", "team": "FC Inter Turku", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1016540", "name": "Tobias Carlsson", "team": "FH Hafnarfjörður", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "566351", "name": "Diego Montiel", "team": "KA Akureyri", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "293718", "name": "Joeri de Kamps", "team": "Sepsi OSK", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "759565", "name": "Kristopher Da Graça", "team": "Krasava Ypsonas FC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "965710", "name": "Óli Valur Ómarsson", "team": "Breiðablik", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1276686", "name": "Leo Walta", "team": "Los Angeles FC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "561838", "name": "Isak Ssewankambo", "team": "Vancouver FC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "767777", "name": "Moustafa Zeidan", "team": "Al Masry SC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1022484", "name": "André Alsanati", "team": "Mosul SC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1000835", "name": "Jakob Tånnander", "team": "SC Farense", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1109472", "name": "Patrick Nwadike", "team": "Spartak Trnava", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "948374", "name": "Filip Majchrowicz", "team": "Radomiak Radom", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1457824", "name": "Malcolm Jeng", "team": "FC Groningen", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "961305", "name": "Benjamin Mbunga Kimpioka", "team": "Asteras Tripolis", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "839970", "name": "Magnus Kaastrup", "team": "Aarhus Fremad", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1183360", "name": "Yousef Salech", "team": "Cardiff City", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "793909", "name": "Joseph Colley", "team": "KF Tirana", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "831044", "name": "Hjalmar Ekdal", "team": "Burnley", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "639580", "name": "Marcus Mathisen", "team": "FC St. Pauli", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "619826", "name": "Jesper Nyholm", "team": "Prachuap FC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "982336", "name": "Tashreeq Matthews", "team": "Mamelodi Sundowns FC", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "528409", "name": "Kerim Mrabti", "team": "AEK Larnaca", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "474133", "name": "Aron Bjarnason", "team": "Breiðablik", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "919036", "name": "Wessam Abou Ali", "team": "Columbus Crew", "track": "utland", "trackName": "Utlandsspåret"},
    {"id": "1129082", "name": "Jamie Roche", "team": "Kortrijk", "track": "utland", "trackName": "Utlandsspåret"}
]

def generate_matches_json():
    # Här placerar du logiken för att hämta matchdata via API eller bygga din matches.json
    matches = []
    
    # Exempelstruktur för sparande till fil
    output_data = {
        "updated_at": datetime.now().isoformat(),
        "matches": matches
    }
    
    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Genererade matches.json med {len(TRACK_PLAYERS)} övervakade spelare.")

if __name__ == "__main__":
    generate_matches_json()
