#!/usr/bin/env python3
"""Build data/matches.json from API-Football v3. API key must be a GitHub Actions secret."""
import json
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://v3.football.api-sports.io"
API_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
SEASON = int(os.environ.get("FOOTBALL_SEASON", datetime.now().year))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "7"))
LOOKAHEAD_DAYS = int(os.environ.get("LOOKAHEAD_DAYS", "7"))
OUT = ROOT / "data" / "matches.json"
HEADERS = {"x-apisports-key": API_KEY, "Accept": "application/json", "User-Agent": "BlasvartaSpar/1.0"}

def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)

def api(path, params):
    url = BASE_URL + path + "?" + urlencode(params)
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"API-Football HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"API-Football connection failed: {exc}") from exc
    if payload.get("errors"):
        raise RuntimeError(f"API-Football error: {payload['errors']}")
    return payload.get("response", [])

def pick(d, *keys):
    for key in keys:
        if isinstance(d, dict) and d.get(key) is not None:
            return d[key]
    return None

def main():
    if not API_KEY:
        print("Missing API_FOOTBALL_KEY environment variable.", file=sys.stderr)
        sys.exit(2)

    config = json.loads((ROOT / "players.json").read_text(encoding="utf-8"))
    start = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    end = (date.today() + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    output = []
    errors = []
    cache_team_search = {}
    cache_fixtures = {}

    for tracked in config["players"]:
        player_name = tracked["name"]
        team_name = tracked["team"]
        try:
            # Resolve team by API-Football's search endpoint; cache to avoid duplicate calls.
            if team_name not in cache_team_search:
                candidates = api("/teams", {"search": team_name})
                wanted = norm(team_name)
                exact = [x for x in candidates if norm(x.get("team", {}).get("name")) == wanted]
                selected = exact[0] if exact else (candidates[0] if candidates else None)
                cache_team_search[team_name] = selected
                time.sleep(0.25)
            team_record = cache_team_search[team_name]
            if not team_record:
                errors.append(f"{player_name}: could not resolve team '{team_name}'")
                continue
            team = team_record.get("team", {})
            team_id = team.get("id")
            if not team_id:
                errors.append(f"{player_name}: no team ID for '{team_name}'")
                continue

            cache_key = (team_id, start, end)
            if cache_key not in cache_fixtures:
                cache_fixtures[cache_key] = api("/fixtures", {
                    "team": team_id, "from": start, "to": end, "season": SEASON
                })
                time.sleep(0.25)

            for fixture in cache_fixtures[cache_key]:
                fx = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                goals = fixture.get("goals", {})
                league = fixture.get("league", {})
                fixture_id = fx.get("id")
                status = pick(fx.get("status", {}), "long", "short") or "Okänd status"
                match_date = str(fx.get("date", ""))[:10]
                if not fixture_id or not match_date:
                    continue

                # Player-level stats and ratings are only present where the provider has coverage.
                try:
                    players_response = api("/fixtures/players", {"fixture": fixture_id})
                    time.sleep(0.25)
                except Exception as exc:
                    errors.append(f"{player_name}: player stats fixture {fixture_id}: {exc}")
                    continue

                found = None
                for team_block in players_response:
                    for player_block in team_block.get("players", []):
                        p = player_block.get("player", {})
                        if norm(p.get("name")) == norm(player_name):
                            found = (p, player_block.get("statistics", [{}])[0])
                            break
                    if found:
                        break
                if not found:
                    # Don't invent a player appearance if the provider doesn't list the player.
                    continue

                player, stats = found
                games = stats.get("games", {}) or {}
                shots = stats.get("shots", {}) or {}
                goals_stats = stats.get("goals", {}) or {}
                passes = stats.get("passes", {}) or {}
                duels = stats.get("duels", {}) or {}
                home = teams.get("home", {}) or {}
                away = teams.get("away", {}) or {}
                score_home = goals.get("home")
                score_away = goals.get("away")
                output.append({
                    "playerName": player_name,
                    "playerId": str(player.get("id") or ""),
                    "track": tracked.get("track", "utland"),
                    "trackName": tracked.get("trackName", ""),
                    "playerTeam": team_name,
                    "position": games.get("position") or tracked.get("position", ""),
                    "leagueName": league.get("name", ""),
                    "matchDate": match_date,
                    "homeTeam": home.get("name", ""),
                    "awayTeam": away.get("name", ""),
                    "homeScore": score_home,
                    "awayScore": score_away,
                    "status": status,
                    "minutesPlayed": games.get("minutes"),
                    "goals": goals_stats.get("total"),
                    "assists": goals_stats.get("assists"),
                    "rating": stats.get("games", {}).get("rating"),
                    "passes": (f"{passes.get('total')}/{passes.get('total')}" if passes.get("total") is not None else None),
                    "chancesCreated": passes.get("key"),
                    "bigChancesCreated": None,
                    "shotsOnTarget": shots.get("on"),
                    "touches": stats.get("games", {}).get("appearences"),
                    "matchUrl": f"https://www.api-football.com/"
                })
        except Exception as exc:
            errors.append(f"{player_name} ({team_name}): {exc}")

    # Keep output deterministic and include provenance/update time for debugging.
    output.sort(key=lambda m: (m["matchDate"], m["playerName"]))
    result = {
        "matches": output,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "API-Football",
        "window": {"from": start, "to": end, "season": SEASON},
        "warnings": errors
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(output)} player-match rows to {OUT}")
    if errors:
        print("Warnings:")
        for err in errors:
            print(" - " + err)
    if not output:
        print("No player appearances found. Verify the API key, team names, season, and league coverage.")

if __name__ == "__main__":
    main()
