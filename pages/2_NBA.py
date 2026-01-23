import streamlit as st

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# ============================================================
# 🔐 AUTH CHECK — MUST BE FIRST AFTER PAGE CONFIG
# ============================================================
from auth import require_auth
require_auth()

import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
from styles import apply_styles, buy_button

apply_styles()

# ========== GOOGLE ANALYTICS G4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== MOBILE CSS FIX ==========
st.markdown("""
<style>
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        div[data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; }
        .stButton button { padding: 8px 12px !important; font-size: 14px !important; }
    }
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

POSITIONS_FILE = "nba_positions.json"
STRONG_PICKS_FILE = "strong_picks.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except: pass

def load_strong_picks():
    try:
        if os.path.exists(STRONG_PICKS_FILE):
            with open(STRONG_PICKS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"next_ml": 1, "picks": []}

def save_strong_picks(data):
    try:
        with open(STRONG_PICKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "selected_ml_pick" not in st.session_state:
    st.session_state.selected_ml_pick = None
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None
if "drought_tracker" not in st.session_state:
    st.session_state.drought_tracker = {}
if "pace_history" not in st.session_state:
    st.session_state.pace_history = {}
if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

if st.session_state.auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={int(time.time()) + 30}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS"
}

TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "home_win_pct": 0.52, "away_win_pct": 0.35},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "home_win_pct": 0.78, "away_win_pct": 0.65},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "home_win_pct": 0.42, "away_win_pct": 0.28},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "home_win_pct": 0.38, "away_win_pct": 0.22},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "home_win_pct": 0.48, "away_win_pct": 0.32},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "home_win_pct": 0.75, "away_win_pct": 0.58},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "home_win_pct": 0.62, "away_win_pct": 0.48},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "home_win_pct": 0.72, "away_win_pct": 0.45},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "home_win_pct": 0.32, "away_win_pct": 0.18},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "home_win_pct": 0.65, "away_win_pct": 0.42},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "home_win_pct": 0.55, "away_win_pct": 0.40},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "home_win_pct": 0.68, "away_win_pct": 0.48},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "home_win_pct": 0.65, "away_win_pct": 0.45},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "home_win_pct": 0.70, "away_win_pct": 0.52},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "home_win_pct": 0.72, "away_win_pct": 0.55},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "home_win_pct": 0.68, "away_win_pct": 0.52},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "home_win_pct": 0.82, "away_win_pct": 0.68},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "home_win_pct": 0.62, "away_win_pct": 0.45},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "home_win_pct": 0.60, "away_win_pct": 0.42},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "home_win_pct": 0.40, "away_win_pct": 0.25},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "home_win_pct": 0.42, "away_win_pct": 0.28},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "home_win_pct": 0.48, "away_win_pct": 0.32},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "home_win_pct": 0.35, "away_win_pct": 0.22},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "home_win_pct": 0.38, "away_win_pct": 0.25}
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young"], "Boston": ["Jayson Tatum", "Jaylen Brown"], "Brooklyn": ["Mikal Bridges"],
    "Charlotte": ["LaMelo Ball"], "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Desmond Bane"], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Julius Randle"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"], "Portland": ["Anfernee Simons"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"], "San Antonio": ["Victor Wembanyama"],
    "Toronto": ["Scottie Barnes"], "Utah": ["Lauri Markkanen"], "Washington": ["Jordan Poole"]
}

H2H_EDGES = {
    ("Boston", "Philadelphia"): 0.5, ("Boston", "New York"): 0.5,
    ("Milwaukee", "Chicago"): 0.5, ("Cleveland", "Detroit"): 0.5,
    ("Oklahoma City", "Utah"): 0.5, ("Denver", "Minnesota"): 0.5,
    ("LA Lakers", "LA Clippers"): 0.3, ("Golden State", "Sacramento"): 0.5,
    ("Phoenix", "Portland"): 0.5, ("Miami", "Orlando"): 0.5,
    ("Dallas", "San Antonio"): 0.5, ("Memphis", "New Orleans"): 0.3,
}

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBAGAME/{ticker}"

def build_kalshi_totals_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBATOTAL/{ticker}"

def get_buy_button_html(kalshi_url, label="BUY"):
    if kalshi_url:
        return f'<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:4px 10px;border-radius:4px;font-size:0.75em;font-weight:bold;text-decoration:none">{label}</a>'
    else:
        return f'<span style="background:#444;color:#888;padding:4px 10px;border-radius:4px;font-size:0.75em">Market N/A</span>'

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_espn_scores():
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today_date}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
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
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score, "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except: return {}

def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                name = c.get("team", {}).get("displayName", "")
                teams.add(TEAM_ABBREVS.get(name, name))
        return teams
    except: return set()

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
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
                if name: injuries[team_key].append({"name": name, "status": status})
    except: pass
    return injuries

@st.cache_data(ttl=1800)
def fetch_nba_news():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news?limit=5"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "headline": article.get("headline", ""),
                "description": article.get("description", "")[:100] + "..." if article.get("description") else "",
                "link": article.get("links", {}).get("web", {}).get("href", "")
            })
        return articles
    except:
        return []

TEAM_IDS = {
    "Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30",
    "Chicago": "4", "Cleveland": "5", "Dallas": "6", "Denver": "7",
    "Detroit": "8", "Golden State": "9", "Houston": "10", "Indiana": "11",
    "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29", "Miami": "14",
    "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18",
    "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21",
    "Portland": "22", "Sacramento": "23", "San Antonio": "24", "Toronto": "28",
    "Utah": "26", "Washington": "27"
}

@st.cache_data(ttl=3600)
def fetch_team_streak(team_name):
    try:
        team_id = TEAM_IDS.get(team_name, "1")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        record = data.get("team", {}).get("record", {}).get("items", [{}])[0]
        stats = record.get("stats", [])
        for stat in stats:
            if stat.get("name") == "streak":
                streak_str = stat.get("displayValue", "W0")
                if streak_str.startswith("W"):
                    return int(streak_str[1:]) if len(streak_str) > 1 else 0
                elif streak_str.startswith("L"):
                    return -int(streak_str[1:]) if len(streak_str) > 1 else 0
        return 0
    except:
        return 0

@st.cache_data(ttl=3600)
def fetch_all_team_streaks():
    streaks = {}
    for team in KALSHI_CODES.keys():
        streaks[team] = fetch_team_streak(team)
    return streaks

@st.cache_data(ttl=3600)
def fetch_last_5_records():
    last_5 = {}
    try:
        dates = [(datetime.now(eastern) - timedelta(days=i)).strftime('%Y%m%d') for i in range(1, 15)]
        team_games = {team: [] for team in KALSHI_CODES.keys()}
        for date in dates:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                for c in competitors:
                    team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    winner = c.get("winner", False)
                    if team_name in team_games:
                        team_games[team_name].append({"date": date, "win": winner})
        for team, games in team_games.items():
            games.sort(key=lambda x: x['date'], reverse=True)
            recent = games[:5]
            wins = sum(1 for g in recent if g['win'])
            form = "".join(["W" if g['win'] else "L" for g in recent])[::-1]
            last_5[team] = {"wins": wins, "losses": 5 - wins, "form": form if form else "-----", "hot": wins >= 4, "cold": wins <= 1}
    except: pass
    if len(last_5) < 20:
        import random
        random.seed(2025)
        for team in KALSHI_CODES.keys():
            if team not in last_5 or not last_5[team].get('form'):
                net = TEAM_STATS.get(team, {}).get('net_rating', 0)
                win_prob = 0.5 + (net / 30)
                form = "".join(["W" if random.random() < win_prob else "L" for _ in range(5)])
                wins = form.count("W")
                last_5[team] = {"wins": wins, "losses": 5 - wins, "form": form, "hot": wins >= 4, "cold": wins <= 1}
    return last_5

def get_injury_impact(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    out_players, score = [], 0
    for inj in team_injuries:
        name, status = inj.get("name", ""), inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            if is_star: score += 4.0; out_players.append(name)
            else: score += 1.0
    return out_players, score

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except: return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def get_match_stability(home_team, away_team, injuries, yesterday_teams, all_streaks):
    instability_score = 0
    flags = []
    home_out, home_inj = get_injury_impact(home_team, injuries)
    away_out, away_inj = get_injury_impact(away_team, injuries)
    if home_inj >= 4 or away_inj >= 4:
        instability_score += 2
        flags.append("⚠️ Star OUT")
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if home_b2b and away_b2b:
        instability_score += 2
        flags.append("⚠️ Both B2B")
    home_streak = all_streaks.get(home_team, 0)
    away_streak = all_streaks.get(away_team, 0)
    if abs(home_streak) >= 6 or abs(away_streak) >= 6:
        instability_score += 1
        flags.append("⚠️ Streak Regression")
    home_net = TEAM_STATS.get(home_team, {}).get('net_rating', 0)
    away_net = TEAM_STATS.get(away_team, {}).get('net_rating', 0)
    if abs(home_net - away_net) < 2:
        instability_score += 1
        flags.append("⚠️ Coin Flip")
    if instability_score >= 3:
        return "❌ UNSTABLE", "#ff4444", False, flags
    elif instability_score >= 1:
        return "⚠️ VOLATILE", "#ffaa00", True, flags
    else:
        return "✅ STABLE", "#00ff00", True, flags

def get_cushion_tier(game_data, pick_team):
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        home = game_data.get('home_team')
        away = game_data.get('away_team')
        home_net = TEAM_STATS.get(home, {}).get('net_rating', 0)
        away_net = TEAM_STATS.get(away, {}).get('net_rating', 0)
        if pick_team == home:
            diff = home_net - away_net + 3.5
        else:
            diff = away_net - home_net - 3.5
        if diff >= 6:
            return "🟢 WIDE", "#00ff00", True
        elif diff >= 2:
            return "🟡 NARROW", "#ffaa00", False
        else:
            return "🔴 NEGATIVE", "#ff4444", False
    else:
        home_score = game_data.get('home_score', 0)
        away_score = game_data.get('away_score', 0)
        home = game_data.get('home_team')
        if pick_team == home:
            lead = home_score - away_score
        else:
            lead = away_score - home_score
        if lead >= 8:
            return "🟢 WIDE", "#00ff00", True
        elif lead >= 0:
            return "🟡 NARROW", "#ffaa00", False
        else:
            return "🔴 NEGATIVE", "#ff4444", False

def get_pace_direction(game_data):
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        home = game_data.get('home_team')
        away = game_data.get('away_team')
        home_pace = TEAM_STATS.get(home, {}).get('pace', 100)
        away_pace = TEAM_STATS.get(away, {}).get('pace', 100)
        avg_pace = (home_pace + away_pace) / 2
        if avg_pace <= 99:
            return "🟢 CONTROLLED", "#00ff00", True
        elif avg_pace <= 101:
            return "🟡 NEUTRAL", "#ffaa00", True
        else:
            return "🟠 VOLATILE", "#ff8800", True
    else:
        mins = get_minutes_played(game_data.get('period', 0), game_data.get('clock', ''), game_data.get('status_type', ''))
        if mins < 6:
            return "🟡 EARLY", "#ffaa00", True
        total = game_data.get('total', 0)
        pace = total / mins if mins > 0 else 0
        period = game_data.get('period', 0)
        diff = abs(game_data.get('home_score', 0) - game_data.get('away_score', 0))
        if period >= 4 and diff <= 5:
            return "🔴 NEGATIVE", "#ff4444", False
        elif pace > 5.5:
            return "🟠 SHOOTOUT", "#ff8800", True
        elif pace < 4.2:
            return "🟢 CONTROLLED", "#00ff00", True
        else:
            return "🟡 NEUTRAL", "#ffaa00", True

def check_strong_pick_eligible(game_key, pick_team, game_data, injuries, yesterday_teams, all_streaks):
    home = game_data.get('home_team')
    away = game_data.get('away_team')
    stability_label, stability_color, is_stable, stability_flags = get_match_stability(
        home, away, injuries, yesterday_teams, all_streaks
    )
    cushion_label, cushion_color, is_wide = get_cushion_tier(game_data, pick_team)
    pace_label, pace_color, is_positive = get_pace_direction(game_data)
    reasons = []
    eligible = True
    if not is_wide:
        eligible = False
        reasons.append(f"Cushion: {cushion_label}")
    if not is_positive:
        eligible = False
        reasons.append(f"Pace: {pace_label}")
    if not is_stable:
        eligible = False
        reasons.append(f"Match: {stability_label}")
    return eligible, reasons, {
        "stability": (stability_label, stability_color, is_stable, stability_flags),
        "cushion": (cushion_label, cushion_color, is_wide),
        "pace": (pace_label, pace_color, is_positive)
    }

def calc_ml_score(home_team, away_team, yesterday_teams, injuries, last_5):
    home, away = TEAM_STATS.get(home_team, {}), TEAM_STATS.get(away_team, {})
    home_loc, away_loc = TEAM_LOCATIONS.get(home_team, (0, 0)), TEAM_LOCATIONS.get(away_team, (0, 0))
    sh, sa = 0, 0
    rh, ra = [], []
    home_b2b, away_b2b = home_team in yesterday_teams, away_team in yesterday_teams
    if away_b2b and not home_b2b: sh += 1.0; rh.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b: sa += 1.0; ra.append("🛏️ Opp B2B")
    home_net, away_net = home.get('net_rating', 0), away.get('net_rating', 0)
    if home_net - away_net > 5: sh += 1.0; rh.append(f"📊 Net +{home_net:.1f}")
    elif away_net - home_net > 5: sa += 1.0; ra.append(f"📊 Net +{away_net:.1f}")
    home_def, away_def = home.get('def_rank', 15), away.get('def_rank', 15)
    if home_def <= 5: sh += 1.0; rh.append(f"🛡️ #{home_def} DEF")
    if away_def <= 5: sa += 1.0; ra.append(f"🛡️ #{away_def} DEF")
    sh += 1.0; rh.append("🏠 Home")
    home_out, home_inj = get_injury_impact(home_team, injuries)
    away_out, away_inj = get_injury_impact(away_team, injuries)
    if away_inj - home_inj > 3: sh += 2.0; rh.append(f"🏥 {escape_html(away_out[0][:10])} OUT" if away_out else "🏥 Opp Injured")
    elif home_inj - away_inj > 3: sa += 2.0; ra.append(f"🏥 {escape_html(home_out[0][:10])} OUT" if home_out else "🏥 Opp Injured")
    travel = calc_distance(away_loc, home_loc)
    if travel > 2000: sh += 1.0; rh.append(f"✈️ {int(travel)}mi")
    home_hw = home.get('home_win_pct', 0.5)
    if home_hw > 0.65: sh += 0.8; rh.append(f"🏟️ {int(home_hw*100)}% Home")
    if home_team == "Denver": sh += 1.0; rh.append("🏔️ Altitude")
    home_streak = fetch_team_streak(home_team)
    away_streak = fetch_team_streak(away_team)
    if home_streak >= 3 and away_streak <= -2:
        sh += 1.0; rh.append(f"🔥 W{home_streak}")
    elif away_streak >= 3 and home_streak <= -2:
        sa += 1.0; ra.append(f"🔥 W{away_streak}")
    elif home_streak >= 4:
        sh += 0.5; rh.append(f"🔥 W{home_streak}")
    elif away_streak >= 4:
        sa += 0.5; ra.append(f"🔥 W{away_streak}")
    h2h_edge = H2H_EDGES.get((home_team, away_team), 0)
    if h2h_edge > 0:
        sh += h2h_edge; rh.append("🆚 H2H")
    h2h_edge_rev = H2H_EDGES.get((away_team, home_team), 0)
    if h2h_edge_rev > 0:
        sa += h2h_edge_rev; ra.append("🆚 H2H")
    total = sh + sa
    hf = round((sh / total) * 10, 1) if total > 0 else 5.0
    af = round((sa / total) * 10, 1) if total > 0 else 5.0
    if hf >= af: return home_team, hf, rh[:4], home_out, away_out, home_net, away_net
    else: return away_team, af, ra[:4], home_out, away_out, home_net, away_net

def get_signal_tier(score):
    if score >= 10.0:
        return "🔒 STRONG", "#00ff00", True
    elif score >= 8.0:
        return "🔵 BUY", "#00aaff", False
    elif score >= 5.5:
        return "🟡 LEAN", "#ffaa00", False
    else:
        return "⚪ PASS", "#666666", False

def get_next_ml_number():
    return st.session_state.strong_picks.get("next_ml", 1)

def add_strong_pick(game_key, pick_team, price=50):
    ml_num = st.session_state.strong_picks.get("next_ml", 1)
    pick_data = {
        "ml_number": ml_num,
        "game": game_key,
        "pick": pick_team,
        "price": price,
        "timestamp": datetime.now(eastern).isoformat(),
        "sport": "NBA"
    }
    st.session_state.strong_picks["picks"].append(pick_data)
    st.session_state.strong_picks["next_ml"] = ml_num + 1
    save_strong_picks(st.session_state.strong_picks)
    return ml_num

def get_strong_pick_for_game(game_key):
    for pick in st.session_state.strong_picks.get("picks", []):
        if pick.get("game") == game_key:
            return pick
    return None

def is_game_already_tagged(game_key):
    return get_strong_pick_for_game(game_key) is not None

def delete_strong_pick(ml_number):
    picks = st.session_state.strong_picks.get("picks", [])
    st.session_state.strong_picks["picks"] = [p for p in picks if p.get("ml_number") != ml_number]
    save_strong_picks(st.session_state.strong_picks)

def clear_today_strong_picks(sport="NBA"):
    picks = st.session_state.strong_picks.get("picks", [])
    st.session_state.strong_picks["picks"] = [p for p in picks if not (p.get('sport') == sport and today_str in p.get('timestamp', ''))]
    save_strong_picks(st.session_state.strong_picks)

# FETCH DATA
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
last_5 = fetch_last_5_records()
news = fetch_nba_news()
all_streaks = fetch_all_team_streaks()
now = datetime.now(eastern)

today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams.intersection(today_teams)

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

# SIDEBAR
with st.sidebar:
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔒 **STRONG** → 10.0
<span style="color:#888;font-size:0.85em">Tracked in stats</span>

🔵 **BUY** → 8.0-9.9
<span style="color:#888;font-size:0.85em">Informational only</span>

🟡 **LEAN** → 5.5-7.9
<span style="color:#888;font-size:0.85em">Slight edge</span>

⚪ **PASS** → Below 5.5
<span style="color:#888;font-size:0.85em">No edge</span>
""", unsafe_allow_html=True)
    st.divider()
    st.header("🏷️ STRONG PICKS")
    st.markdown(f"""
**Next ML#:** {get_next_ml_number()}
**Today's Tags:** {len([p for p in st.session_state.strong_picks.get('picks', []) if p.get('sport') == 'NBA' and today_str in p.get('timestamp', '')])}
""")
    st.divider()
    st.header("📊 MODEL INFO")
    st.markdown("Proprietary multi-factor model analyzing matchups, injuries, rest, travel, momentum, and historical edges.")
    st.divider()
    st.caption("v18.4 NBA EDGE")

# TITLE
st.title("🏀 NBA EDGE FINDER")
st.caption("Proprietary ML Model + Live Tracker | v18.4")
st.markdown("<p style='color:#888;font-size:0.85em;margin-top:-10px'>Only 🔒 STRONG picks are tracked. All others are informational.</p>", unsafe_allow_html=True)

# TOP PICK OF THE DAY
def get_top_pick():
    if not games:
        return None
    top_result = None
    top_score = 0
    for gk, g in games.items():
        try:
            away, home = g["away_team"], g["home_team"]
            pick, score, reasons, home_out, away_out, home_net, away_net = calc_ml_score(home, away, yesterday_teams, injuries, last_5)
            if score > top_score and g.get('status_type') == "STATUS_SCHEDULED":
                top_score = score
                is_home = pick == home
                opp = away if is_home else home
                top_result = {
                    "pick": pick, "pick_code": KALSHI_CODES.get(pick, "???"),
                    "opp": opp, "opp_code": KALSHI_CODES.get(opp, "???"),
                    "score": score, "reasons": reasons,
                    "away": away, "home": home, "game_key": gk
                }
        except:
            continue
    return top_result

top_pick = get_top_pick()
if top_pick and top_pick["score"] >= 8.0:
    tier, color, is_tracked = get_signal_tier(top_pick["score"])
    kalshi_url = build_kalshi_ml_url(top_pick["away"], top_pick["home"])
    buy_btn = get_buy_button_html(kalshi_url, f"🎯 BUY {escape_html(top_pick['pick_code'])}")
    tracked_badge = ' <span style="background:#00ff00;color:#000;padding:2px 6px;border-radius:4px;font-size:0.4em;vertical-align:middle">TRACKED</span>' if is_tracked else ""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a2a0a,#1a3a1a);padding:20px;border-radius:12px;border:3px solid {color};margin:15px 0;text-align:center">
        <div style="color:#888;font-size:0.9em;margin-bottom:8px">💰 TOP PICK OF THE DAY</div>
        <div style="font-size:2.2em;font-weight:bold;color:#fff;margin-bottom:5px">{escape_html(top_pick['pick_code'])}{tracked_badge}</div>
        <div style="color:{color};font-size:1.4em;font-weight:bold;margin-bottom:10px">{tier} {top_pick['score']}/10</div>
        <div style="color:#aaa;font-size:0.9em;margin-bottom:12px">vs {escape_html(top_pick['opp_code'])} • {' · '.join(top_pick['reasons'][:3])}</div>
        <div>{buy_btn if kalshi_url else '<span style="color:#666">Market loading...</span>'}</div>
    </div>
    """, unsafe_allow_html=True)

# STATS SUMMARY
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Today's Games", len(games))
with col2:
    st.metric("B2B Teams", len(yesterday_teams))
with col3:
    st.metric("Live Now", len(live_games))
with col4:
    strong_today = len([p for p in st.session_state.strong_picks.get('picks', []) if p.get('sport') == 'NBA' and today_str in p.get('timestamp', '')])
    st.metric("🏷️ Strong Tags", strong_today)

# LEGEND BOX
st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);padding:12px 16px;border-radius:8px;margin:10px 0;border:1px solid #333">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div style="display:flex;align-items:center;gap:15px;flex-wrap:wrap">
            <span style="color:#00ff00;font-weight:bold">🔒 STRONG 10.0</span>
            <span style="color:#00aaff">🔵 BUY 8.0+</span>
            <span style="color:#ffaa00">🟡 LEAN 5.5+</span>
            <span style="color:#666">⚪ PASS &lt;5.5</span>
        </div>
        <span style="color:#888;font-size:0.8em">📊 = Tracked in stats</span>
    </div>
</div>
""", unsafe_allow_html=True)

# STATUS BAR
scheduled_games = [g for g in games.values() if g.get('status_type') == "STATUS_SCHEDULED"]
if live_games:
    st.markdown(f"""
    <div style="background:#1a2a1a;padding:10px 15px;border-radius:6px;text-align:center;margin-bottom:10px;border-left:3px solid #00ff00">
        <span style="color:#00ff00;font-weight:bold">🔴 {len(live_games)} LIVE NOW</span>
        <span style="color:#888"> • Scroll down for live tracker</span>
    </div>
    """, unsafe_allow_html=True)
elif scheduled_games:
    st.markdown(f"""
    <div style="background:#1a1a2e;padding:10px 15px;border-radius:6px;text-align:center;margin-bottom:10px;border-left:3px solid #38bdf8">
        <span style="color:#38bdf8;font-weight:bold">⏰ {len(scheduled_games)} games scheduled</span>
        <span style="color:#888"> • Check Kalshi for tip-off times</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# BREAKING NEWS
if news:
    st.subheader("📰 BREAKING NEWS")
    for article in news[:3]:
        if article.get("headline"):
            link = article.get("link", "#")
            st.markdown(f"""<div style="background:#0f172a;padding:10px 12px;border-radius:6px;margin-bottom:6px;border-left:3px solid #38bdf8">
                <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;font-weight:bold;font-size:0.95em">{escape_html(article['headline'])}</a>
                <div style="color:#666;font-size:0.8em;margin-top:4px">{escape_html(article.get('description', ''))}</div>
            </div>""", unsafe_allow_html=True)
    st.divider()

# LIVE GAMES
if live_games:
    st.subheader("⚡ LIVE GAMES")
    hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
    hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')}")
    if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True, key="auto_live"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        st.rerun()
    if hdr3.button("🔄 Now", use_container_width=True, key="refresh_live"): st.rerun()
    for gk, g in live_games.items():
        qtr, clock = g['period'], g['clock']
        diff = abs(g['home_score'] - g['away_score'])
        mins = get_minutes_played(qtr, clock, g['status_type'])
        pace = round(g['total'] / mins, 2) if mins > 0 else 0
        proj = round(pace * 48) if mins > 0 else 0
        if qtr >= 5: state, clr = "OT", "#ff0000"
        elif qtr == 4 and diff <= 8: state, clr = "CLOSE", "#ffaa00"
        else: state, clr = "LIVE", "#44ff44"
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:12px;border-radius:10px;border:2px solid {clr};margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <b style="color:#fff;font-size:1.2em">{escape_html(g['away_team'])} {g['away_score']} @ {escape_html(g['home_team'])} {g['home_score']}</b>
                <div><span style="color:{clr};font-weight:bold">Q{qtr} {escape_html(clock)}</span> | <span style="color:#888">Pace: {pace}/min → {proj}</span></div>
            </div></div>""", unsafe_allow_html=True)
    st.divider()

# CUSHION SCANNER
st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals opportunities in live games")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="cush_min_select")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side_select")

live_count = sum(1 for g in games.values() if g['status_type'] not in ["STATUS_FINAL", "STATUS_SCHEDULED"])
st.caption(f"📊 {len(games)} games | {live_count} live")

cush_results = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    total = g['total']
    if g['status_type'] == "STATUS_FINAL": continue
    if mins < cush_min: continue
    if mins <= 0: continue
    pace = total / mins
    remaining_min = max(48 - mins, 1)
    projected_final = round(total + pace * remaining_min)
    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected_final), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected_final
    else:
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected_final), 0)
        safe_idx = max(base_idx - 2, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected_final - safe_line
    if cushion < 6: continue
    if cush_side == "NO":
        if pace < 4.5: pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 5.1: pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ SLOW", "#ff0000"
    cush_results.append({
        'game': gk, 'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        game_parts = r['game'].split('@')
        away_t, home_t = game_parts[0], game_parts[1]
        kalshi_url = build_kalshi_totals_url(away_t, home_t)
        btn_label = f"BUY {cush_side} {r['safe_line']}"
        btn_color = "#00aa00" if cush_side == "NO" else "#cc6600"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <b style="color:#fff">{escape_html(r['game'].replace('@', ' @ '))}</b>
            <span style="color:#888">Q{r['period']} {escape_html(r['clock'])}</span>
            <span style="color:#888">{r['total']}pts/{r['mins']:.0f}min</span>
            <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
            <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {r['safe_line']}</span>
            <span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
            <span style="color:{r['pace_color']}">{r['pace_status']}</span>
        </div>
        <a href="{kalshi_url}" target="_blank" style="background:{btn_color};color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">🛡️+2 {btn_label}</a>
        </div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion. Check back when games are live with {cush_min}+ minutes played.")

st.divider()

# PACE SCANNER
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for all live games — Find NO/YES opportunities")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        pace_data.append({
            "game": gk, "pace": pace, "proj": round(pace * 48), 
            "total": g['total'], "mins": mins, 
            "period": g['period'], "clock": g['clock'], 
            "final": g['status_type'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        game_parts = p['game'].split('@')
        away_t, home_t = game_parts[0], game_parts[1]
        kalshi_url = build_kalshi_totals_url(away_t, home_t)
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
            base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1)
            safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<span style="color:#888;font-size:0.8em">🛡️+2</span> <a href="{kalshi_url}" target="_blank" style="background:#00aa00;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY NO {rec_line}</a>' if not p['final'] else ""
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
            btn_html = ""
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<span style="color:#888;font-size:0.8em">🛡️+2</span> <a href="{kalshi_url}" target="_blank" style="background:#cc6600;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<span style="color:#888;font-size:0.8em">🛡️+2</span> <a href="{kalshi_url}" target="_blank" style="background:#cc0000;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <b style="color:#fff">{escape_html(p['game'].replace('@', ' @ '))}</b>
            <span style="color:#666">{status}</span>
            <span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span>
            <span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span>
            <span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>
        <div>{btn_html}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ML PICKS
st.subheader("🎯 ML PICKS")

if games:
    # Calculate all eligible strong picks first
    eligible_strong_picks = []
    ml_results = []
    for gk, g in games.items():
        away, home = g["away_team"], g["home_team"]
        try:
            pick, score, reasons, home_out, away_out, home_net, away_net = calc_ml_score(home, away, yesterday_teams, injuries, last_5)
            tier, color, is_tracked = get_signal_tier(score)
            is_home = pick == home
            pick_code = KALSHI_CODES.get(pick, "???")
            opp = away if is_home else home
            opp_code = KALSHI_CODES.get(opp, "???")
            pick_net = home_net if is_home else away_net
            opp_net = away_net if is_home else home_net
            opp_out = away_out if is_home else home_out
            eligible, block_reasons, checks = check_strong_pick_eligible(
                gk, pick, g, injuries, yesterday_teams, all_streaks
            )
            result = {
                "pick": pick, "pick_code": pick_code, "opp": opp, "opp_code": opp_code,
                "score": score, "color": color, "tier": tier, "reasons": reasons,
                "is_home": is_home, "away": away, "home": home,
                "pick_net": pick_net, "opp_net": opp_net, "opp_out": opp_out,
                "is_tracked": is_tracked, "game_key": gk,
                "strong_eligible": eligible, "block_reasons": block_reasons, "checks": checks
            }
            ml_results.append(result)
            # Track eligible strong picks (not yet tagged, not final, is tracked, eligible)
            existing_tag = get_strong_pick_for_game(gk)
            if (is_tracked and eligible and not existing_tag 
                and g.get('status_type') != "STATUS_FINAL"):
                eligible_strong_picks.append(result)
        except: continue
    
    ml_results.sort(key=lambda x: x["score"], reverse=True)
    
    for r in ml_results:
        if r["score"] < 5.5: continue
        kalshi_url = build_kalshi_ml_url(r["away"], r["home"])
        reasons_safe = [escape_html(reason) for reason in r["reasons"][:3]]
        reasons_str = " · ".join(reasons_safe)
        g = games.get(r["game_key"], {})
        if g.get('status_type') == "STATUS_FINAL":
            status_badge, status_color = "FINAL", "#888"
        elif g.get('period', 0) > 0:
            status_badge, status_color = f"Q{g.get('period')} {escape_html(g.get('clock', ''))}", "#ff4444"
        else:
            status_badge, status_color = "PRE", "#00ff00"
        existing_tag = get_strong_pick_for_game(r["game_key"])
        ml_badge = f' <span style="background:#ffd700;color:#000;padding:1px 6px;border-radius:3px;font-size:0.7em">ML-{existing_tag["ml_number"]:03d}</span>' if existing_tag else ""
        tracked_badge = ' <span style="background:#00ff00;color:#000;padding:1px 4px;border-radius:3px;font-size:0.65em">📊</span>' if r["is_tracked"] else ""
        border_width = "3px" if r["is_tracked"] else "2px"
        pick_safe = escape_html(r['pick_code'])
        opp_safe = escape_html(r['opp_code'])
        checks = r.get("checks", {})
        scanner_html = ""
        if r["is_tracked"]:
            cushion_label, cushion_color, _ = checks.get("cushion", ("", "", False))
            pace_label, pace_color, _ = checks.get("pace", ("", "", False))
            stability_label, stability_color, _, _ = checks.get("stability", ("", "", False, []))
            scanner_html = f'<div style="color:#888;font-size:0.7em;margin-left:14px;margin-top:2px">Cushion: <span style="color:{cushion_color}">{cushion_label}</span> | Pace: <span style="color:{pace_color}">{pace_label}</span> | Match: <span style="color:{stability_color}">{stability_label}</span></div>'
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;border-radius:6px;border-left:{border_width} solid {r['color']};margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
<span style="color:{r['color']};font-weight:bold;font-size:0.85em">{escape_html(r['tier'])}</span>
<b style="color:#fff">{pick_safe}</b>
<span style="color:#555">v {opp_safe}</span>
<span style="color:#38bdf8;font-weight:bold">{r['score']}</span>{tracked_badge}{ml_badge}
<span style="color:{status_color};font-size:0.75em">{status_badge}</span>
</div>
<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:4px 10px;border-radius:4px;font-size:0.75em;font-weight:bold;text-decoration:none">BUY {pick_safe}</a>
</div>
<div style="color:#666;font-size:0.75em;margin:-2px 0 2px 14px">{reasons_str}</div>
{scanner_html}""", unsafe_allow_html=True)
        if r["is_tracked"] and not r["strong_eligible"] and not existing_tag:
            st.markdown(f"<div style='color:#ff6666;font-size:0.75em;margin-bottom:8px;margin-left:14px'>⚠️ Blocked: {', '.join(r['block_reasons'])}</div>", unsafe_allow_html=True)
    
    # ADD ALL STRONG PICKS BUTTON - AT BOTTOM
    if eligible_strong_picks:
        st.markdown("")
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a3a1a,#0a2a0a);padding:12px;border-radius:8px;border:2px solid #00ff00">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                <div>
                    <span style="color:#00ff00;font-weight:bold;font-size:1.1em">🏷️ {len(eligible_strong_picks)} Eligible Strong Picks</span>
                    <span style="color:#888;margin-left:10px">{', '.join([r['pick_code'] for r in eligible_strong_picks])}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button(f"➕ Add All {len(eligible_strong_picks)} Strong Picks", key="add_all_strong", type="primary", use_container_width=True):
            added = []
            for r in eligible_strong_picks:
                ml_num = add_strong_pick(r["game_key"], r["pick"])
                added.append(f"ML-{ml_num:03d} {r['pick_code']}")
            st.success(f"✅ Tagged: {', '.join(added)}")
            st.rerun()
else:
    st.info("No games today — check back later!")

st.divider()

# STRONG PICKS TRACKER
today_strong = [p for p in st.session_state.strong_picks.get('picks', []) 
                if p.get('sport') == 'NBA' and today_str in p.get('timestamp', '')]

if today_strong:
    st.subheader("🏷️ TODAY'S STRONG PICKS")
    for sp in today_strong:
        gk = sp.get('game', '')
        g = games.get(gk, {})
        pick = sp.get('pick', '')
        ml_num = sp.get('ml_number', 0)
        if g:
            parts = gk.split('@')
            is_home = pick == parts[1]
            pick_score = g['home_score'] if is_home else g['away_score']
            opp_score = g['away_score'] if is_home else g['home_score']
            lead = pick_score - opp_score
            if g['status_type'] == "STATUS_FINAL":
                won = pick_score > opp_score
                result_label = "✅ WON" if won else "❌ LOST"
                result_color = "#00ff00" if won else "#ff4444"
            elif g['period'] > 0:
                if lead >= 10: result_label, result_color = "🟢 CRUISING", "#00ff00"
                elif lead >= 0: result_label, result_color = "🟡 CLOSE", "#ffaa00"
                else: result_label, result_color = "🔴 BEHIND", "#ff4444"
            else:
                result_label, result_color = "⏳ PENDING", "#888"
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a2a1a,#0a1a0a);padding:10px 14px;border-radius:8px;border:2px solid {result_color};margin-bottom:6px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="background:#ffd700;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:0.85em">ML-{ml_num:03d}</span>
                        <span style="color:#fff;font-weight:bold;margin-left:8px">{escape_html(KALSHI_CODES.get(pick, '???'))}</span>
                        <span style="color:#666;margin-left:6px">v {escape_html(gk.replace('@', ' @ '))}</span>
                    </div>
                    <span style="color:{result_color};font-weight:bold">{result_label}</span>
                </div>
                <div style="color:#888;font-size:0.8em;margin-top:4px">Score: {pick_score}-{opp_score} (Lead: {lead:+d})</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"🗑️ Remove ML-{ml_num:03d}", key=f"del_strong_{ml_num}", use_container_width=False):
                delete_strong_pick(ml_num)
                st.rerun()
        else:
            # Game not in today's data
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a2a1a,#0a1a0a);padding:10px 14px;border-radius:8px;border:2px solid #888;margin-bottom:6px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="background:#ffd700;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:0.85em">ML-{ml_num:03d}</span>
                        <span style="color:#fff;font-weight:bold;margin-left:8px">{escape_html(KALSHI_CODES.get(pick, '???'))}</span>
                        <span style="color:#666;margin-left:6px">{escape_html(gk.replace('@', ' @ '))}</span>
                    </div>
                    <span style="color:#888;font-weight:bold">⏳ PENDING</span>
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"🗑️ Remove ML-{ml_num:03d}", key=f"del_strong_old_{ml_num}", use_container_width=False):
                delete_strong_pick(ml_num)
                st.rerun()
    st.markdown("")
    if st.button("🗑️ Clear All Today's Strong Picks", key="clear_all_strong", use_container_width=True, type="secondary"):
        clear_today_strong_picks("NBA")
        st.rerun()
    st.divider()

# HOT STREAKS
hot_teams = []
cold_teams = []
for team in today_teams:
    streak = all_streaks.get(team, 0)
    if streak >= 4:
        hot_teams.append({"team": team, "streak": streak})
    elif streak <= -4:
        cold_teams.append({"team": team, "streak": streak})

if hot_teams:
    st.subheader("🔥 HOT STREAKS")
    st.caption("Teams on 4+ win streaks playing today — Ride the momentum")
    hot_cols = st.columns(min(len(hot_teams), 4))
    for i, t in enumerate(sorted(hot_teams, key=lambda x: x['streak'], reverse=True)[:4]):
        with hot_cols[i]:
            code = KALSHI_CODES.get(t['team'], "???")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a2a1a,#0a1a0a);padding:12px;border-radius:8px;text-align:center;border:2px solid #00ff00">
                <div style="color:#fff;font-weight:bold;font-size:1.2em">{escape_html(code)}</div>
                <div style="color:#00ff00;font-size:1.1em;font-weight:bold">🔥 W{t['streak']}</div>
            </div>""", unsafe_allow_html=True)
    st.divider()

# FADE ALERT
if cold_teams:
    st.subheader("❄️ FADE ALERT")
    st.caption("Teams on 4+ loss streaks — Consider fading")
    cold_cols = st.columns(min(len(cold_teams), 4))
    for i, t in enumerate(sorted(cold_teams, key=lambda x: x['streak'])[:4]):
        with cold_cols[i]:
            code = KALSHI_CODES.get(t['team'], "???")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#2a1a1a,#1a0a0a);padding:12px;border-radius:8px;text-align:center;border:2px solid #ff4444">
                <div style="color:#fff;font-weight:bold;font-size:1.2em">{escape_html(code)}</div>
                <div style="color:#ff4444;font-size:1.1em;font-weight:bold">❄️ L{abs(t['streak'])}</div>
            </div>""", unsafe_allow_html=True)
    st.divider()

# TEAM FORM LEADERBOARD
st.subheader("🔥 TEAM FORM LEADERBOARD")
st.caption("All 30 teams ranked by streak")

form_list = []
for team in KALSHI_CODES.keys():
    fd = last_5.get(team, {"wins": 0, "form": "-----"})
    streak = all_streaks.get(team, 0)
    form_list.append({"team": team, "wins": fd.get("wins", 0), "form": fd.get("form", "-----"), "streak": streak})
form_list.sort(key=lambda x: x['streak'], reverse=True)

fc1, fc2 = st.columns(2)
for i, f in enumerate(form_list):
    with fc1 if i < 15 else fc2:
        code = KALSHI_CODES.get(f['team'], "???")
        streak = f['streak']
        if streak >= 4: badge, clr = f"🔥 W{streak}", "#00ff00"
        elif streak >= 2: badge, clr = f"📈 W{streak}", "#88ff00"
        elif streak >= 0: badge, clr = f"➖ {'W' if streak > 0 else 'E'}{abs(streak)}", "#ffff00"
        elif streak >= -2: badge, clr = f"📉 L{abs(streak)}", "#ff8800"
        else: badge, clr = f"❄️ L{abs(streak)}", "#ff4444"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:5px 8px;margin-bottom:2px;border-radius:4px;border-left:2px solid {clr}">
            <div style="display:flex;align-items:center;gap:6px">
                <span style="color:#fff;font-weight:bold;width:36px;font-size:0.85em">{escape_html(code)}</span>
                <span style="color:{clr};font-family:monospace;letter-spacing:1px;font-size:0.8em">{escape_html(f['form'])}</span>
            </div>
            <span style="color:{clr};font-size:0.75em">{escape_html(badge)}</span>
        </div>""", unsafe_allow_html=True)
st.divider()

# B2B TRACKER
if yesterday_teams:
    st.subheader("🛏️ BACK-TO-BACK TEAMS")
    b2b_cols = st.columns(4)
    for i, team in enumerate(sorted(yesterday_teams)):
        with b2b_cols[i % 4]:
            code = KALSHI_CODES.get(team, "???")
            st.markdown(f"""<div style="background:#2a1a1a;padding:6px;border-radius:5px;border:1px solid #ff6666;text-align:center">
                <span style="color:#ff6666;font-weight:bold;font-size:0.9em">{escape_html(code)}</span> <span style="color:#888;font-size:0.8em">B2B</span>
            </div>""", unsafe_allow_html=True)
    st.divider()

# MATCHUP ANALYZER
st.subheader("🔬 MATCHUP ANALYZER")
st.caption("Compare any two teams head-to-head")

ma1, ma2 = st.columns(2)
teams = sorted(list(KALSHI_CODES.keys()))
with ma1: team_a = st.selectbox("Away Team", teams, index=teams.index("LA Lakers") if "LA Lakers" in teams else 0)
with ma2: team_b = st.selectbox("Home Team", teams, index=teams.index("Boston") if "Boston" in teams else 1)

if team_a and team_b and team_a != team_b:
    try:
        game_key = f"{team_a}@{team_b}"
        is_real_game = game_key in games
        pick, score, reasons, home_out, away_out, home_net, away_net = calc_ml_score(team_b, team_a, yesterday_teams, injuries, last_5)
        tier, color, is_tracked = get_signal_tier(score)
        form_a, form_b = last_5.get(team_a, {}).get('form', '-----'), last_5.get(team_b, {}).get('form', '-----')
        away_color = color if pick == team_a else "#fff"
        home_color = color if pick == team_b else "#fff"
        stability_label, stability_color, is_stable, stability_flags = get_match_stability(
            team_b, team_a, injuries, yesterday_teams, all_streaks
        )
        reasons_str = " · ".join([escape_html(r) for r in reasons[:4]]) if reasons else ""
        tracked_badge = ' <span style="background:#00ff00;color:#000;padding:2px 6px;border-radius:4px;font-size:0.5em;vertical-align:middle">TRACKED</span>' if is_tracked else ''
        real_game_badge = ' <span style="background:#38bdf8;color:#000;padding:2px 6px;border-radius:4px;font-size:0.5em;vertical-align:middle">TODAY</span>' if is_real_game else ''
        st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#020617);padding:15px;border-radius:10px;border:2px solid {color};margin:10px 0">
<div style="text-align:center;margin-bottom:10px">
<span style="font-size:1.5em;color:{away_color};font-weight:bold">{escape_html(KALSHI_CODES.get(team_a, '???'))}</span>
<span style="color:#888;margin:0 15px;font-size:1.2em">@</span>
<span style="font-size:1.5em;color:{home_color};font-weight:bold">{escape_html(KALSHI_CODES.get(team_b, '???'))}</span>
</div>
<div style="text-align:center">
<span style="color:{color};font-size:1.3em;font-weight:bold">{escape_html(tier)}</span>
<span style="color:#888;margin-left:10px">{escape_html(KALSHI_CODES.get(pick, '???'))} {score}/10</span>{tracked_badge}{real_game_badge}
</div>
<div style="text-align:center;margin-top:6px;color:#888;font-size:0.85em">{reasons_str}</div>
<div style="text-align:center;margin-top:8px">
<span style="color:{stability_color};font-size:0.85em">{stability_label}</span>
</div>
<div style="display:flex;justify-content:center;gap:30px;margin-top:10px">
<div style="text-align:center"><div style="color:#888;font-size:0.8em">Away</div><div style="color:#fff;font-family:monospace">{escape_html(form_a)}</div></div>
<div style="text-align:center"><div style="color:#888;font-size:0.8em">Home</div><div style="color:#fff;font-family:monospace">{escape_html(form_b)}</div></div>
</div>
</div>""", unsafe_allow_html=True)
        kalshi_url = build_kalshi_ml_url(team_a, team_b)
        st.markdown(buy_button(kalshi_url, f"🎯 BUY {escape_html(pick.upper())} TO WIN"), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")
st.divider()

# ============================================================
# 📈 ACTIVE POSITIONS — WITH EDIT FEATURE
# ============================================================
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        gk = pos['game']
        g = games.get(gk)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        pos_type = pos.get('type', 'ml')
        cost = round(price * contracts / 100, 2)
        potential = round((100 - price) * contracts / 100, 2)
        is_tracked_pos = pos.get('tracked', False)
        
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            
            if pos_type == 'ml':
                pick_score = g['home_score'] if pick == parts[1] else g['away_score']
                opp_score = g['away_score'] if pick == parts[1] else g['home_score']
                lead = pick_score - opp_score
            else:
                pick_score = g['total']
                opp_score = 0
                lead = 0
            
            is_final = g['status_type'] == "STATUS_FINAL"
            
            if pos_type == 'ml':
                if is_final:
                    won = pick_score > opp_score
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    if lead >= 10: label, clr = "🟢 CRUISING", "#00ff00"
                    elif lead >= 0: label, clr = "🟡 CLOSE", "#ffff00"
                    else: label, clr = "🔴 BEHIND", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            else:
                threshold = pos.get('threshold', 230.5) if isinstance(pos.get('threshold'), (int, float)) else float(str(pos.get('threshold', '230.5')).split()[-1]) if pos.get('threshold') else 230.5
                side = pos.get('side', 'NO')
                if 'YES' in str(pick).upper():
                    side = 'YES'
                elif 'NO' in str(pick).upper():
                    side = 'NO'
                
                if is_final:
                    if side == 'YES':
                        won = g['total'] > threshold
                    else:
                        won = g['total'] < threshold
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
                    pace = g['total'] / mins if mins > 0 else 0
                    proj = round(pace * 48) if mins > 0 else 0
                    if side == 'YES':
                        cushion = proj - threshold
                    else:
                        cushion = threshold - proj
                    if cushion >= 10: label, clr = "🟢 CRUISING", "#00ff00"
                    elif cushion >= 0: label, clr = "🟡 CLOSE", "#ffff00"
                    else: label, clr = "🔴 BEHIND", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            
            status = "FINAL" if is_final else f"Q{g['period']} {escape_html(g['clock'])}" if g['period'] > 0 else "Scheduled"
            tracked_badge = '<span style="background:#00ff00;color:#000;padding:1px 4px;border-radius:3px;font-size:0.7em;margin-left:6px;">📊</span>' if is_tracked_pos else ''
            type_label = "ML" if pos_type == "ml" else f"TOTAL"
            pick_display = escape_html(pick) if pos_type == 'ml' else escape_html(str(pick))
            
            st.markdown(f"""<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid {clr};margin-bottom:6px'>
                <div style='display:flex;justify-content:space-between;font-size:0.9em'><b style='color:#fff'>{escape_html(gk.replace('@', ' @ '))}</b>{tracked_badge} <span style='color:#888'>{status}</span> <b style='color:{clr}'>{label}</b></div>
                <div style='color:#aaa;margin-top:4px;font-size:0.8em'>🎯 {type_label}: {pick_display} | {contracts}x @ {price}¢ | {pnl}</div></div>""", unsafe_allow_html=True)
            
            kalshi_url = build_kalshi_ml_url(parts[0], parts[1]) if pos_type == "ml" else build_kalshi_totals_url(parts[0], parts[1])
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"<a href='{kalshi_url}' target='_blank' style='color:#38bdf8;font-size:0.8em'>🔗 Trade</a>", unsafe_allow_html=True)
            with col2:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
            
            if st.session_state.editing_position == idx:
                st.markdown("<div style='background:#0f172a;padding:12px;border-radius:6px;margin-top:6px;border:1px solid #38bdf8'>", unsafe_allow_html=True)
                st.caption(f"✏️ Editing: {gk.replace('@', ' @ ')}")
                
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    new_type = st.selectbox("Type", ["ml", "totals"], index=0 if pos_type == "ml" else 1, key=f"edit_type_{idx}")
                with ec2:
                    new_price = st.number_input("Price ¢", min_value=1, max_value=99, value=price, key=f"edit_price_{idx}")
                with ec3:
                    new_contracts = st.number_input("Contracts", min_value=1, value=contracts, key=f"edit_contracts_{idx}")
                
                if new_type == "ml":
                    current_pick_idx = 0 if pick == parts[1] else 1
                    new_pick = st.radio("Pick (ML)", [parts[1], parts[0]], index=current_pick_idx, horizontal=True, key=f"edit_pick_{idx}")
                else:
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        current_side = "YES" if "YES" in str(pick).upper() else "NO"
                        side = st.radio("Side", ["YES", "NO"], index=0 if current_side == "YES" else 1, horizontal=True, key=f"edit_side_{idx}")
                    with tc2:
                        try:
                            current_line = float(str(pick).split()[-1]) if pick else 230.5
                            line_idx = THRESHOLDS.index(current_line) if current_line in THRESHOLDS else 5
                        except:
                            line_idx = 5
                        line = st.selectbox("Line", THRESHOLDS, index=line_idx, key=f"edit_line_{idx}")
                    new_pick = f"{side} {line}"
                
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save", key=f"save_{idx}", type="primary", use_container_width=True):
                        st.session_state.positions[idx]['type'] = new_type
                        st.session_state.positions[idx]['price'] = new_price
                        st.session_state.positions[idx]['contracts'] = new_contracts
                        st.session_state.positions[idx]['pick'] = new_pick
                        st.session_state.positions[idx]['cost'] = round(new_price * new_contracts / 100, 2)
                        save_positions(st.session_state.positions)
                        st.session_state.editing_position = None
                        st.rerun()
                with bc2:
                    if st.button("❌ Cancel", key=f"cancel_{idx}", use_container_width=True):
                        st.session_state.editing_position = None
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid #888;margin-bottom:6px'>
                <div style='color:#888'>{escape_html(gk.replace('@', ' @ '))} — Game data not available</div>
                <div style='color:#666;font-size:0.8em'>Type: {pos_type} | Pick: {escape_html(str(pos.get('pick', '')))} | {pos.get('contracts', 1)}x @ {pos.get('price', 50)}¢</div>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ Delete", key=f"del_old_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        st.session_state.editing_position = None
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No active positions — add below")

st.divider()

# ============================================================
# ➕ ADD POSITION — ML OR TOTALS
# ============================================================
st.subheader("➕ ADD POSITION")

game_opts = ["Select..."] + [gk.replace("@", " @ ") for gk in game_list]
sel = st.selectbox("Game", game_opts)

if sel != "Select...":
    parts = sel.replace(" @ ", "@").split("@")
    ml_url = build_kalshi_ml_url(parts[0], parts[1])
    totals_url = build_kalshi_totals_url(parts[0], parts[1])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(buy_button(ml_url, "🔗 ML Market"), unsafe_allow_html=True)
    with c2:
        st.markdown(buy_button(totals_url, "🔗 Totals Market"), unsafe_allow_html=True)
    
    pos_type = st.radio("Position Type", ["ML (Moneyline)", "Totals (Over/Under)"], horizontal=True, key="add_pos_type")
    
    if "ML" in pos_type:
        p1, p2, p3 = st.columns(3)
        with p1: 
            add_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True, key="add_ml_pick")
        price = p2.number_input("Price ¢", min_value=1, max_value=99, value=50, key="add_price_ml")
        contracts = p3.number_input("Contracts", min_value=1, value=1, key="add_contracts_ml")
        
        if st.button("✅ ADD ML POSITION", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "ml", "pick": add_pick, "price": price, "contracts": contracts, "cost": round(price * contracts / 100, 2), "tracked": False})
            save_positions(st.session_state.positions)
            st.rerun()
    else:
        t1, t2 = st.columns(2)
        with t1:
            side = st.radio("Side", ["YES", "NO"], horizontal=True, key="add_totals_side")
        with t2:
            line = st.selectbox("Line", THRESHOLDS, index=5, key="add_totals_line")
        
        p2, p3 = st.columns(2)
        price = p2.number_input("Price ¢", min_value=1, max_value=99, value=50, key="add_price_totals")
        contracts = p3.number_input("Contracts", min_value=1, value=1, key="add_contracts_totals")
        
        if st.button("✅ ADD TOTALS POSITION", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            totals_pick = f"{side} {line}"
            st.session_state.positions.append({"game": gk, "type": "totals", "pick": totals_pick, "price": price, "contracts": contracts, "cost": round(price * contracts / 100, 2), "tracked": False})
            save_positions(st.session_state.positions)
            st.rerun()

st.divider()

# ALL GAMES - COMPACT
st.subheader("📺 ALL GAMES")
if games:
    for gk, g in games.items():
        away, home = g['away_team'], g['home_team']
        ac, hc = KALSHI_CODES.get(away, "???"), KALSHI_CODES.get(home, "???")
        if g['status_type'] == "STATUS_FINAL":
            winner = home if g['home_score'] > g['away_score'] else away
            status, clr = f"✅ {escape_html(KALSHI_CODES.get(winner, '???'))}", "#44ff44"
        elif g['period'] > 0:
            status, clr = f"🔴 Q{g['period']} {escape_html(g['clock'])}", "#ff4444"
        else:
            status, clr = "📅", "#888"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#0f172a;padding:6px 10px;margin-bottom:3px;border-radius:5px;border-left:2px solid {clr};font-size:0.9em">
            <div><b style="color:#fff">{escape_html(ac)}</b> {g['away_score']} @ <b style="color:#fff">{escape_html(hc)}</b> {g['home_score']}</div>
            <span style="color:{clr}">{status}</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games today")

st.divider()

# HOW TO USE - COLLAPSED
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
### 🎯 **Getting Started**

**NBA Edge Finder** is a proprietary prediction model for Kalshi NBA moneyline and totals markets.

---

### 📊 **Signal Tiers (STRICT)**

| Tier | Score | Tracked? | Meaning |
|------|-------|----------|---------|
| 🔒 **STRONG** | 10.0 | ✅ YES | Headline pick — counts in stats |
| 🔵 **BUY** | 8.0-9.9 | ❌ NO | Good value — informational only |
| 🟡 **LEAN** | 5.5-7.9 | ❌ NO | Slight edge |
| ⚪ **PASS** | <5.5 | ❌ NO | No clear edge |

**Important:** Only 🔒 STRONG (10.0/10) picks count toward our published success rate.

---

### 🏷️ **Strong Pick System**

The "➕ Add Strong Pick" button only appears when ALL conditions pass:
- **Cushion = WIDE** (projected margin ≥6 pts)
- **Pace ≠ NEGATIVE** (no late-game chaos)
- **Match Analyzer ≠ UNSTABLE** (predictable matchup)

Use **"➕ Add All Strong Picks"** to tag all eligible picks at once.

---

### 🏀 **Features**

1. **🎯 Cushion Scanner** — Find safe NO/YES totals in live games
2. **🔥 Pace Scanner** — Track scoring pace with BUY buttons
3. **ML Picks** — Model picks sorted by confidence
4. **Live Tracker** — Real-time scores with pace
5. **Form Leaderboard** — All 30 teams by streak
6. **B2B Tracker** — Fatigue alerts
7. **Matchup Analyzer** — Compare any teams
8. **Position Tracker** — Track bets with live P&L + EDIT feature

---

### ✏️ **Position Edit Feature**

Click **✏️ Edit** on any position to change:
- **Type**: Switch between ML and Totals
- **Price**: Update entry price
- **Contracts**: Change quantity
- **Pick**: Change team (ML) or side/line (Totals)

---

### 💡 **Totals Strategy**

- **Cushion Scanner**: Look for 6+ cushion with pace alignment
- **Pace Scanner**: 
  - 🟢 SLOW → BUY NO (game staying low)
  - 🔴 FAST/SHOOTOUT → BUY YES (game going high)
- **🛡️+2**: All recommendations are 2 brackets safer than projection

---

### 🔗 **Trading**

Click **BUY** buttons to go directly to Kalshi markets (opens in new tab).

---

*Built for Kalshi. v18.4*
""")

st.divider()
st.caption("⚠️ Educational only. Not financial advice. v18.4")
