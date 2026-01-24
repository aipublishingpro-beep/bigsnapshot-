import streamlit as st
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")
st_autorefresh(interval=24000, key="datarefresh")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NBA Edge Finder", "/NBA")

import extra_streamlit_components as stx
cookie_manager = stx.CookieManager()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

saved_auth = cookie_manager.get("authenticated")
if saved_auth == "true":
    st.session_state.authenticated = True

if not st.session_state.authenticated:
    st.switch_page("Home.py")

import requests
import json
import os
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
MIN_MINUTES_FOR_PROJECTION = 6

TEAM_STATS = {
    "Atlanta": {"net": -3.2, "pace": 100.5, "home_pct": 0.52, "tier": "weak", "def_last10": 114.8},
    "Boston": {"net": 11.2, "pace": 99.8, "home_pct": 0.78, "tier": "elite", "def_last10": 110.5},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "home_pct": 0.42, "tier": "weak", "def_last10": 115.2},
    "Charlotte": {"net": -6.8, "pace": 99.5, "home_pct": 0.38, "tier": "weak", "def_last10": 116.1},
    "Chicago": {"net": -2.1, "pace": 98.8, "home_pct": 0.48, "tier": "weak", "def_last10": 113.9},
    "Cleveland": {"net": 8.5, "pace": 97.2, "home_pct": 0.75, "tier": "elite", "def_last10": 109.8},
    "Dallas": {"net": 4.2, "pace": 99.0, "home_pct": 0.62, "tier": "good", "def_last10": 111.4},
    "Denver": {"net": 5.8, "pace": 98.5, "home_pct": 0.72, "tier": "good", "def_last10": 112.3},
    "Detroit": {"net": -8.2, "pace": 97.8, "home_pct": 0.32, "tier": "weak", "def_last10": 108.5},  # recent strong D
    "Golden State": {"net": 3.5, "pace": 100.2, "home_pct": 0.65, "tier": "good", "def_last10": 113.0},
    "Houston": {"net": 1.2, "pace": 101.5, "home_pct": 0.55, "tier": "mid", "def_last10": 112.8},
    "Indiana": {"net": 2.8, "pace": 103.5, "home_pct": 0.58, "tier": "mid", "def_last10": 114.2},
    "LA Clippers": {"net": 1.5, "pace": 98.0, "home_pct": 0.55, "tier": "mid", "def_last10": 112.0},
    "LA Lakers": {"net": 2.2, "pace": 99.5, "home_pct": 0.58, "tier": "mid", "def_last10": 113.5},
    "Memphis": {"net": 4.5, "pace": 100.8, "home_pct": 0.68, "tier": "good", "def_last10": 111.9},
    "Miami": {"net": 3.8, "pace": 97.5, "home_pct": 0.65, "tier": "good", "def_last10": 110.8},
    "Milwaukee": {"net": 5.2, "pace": 99.2, "home_pct": 0.70, "tier": "good", "def_last10": 112.1},
    "Minnesota": {"net": 7.5, "pace": 98.8, "home_pct": 0.72, "tier": "elite", "def_last10": 109.2},
    "New Orleans": {"net": 1.8, "pace": 100.0, "home_pct": 0.55, "tier": "mid", "def_last10": 113.4},
    "New York": {"net": 6.2, "pace": 98.5, "home_pct": 0.68, "tier": "good", "def_last10": 110.9},
    "Oklahoma City": {"net": 12.5, "pace": 99.8, "home_pct": 0.82, "tier": "elite", "def_last10": 105.5},  # elite D
    "Orlando": {"net": 3.2, "pace": 97.0, "home_pct": 0.62, "tier": "good", "def_last10": 111.2},
    "Philadelphia": {"net": 2.5, "pace": 98.2, "home_pct": 0.58, "tier": "mid", "def_last10": 112.6},
    "Phoenix": {"net": 2.0, "pace": 99.0, "home_pct": 0.60, "tier": "mid", "def_last10": 114.0},
    "Portland": {"net": -5.5, "pace": 99.5, "home_pct": 0.40, "tier": "weak", "def_last10": 116.5},
    "Sacramento": {"net": 0.8, "pace": 101.2, "home_pct": 0.55, "tier": "mid", "def_last10": 119.3},  # poor recent D
    "San Antonio": {"net": -4.8, "pace": 100.5, "home_pct": 0.42, "tier": "weak", "def_last10": 111.6},
    "Toronto": {"net": -1.5, "pace": 98.8, "home_pct": 0.48, "tier": "weak", "def_last10": 115.0},
    "Utah": {"net": -7.5, "pace": 100.2, "home_pct": 0.35, "tier": "weak", "def_last10": 122.2},  # worst recent D
    "Washington": {"net": -6.2, "pace": 101.0, "home_pct": 0.38, "tier": "weak", "def_last10": 120.5},
}

STARS = {
    "Nikola Jokic": ("Denver", 3), "Shai Gilgeous-Alexander": ("Oklahoma City", 3),
    "Giannis Antetokounmpo": ("Milwaukee", 3), "Luka Doncic": ("Dallas", 3),
    "Joel Embiid": ("Philadelphia", 3), "Jayson Tatum": ("Boston", 3),
    "Stephen Curry": ("Golden State", 3), "Kevin Durant": ("Phoenix", 3),
    "LeBron James": ("LA Lakers", 3), "Anthony Edwards": ("Minnesota", 3),
    "Ja Morant": ("Memphis", 3), "Donovan Mitchell": ("Cleveland", 3),
    "Trae Young": ("Atlanta", 3), "Devin Booker": ("Phoenix", 3),
    "Jaylen Brown": ("Boston", 2), "Anthony Davis": ("LA Lakers", 2),
    "Damian Lillard": ("Milwaukee", 2), "Kyrie Irving": ("Dallas", 2),
    "Jimmy Butler": ("Miami", 2), "Bam Adebayo": ("Miami", 2),
    "Tyrese Haliburton": ("Indiana", 2), "De'Aaron Fox": ("Sacramento", 2),
    "Jalen Brunson": ("New York", 2), "Chet Holmgren": ("Oklahoma City", 2),
    "Paolo Banchero": ("Orlando", 2), "Franz Wagner": ("Orlando", 2),
    "Victor Wembanyama": ("San Antonio", 2), "Evan Mobley": ("Cleveland", 2),
    "Zion Williamson": ("New Orleans", 2), "LaMelo Ball": ("Charlotte", 2),
    "Cade Cunningham": ("Detroit", 2), "Tyrese Maxey": ("Philadelphia", 2),
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

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 242.5, 245.5, 250.5, 255.5]

H2H_EDGES = {
    ("Boston", "Philadelphia"): "Boston", ("Boston", "New York"): "Boston",
    ("Cleveland", "Chicago"): "Cleveland", ("Oklahoma City", "Utah"): "Oklahoma City",
    ("Denver", "Portland"): "Denver", ("Milwaukee", "Indiana"): "Milwaukee",
    ("Golden State", "Portland"): "Golden State", ("LA Lakers", "San Antonio"): "LA Lakers",
    ("Miami", "Atlanta"): "Miami", ("Phoenix", "Sacramento"): "Phoenix",
    ("Minnesota", "Charlotte"): "Minnesota", ("Dallas", "Houston"): "Dallas",
    ("Memphis", "New Orleans"): "Memphis",
}

TEAM_LOCATIONS = {
    "Boston": "ET", "Brooklyn": "ET", "New York": "ET", "Philadelphia": "ET", "Toronto": "ET",
    "Atlanta": "ET", "Charlotte": "ET", "Miami": "ET", "Orlando": "ET", "Washington": "ET",
    "Chicago": "CT", "Cleveland": "ET", "Detroit": "ET", "Indiana": "ET", "Milwaukee": "CT",
    "Dallas": "CT", "Houston": "CT", "Memphis": "CT", "New Orleans": "CT", "San Antonio": "CT",
    "Denver": "MT", "Minnesota": "CT", "Oklahoma City": "CT", "Portland": "PT", "Utah": "MT",
    "Golden State": "PT", "LA Clippers": "PT", "LA Lakers": "PT", "Phoenix": "MT", "Sacramento": "PT",
}

def is_cross_country(team1, team2):
    loc1, loc2 = TEAM_LOCATIONS.get(team1, ""), TEAM_LOCATIONS.get(team2, "")
    return (loc1 == "ET" and loc2 == "PT") or (loc1 == "PT" and loc2 == "ET")

def get_h2h_edge(home, away):
    if (home, away) in H2H_EDGES: return H2H_EDGES[(home, away)]
    if (away, home) in H2H_EDGES: return H2H_EDGES[(away, home)]
    return None

def get_conviction(mins, lead):
    abs_lead = abs(lead)
    if mins >= 44:
        if abs_lead >= 10: return "🟢🟢🟢 VERY HIGH", "#00ff00"
        elif abs_lead >= 5: return "🟢🟢 HIGH", "#00ff00"
        else: return "🟡 MEDIUM", "#cccc00"
    if mins >= 36:
        if abs_lead >= 15: return "🟢🟢 HIGH", "#00ff00"
        elif abs_lead >= 10: return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 5: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    if mins >= 24:
        if abs_lead >= 12: return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 8: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    if mins >= 12:
        if abs_lead >= 10: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    return "🔴 LOW", "#ff6666"

def get_pace_label(pace):
    if pace is None: return ""
    if pace > 5.0: return "🔥 FAST"
    elif pace < 4.2: return "🐢 SLOW"
    return "⚖️ AVG"

def get_safe_projection(total, mins, home, away):
    if mins < MIN_MINUTES_FOR_PROJECTION: return None, None
    raw_pace = total / mins if mins > 0 else 0
    h_pace = TEAM_STATS.get(home, {}).get("pace", 99)
    a_pace = TEAM_STATS.get(away, {}).get("pace", 99)
    blended_pace = (h_pace + a_pace + raw_pace * 2) / 4  # weight live data heavier
    projected = round(blended_pace * 48)
    return projected, round(blended_pace, 2)

def get_totals_thresholds(projected):
    if projected is None: return None, None, None, None
    no_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected), len(THRESHOLDS)-1)
    safe_no_idx = min(no_idx + 1, len(THRESHOLDS) - 1)
    safe_no = THRESHOLDS[safe_no_idx]
    no_cushion = safe_no - projected
    yes_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected), 0)
    safe_yes_idx = max(yes_idx - 1, 0)
    safe_yes = THRESHOLDS[safe_yes_idx]
    yes_cushion = projected - safe_yes
    return safe_no, no_cushion, safe_yes, yes_cushion

@st.cache_data(ttl=45)
def fetch_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        data = requests.get(url, timeout=10).json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home, away = None, None
            for c in competitors:
                name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home": home = {"team": name, "score": score}
                else: away = {"team": name, "score": score}
            status = event.get("status", {})
            game_time = event.get("date", "")
            try:
                game_dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                game_dt_eastern = game_dt.astimezone(eastern)
                time_str = game_dt_eastern.strftime("%I:%M %p")
            except:
                time_str, game_dt_eastern = "", None
            games.append({"home": home["team"], "away": away["team"], "home_score": home["score"], "away_score": away["score"], "status": status.get("type", {}).get("name", ""), "period": status.get("period", 0), "clock": status.get("displayClock", ""), "time": time_str, "datetime": game_dt_eastern})
        return games
    except: return []

@st.cache_data(ttl=600)  # 10 min — injuries change slowly
def fetch_injuries():
    injuries = {}
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", timeout=10).json()
        for team_data in data.get("injuries", []):
            team = TEAM_ABBREVS.get(team_data.get("displayName", ""), "")
            if not team: continue
            injuries[team] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "").upper()
                if name and "OUT" in status: injuries[team].append(name)
        return injuries
    except: return {}

@st.cache_data(ttl=14400)  # 4 hours — rest schedule stable
def fetch_rest_days():
    rest = {"b2b": set(), "3in4": set(), "4in5": set(), "rested": set()}
    today = datetime.now(eastern).date()
    try:
        for days_ago in range(1, 6):  # look back 5 days
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                for c in event.get("competitions", [{}])[0].get("competitors", []):
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if not team: continue
                    game_date = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).date()
                    days_rest = (today - game_date).days
                    if days_ago == 1:
                        rest["b2b"].add(team)
                    if days_rest <= 3 and days_rest >= 1:  # played within last 3 days → 3-in-4 incl today
                        rest["3in4"].add(team)
                    if days_rest <= 4 and days_rest >= 1:
                        rest["4in5"].add(team)
                    if days_ago >= 2 and team not in rest["b2b"]:
                        rest["rested"].add(team)
        return rest
    except: return {"b2b": set(), "3in4": set(), "4in5": set(), "rested": set()}

@st.cache_data(ttl=1800)
def fetch_news():
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news", timeout=10).json()
        return [{"headline": item.get("headline", ""), "description": item.get("description", ""), "link": item.get("links", {}).get("web", {}).get("href", "")} for item in data.get("articles", [])[:8]]
    except: return []

# ... (keep your existing fetch_team_record, get_record_display, get_streak, get_minutes_played, calc_live_ml_alignment)

def calc_edge(home, away, injuries, rest):
    home_pts, away_pts = 0, 0
    home_reasons, away_reasons = [], []
    h_stats, a_stats = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
    h_net, a_net = h_stats.get("net", 0), a_stats.get("net", 0)
    home_out, away_out = injuries.get(home, []), injuries.get(away, [])

    # Star injuries
    for star, (team, tier) in STARS.items():
        if team == home and any(star.lower() in p.lower() for p in home_out):
            away_pts += 5 if tier == 3 else 3
            away_reasons.append(f"{star.split()[-1]} OUT")
        if team == away and any(star.lower() in p.lower() for p in away_out):
            home_pts += 5 if tier == 3 else 3
            home_reasons.append(f"{star.split()[-1]} OUT")

    # Expanded rest / schedule edges
    h_b2b = home in rest.get("b2b", set())
    a_b2b = away in rest.get("b2b", set())
    h_3in4 = home in rest.get("3in4", set())
    a_3in4 = away in rest.get("3in4", set())
    h_4in5 = home in rest.get("4in5", set())
    a_4in5 = away in rest.get("4in5", set())

    if a_b2b and not h_b2b:
        home_pts += 4.5
        home_reasons.append("Opp B2B")
    elif h_b2b and not a_b2b:
        away_pts += 4.5
        away_reasons.append("Opp B2B")

    if a_3in4 and not h_3in4:
        home_pts += 3.0
        home_reasons.append("Opp 3-in-4")
    elif h_3in4 and not a_3in4:
        away_pts += 3.0
        away_reasons.append("Opp 3-in-4")

    if a_4in5 and not h_4in5:
        home_pts += 1.8
        home_reasons.append("Opp 4-in-5 fatigue")

    if a_b2b and is_cross_country(away, home):
        home_pts += 3.0
        home_reasons.append("Opp B2B + cross-country travel")
    elif h_b2b and is_cross_country(home, away):
        away_pts += 3.0
        away_reasons.append("Opp B2B + cross-country travel")

    # Recent defensive efficiency edge
    h_def = h_stats.get("def_last10", 112.0)
    a_def = a_stats.get("def_last10", 112.0)
    def_gap = a_def - h_def  # positive = home better D
    if def_gap >= 5:
        home_pts += 2.8
        home_reasons.append(f"Recent D edge +{def_gap:.1f}")
    elif def_gap >= 2.5:
        home_pts += 1.4
        home_reasons.append(f"Recent D edge +{def_gap:.1f}")
    elif def_gap <= -5:
        away_pts += 2.8
        away_reasons.append(f"Recent D edge +{-def_gap:.1f}")
    elif def_gap <= -2.5:
        away_pts += 1.4
        away_reasons.append(f"Recent D edge +{-def_gap:.1f}")

    # Existing factors (net, h2h, pace, altitude, etc.)
    h2h_winner = get_h2h_edge(home, away)
    if h2h_winner == home: 
        home_pts += 1.5
        home_reasons.append("H2H edge")
    elif h2h_winner == away: 
        away_pts += 1.5
        away_reasons.append("H2H edge")

    net_gap = h_net - a_net
    if net_gap >= 15: 
        home_pts += 3
        home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap >= 10: 
        home_pts += 2
        home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap >= 5: 
        home_pts += 1
        home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap <= -15: 
        away_pts += 3
        away_reasons.append(f"Net +{-net_gap:.0f}")
    elif net_gap <= -10: 
        away_pts += 2
        away_reasons.append(f"Net +{-net_gap:.0f}")
    elif net_gap <= -5: 
        away_pts += 1
        away_reasons.append(f"Net +{-net_gap:.0f}")

    if home == "Denver": 
        home_pts += 1.5
        home_reasons.append("Altitude")

    h_pace, a_pace = h_stats.get("pace", 99), a_stats.get("pace", 99)
    if h_pace >= 101 and a_pace <= 98: 
        home_pts += 1.5
        home_reasons.append("Pace edge")
    elif a_pace >= 101 and h_pace <= 98: 
        away_pts += 1.5
        away_reasons.append("Pace edge")

    h_tier, a_tier = h_stats.get("tier", "mid"), a_stats.get("tier", "mid")
    if h_tier == "weak" and a_tier in ["elite", "good"]: 
        away_pts += 1.5
        away_reasons.append("Weak home")
    if a_tier == "elite" and h_tier != "elite": 
        away_pts += 1
        away_reasons.append("Elite road")

    base_score = max(25, min(85, 50 + (net_gap * 1.5)))
    total_pts = home_pts + away_pts

    if total_pts > 0:
        if home_pts > away_pts:
            edge_score = min(90, base_score + (home_pts / total_pts) * 15)
            pick, reasons, edge = home, home_reasons, home_pts - away_pts
        else:
            edge_score = min(90, (100 - base_score) + (away_pts / total_pts) * 15)
            pick, reasons, edge = away, away_reasons, away_pts - home_pts
    else:
        if base_score >= 55: 
            pick, edge_score, reasons, edge = home, base_score, ["Better team"], 0
        elif base_score <= 45: 
            pick, edge_score, reasons, edge = away, 100 - base_score, ["Better team"], 0
        else: 
            return None

    return {
        "pick": pick, 
        "opponent": away if pick == home else home, 
        "edge_score": round(edge_score), 
        "edge_pts": round(edge, 1), 
        "reasons": reasons[:5],  # show more reasons now
        "home": home, 
        "away": away, 
        "is_home": pick == home
    }

# Keep your build_kalshi_url, build_kalshi_totals_url, load/save_positions, UI code as-is
# ... (the rest of your original script from # UI onwards remains unchanged)

st.title("🏀 NBA EDGE FINDER v5.0 — Enhanced Rest + Defense")
st.caption(f"Rest depth + recent D-rating added | {now.strftime('%b %d, %Y %I:%M %p ET')} | Refresh 24s")

# Your existing disclaimer, sidebar, metrics, live monitor, injuries, news, pre-game, games list, positions tracker...
