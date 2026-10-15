#!/usr/bin/env python3
"""
Hämtar senaste matcher för spelarna ni följer från FotMob och skriver matches.json
i det format som index.html läser. Körs manuellt: python update_matches.py [dagar]

Inga värden hittas på: saknas ett fält hos FotMob skrivs null (visas som "–").
Bara Pythons standardbibliotek behövs.
"""
import json, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

OUT = Path(__file__).with_name("matches.json")
DAYS_BACK = int(sys.argv[1]) if len(sys.argv) > 1 else 30
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Lägg till/ta bort spelare här. id = siffrorna i FotMob-länken.
PLAYERS = [
    {"name": "Kerim Mrabti",    "id": "528409",  "track": "utland", "team": "AEK Larnaca"},
    {"name": "Herman Sjögrell", "id": "1177212", "track": "utland", "team": "FC Inter Turku"},
    {"name": "Aron Bjarnason",  "id": "474133",  "track": "utland", "team": "Breiðablik"},
    {"name": "Wessam Abou Ali", "id": "919036",  "track": "utland", "team": "Columbus Crew"},
    {"name": "Jamie Roche",     "id": "1129082", "track": "utland", "team": "Kortrijk"},
    {"name": "Jesper Nyholm",   "id": "619826",  "track": "utland", "team": "Prachuap FC"},
    {"name": "Tashreeq Matthews", "id": "982336", "track": "utland", "team": "Mamelodi Sundowns FC"},
    {"name": "Marcus Mathisen", "id": "639580", "track": "utland", "team": "FC St. Pauli"},
    {"name": "Hjalmar Ekdal", "id": "831044", "track": "utland", "team": "Burnley"},
    {"name": "Joseph Colley", "id": "793909", "track": "utland", "team": "KF Tirana"},
    {"name": "Yousef Salech", "id": "1183360", "track": "utland", "team": "Cardiff City"},
    {"name": "Magnus Kaastrup", "id": "839970", "track": "utland", "team": "Aarhus Fremad"},
    {"name": "Benjamin Mbunga Kimpioka", "id": "961305", "track": "utland", "team": "Asteras Tripolis"},
]


def get(url, as_json=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
        "Accept": "application/json" if as_json else "text/html"})
    with urllib.request.urlopen(req, timeout=25) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body) if as_json else body


def next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("hittade inte __NEXT_DATA__ (FotMob kan ha ändrat sidan eller blockerar)")
    return json.loads(m.group(1))


def player_data(pid):
    """Provar sidan, sedan API:t. Returnerar dict eller None."""
    try:
        nd = next_data(get(f"https://www.fotmob.com/sv/players/{pid}"))
        pp = (nd.get("props") or {}).get("pageProps") or {}
        data = pp.get("data") or pp.get("playerData")
        if isinstance(data, dict) and data:
            return data
        print(f"  sidan saknade spelardata (pageProps-nycklar: {list(pp.keys())[:8]})")
    except Exception as e:
        print(f"  sidan misslyckades ({e})")
    try:
        data = get(f"https://www.fotmob.com/api/playerData?id={pid}", as_json=True)
        if isinstance(data, dict) and data:
            return data
        print("  API:t gav tomt svar")
    except Exception as e:
        print(f"  API:t misslyckades ({e})")
    return None



UPCOMING_DAYS = 14
_fixture_cache = {}


def find_fixtures(node, out):
    """Letar rekursivt efter matchobjekt (har home, away och status med utcTime)."""
    if isinstance(node, dict):
        st = node.get("status")
        if isinstance(st, dict) and st.get("utcTime") and "home" in node and "away" in node:
            out.append(node)
        else:
            for v in node.values():
                find_fixtures(v, out)
    elif isinstance(node, list):
        for v in node:
            find_fixtures(v, out)


def team_fixtures(team_id):
    if team_id in _fixture_cache:
        return _fixture_cache[team_id]
    found = []
    for tab in ("fixtures", "overview"):
        try:
            nd = next_data(get(f"https://www.fotmob.com/sv/teams/{team_id}/{tab}"))
            find_fixtures(((nd.get("props") or {}).get("pageProps")) or {}, found)
            if found:
                break
        except Exception as e:
            print(f"  lagsidan ({tab}) misslyckades: {e}")
    uniq = {}
    for f in found:
        uniq[str(f.get("id"))] = f
    _fixture_cache[team_id] = list(uniq.values())
    time.sleep(0.7)
    return _fixture_cache[team_id]


def upcoming_rows(p, team_id, team_name, now):
    rows = []
    fx = team_fixtures(team_id)
    print(f"  matcher i lagets schema: {len(fx)}")
    horizon = now + timedelta(days=UPCOMING_DAYS)
    for f in fx:
        st = f.get("status") or {}
        if st.get("finished") or st.get("cancelled"):
            continue
        try:
            utc = datetime.fromisoformat(st["utcTime"].replace("Z", "+00:00"))
        except Exception:
            continue
        started = bool(st.get("started"))
        if not started and not (now - timedelta(hours=1) <= utc <= horizon):
            continue
        if started and utc < now - timedelta(hours=4):
            continue
        local = utc.astimezone(ZoneInfo("Europe/Stockholm"))
        sh = sa = None
        m = re.match(r"\s*(\d+)\s*-\s*(\d+)\s*$", str(st.get("scoreStr") or ""))
        if started and m:
            sh, sa = int(m.group(1)), int(m.group(2))
        tour = f.get("tournament") or {}
        page = f.get("pageUrl") or ""
        rows.append({
            "matchId": str(f.get("id", "")),
            "player": p["name"], "team": team_name, "playerId": p["id"], "track": p["track"],
            "league": tour.get("name") or tour.get("leagueName") or f.get("leagueName") or "",
            "matchDate": local.date().isoformat(), "kickoff": local.strftime("%H:%M"),
            "home": (f.get("home") or {}).get("name", ""), "away": (f.get("away") or {}).get("name", ""),
            "scoreHome": sh, "scoreAway": sa,
            "status": "Pågår" if started else "Kommande",
            "rating": None, "mins": None, "goals": None, "ass": None, "passes": None, "chances": None,
            "matchUrl": ("https://www.fotmob.com" + page) if page else "",
        })
    rows.sort(key=lambda r: (r["matchDate"], r["kickoff"]))
    return rows


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def match_details(match_url, pid):
    """Extra statistik (passningar m.m.) från matchsidan. Best effort."""
    out = {}
    try:
        d = next_data(get("https://www.fotmob.com" + match_url))
        content = ((d.get("props") or {}).get("pageProps") or {}).get("content") or {}
        ps = (content.get("playerStats") or {}).get(str(pid))
        if not ps:
            return out
        found = {}
        for grp in ps.get("stats") or []:
            for title, obj in ((grp or {}).get("stats") or {}).items():
                found[title.lower()] = ((obj or {}).get("stat")) or {}
        def val(*names):
            for n in names:
                if n in found:
                    return found[n]
            return None
        p = val("accurate passes")
        if p and p.get("value") is not None and p.get("total") is not None:
            out["passes"] = f'{p["value"]}/{p["total"]}'
        r = val("fotmob rating")
        if r and num(r.get("value")) is not None:
            out["rating"] = num(r["value"])
        for key, names in {"chances": ("chances created",), "bigChances": ("big chances created",),
                           "shotsTarget": ("shots on target",), "touches": ("touches",)}.items():
            s_ = val(*names)
            if s_ and s_.get("value") is not None:
                out[key] = s_["value"]
    except Exception as e:
        print(f"    (ingen detaljstatistik: {e})")
    return out


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            pass
    kept = {(m["playerId"], m["matchId"]): m for m in old.get("matches", [])
            if m.get("matchId") and m.get("status") not in ("Kommande", "Pågår")}
    now = datetime.now(timezone.utc)
    ok = 0

    for p in PLAYERS:
        print(f'{p["name"]} ({p["id"]})')
        try:
            data = player_data(p["id"])
        except Exception as e:
            print(f"  FEL: {e}")
            continue
        if not data:
            print("  hoppar över spelaren (ingen data)")
            continue
        ok += 1
        fm_name = data.get("name") or "?"
        fm_team = (data.get("primaryTeam") or {}).get("teamName") or "?"
        warn = "" if fm_name.lower() == p["name"].lower() else "   <-- OBS: NAMNET STÄMMER INTE, kontrollera ID"
        print(f"  FotMob säger: {fm_name} ({fm_team}){warn}")
        recent = data.get("recentMatches") or []
        if isinstance(recent, dict):
            recent = recent.get("matches", [])
        team = (data.get("primaryTeam") or {}).get("teamName") or p["team"]
        if recent:
            print(f"  fält i matchlistan: {sorted(recent[0].keys())}")
        else:
            print(f"  inga recentMatches (nycklar i data: {sorted(data.keys())[:10]})")
        if recent:
            try:
                print(f"  senaste match hos FotMob: {recent[0]['matchDate']['utcTime'][:10]}")
                print(f"  ratingProps (första): {recent[0].get('ratingProps')}")
            except Exception:
                pass
        for r in recent:
            try:
                utc = datetime.fromisoformat(
                    (r.get("matchDate") or {}).get("utcTime", "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if utc < cutoff:
                continue
            home_is_player = bool(r.get("isHomeTeam"))
            mine, opp = r.get("teamName", ""), r.get("opponentTeamName", "")
            row = {
                "matchId": str(r.get("id", "")),
                "player": p["name"], "team": team, "playerId": p["id"], "track": p["track"],
                "league": r.get("leagueName", ""),
                "matchDate": utc.astimezone(ZoneInfo("Europe/Stockholm")).date().isoformat(),
                "home": mine if home_is_player else opp,
                "away": opp if home_is_player else mine,
                "scoreHome": r.get("homeScore"), "scoreAway": r.get("awayScore"),
                "status": "Slut",
                "rating": (num((r.get("ratingProps") or {}).get("rating")) or None),
                "mins": r.get("minutesPlayed"), "goals": r.get("goals"), "ass": r.get("assists"),
                "passes": None, "chances": None,
                "matchUrl": ("https://www.fotmob.com" + r["matchPageUrl"]) if r.get("matchPageUrl") else "",
            }
            if r.get("onBench") and not row["mins"]:
                row["status"] = "Slut (bänken)"
            if r.get("matchPageUrl") and row["mins"]:
                det = match_details(r["matchPageUrl"], p["id"])
                if row["rating"] is not None:
                    det.pop("rating", None)
                elif det.get("rating"):
                    det["rating"] = round(det["rating"], 1)
                row.update(det)
                time.sleep(0.7)
            kept[(p["id"], row["matchId"])] = row
            print(f'  {row["matchDate"]} {row["home"]} {row["scoreHome"]}-{row["scoreAway"]} {row["away"]}'
                  f' | betyg {row["rating"]} | {row["mins"]} min')
        tid = (data.get("primaryTeam") or {}).get("teamId")
        if tid:
            try:
                ups = upcoming_rows(p, tid, team, now)
                for row in ups:
                    key = (p["id"], row["matchId"])
                    if key not in kept:
                        kept[key] = row
                if ups:
                    n = ups[0]
                    print(f'  nästa: {n["matchDate"]} {n["kickoff"]} {n["home"]} - {n["away"]} ({n["status"]})')
                else:
                    print("  inga kommande matcher hittades")
            except Exception as e:
                print(f"  kunde inte hämta kommande matcher: {e}")
        else:
            print("  hittade inget lag-ID, hoppar över kommande matcher")
        time.sleep(1)

    if ok == 0:
        sys.exit("Ingen spelare kunde hämtas - matches.json lämnas orörd.")

    matches = sorted(kept.values(), key=lambda m: (m["matchDate"], m.get("kickoff", ""), m["player"]), reverse=True)
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "matches": matches, "players": old.get("players", {})}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nKlart: {len(matches)} matcher skrivna till {OUT.name}")


if __name__ == "__main__":
    main()
