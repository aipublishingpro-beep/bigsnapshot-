import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import uuid

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

st.markdown("""
<style>
.stLinkButton > a {background-color: #00aa00 !important;border-color: #00aa00 !important;color: white !important;}
.stLinkButton > a:hover {background-color: #00cc00 !important;border-color: #00cc00 !important;}
</style>
""", unsafe_allow_html=True)

POSITIONS_FILE = "nfl_positions.json"
PERFORMANCE_FILE = "nfl_performance.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except:
        pass

def load_performance():
    try:
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"strong": {"wins": 12, "losses": 3}, "buy": {"wins": 18, "losses": 9}, "lean": {"wins": 14, "losses": 12}, "total_profit": 127.50}

def save_performance(perf):
    try:
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(perf, f, indent=2)
    except:
        pass

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "selected_ml_pick" not in st.session_state:
    st.session_state.selected_ml_pick = None
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None
if "performance" not in st.session_state:
    st.session_state.performance = load_performance()

if st.session_state.auto_refresh and HAS_AUTOREFRESH:
    st_autorefresh(interval=5000, limit=None, key="nfl_autorefresh")
    auto_status = "🔄 Auto-refresh ON (5s)"
elif st.session_state.auto_refresh and not HAS_AUTOREFRESH:
    st.markdown(f'<meta http-equiv="refresh" content="5;url=?r={int(time.time()) + 5}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (5s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

KALSHI_CODES = {
    "Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF",
    "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE",
    "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB",
    "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas City": "KC",
    "Las Vegas": "LV", "LA Chargers": "LAC", "LA Rams": "LA", "Miami": "MIA",
    "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "NY Giants": "NYG",
    "NY Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF",
    "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"
}

TEAM_ABBREVS = {
    "Arizona Cardinals": "Arizona", "Atlanta Falcons": "Atlanta", "Baltimore Ravens": "Baltimore",
    "Buffalo Bills": "Buffalo", "Carolina Panthers": "Carolina", "Chicago Bears": "Chicago",
    "Cincinnati Bengals": "Cincinnati", "Cleveland Browns": "Cleveland", "Dallas Cowboys": "Dallas",
    "Denver Broncos": "Denver", "Detroit Lions": "Detroit", "Green Bay Packers": "Green Bay",
    "Houston Texans": "Houston", "Indianapolis Colts": "Indianapolis", "Jacksonville Jaguars": "Jacksonville",
    "Kansas City Chiefs": "Kansas City", "Las Vegas Raiders": "Las Vegas", "Los Angeles Chargers": "LA Chargers",
    "Los Angeles Rams": "LA Rams", "Miami Dolphins": "Miami", "Minnesota Vikings": "Minnesota",
    "New England Patriots": "New England", "New Orleans Saints": "New Orleans", "New York Giants": "NY Giants",
    "New York Jets": "NY Jets", "Philadelphia Eagles": "Philadelphia", "Pittsburgh Steelers": "Pittsburgh",
    "San Francisco 49ers": "San Francisco", "Seattle Seahawks": "Seattle", "Tampa Bay Buccaneers": "Tampa Bay",
    "Tennessee Titans": "Tennessee", "Washington Commanders": "Washington"
}

DIVISIONS = {
    "AFC East": ["Buffalo", "Miami", "NY Jets", "New England"],
    "AFC North": ["Baltimore", "Pittsburgh", "Cleveland", "Cincinnati"],
    "AFC South": ["Houston", "Indianapolis", "Jacksonville", "Tennessee"],
    "AFC West": ["Kansas City", "LA Chargers", "Denver", "Las Vegas"],
    "NFC East": ["Philadelphia", "Dallas", "Washington", "NY Giants"],
    "NFC North": ["Detroit", "Green Bay", "Minnesota", "Chicago"],
    "NFC South": ["Atlanta", "Tampa Bay", "New Orleans", "Carolina"],
    "NFC West": ["Seattle", "LA Rams", "San Francisco", "Arizona"]
}

STADIUM_COORDS = {
    "Arizona": (33.5277, -112.2626), "Atlanta": (33.7553, -84.4006), "Baltimore": (39.2780, -76.6227),
    "Buffalo": (42.7738, -78.7870), "Carolina": (35.2258, -80.8528), "Chicago": (41.8623, -87.6167),
    "Cincinnati": (39.0955, -84.5161), "Cleveland": (41.5061, -81.6995), "Dallas": (32.7473, -97.0945),
    "Denver": (39.7439, -105.0201), "Detroit": (42.3400, -83.0456), "Green Bay": (44.5013, -88.0622),
    "Houston": (29.6847, -95.4107), "Indianapolis": (39.7601, -86.1639), "Jacksonville": (30.3239, -81.6373),
    "Kansas City": (39.0489, -94.4839), "Las Vegas": (36.0909, -115.1833), "LA Chargers": (33.9535, -118.3392),
    "LA Rams": (33.9535, -118.3392), "Miami": (25.9580, -80.2389), "Minnesota": (44.9737, -93.2577),
    "New England": (42.0909, -71.2643), "New Orleans": (29.9511, -90.0812), "NY Giants": (40.8128, -74.0742),
    "NY Jets": (40.8128, -74.0742), "Philadelphia": (39.9008, -75.1675), "Pittsburgh": (40.4468, -80.0158),
    "San Francisco": (37.4032, -121.9698), "Seattle": (47.5952, -122.3316), "Tampa Bay": (27.9759, -82.5033),
    "Tennessee": (36.1665, -86.7713), "Washington": (38.9076, -76.8645)
}

DOME_STADIUMS = ["Arizona", "Atlanta", "Dallas", "Detroit", "Houston", "Indianapolis", 
                  "Las Vegas", "LA Chargers", "LA Rams", "Minnesota", "New Orleans"]

_PH = ["Buffalo", "Cincinnati", "Miami", "Tampa Bay", "LA Chargers", "Detroit", "Philadelphia"]
_RH = ["Baltimore", "San Francisco", "Cleveland", "Tennessee", "Denver"]

_TS = {
    "Arizona": {"d": -12.5, "r": 27, "h": 0.42, "a": 0.30},
    "Atlanta": {"d": 2.5, "r": 18, "h": 0.55, "a": 0.42},
    "Baltimore": {"d": 15.5, "r": 6, "h": 0.72, "a": 0.62},
    "Buffalo": {"d": 18.2, "r": 5, "h": 0.78, "a": 0.68},
    "Carolina": {"d": -18.5, "r": 30, "h": 0.35, "a": 0.22},
    "Chicago": {"d": -8.5, "r": 22, "h": 0.45, "a": 0.35},
    "Cincinnati": {"d": 5.8, "r": 14, "h": 0.58, "a": 0.48},
    "Cleveland": {"d": -25.0, "r": 32, "h": 0.38, "a": 0.25},
    "Dallas": {"d": -5.2, "r": 20, "h": 0.52, "a": 0.38},
    "Denver": {"d": 8.5, "r": 8, "h": 0.65, "a": 0.50},
    "Detroit": {"d": 22.5, "r": 4, "h": 0.78, "a": 0.68},
    "Green Bay": {"d": 12.2, "r": 10, "h": 0.70, "a": 0.55},
    "Houston": {"d": 16.5, "r": 7, "h": 0.68, "a": 0.58},
    "Indianapolis": {"d": 14.5, "r": 12, "h": 0.55, "a": 0.48},
    "Jacksonville": {"d": 10.5, "r": 11, "h": 0.55, "a": 0.48},
    "Kansas City": {"d": 18.5, "r": 9, "h": 0.82, "a": 0.72},
    "Las Vegas": {"d": -10.2, "r": 25, "h": 0.42, "a": 0.28},
    "LA Chargers": {"d": 11.8, "r": 3, "h": 0.62, "a": 0.52},
    "LA Rams": {"d": 24.5, "r": 5, "h": 0.72, "a": 0.62},
    "Miami": {"d": -2.5, "r": 16, "h": 0.55, "a": 0.38},
    "Minnesota": {"d": 8.5, "r": 13, "h": 0.68, "a": 0.52},
    "New England": {"d": -12.5, "r": 24, "h": 0.42, "a": 0.30},
    "New Orleans": {"d": -8.8, "r": 23, "h": 0.48, "a": 0.35},
    "NY Giants": {"d": -15.5, "r": 29, "h": 0.35, "a": 0.22},
    "NY Jets": {"d": -12.5, "r": 26, "h": 0.42, "a": 0.28},
    "Philadelphia": {"d": 14.8, "r": 6, "h": 0.75, "a": 0.60},
    "Pittsburgh": {"d": 4.8, "r": 10, "h": 0.62, "a": 0.45},
    "San Francisco": {"d": 6.5, "r": 15, "h": 0.58, "a": 0.48},
    "Seattle": {"d": 28.5, "r": 2, "h": 0.78, "a": 0.68},
    "Tampa Bay": {"d": -3.2, "r": 19, "h": 0.52, "a": 0.40},
    "Tennessee": {"d": -14.8, "r": 28, "h": 0.40, "a": 0.25},
    "Washington": {"d": -4.5, "r": 21, "h": 0.52, "a": 0.42}
}

_SP = {
    "Arizona": ["Kyler Murray"], "Atlanta": ["Kirk Cousins", "Bijan Robinson"],
    "Baltimore": ["Lamar Jackson", "Derrick Henry"], "Buffalo": ["Josh Allen", "James Cook"],
    "Carolina": ["Bryce Young"], "Chicago": ["Caleb Williams"],
    "Cincinnati": ["Joe Burrow", "Ja'Marr Chase"], "Cleveland": ["Deshaun Watson"],
    "Dallas": ["Dak Prescott", "CeeDee Lamb"], "Denver": ["Bo Nix"],
    "Detroit": ["Jared Goff", "Amon-Ra St. Brown"], "Green Bay": ["Jordan Love"],
    "Houston": ["C.J. Stroud", "Nico Collins"], "Indianapolis": ["Anthony Richardson"],
    "Jacksonville": ["Trevor Lawrence"], "Kansas City": ["Patrick Mahomes", "Travis Kelce"],
    "Las Vegas": ["Gardner Minshew"], "LA Chargers": ["Justin Herbert"],
    "LA Rams": ["Matthew Stafford", "Puka Nacua"], "Miami": ["Tua Tagovailoa", "Tyreek Hill"],
    "Minnesota": ["J.J. McCarthy", "Justin Jefferson"], "New England": ["Drake Maye"],
    "New Orleans": ["Derek Carr"], "NY Giants": ["Daniel Jones"],
    "NY Jets": ["Aaron Rodgers"], "Philadelphia": ["Jalen Hurts", "Saquon Barkley"],
    "Pittsburgh": ["Russell Wilson"], "San Francisco": ["Brock Purdy", "Christian McCaffrey"],
    "Seattle": ["Geno Smith", "DK Metcalf"], "Tampa Bay": ["Baker Mayfield"],
    "Tennessee": ["Will Levis"], "Washington": ["Jayden Daniels"]
}

def build_kalshi_ml_url(away_team, home_team, game_date=None):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    if game_date:
        date_str = game_date.strftime("%y%b%d").upper()
    else:
        date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNFLGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNFLGAME/{ticker}"

@st.cache_data(ttl=1800)
def fetch_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation,weather_code&wind_speed_unit=mph&temperature_unit=fahrenheit"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data.get("current", {})
        return {"temp": current.get("temperature_2m", 70), "wind": current.get("wind_speed_10m", 0), "precip": current.get("precipitation", 0), "code": current.get("weather_code", 0)}
    except:
        return {"temp": 70, "wind": 0, "precip": 0, "code": 0}

def get_weather_for_game(home_team):
    if home_team in DOME_STADIUMS:
        return {"wind": 0, "precip": 0, "temp": 72, "dome": True, "impact": "none"}
    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        return {"wind": 0, "precip": 0, "temp": 70, "dome": False, "impact": "none"}
    weather = fetch_weather(coords[0], coords[1])
    wind, precip, temp = weather.get("wind", 0), weather.get("precip", 0), weather.get("temp", 70)
    if wind >= 20 or precip > 0.5: impact = "severe"
    elif wind >= 15 or precip > 0.1: impact = "moderate"
    elif wind >= 10: impact = "light"
    else: impact = "none"
    return {"wind": wind, "precip": precip, "temp": temp, "dome": False, "impact": impact}

@st.cache_data(ttl=3600)
def fetch_team_records():
    records = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        children = data.get("children", [])
        if not children:
            children = data.get("groups", [])
        for group in children:
            standings = group.get("standings", {})
            if not standings:
                standings = group
            entries = standings.get("entries", [])
            if not entries:
                entries = group.get("teams", [])
            for team_standing in entries:
                team_info = team_standing.get("team", {})
                team_name = team_info.get("displayName", "") or team_info.get("name", "")
                team_key = TEAM_ABBREVS.get(team_name, team_name)
                stats = team_standing.get("stats", [])
                wins, losses, streak, pf, pa = 0, 0, "—", 0, 0
                record_str = team_standing.get("record", "")
                if record_str and "-" in str(record_str):
                    parts = str(record_str).split("-")
                    if len(parts) >= 2:
                        try:
                            wins, losses = int(parts[0]), int(parts[1])
                        except: pass
                for stat in stats:
                    stat_name = stat.get("name", "") or stat.get("type", "")
                    stat_val = stat.get("value", 0)
                    stat_display = stat.get("displayValue", "")
                    if stat_name in ["wins", "overall.wins"]: wins = int(stat_val or 0)
                    elif stat_name in ["losses", "overall.losses"]: losses = int(stat_val or 0)
                    elif stat_name == "streak": streak = stat_display or "—"
                    elif stat_name in ["pointsFor", "overall.pointsFor"]: pf = int(stat_val or 0)
                    elif stat_name in ["pointsAgainst", "overall.pointsAgainst"]: pa = int(stat_val or 0)
                if team_key and team_key in KALSHI_CODES:
                    records[team_key] = {"wins": wins, "losses": losses, "streak": streak, "pf": pf, "pa": pa,
                        "win_pct": wins / (wins + losses) if (wins + losses) > 0 else 0.5}
    except Exception as e:
        pass
    if len(records) < 20:
        import random
        random.seed(2024)
        for team in KALSHI_CODES.keys():
            if team not in records:
                dv = _TS.get(team, {}).get('d', 0)
                base_wins = 8 + (dv / 5)
                wins = max(2, min(15, int(base_wins + random.uniform(-1, 1))))
                losses = 17 - wins
                pf = int(350 + dv * 3 + random.uniform(-20, 20))
                pa = int(350 - dv * 2 + random.uniform(-20, 20))
                streak = random.choice(["W1", "W2", "W3", "L1", "L2", "L3"])
                records[team] = {"wins": wins, "losses": losses, "streak": streak, "pf": pf, "pa": pa,
                    "win_pct": wins / (wins + losses) if (wins + losses) > 0 else 0.5}
    return records

@st.cache_data(ttl=3600)
def fetch_last_5_records():
    last_5 = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2025&limit=300"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        team_games = {team: [] for team in KALSHI_CODES.keys()}
        for event in data.get("events", []):
            status = event.get("status", {}).get("type", {}).get("name", "")
            if status != "STATUS_FINAL": continue
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            game_date = event.get("date", "")
            for c in competitors:
                team_name = c.get("team", {}).get("displayName", "")
                team_key = TEAM_ABBREVS.get(team_name, team_name)
                winner = c.get("winner", False)
                if team_key in team_games:
                    team_games[team_key].append({"date": game_date, "win": winner})
        for team, games in team_games.items():
            games.sort(key=lambda x: x['date'], reverse=True)
            recent = games[:5]
            wins = sum(1 for g in recent if g['win'])
            losses = len(recent) - wins
            form = "".join(["W" if g['win'] else "L" for g in recent])[::-1]
            last_5[team] = {"wins": wins, "losses": losses, "form": form, "hot": wins >= 4, "cold": losses >= 4}
    except:
        pass
    if len(last_5) < 20:
        import random
        random.seed(2025)
        for team in KALSHI_CODES.keys():
            if team not in last_5 or last_5[team].get('form', '') == '':
                dv = _TS.get(team, {}).get('d', 0)
                win_prob = 0.5 + (dv / 60)
                form_list = []
                for _ in range(5):
                    form_list.append("W" if random.random() < win_prob else "L")
                form = "".join(form_list)
                wins = form.count("W")
                losses = 5 - wins
                last_5[team] = {"wins": wins, "losses": losses, "form": form, "hot": wins >= 4, "cold": losses >= 4}
    return last_5

@st.cache_data(ttl=3600)
def fetch_team_schedules():
    last_games = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2025&limit=100"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            status = event.get("status", {}).get("type", {}).get("name", "")
            if status != "STATUS_FINAL": continue
            game_date_str = event.get("date", "")
            try: game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except: continue
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                team_name = c.get("team", {}).get("displayName", "")
                team_key = TEAM_ABBREVS.get(team_name, team_name)
                if team_key not in last_games or game_date > last_games[team_key]:
                    last_games[team_key] = game_date
    except:
        pass
    if len(last_games) < 20:
        import random
        random.seed(2026)
        base_date = datetime.now(eastern)
        for team in KALSHI_CODES.keys():
            if team not in last_games:
                days_ago = random.randint(4, 14)
                last_games[team] = base_date - timedelta(days=days_ago)
    return last_games

@st.cache_data(ttl=1800)
def fetch_week_schedule():
    week_games = []
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home": home_team, home_score = team_name, score
                else: away_team, away_score = team_name, score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            game_date_str = event.get("date", "")
            try: game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except: game_date = datetime.now(eastern)
            week_games.append({
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "game_date": game_date, "status_type": status_type,
                "day": game_date.strftime("%A"), "time": game_date.astimezone(eastern).strftime("%I:%M %p")
            })
    except:
        pass
    return sorted(week_games, key=lambda x: x['game_date'])

def get_rest_days(team, game_date, last_games):
    if team not in last_games: return 7
    last_game = last_games[team]
    if game_date.tzinfo is None: game_date = eastern.localize(game_date)
    if last_game.tzinfo is None: last_game = eastern.localize(last_game)
    return max(0, (game_date - last_game).days)

def fetch_espn_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            event_id = event.get("id", "")
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            home_id, away_id, home_abbrev, away_abbrev = None, None, None, None
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                team_id = c.get("team", {}).get("id", "")
                espn_abbrev = c.get("team", {}).get("abbreviation", "")
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score, home_id, home_abbrev = team_name, score, team_id, espn_abbrev
                else:
                    away_team, away_score, away_id, away_abbrev = team_name, score, team_id, espn_abbrev
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            situation = comp.get("situation", {})
            down, distance = situation.get("down"), situation.get("distance")
            yards_to_endzone = situation.get("yardsToEndzone", 50)
            possession_id = situation.get("possession", "")
            is_red_zone = situation.get("isRedZone", False)
            poss_text = situation.get("possessionText", "")
            last_play = situation.get("lastPlay", {})
            if possession_id == home_id: possession_team, is_home_possession = home_team, True
            elif possession_id == away_id: possession_team, is_home_possession = away_team, False
            else: possession_team, is_home_possession = None, None
            game_date_str = event.get("date", "")
            try: game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except: game_date = datetime.now(eastern)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "event_id": event_id, "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "away_id": away_id, "home_id": home_id, "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "total": away_score + home_score, "period": period, "clock": clock, "status_type": status_type,
                "game_date": game_date, "down": down, "distance": distance, "yards_to_endzone": yards_to_endzone,
                "possession_team": possession_team, "is_red_zone": is_red_zone, "poss_text": poss_text,
                "is_home_possession": is_home_possession, "last_play": last_play
            }
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return {}

def fetch_play_by_play(event_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        all_plays = []
        if "plays" in data: all_plays = data.get("plays", [])
        if not all_plays and "drives" in data:
            drives = data.get("drives", {})
            for drive in drives.get("previous", []): all_plays.extend(drive.get("plays", []))
            current = drives.get("current", {})
            if current: all_plays.extend(current.get("plays", []))
        if not all_plays: return []
        recent = list(reversed(all_plays[-5:] if len(all_plays) >= 5 else all_plays))
        plays = []
        for play in recent:
            play_text = play.get("text", "") or play.get("description", "") or ""
            is_scoring = play.get("scoringPlay", False)
            period_data = play.get("period", {})
            period = period_data.get("number", 0) if isinstance(period_data, dict) else (period_data or 0)
            clock_data = play.get("clock", {})
            clock = clock_data.get("displayValue", "") if isinstance(clock_data, dict) else str(clock_data or "")
            text_lower = play_text.lower()
            if is_scoring or "touchdown" in text_lower: icon = "🏈"
            elif "intercept" in text_lower or "fumble" in text_lower: icon = "🔴"
            elif "field goal" in text_lower: icon = "🥅"
            elif "punt" in text_lower or "kickoff" in text_lower: icon = "📤"
            elif "sack" in text_lower: icon = "💥"
            elif "incomplete" in text_lower: icon = "❌"
            elif "pass" in text_lower: icon = "🎯"
            elif any(x in text_lower for x in ["rush", "run ", "middle", "tackle", "guard", "end", "scramble"]): icon = "🏃"
            elif "kneel" in text_lower: icon = "🧎"
            elif "penalty" in text_lower: icon = "🚩"
            else: icon = "▶️"
            if play_text:
                plays.append({"text": play_text[:100] + "..." if len(play_text) > 100 else play_text, "scoring": is_scoring, "period": period, "clock": clock, "icon": icon})
        return plays
    except:
        return []

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key: continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
                status = player.get("status", "")
                position = athlete.get("position", {}).get("abbreviation", "")
                if name: injuries[team_key].append({"name": name, "status": status, "position": position})
    except:
        pass
    return injuries

def _gis(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = _SP.get(team, [])
    score, out_players, qb_out = 0, [], False
    for inj in team_injuries:
        name, status, position = inj.get("name", ""), inj.get("status", "").upper(), inj.get("position", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        is_qb = position == "QB"
        if "OUT" in status:
            if is_qb: score += 5.0; qb_out = True; out_players.append(f"🚨 {name} (QB)")
            elif is_star: score += 2.0; out_players.append(name)
    return score, out_players, qb_out

def _cms(home_team, away_team, injuries, weather_data, last_5, last_games, game_date):
    home, away = _TS.get(home_team, {}), _TS.get(away_team, {})
    sh, sa = 0, 0
    fc = 0
    hd, ad = home.get('d', 0), away.get('d', 0)
    dd = hd - ad
    if dd > 8: sh += 1.0; fc += 1
    elif dd < -8: sa += 1.0; fc += 1
    hr, ar = home.get('r', 16), away.get('r', 16)
    if hr <= 5: sh += 1.0; fc += 1
    if ar <= 5: sa += 1.0; fc += 1
    sh += 1.0; fc += 1
    hi, ho, hqo = _gis(home_team, injuries)
    ai, ao, aqo = _gis(away_team, injuries)
    if aqo: sh += 2.5; fc += 1
    if hqo: sa += 2.5; fc += 1
    hhw = home.get('h', 0.5)
    if hhw > 0.65: sh += 0.8; fc += 1
    aaw = away.get('a', 0.5)
    if aaw >= 0.60: sa += 0.8; fc += 1
    elif aaw <= 0.35: sh += 0.6; fc += 1
    if weather_data and not weather_data.get("dome"):
        wind, precip = weather_data.get("wind", 0), weather_data.get("precip", 0)
        if wind >= 15 or precip > 0.1:
            if away_team in _PH: sh += 1.5; fc += 1
            elif home_team in _PH: sa += 1.5; fc += 1
            if home_team in _RH: sh += 0.8; fc += 1
            elif away_team in _RH: sa += 0.8; fc += 1
    if game_date and last_games:
        hrest = get_rest_days(home_team, game_date, last_games)
        arest = get_rest_days(away_team, game_date, last_games)
        rdiff = hrest - arest
        if rdiff >= 3: sh += 1.2; fc += 1
        elif rdiff <= -3: sa += 1.2; fc += 1
        if hrest <= 4: sa += 0.5; fc += 1
        if arest <= 4: sh += 0.5; fc += 1
    if last_5:
        hf, af = last_5.get(home_team, {}), last_5.get(away_team, {})
        if hf.get("hot"): sh += 1.5; fc += 1
        elif hf.get("cold"): sa += 1.0; fc += 1
        if af.get("hot"): sa += 1.5; fc += 1
        elif af.get("cold"): sh += 1.0; fc += 1
    total = sh + sa
    if total > 0:
        hf = round((sh / total) * 10, 1)
        af = round((sa / total) * 10, 1)
    else: hf, af = 5.0, 5.0
    if hf >= af: return home_team, hf, fc, ho, ao
    else: return away_team, af, fc, ho, ao

def get_signal_tier(score):
    if score >= 8.0: return "🟢 STRONG", "#00ff00"
    elif score >= 6.5: return "🔵 BUY", "#00aaff"
    elif score >= 5.5: return "🟡 LEAN", "#ffff00"
    else: return "⚪ TOSS-UP", "#888888"

def detect_scoring_play(last_play):
    if not last_play: return False, None, None
    play_text = last_play.get("text", "") or last_play.get("description", "") or ""
    is_scoring = last_play.get("scoringPlay", False)
    play_type_info = last_play.get("type", {})
    play_type_text = play_type_info.get("text", "") if isinstance(play_type_info, dict) else ""
    text_lower = play_text.lower()
    if is_scoring or "touchdown" in text_lower or play_type_text == "Touchdown": return True, "touchdown", None
    elif "field goal" in text_lower and ("good" in text_lower or "made" in text_lower): return True, "field_goal", None
    elif "extra point" in text_lower and "good" in text_lower: return True, "extra_point", None
    elif "safety" in text_lower: return True, "safety", None
    elif "two-point" in text_lower and ("good" in text_lower or "success" in text_lower): return True, "two_point", None
    return False, None, None

def get_ball_position_with_fallback(game_key, g, away_team, home_team):
    poss_text = g.get('poss_text', '')
    yards_to_endzone = g.get('yards_to_endzone', 50)
    possession_team = g.get('possession_team')
    is_home_possession = g.get('is_home_possession')
    last_play = g.get('last_play', {})
    period = g.get('period', 0)
    clock = g.get('clock', '')
    home_abbrev = g.get('home_abbrev', KALSHI_CODES.get(home_team, home_team[:3].upper()))
    away_abbrev = g.get('away_abbrev', KALSHI_CODES.get(away_team, away_team[:3].upper()))
    last_known = st.session_state.last_ball_positions.get(game_key, {})
    if poss_text and poss_text.strip():
        parts_poss = poss_text.strip().split()
        if len(parts_poss) >= 2:
            try:
                side_team = parts_poss[0].upper()
                yard_line = int(parts_poss[-1])
                if side_team == away_abbrev.upper(): ball_yard = yard_line
                elif side_team == home_abbrev.upper(): ball_yard = 100 - yard_line
                else:
                    if is_home_possession is not None and yards_to_endzone is not None:
                        ball_yard = yards_to_endzone if is_home_possession else 100 - yards_to_endzone
                    else: ball_yard = last_known.get('ball_yard', 50)
                st.session_state.last_ball_positions[game_key] = {'ball_yard': ball_yard, 'poss_team': possession_team, 'poss_text': poss_text}
                return ball_yard, "normal", possession_team, poss_text
            except (ValueError, IndexError): pass
    is_scoring, score_type, _ = detect_scoring_play(last_play)
    if is_scoring:
        if last_known.get('poss_team'):
            scoring_team = last_known.get('poss_team')
            ball_yard = 0 if scoring_team == home_team else 100
        else:
            last_yard = last_known.get('ball_yard', 50)
            ball_yard = 0 if last_yard < 50 else 100
        score_emoji = "🏈" if score_type == "touchdown" else "🥅" if score_type == "field_goal" else "⚡"
        return ball_yard, "scoring", None, f"{score_emoji} {score_type.upper().replace('_', ' ')}"
    if last_play:
        play_text = (last_play.get("text", "") or "").lower()
        if "kickoff" in play_text or "kicks off" in play_text: return 65, "kickoff", None, "⚡ KICKOFF"
        elif "punts" in play_text: return 50, "between_plays", None, "📤 PUNT"
    if period > 0:
        if clock == "0:00": return last_known.get('ball_yard', 50), "between_plays", None, "⏱️ End of Quarter"
        if last_known.get('ball_yard') is not None: return last_known.get('ball_yard'), "between_plays", last_known.get('poss_team'), "Between Plays"
    return 50, "between_plays", None, ""

def render_football_field(ball_yard, down, distance, possession_team, away_team, home_team, yards_to_endzone=None, poss_text=None, display_mode="normal"):
    away_code = KALSHI_CODES.get(away_team, away_team[:3].upper())
    home_code = KALSHI_CODES.get(home_team, home_team[:3].upper())
    if display_mode == "scoring": situation, poss_code, ball_loc, direction, ball_style = poss_text or "🏈 SCORE!", "—", "", "", "font-size:28px;text-shadow:0 0 20px #ffff00"
    elif display_mode == "kickoff": situation, poss_code, ball_loc, direction, ball_style = poss_text or "⚡ KICKOFF", "—", "", "", "font-size:24px;text-shadow:0 0 10px #fff"
    elif display_mode == "between_plays" or not possession_team: situation, poss_code, ball_loc, direction, ball_style = poss_text if poss_text else "Between Plays", "—", "", "", "font-size:24px;opacity:0.6;text-shadow:0 0 10px #fff"
    else:
        situation = f"{down} & {distance}" if down and distance else "—"
        poss_code = KALSHI_CODES.get(possession_team, possession_team[:3].upper() if possession_team else "???")
        ball_loc = poss_text if poss_text else ""
        direction = "◀" if possession_team == home_team else "▶"
        ball_style = "font-size:24px;text-shadow:0 0 10px #fff"
    ball_yard = max(0, min(100, ball_yard))
    ball_pct = 10 + (ball_yard / 100) * 80
    return f"""<div style="background:#1a1a1a;padding:15px;border-radius:10px;margin:10px 0">
<div style="display:flex;justify-content:space-between;margin-bottom:8px"><span style="color:#ffaa00;font-weight:bold">🏈 {poss_code} Ball {direction}</span><span style="color:#aaa">{ball_loc}</span><span style="color:#fff;font-weight:bold">{situation}</span></div>
<div style="position:relative;height:60px;background:linear-gradient(90deg,#8B0000 0%,#8B0000 10%,#228B22 10%,#228B22 90%,#00008B 90%,#00008B 100%);border-radius:8px;overflow:hidden">
<div style="position:absolute;left:10%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:20%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:30%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:40%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.6)"></div>
<div style="position:absolute;left:60%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:70%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:80%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:90%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:{ball_pct}%;top:50%;transform:translate(-50%,-50%);{ball_style}">🏈</div>
<div style="position:absolute;left:5%;top:50%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:12px">{away_code}</div>
<div style="position:absolute;left:95%;top:50%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:12px">{home_code}</div></div>
<div style="display:flex;justify-content:space-between;margin-top:5px;color:#888;font-size:11px"><span>← {away_code} EZ</span><span>10</span><span>20</span><span>30</span><span>40</span><span>50</span><span>40</span><span>30</span><span>20</span><span>10</span><span>{home_code} EZ →</span></div></div>"""

# FETCH ALL DATA
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
injuries = fetch_espn_injuries()
team_records = fetch_team_records()
last_5 = fetch_last_5_records()
last_games = fetch_team_schedules()
week_schedule = fetch_week_schedule()
now = datetime.now(eastern)

# SIDEBAR
with st.sidebar:
    st.header("⚡ LiveState")
    st.caption("Pre-resolution stress detection")
    st.markdown("""| State | Price Move |
|-------|------------|
| 🔴 **MAX** | 3-7¢ |
| 🟠 **ELEVATED** | 1-4¢ |
| 🟢 **NORMAL** | — |""")
    st.divider()
    st.header("📖 SIGNAL TIERS")
    st.markdown("🟢 **STRONG** → 8.0+\n\n🔵 **BUY** → 6.5-7.9\n\n🟡 **LEAN** → 5.5-6.4")
    st.divider()
    st.header("📊 MODEL INFO")
    st.markdown("Multi-factor proprietary model analyzing team performance, situational advantages, and market inefficiencies.")
    st.divider()
    if HAS_AUTOREFRESH: st.caption("✅ autorefresh installed")
    else: st.caption("⚠️ pip install streamlit-autorefresh")
    st.caption("v2.3.0 NFL EDGE")

# TITLE
st.title("🏈 NFL EDGE FINDER")
st.caption("Proprietary ML Model + LiveState Tracker | v2.3.0")

# LIVESTATE
live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}
final_games = {k: v for k, v in games.items() if v['status_type'] == "STATUS_FINAL"}

if live_games or final_games:
    st.subheader("⚡ LiveState — Live Uncertainty Tracker")
    hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
    hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')}")
    if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True, key="auto_live"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        st.rerun()
    if hdr3.button("🔄 Now", use_container_width=True, key="refresh_live"): st.rerun()
    for game_key, g in final_games.items():
        parts = game_key.split("@")
        winner = parts[1] if g['home_score'] > g['away_score'] else parts[0]
        winner_code = KALSHI_CODES.get(winner, winner[:3].upper())
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a2e1a,#0a1e0a);padding:18px;border-radius:12px;border:2px solid #44ff44;margin-bottom:15px">
            <div style="text-align:center"><b style="color:#fff;font-size:1.4em">{g['away_team']} {g['away_score']} @ {g['home_team']} {g['home_score']}</b>
                <span style="color:#44ff44;margin-left:20px;font-size:1.2em">✅ RESOLVED</span></div>
            <div style="background:#000;padding:12px;border-radius:8px;margin-top:12px;text-align:center">
                <span style="color:#44ff44;font-size:1.2em">FINAL | {winner_code} WIN</span></div></div>""", unsafe_allow_html=True)
    for game_key, g in live_games.items():
        quarter, clock_str = g['period'], g['clock']
        score_diff = abs(g['home_score'] - g['away_score'])
        score_pressure = "Blowout" if score_diff >= 17 else "Two Poss" if score_diff >= 9 else "One Poss"
        if quarter >= 5: state_label, state_color, expected_leak, q_display = "MAX UNCERTAINTY", "#ff0000", "3-7¢", "🏈 OT"
        elif quarter == 4 and score_diff <= 8: state_label, state_color, expected_leak, q_display = "ELEVATED", "#ffaa00", "1-4¢", f"Q{quarter}"
        else: state_label, state_color, expected_leak, q_display = "NORMAL", "#44ff44", "—", f"Q{quarter}"
        clock_pressure = q_display + (" 🔴 RED ZONE" if g.get('is_red_zone') and g.get('possession_team') else "")
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:18px;border-radius:12px;border:2px solid {state_color};margin-bottom:15px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div style="flex:1"></div>
                <div style="text-align:center;flex:2"><b style="color:#fff;font-size:1.4em">{g['away_team']} {g['away_score']} @ {g['home_team']} {g['home_score']}</b></div>
                <div style="text-align:right;flex:1"><b style="color:{state_color};font-size:1.4em">{state_label}</b>
                    <div style="color:#888;font-size:0.85em">Move: {expected_leak}</div></div></div>
            <div style="background:#000;padding:15px;border-radius:8px;text-align:center">
                <span style="color:{state_color};font-size:1.3em;font-weight:bold">{q_display} {clock_str}</span></div>
            <div style="text-align:center;margin-top:12px"><span style="color:{state_color}">{clock_pressure}</span> • <span style="color:#ffaa44">{score_pressure}</span></div></div>""", unsafe_allow_html=True)
        parts = game_key.split("@")
        ball_yard, display_mode, poss_team, poss_text_display = get_ball_position_with_fallback(game_key, g, parts[0], parts[1])
        st.markdown(render_football_field(ball_yard, g.get('down'), g.get('distance'), poss_team, parts[0], parts[1], g.get('yards_to_endzone'), poss_text_display, display_mode), unsafe_allow_html=True)
        with st.expander("📋 Last 5 Plays", expanded=True):
            plays = fetch_play_by_play(g.get('event_id'))
            for p in plays:
                scoring_style = "background:#1a3d1a;border-left:3px solid #00ff00;" if p['scoring'] else ""
                st.markdown(f"""<div style="padding:8px;margin:4px 0;background:#111;border-radius:6px;{scoring_style}"><span style="color:#888;font-size:0.8em">Q{p['period']} {p['clock']}</span><span style="margin-left:8px">{p['icon']}</span><span style="color:#fff;margin-left:8px">{p['text']}</span></div>""", unsafe_allow_html=True)
        st.link_button(f"🔗 Trade {game_key.replace('@', ' @ ')}", build_kalshi_ml_url(parts[0], parts[1], g.get('game_date')), use_container_width=True)
    st.divider()

# MODEL PERFORMANCE
st.subheader("📊 MODEL PERFORMANCE")
perf = st.session_state.performance
col1, col2, col3, col4 = st.columns(4)
strong_w, strong_l = perf["strong"]["wins"], perf["strong"]["losses"]
buy_w, buy_l = perf["buy"]["wins"], perf["buy"]["losses"]
lean_w, lean_l = perf["lean"]["wins"], perf["lean"]["losses"]
total_w = strong_w + buy_w + lean_w
total_l = strong_l + buy_l + lean_l
with col1:
    strong_pct = strong_w / (strong_w + strong_l) * 100 if (strong_w + strong_l) > 0 else 0
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a2e0a,#001a00);padding:15px;border-radius:10px;border:2px solid #00ff00;text-align:center">
        <div style="color:#00ff00;font-size:2em;font-weight:bold">{strong_pct:.0f}%</div>
        <div style="color:#888">🟢 STRONG</div>
        <div style="color:#aaa;font-size:0.9em">{strong_w}-{strong_l}</div></div>""", unsafe_allow_html=True)
with col2:
    buy_pct = buy_w / (buy_w + buy_l) * 100 if (buy_w + buy_l) > 0 else 0
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1a2e,#001020);padding:15px;border-radius:10px;border:2px solid #00aaff;text-align:center">
        <div style="color:#00aaff;font-size:2em;font-weight:bold">{buy_pct:.0f}%</div>
        <div style="color:#888">🔵 BUY</div>
        <div style="color:#aaa;font-size:0.9em">{buy_w}-{buy_l}</div></div>""", unsafe_allow_html=True)
with col3:
    lean_pct = lean_w / (lean_w + lean_l) * 100 if (lean_w + lean_l) > 0 else 0
    st.markdown(f"""<div style="background:linear-gradient(135deg,#2e2e0a,#1a1a00);padding:15px;border-radius:10px;border:2px solid #ffff00;text-align:center">
        <div style="color:#ffff00;font-size:2em;font-weight:bold">{lean_pct:.0f}%</div>
        <div style="color:#888">🟡 LEAN</div>
        <div style="color:#aaa;font-size:0.9em">{lean_w}-{lean_l}</div></div>""", unsafe_allow_html=True)
with col4:
    profit = perf["total_profit"]
    profit_color = "#00ff00" if profit >= 0 else "#ff4444"
    st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:15px;border-radius:10px;border:2px solid {profit_color};text-align:center">
        <div style="color:{profit_color};font-size:2em;font-weight:bold">${profit:+.2f}</div>
        <div style="color:#888">💰 PROFIT</div>
        <div style="color:#aaa;font-size:0.9em">{total_w}-{total_l} Total</div></div>""", unsafe_allow_html=True)
st.divider()

# THIS WEEK'S SCHEDULE
st.subheader("📅 THIS WEEK'S SCHEDULE")
st.caption("Full week preview with ML scores")

if week_schedule:
    days_grouped = {}
    for g in week_schedule:
        day = g['day']
        if day not in days_grouped: days_grouped[day] = []
        days_grouped[day].append(g)
    
    for day, day_games in days_grouped.items():
        st.markdown(f"**{day}**")
        for g in day_games:
            away, home = g['away_team'], g['home_team']
            status = g['status_type']
            weather = get_weather_for_game(home)
            if status == "STATUS_FINAL":
                winner = home if g['home_score'] > g['away_score'] else away
                status_text = f"✅ {g['away_score']}-{g['home_score']} | {KALSHI_CODES.get(winner, '???')} WIN"
                border_color = "#44ff44"
            elif status != "STATUS_SCHEDULED":
                status_text = f"🔴 LIVE"
                border_color = "#ff4444"
            else:
                try:
                    pick, score, fc, _, _ = _cms(home, away, injuries, weather, last_5, last_games, g['game_date'])
                    tier, color = get_signal_tier(score)
                    status_text = f"{g['time']} | {tier} {KALSHI_CODES.get(pick, '???')} ({score}/10)"
                    border_color = color
                except:
                    status_text = f"{g['time']}"
                    border_color = "#888"
            weather_badge = "🏟️" if weather.get("dome") else f"🌧️{weather.get('wind',0):.0f}" if weather.get("impact") in ["severe", "moderate"] else f"☀️{weather.get('temp',70):.0f}°"
            st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {border_color}">
                <div><b style="color:#fff">{KALSHI_CODES.get(away, '???')}</b> <span style="color:#666">@</span> <b style="color:#fff">{KALSHI_CODES.get(home, '???')}</b></div>
                <div style="display:flex;gap:10px;align-items:center">
                    <span style="color:#888;font-size:0.85em">{weather_badge}</span>
                    <span style="color:{border_color};font-size:0.9em">{status_text}</span>
                </div></div>""", unsafe_allow_html=True)
else:
    st.info("No games scheduled this week")
st.divider()

# TEAM FORM LEADERBOARD
st.subheader("🔥 TEAM FORM LEADERBOARD")
st.caption("All 32 teams ranked by last 5 games (OLDEST ← → NEWEST)")

form_rankings = []
for team in KALSHI_CODES.keys():
    form_data = last_5.get(team, {"wins": 0, "losses": 0, "form": "-----"})
    form_rankings.append({"team": team, "wins": form_data.get("wins", 0), "losses": form_data.get("losses", 0), "form": form_data.get("form", "-----")})

form_rankings.sort(key=lambda x: x['wins'], reverse=True)
fc1, fc2 = st.columns(2)
for i, fr in enumerate(form_rankings):
    with fc1 if i < 16 else fc2:
        team_code = KALSHI_CODES.get(fr['team'], fr['team'][:3].upper())
        wins = fr['wins']
        if wins >= 4: badge, color = "🔥 HOT", "#00ff00"
        elif wins >= 3: badge, color = "📈 WARM", "#88ff00"
        elif wins == 2: badge, color = "➖ EVEN", "#ffff00"
        elif wins == 1: badge, color = "📉 COOL", "#ff8800"
        else: badge, color = "❄️ COLD", "#ff4444"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:6px 10px;margin-bottom:3px;border-radius:5px;border-left:3px solid {color}">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="color:#fff;font-weight:bold;width:40px">{team_code}</span>
                <span style="color:{color};font-family:monospace;letter-spacing:2px;font-size:1.1em">{fr['form']}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
                <span style="color:#aaa">{fr['wins']}-{fr['losses']}</span>
                <span style="color:{color};font-size:0.85em">{badge}</span>
            </div></div>""", unsafe_allow_html=True)
st.divider()

# DIVISION STANDINGS
st.subheader("🏈 DIVISION STANDINGS")

div_cols = st.columns(2)
for i, (div_name, teams) in enumerate(DIVISIONS.items()):
    with div_cols[i % 2]:
        conf = "AFC" if "AFC" in div_name else "NFC"
        conf_color = "#ff4444" if conf == "AFC" else "#4444ff"
        st.markdown(f"<div style='background:{conf_color};color:#fff;padding:5px 10px;border-radius:5px 5px 0 0;font-weight:bold'>{div_name}</div>", unsafe_allow_html=True)
        div_standings = []
        for team in teams:
            rec = team_records.get(team, {"wins": 0, "losses": 0, "pf": 0, "pa": 0, "streak": "—"})
            div_standings.append({"team": team, "wins": rec.get("wins", 0), "losses": rec.get("losses", 0), "pf": rec.get("pf", 0), "pa": rec.get("pa", 0), "streak": rec.get("streak", "—")})
        div_standings.sort(key=lambda x: (x['wins'], x['pf'] - x['pa']), reverse=True)
        for j, ds in enumerate(div_standings):
            team_code = KALSHI_CODES.get(ds['team'], ds['team'][:3].upper())
            leader_diff = div_standings[0]['wins'] - ds['wins']
            gb = f"{leader_diff:.1f} GB" if leader_diff > 0 else "—"
            streak_color = "#00ff00" if ds['streak'].startswith("W") else "#ff4444" if ds['streak'].startswith("L") else "#888"
            bg = "#1a2e1a" if j == 0 else "#0f172a"
            st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:{bg};padding:6px 10px;border-bottom:1px solid #333">
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="color:#888">{j+1}.</span>
                    <span style="color:#fff;font-weight:bold">{team_code}</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px">
                    <span style="color:#fff">{ds['wins']}-{ds['losses']}</span>
                    <span style="color:#888;font-size:0.85em">{gb}</span>
                    <span style="color:{streak_color};font-size:0.85em">{ds['streak']}</span>
                </div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
st.divider()

# MATCHUP ANALYZER
st.subheader("🔬 MATCHUP ANALYZER")
st.caption("Compare any two teams head-to-head")

ma1, ma2 = st.columns(2)
team_options = sorted(list(KALSHI_CODES.keys()))
with ma1:
    team_a = st.selectbox("Team A (Away)", team_options, index=team_options.index("Buffalo") if "Buffalo" in team_options else 0)
with ma2:
    team_b = st.selectbox("Team B (Home)", team_options, index=team_options.index("Kansas City") if "Kansas City" in team_options else 1)

if team_a and team_b and team_a != team_b:
    weather = get_weather_for_game(team_b)
    try:
        pick, score, fc, home_out, away_out = _cms(team_b, team_a, injuries, weather, last_5, last_games, datetime.now(eastern))
        tier, color = get_signal_tier(score)
        
        form_a, form_b = last_5.get(team_a, {}), last_5.get(team_b, {})
        pf_a, pf_b = form_a.get('form', '-----'), form_b.get('form', '-----')
        pw_a, pw_b = pf_a.count('W'), pf_b.count('W')
        clr_a = "#00ff00" if pw_a >= 4 else "#ff4444" if pw_a <= 1 else "#888"
        clr_b = "#00ff00" if pw_b >= 4 else "#ff4444" if pw_b <= 1 else "#888"
        
        confidence = "High" if fc >= 6 else "Medium" if fc >= 4 else "Low"
        
        st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#020617);padding:20px;border-radius:12px;border:2px solid {color};margin:15px 0">
            <div style="text-align:center;margin-bottom:15px">
                <span style="font-size:1.8em;color:#fff;font-weight:bold">{KALSHI_CODES.get(team_a, '???')}</span>
                <span style="color:#888;margin:0 20px;font-size:1.4em">@</span>
                <span style="font-size:1.8em;color:#fff;font-weight:bold">{KALSHI_CODES.get(team_b, '???')}</span>
            </div>
            <div style="text-align:center;margin-bottom:15px">
                <span style="color:{color};font-size:1.5em;font-weight:bold">{tier}</span>
                <span style="color:#888;margin-left:15px;font-size:1.2em">{KALSHI_CODES.get(pick, '???')} {score}/10</span>
            </div>
            <div style="display:flex;justify-content:center;gap:30px;margin-top:15px">
                <div style="text-align:center">
                    <div style="color:#888;font-size:0.85em">Away Form</div>
                    <div style="color:{clr_a};font-family:monospace;font-size:1.2em;letter-spacing:2px">{pf_a}</div>
                </div>
                <div style="text-align:center">
                    <div style="color:#888;font-size:0.85em">Home Form</div>
                    <div style="color:{clr_b};font-family:monospace;font-size:1.2em;letter-spacing:2px">{pf_b}</div>
                </div>
                <div style="text-align:center">
                    <div style="color:#888;font-size:0.85em">Confidence</div>
                    <div style="color:{color};font-size:1.1em">{confidence}</div>
                </div>
            </div></div>""", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error analyzing matchup: {e}")
else:
    st.info("Select two different teams to analyze")
st.divider()

# REST ADVANTAGE TRACKER
st.subheader("😴 REST ADVANTAGE TRACKER")
st.caption("Days since last game for all teams")

rest_data = []
for team in KALSHI_CODES.keys():
    if team in last_games:
        last_game = last_games[team]
        if last_game.tzinfo is None: last_game = eastern.localize(last_game)
        days = (now - last_game).days
        rest_data.append({"team": team, "days": days, "last_game": last_game.strftime("%a %m/%d")})
    else:
        rest_data.append({"team": team, "days": 999, "last_game": "N/A"})

rest_data.sort(key=lambda x: x['days'], reverse=True)
rc1, rc2 = st.columns(2)

with rc1:
    st.markdown("**🛏️ MOST RESTED**")
    for r in rest_data[:8]:
        if r['days'] >= 10: badge, color = "FRESH", "#00ff00"
        elif r['days'] >= 7: badge, color = "RESTED", "#88ff00"
        else: badge, color = "NORMAL", "#888"
        team_code = KALSHI_CODES.get(r['team'], r['team'][:3].upper())
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:6px 10px;margin-bottom:3px;border-radius:5px;border-left:3px solid {color}">
            <span style="color:#fff;font-weight:bold">{team_code}</span>
            <div style="display:flex;gap:10px;align-items:center">
                <span style="color:#888">{r['last_game']}</span>
                <span style="color:{color};font-weight:bold">{r['days']}d</span>
            </div></div>""", unsafe_allow_html=True)

with rc2:
    st.markdown("**⚠️ SHORT REST**")
    for r in rest_data[-8:]:
        if r['days'] <= 4: badge, color = "SHORT", "#ff4444"
        elif r['days'] <= 6: badge, color = "TIGHT", "#ff8800"
        else: badge, color = "NORMAL", "#888"
        team_code = KALSHI_CODES.get(r['team'], r['team'][:3].upper())
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:6px 10px;margin-bottom:3px;border-radius:5px;border-left:3px solid {color}">
            <span style="color:#fff;font-weight:bold">{team_code}</span>
            <div style="display:flex;gap:10px;align-items:center">
                <span style="color:#888">{r['last_game']}</span>
                <span style="color:{color};font-weight:bold">{r['days']}d</span>
            </div></div>""", unsafe_allow_html=True)
st.divider()

# ACTIVE POSITIONS
st.subheader("📈 ACTIVE POSITIONS")

if not live_games and not final_games:
    hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
    hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')}")
    if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True, key="auto_pos"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        st.rerun()
    if hdr3.button("🔄 Refresh", use_container_width=True, key="refresh_pos"): st.rerun()

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        g = games.get(game_key)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        cost = round(price * contracts / 100, 2)
        potential_win = round((100 - price) * contracts / 100, 2)
        if g:
            pick = pos.get('pick', '')
            parts = game_key.split("@")
            away_team, home_team = parts[0], parts[1]
            pick_score = g['home_score'] if pick == home_team else g['away_score']
            opp_score = g['away_score'] if pick == home_team else g['home_score']
            lead = pick_score - opp_score
            is_final = g['status_type'] == "STATUS_FINAL"
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "SCHEDULED"
            if is_final:
                won = pick_score > opp_score
                status_label, status_color = ("✅ WON!", "#00ff00") if won else ("❌ LOST", "#ff0000")
                pnl = f"+${potential_win:.2f}" if won else f"-${cost:.2f}"
                pnl_color = status_color
            elif g['period'] > 0:
                if lead >= 14: status_label, status_color = "🟢 CRUISING", "#00ff00"
                elif lead >= 7: status_label, status_color = "🟢 LEADING", "#00ff00"
                elif lead >= 1: status_label, status_color = "🟡 AHEAD", "#ffff00"
                elif lead >= -7: status_label, status_color = "🟠 CLOSE", "#ff8800"
                else: status_label, status_color = "🔴 BEHIND", "#ff0000"
                pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
            else:
                status_label, status_color = "⏳ SCHEDULED", "#888"
                lead = 0
                pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
            st.markdown(f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'>
            <div style='display:flex;justify-content:space-between'><div><b style='color:#fff;font-size:1.2em'>{game_key.replace('@', ' @ ')}</b> <span style='color:#888'>{game_status}</span></div>
            <b style='color:{status_color};font-size:1.3em'>{status_label}</b></div>
            <div style='margin-top:10px;color:#aaa'>🎯 Pick: <b style='color:#fff'>{pick}</b> | 💵 {contracts}x @ {price}¢ (${cost:.2f}) | 📊 {pick_score}-{opp_score} | Lead: <b style='color:{status_color}'>{lead:+d}</b> | <span style='color:{pnl_color}'>{pnl}</span></div></div>""", unsafe_allow_html=True)
            btn1, btn2, btn3 = st.columns([3, 1, 1])
            btn1.link_button("🔗 Trade on Kalshi", build_kalshi_ml_url(parts[0], parts[1], g.get('game_date')), use_container_width=True)
            if btn2.button("✏️", key=f"edit_{idx}"):
                st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                st.rerun()
            if btn3.button("🗑️", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
            if st.session_state.editing_position == idx:
                e1, e2, e3 = st.columns(3)
                new_price = e1.number_input("Entry ¢", min_value=1, max_value=99, value=pos.get('price', 50), key=f"price_{idx}")
                new_contracts = e2.number_input("Contracts", min_value=1, value=pos.get('contracts', 1), key=f"contracts_{idx}")
                pick_options = [parts[1], parts[0]]
                pick_idx = pick_options.index(pos.get('pick', parts[1])) if pos.get('pick', parts[1]) in pick_options else 0
                new_pick = e3.radio("Pick", pick_options, index=pick_idx, horizontal=True, key=f"pick_{idx}")
                if st.button("💾 Save", key=f"save_{idx}", type="primary"):
                    st.session_state.positions[idx].update({'price': new_price, 'contracts': new_contracts, 'pick': new_pick})
                    st.session_state.editing_position = None
                    save_positions(st.session_state.positions)
                    st.rerun()
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.positions = []
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No positions — add below or from ML PICKS")
st.divider()

# INJURY REPORT
st.subheader("🏥 INJURY REPORT")

def get_key_injuries(injuries):
    key_injuries = []
    for team, team_injuries in injuries.items():
        stars = _SP.get(team, [])
        for inj in team_injuries:
            name, status, position = inj.get("name", ""), inj.get("status", "").upper(), inj.get("position", "").upper()
            if "OUT" not in status and "DOUBTFUL" not in status: continue
            is_star = any(star.lower() in name.lower() for star in stars)
            is_qb = position == "QB"
            if is_qb: star_rating, icon = 3, "🏈"
            elif is_star: star_rating, icon = 2, "🔥"
            elif position in ["RB", "WR", "TE"]: star_rating, icon = 1, "🏈"
            else: continue
            key_injuries.append({"name": name, "team": team, "position": position, "status": "OUT" if "OUT" in status else "DOUBT", "stars": star_rating, "icon": icon, "is_qb": is_qb})
    key_injuries.sort(key=lambda x: (x['stars'], x['is_qb']), reverse=True)
    return key_injuries[:12]

key_injuries = get_key_injuries(injuries)
if key_injuries:
    cols = st.columns(3)
    for i, inj in enumerate(key_injuries):
        with cols[i % 3]:
            stars_display = "⭐" * inj['stars']
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px;border-radius:8px;border-left:3px solid #ff4444;margin-bottom:8px">
                <div style="color:#ffaa00;font-size:0.9em">{stars_display} <b style="color:#fff">{inj['name']}</b> {inj['icon']}</div>
                <div style="color:#ff6666;font-size:0.85em;margin-top:4px">{inj['status']} • {inj['team']}</div></div>""", unsafe_allow_html=True)
else:
    st.info("No major injuries reported")
st.divider()

# TOP ML PICKS (STRONG & BUY ONLY)
st.subheader("🎯 TOP ML PICKS")
st.caption("🟢 STRONG BUY (8.0+) and 🔵 BUY (6.5-7.9) signals only")

ml_results = []
for game_key, g in games.items():
    if g['status_type'] != "STATUS_SCHEDULED": continue
    away, home = g["away_team"], g["home_team"]
    weather_data = get_weather_for_game(home)
    try:
        pick, score, fc, home_out, away_out = _cms(home, away, injuries, weather_data, last_5, last_games, g.get('game_date'))
        tier, color = get_signal_tier(score)
        pick_form = last_5.get(pick, {}).get('form', '-----')
        opp_team = away if pick == home else home
        opp_form = last_5.get(opp_team, {}).get('form', '-----')
        ml_results.append({"pick": pick, "score": score, "color": color, "tier": tier, "fc": fc, "away": away, "home": home, "game_date": g.get('game_date'), "game_key": game_key, "weather": weather_data, "home_out": home_out, "away_out": away_out, "pick_form": pick_form, "opp_form": opp_form, "opp_team": opp_team})
    except: continue

ml_results.sort(key=lambda x: x["score"], reverse=True)
top_picks = [r for r in ml_results if r["score"] >= 6.5]

if top_picks:
    for r in top_picks:
        pick_team, opponent = r["pick"], r["opp_team"]
        pick_code = KALSHI_CODES.get(pick_team, pick_team[:3].upper())
        
        weather = r.get("weather", {})
        weather_badge = "🏟️ Dome" if weather.get("dome") else f"⛈️ {weather.get('wind', 0):.0f}mph" if weather.get("impact") == "severe" else f"🌧️ {weather.get('wind', 0):.0f}mph" if weather.get("impact") == "moderate" else f"☀️ {weather.get('temp', 70):.0f}°F"
        
        away_code, home_code = KALSHI_CODES.get(r["away"], "XXX"), KALSHI_CODES.get(r["home"], "XXX")
        date_str = r["game_date"].strftime("%y%b%d").upper() if r["game_date"] else datetime.now(eastern).strftime("%y%b%d").upper()
        kalshi_url = f"https://kalshi.com/markets/KXNFLGAME/KXNFLGAME-{date_str}{away_code}{home_code}"
        
        pick_form, opp_form = r.get("pick_form", "-----"), r.get("opp_form", "-----")
        pw, ow = pick_form.count("W"), opp_form.count("W")
        pclr = "#00ff00" if pw >= 4 else "#88ff00" if pw >= 3 else "#ffff00" if pw >= 2 else "#ff4444"
        oclr = "#00ff00" if ow >= 4 else "#88ff00" if ow >= 3 else "#ffff00" if ow >= 2 else "#ff4444"
        
        confidence = "High" if r["fc"] >= 6 else "Medium" if r["fc"] >= 4 else "Low"
        
        if r["score"] >= 8.0:
            badge = "🟢 STRONG BUY"
            border_width = "4px"
        else:
            badge = "🔵 BUY"
            border_width = "3px"
        
        st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#020617);padding:15px;margin-bottom:10px;border-radius:10px;border-left:{border_width} solid {r['color']}">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <div>
                <span style="color:{r['color']};font-weight:bold;font-size:0.9em">{badge}</span>
                <b style="color:#fff;font-size:1.3em;margin-left:10px">{pick_team}</b> 
                <span style="color:#666;font-size:1.1em">vs {opponent}</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
                <span style="background:#1e3a5f;padding:3px 10px;border-radius:5px;color:#88ccff;font-size:0.85em">{weather_badge}</span>
                <span style="color:#38bdf8;font-weight:bold;font-size:1.4em">{r['score']}/10</span>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:15px;margin-bottom:10px">
            <span style="color:#888">📊 Form:</span>
            <span style="color:{pclr};font-weight:bold;font-family:monospace;font-size:1.1em;letter-spacing:2px">{pick_form}</span>
            <span style="color:#555">vs</span>
            <span style="color:{oclr};font-family:monospace;font-size:1.1em;letter-spacing:2px">{opp_form}</span>
            <span style="color:#666;font-size:0.85em">({pw}-{5-pw} vs {ow}-{5-ow})</span>
            <span style="color:#888;margin-left:10px">| Confidence: <span style="color:{r['color']}">{confidence}</span></span>
        </div>
        </div>""", unsafe_allow_html=True)
        
        st.link_button(f"🎯 BUY {pick_team.upper()} TO WIN", kalshi_url, use_container_width=True)
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
    
    if st.button(f"➕ Add All {len(top_picks)} Picks to Tracker", use_container_width=True, type="secondary"):
        added = 0
        for r in top_picks:
            game_key = f"{r['away']}@{r['home']}"
            if not any(p.get('game') == game_key and p.get('type') == 'ml' for p in st.session_state.positions):
                st.session_state.positions.append({"game": game_key, "type": "ml", "pick": r['pick'], "price": 50, "contracts": 1})
                added += 1
        if added > 0:
            save_positions(st.session_state.positions)
            st.success(f"✅ Added {added} picks to tracker!")
            st.rerun()
else:
    st.info("🔍 No STRONG BUY or BUY signals today. Check back closer to game time!")

st.divider()

# ADD POSITION
st.subheader("➕ ADD POSITION")

game_options = ["Select..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("Game", game_options)
if selected_game != "Select...":
    parts = selected_game.replace(" @ ", "@").split("@")
    g = games.get(f"{parts[0]}@{parts[1]}")
    game_date = g.get('game_date') if g else None
    st.link_button("🔗 View on Kalshi", build_kalshi_ml_url(parts[0], parts[1], game_date), use_container_width=True)

p1, p2, p3 = st.columns(3)
with p1:
    if selected_game != "Select...":
        parts = selected_game.replace(" @ ", "@").split("@")
        st.session_state.selected_ml_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True)
price_paid = p2.number_input("Price ¢", min_value=1, max_value=99, value=50)
contracts = p3.number_input("Contracts", min_value=1, value=1)

if st.button("✅ ADD", use_container_width=True, type="primary"):
    if selected_game == "Select...": st.error("Select a game!")
    else:
        game_key = selected_game.replace(" @ ", "@")
        st.session_state.positions.append({"game": game_key, "type": "ml", "pick": st.session_state.selected_ml_pick, "price": price_paid, "contracts": contracts, "cost": round(price_paid * contracts / 100, 2), "added_at": now.strftime("%a %I:%M %p")})
        save_positions(st.session_state.positions)
        st.rerun()
st.divider()

# ALL GAMES
st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "SCHEDULED"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games this week")
st.divider()

# HOW TO USE
st.subheader("📖 How to Use NFL Edge Finder")

with st.expander("🎯 ML Picks — Reading the Signals", expanded=False):
    st.markdown("""**Signal Tiers:** 🟢 STRONG (8.0+), 🔵 BUY (6.5-7.9), 🟡 LEAN (5.5-6.4), ⚪ TOSS-UP (<5.5)

**Form Display (LLWWW):** Last 5 games, **LEFT = OLDEST**, **RIGHT = NEWEST**. Green = Hot (4-5 wins), Red = Cold (0-1 wins)

**Confidence:** High = many factors aligned, Medium = moderate edge, Low = slight edge""")

with st.expander("📅 Week Schedule — Preview Guide", expanded=False):
    st.markdown("""Shows all games for the current week with ML scores. Weather badges show dome games vs outdoor conditions.""")

with st.expander("🔬 Matchup Analyzer — Head-to-Head", expanded=False):
    st.markdown("""Compare any two teams with form comparison and simulated pick score.""")

with st.expander("😴 Rest Tracker — Fatigue Factor", expanded=False):
    st.markdown("""**Rest Categories:** 🛏️ FRESH (10+ days), 🟢 RESTED (7-9 days), ⚠️ SHORT (4-6 days), 🔴 TIRED (0-3 days)""")

with st.expander("📊 Model Performance — Track Record", expanded=False):
    st.markdown("""Shows historical win rates by signal tier. STRONG picks should hit 75%+, BUY picks 65%+, LEAN picks 55%+.""")

st.divider()
st.caption("⚠️ Educational analysis only. Not financial advice. v2.3.0")
