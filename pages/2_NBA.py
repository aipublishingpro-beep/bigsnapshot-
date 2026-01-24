import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# Auto-refresh every 24 seconds (1 possession)
st_autorefresh(interval=24000, key="datarefresh")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NBA Edge Finder", "/NBA")

# ============================================================
# COOKIE AUTH CHECK
# ============================================================
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

# Minimum minutes before showing totals projection
MIN_MINUTES_FOR_PROJECTION = 6
# Maximum reasonable pace (caps projection at ~264)
MAX_PACE = 5.5

TEAM_STATS = {
    "Atlanta": {"net": -3.2, "pace": 100.5, "home_pct": 0.52, "tier": "weak"},
    "Boston": {"net": 11.2, "pace": 99.8, "home_pct": 0.78, "tier": "elite"},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "home_pct": 0.42, "tier": "weak"},
    "Charlotte": {"net": -6.8, "pace": 99.5, "home_pct": 0.38, "tier": "weak"},
    "Chicago": {"net": -2.1, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Cleveland": {"net": 8.5, "pace": 97.2, "home_pct": 0.75, "tier": "elite"},
    "Dallas": {"net": 4.2, "pace": 99.0, "home_pct": 0.62, "tier": "good"},
    "Denver": {"net": 5.8, "pace": 98.5, "home_pct": 0.72, "tier": "good"},
    "Detroit": {"net": -8.2, "pace": 97.8, "home_pct": 0.32, "tier": "weak"},
    "Golden State": {"net": 3.5, "pace": 100.2, "home_pct": 0.65, "tier": "good"},
    "Houston": {"net": 1.2, "pace": 101.5, "home_pct": 0.55, "tier": "mid"},
    "Indiana": {"net": 2.8, "pace": 103.5, "home_pct": 0.58, "tier": "mid"},
    "LA Clippers": {"net": 1.5, "pace": 98.0, "home_pct": 0.55, "tier": "mid"},
    "LA Lakers": {"net": 2.2, "pace": 99.5, "home_pct": 0.58, "tier": "mid"},
    "Memphis": {"net": 4.5, "pace": 100.8, "home_pct": 0.68, "tier": "good"},
    "Miami": {"net": 3.8, "pace": 97.5, "home_pct": 0.65, "tier": "good"},
    "Milwaukee": {"net": 5.2, "pace": 99.2, "home_pct": 0.70, "tier": "good"},
    "Minnesota": {"net": 7.5, "pace": 98.8, "home_pct": 0.72, "tier": "elite"},
    "New Orleans": {"net": 1.8, "pace": 100.0, "home_pct": 0.55, "tier": "mid"},
    "New York": {"net": 6.2, "pace": 98.5, "home_pct": 0.68, "tier": "good"},
    "Oklahoma City": {"net": 12.5, "pace": 99.8, "home_pct": 0.82, "tier": "elite"},
    "Orlando": {"net": 3.2, "pace": 97.0, "home_pct": 0.62, "tier": "good"},
    "Philadelphia": {"net": 2.5, "pace": 98.2, "home_pct": 0.58, "tier": "mid"},
    "Phoenix": {"net": 2.0, "pace": 99.0, "home_pct": 0.60, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 99.5, "home_pct": 0.40, "tier": "weak"},
    "Sacramento": {"net": 0.8, "pace": 101.2, "home_pct": 0.55, "tier": "mid"},
    "San Antonio": {"net": -4.8, "pace": 100.5, "home_pct": 0.42, "tier": "weak"},
    "Toronto": {"net": -1.5, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Utah": {"net": -7.5, "pace": 100.2, "home_pct": 0.35, "tier": "weak"},
    "Washington": {"net": -6.2, "pace": 101.0, "home_pct": 0.38, "tier": "weak"}
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

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

H2H_EDGES = {
    ("Boston", "Philadelphia"): "Boston",
    ("Boston", "New York"): "Boston",
    ("Cleveland", "Chicago"): "Cleveland",
    ("Oklahoma City", "Utah"): "Oklahoma City",
    ("Denver", "Portland"): "Denver",
    ("Milwaukee", "Indiana"): "Milwaukee",
    ("Golden State", "Portland"): "Golden State",
    ("LA Lakers", "San Antonio"): "LA Lakers",
    ("Miami", "Atlanta"): "Miami",
    ("Phoenix", "Sacramento"): "Phoenix",
    ("Minnesota", "Charlotte"): "Minnesota",
    ("Dallas", "Houston"): "Dallas",
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
    loc1 = TEAM_LOCATIONS.get(team1, "")
    loc2 = TEAM_LOCATIONS.get(team2, "")
    if (loc1 == "ET" and loc2 == "PT") or (loc1 == "PT" and loc2 == "ET"):
        return True
    return False

def get_h2h_edge(home, away):
    key1 = (home, away)
    key2 = (away, home)
    if key1 in H2H_EDGES:
        return H2H_EDGES[key1]
    if key2 in H2H_EDGES:
        return H2H_EDGES[key2]
    return None

def get_conviction(mins, lead):
    """Get conviction level based on timing guide"""
    abs_lead = abs(lead)
    
    # Q4 final 4 minutes (44+ min played)
    if mins >= 44:
        if abs_lead >= 10:
            return "🟢🟢🟢 VERY HIGH", "#00ff00"
        elif abs_lead >= 5:
            return "🟢🟢 HIGH", "#00ff00"
        else:
            return "🟡 MEDIUM", "#cccc00"
    
    # Q4 (36-44 min)
    if mins >= 36:
        if abs_lead >= 15:
            return "🟢🟢 HIGH", "#00ff00"
        elif abs_lead >= 10:
            return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 5:
            return "🟡 MEDIUM", "#cccc00"
        else:
            return "🔴 LOW", "#ff6666"
    
    # Q3 (24-36 min)
    if mins >= 24:
        if abs_lead >= 12:
            return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 8:
            return "🟡 MEDIUM", "#cccc00"
        else:
            return "🔴 LOW", "#ff6666"
    
    # Q2 (12-24 min)
    if mins >= 12:
        if abs_lead >= 10:
            return "🟡 MEDIUM", "#cccc00"
        else:
            return "🔴 LOW", "#ff6666"
    
    # Q1 (0-12 min) - always low
    return "🔴 LOW", "#ff6666"

def get_pace_label(pace):
    """Get pace emoji label"""
    if pace is None:
        return ""
    if pace > 5.0:
        return "🔥 FAST"
    elif pace < 4.2:
        return "🐢 SLOW"
    else:
        return "⚖️ AVG"

def get_safe_projection(total, mins):
    """Calculate projection only if enough time has passed"""
    if mins < MIN_MINUTES_FOR_PROJECTION:
        return None, None
    
    # Calculate real pace - no cap after 6 min
    pace = total / mins if mins > 0 else 0
    
    # Project full game
    projected = round(pace * 48)
    
    return projected, round(pace, 2)

def get_totals_thresholds(projected):
    """Get safe NO and YES thresholds based on projection"""
    if projected is None:
        return None, None, None, None
    
    # Find safe NO (2 levels above projected)
    no_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected), len(THRESHOLDS)-1)
    safe_no_idx = min(no_idx + 1, len(THRESHOLDS) - 1)
    safe_no = THRESHOLDS[safe_no_idx]
    no_cushion = safe_no - projected
    
    # Find safe YES (2 levels below projected)
    yes_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected), 0)
    safe_yes_idx = max(yes_idx - 1, 0)
    safe_yes = THRESHOLDS[safe_yes_idx]
    yes_cushion = projected - safe_yes
    
    return safe_no, no_cushion, safe_yes, yes_cushion

@st.cache_data(ttl=24)
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
                if c.get("homeAway") == "home":
                    home = {"team": name, "score": score}
                else:
                    away = {"team": name, "score": score}
            status = event.get("status", {})
            game_time = event.get("date", "")
            try:
                game_dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                game_dt_eastern = game_dt.astimezone(eastern)
                time_str = game_dt_eastern.strftime("%I:%M %p")
            except:
                time_str = ""
                game_dt_eastern = None
            games.append({
                "home": home["team"], "away": away["team"],
                "home_score": home["score"], "away_score": away["score"],
                "status": status.get("type", {}).get("name", ""),
                "period": status.get("period", 0),
                "clock": status.get("displayClock", ""),
                "time": time_str,
                "datetime": game_dt_eastern
            })
        return games
    except:
        return []

@st.cache_data(ttl=120)
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
                if name and "OUT" in status:
                    injuries[team].append(name)
        return injuries
    except:
        return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    rest = {"b2b": set(), "rested": set()}
    try:
        for days_ago in [1, 2, 3]:
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                for c in event.get("competitions", [{}])[0].get("competitors", []):
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if team:
                        if days_ago == 1:
                            rest["b2b"].add(team)
                        elif days_ago >= 2 and team not in rest["b2b"]:
                            rest["rested"].add(team)
        return rest
    except:
        return {"b2b": set(), "rested": set()}

@st.cache_data(ttl=600)
def fetch_news():
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news", timeout=10).json()
        articles = []
        for item in data.get("articles", [])[:8]:
            articles.append({
                "headline": item.get("headline", ""),
                "description": item.get("description", ""),
                "link": item.get("links", {}).get("web", {}).get("href", "")
            })
        return articles
    except:
        return []

@st.cache_data(ttl=1800)
def fetch_team_record():
    form = {}
    try:
        for days_ago in range(14):
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL":
                    continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue
                home_team, away_team = None, None
                home_score, away_score = 0, 0
                for c in competitors:
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    score = int(c.get("score", 0) or 0)
                    if c.get("homeAway") == "home":
                        home_team, home_score = team, score
                    else:
                        away_team, away_score = team, score
                if home_team and away_team:
                    home_won = home_score > away_score
                    if home_team not in form:
                        form[home_team] = []
                    if away_team not in form:
                        form[away_team] = []
                    form[home_team].insert(0, "W" if home_won else "L")
                    form[away_team].insert(0, "L" if home_won else "W")
        for team in form:
            form[team] = form[team][-5:]
        return form
    except:
        return {}

def get_record_display(form_list):
    if not form_list:
        return "—"
    display = ""
    for result in form_list:
        if result == "W":
            display += "🟢"
        else:
            display += "🔴"
    return display

def get_streak(form_list):
    if not form_list:
        return ""
    current = form_list[-1]
    count = 0
    for result in reversed(form_list):
        if result == current:
            count += 1
        else:
            break
    return f"{current}{count}"

def get_minutes_played(period, clock, status):
    if status == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except: return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_live_ml_alignment(game):
    home = game['home']
    away = game['away']
    home_score = game['home_score']
    away_score = game['away_score']
    total = home_score + away_score
    mins = get_minutes_played(game['period'], game['clock'], game['status'])
    
    if mins < 6:
        return None
    
    lead_home = home_score - away_score
    
    if abs(lead_home) < 5:
        return None
    
    live_score = 50
    
    if abs(lead_home) >= 20:
        live_score += 25 if lead_home > 0 else -25
    elif abs(lead_home) >= 15:
        live_score += 18 if lead_home > 0 else -18
    elif abs(lead_home) >= 10:
        live_score += 12 if lead_home > 0 else -12
    elif abs(lead_home) >= 5:
        live_score += 6 if lead_home > 0 else -6
    
    if mins >= 36:
        if abs(lead_home) >= 10:
            live_score += 15 if lead_home > 0 else -15
        elif abs(lead_home) >= 5:
            live_score += 8 if lead_home > 0 else -8
    elif mins >= 24:
        if abs(lead_home) >= 15:
            live_score += 8 if lead_home > 0 else -8
    
    # Calculate pace - no cap
    pace = total / mins if mins > 0 else 0
    
    if pace > 5.0 and abs(lead_home) >= 10:
        live_score += -4 if lead_home > 0 else 4
    elif pace < 4.2 and abs(lead_home) >= 10:
        live_score += 3 if lead_home > 0 else -3
    
    if live_score >= 55:
        pick = home
        alignment = live_score
    elif live_score <= 45:
        pick = away
        alignment = 100 - live_score
    else:
        return None
    
    return {
        'pick': pick,
        'opponent': away if pick == home else home,
        'alignment': round(alignment),
        'lead': lead_home if pick == home else -lead_home,
        'mins': mins,
        'period': game['period'],
        'clock': game['clock'],
        'home': home,
        'away': away,
        'home_score': home_score,
        'away_score': away_score,
        'pace': round(pace, 2)
    }

def calc_edge(home, away, injuries, rest):
    home_pts, away_pts = 0, 0
    home_reasons, away_reasons = [], []
    h_stats = TEAM_STATS.get(home, {})
    a_stats = TEAM_STATS.get(away, {})
    h_net = h_stats.get("net", 0)
    a_net = a_stats.get("net", 0)
    home_out = injuries.get(home, [])
    away_out = injuries.get(away, [])
    
    for star, (team, tier) in STARS.items():
        if team == home and any(star.lower() in p.lower() for p in home_out):
            pts = 5 if tier == 3 else 3
            away_pts += pts
            away_reasons.append(f"{star.split()[-1]} OUT")
        if team == away and any(star.lower() in p.lower() for p in away_out):
            pts = 5 if tier == 3 else 3
            home_pts += pts
            home_reasons.append(f"{star.split()[-1]} OUT")
    
    h_b2b = home in rest.get("b2b", set())
    a_b2b = away in rest.get("b2b", set())
    h_rested = home in rest.get("rested", set())
    a_rested = away in rest.get("rested", set())
    if a_b2b and not h_b2b:
        home_pts += 4
        home_reasons.append("Opp B2B")
    elif h_b2b and not a_b2b:
        away_pts += 4
        away_reasons.append("Opp B2B")
    if h_rested and a_b2b:
        home_pts += 2
        home_reasons.append("Rested")
    elif a_rested and h_b2b:
        away_pts += 2
        away_reasons.append("Rested")
    
    if a_b2b and is_cross_country(away, home):
        home_pts += 2
        home_reasons.append("Travel fatigue")
    elif h_b2b and is_cross_country(home, away):
        away_pts += 2
        away_reasons.append("Travel fatigue")
    
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
    
    h_pace = h_stats.get("pace", 99)
    a_pace = a_stats.get("pace", 99)
    if h_pace >= 101 and a_pace <= 98:
        home_pts += 1.5
        home_reasons.append("Pace edge")
    elif a_pace >= 101 and h_pace <= 98:
        away_pts += 1.5
        away_reasons.append("Pace edge")
    
    h_tier = h_stats.get("tier", "mid")
    a_tier = a_stats.get("tier", "mid")
    if h_tier == "weak" and a_tier in ["elite", "good"]:
        away_pts += 1.5
        away_reasons.append("Weak home")
    
    if a_tier == "elite" and h_tier != "elite":
        away_pts += 1
        away_reasons.append("Elite road")
    
    base_score = 50 + (net_gap * 1.5)
    base_score = max(25, min(85, base_score))
    total_pts = home_pts + away_pts
    if total_pts > 0:
        if home_pts > away_pts:
            edge_boost = (home_pts / total_pts) * 15
            edge_score = min(90, base_score + edge_boost)
            pick = home
            reasons = home_reasons
            edge = home_pts - away_pts
        else:
            edge_boost = (away_pts / total_pts) * 15
            edge_score = min(90, (100 - base_score) + edge_boost)
            pick = away
            reasons = away_reasons
            edge = away_pts - home_pts
    else:
        if base_score >= 55:
            pick, edge_score, reasons, edge = home, base_score, ["Better team"], 0
        elif base_score <= 45:
            pick, edge_score, reasons, edge = away, 100 - base_score, ["Better team"], 0
        else:
            return None
    return {
        "pick": pick, "opponent": away if pick == home else home,
        "edge_score": round(edge_score), "edge_pts": round(edge, 1),
        "reasons": reasons[:4], "home": home, "away": away,
        "is_home": pick == home
    }

def build_kalshi_url(away, home):
    a_code = KALSHI_CODES.get(away, "XXX")
    h_code = KALSHI_CODES.get(home, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/kxnbagame/kxnbagame-{date_str}{a_code}{h_code}"

def build_kalshi_totals_url(away, home):
    a_code = KALSHI_CODES.get(away, "XXX")
    h_code = KALSHI_CODES.get(home, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/kxnbatotal/kxnbatotal-{date_str}{a_code}{h_code}"

POSITIONS_FILE = "nba_positions.json"

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

# ============================================================
# UI
# ============================================================
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v3.8 | {now.strftime('%b %d, %Y %I:%M %p ET')} | Auto-refresh 24s")

st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #e94560; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
<p style="color: #e94560; font-weight: 600; margin: 0 0 6px 0;">⚠️ IMPORTANT DISCLAIMER</p>
<p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">
This is <strong>not</strong> a predictive model. The Edge Score shows how many factors currently favor one side — it is <strong>not</strong> a win probability. We show the edge, <strong>you make the call</strong>.
</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📊 EDGE LEGEND")
    st.markdown("**Pre-Game Alignment:**")
    st.success("🟢 **75+** — Multiple factors")
    st.info("🟡 **60-74** — Several factors")
    st.warning("⚪ **Below 60** — Few factors")
    st.markdown("---")
    st.header("🔴 LIVE EDGE")
    st.markdown("**75+** — Strong lead + time")
    st.markdown("**60-74** — Clear advantage")
    st.markdown("**50-59** — Close game")
    st.markdown("**TOO EARLY** — Under 6 min")
    st.markdown("**TOO CLOSE** — Lead under 5")
    st.markdown("---")
    st.header("🎯 CONVICTION")
    st.markdown("🟢🟢🟢 VERY HIGH")
    st.markdown("🟢🟢 HIGH")
    st.markdown("🟢 GOOD")
    st.markdown("🟡 MEDIUM")
    st.markdown("🔴 LOW")

games = fetch_games()
injuries = fetch_injuries()
rest = fetch_rest_days()
team_record = fetch_team_record()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
live_count = len([g for g in games if g['status'] == 'STATUS_IN_PROGRESS'])
c2.metric("🔴 Live Now", live_count)
c3.metric("B2B Teams", len(rest.get("b2b", set())))
c4.metric("Last Update", now.strftime("%I:%M:%S %p"))

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']

if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #4a9eff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
    <p style="color: #4a9eff; font-weight: 600; margin: 0 0 6px 0;">📊 REAL-TIME FACTOR ALIGNMENT</p>
    <p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">
    We show the edge — <strong>you make the call</strong>. Edge scores update every 24 seconds based on live score, lead size, and time remaining. Higher alignment = more factors favor that side. This is <strong>not</strong> a prediction.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 TIMING GUIDE — When to buy?"):
        st.markdown("""
        **The key question: How long into a game before buying with conviction?**
        
        | Quarter | Lead | Conviction |
        |---------|------|------------|
        | Q1 (0-12 min) | Any | 🔴 LOW |
        | Q2 (12-24 min) | 10+ | 🟡 MEDIUM |
        | Q3 (24-36 min) | 12+ | 🟢 GOOD |
        | Q4 (36-44 min) | 15+ | 🟢🟢 HIGH |
        | Q4 (44+ min) | 10+ | 🟢🟢🟢 VERY HIGH |
        
        **Sweet spot:** Q3 with double-digit lead. Real separation + still value in price.
        
        **Too early risk:** Up 12 in Q1 means nothing — one cold streak and it's tied.
        
        **Too late risk:** Up 20 with 3 min left — Kalshi price already 90¢, no value left.
        """)
    
    live_edges = []
    for g in live_games:
        ml_live = calc_live_ml_alignment(g)
        mins = get_minutes_played(g['period'], g['clock'], g['status'])
        lead = g['home_score'] - g['away_score']
        
        if ml_live:
            live_edges.append({
                'game': g,
                'ml': ml_live,
                'alignment': ml_live['alignment'],
                'mins': mins,
                'lead': lead
            })
        else:
            live_edges.append({
                'game': g,
                'ml': None,
                'alignment': 50,
                'lead': lead,
                'mins': mins
            })
    
    live_edges.sort(key=lambda x: x['alignment'], reverse=True)
    
    for item in live_edges:
        g = item['game']
        ml = item['ml']
        mins = item['mins']
        lead = item['lead']
        kalshi_url = build_kalshi_url(g['away'], g['home'])
        kalshi_totals_url = build_kalshi_totals_url(g['away'], g['home'])
        
        # Calculate projection with cap
        total = g['home_score'] + g['away_score']
        projected, pace = get_safe_projection(total, mins)
        
        # Get conviction based on time and lead
        conviction_text, conviction_color = get_conviction(mins, lead)
        pace_label = get_pace_label(pace)
        
        if ml:
            alignment = ml['alignment']
            pick = ml['pick']
            ml_lead = ml['lead']
            
            if alignment >= 75:
                border_color = "#00ff00"
                bg_color = "#0d1f0d"
            elif alignment >= 60:
                border_color = "#88cc00"
                bg_color = "#1a1f0d"
            else:
                border_color = "#cccc00"
                bg_color = "#1f1f0d"
            
            # Build totals display
            if projected:
                safe_no, no_cushion, safe_yes, yes_cushion = get_totals_thresholds(projected)
                # Format cushions with proper signs and labels
                if no_cushion >= 10:
                    no_label = f"🟢 NO {safe_no} (+{no_cushion}) SAFE"
                elif no_cushion >= 5:
                    no_label = f"🟡 NO {safe_no} (+{no_cushion})"
                elif no_cushion >= 0:
                    no_label = f"⚪ NO {safe_no} (+{no_cushion})"
                else:
                    no_label = f"🔴 NO {safe_no} ({no_cushion}) AVOID"
                
                if yes_cushion >= 10:
                    yes_label = f"🟢 YES {safe_yes} (+{yes_cushion}) SAFE"
                elif yes_cushion >= 5:
                    yes_label = f"🟡 YES {safe_yes} (+{yes_cushion})"
                elif yes_cushion >= 0:
                    yes_label = f"⚪ YES {safe_yes} (+{yes_cushion})"
                else:
                    yes_label = f"🔴 YES {safe_yes} ({yes_cushion}) AVOID"
                
                totals_text = f"Proj: {projected} | {no_label} | {yes_label}"
            else:
                totals_text = f"⏳ Totals after {MIN_MINUTES_FOR_PROJECTION} min"
            
            card_html = f'<div style="background: linear-gradient(135deg, #1a1a1a 0%, {bg_color} 100%); border: 2px solid {border_color}; border-radius: 10px; padding: 16px; margin: 10px 0;">'
            card_html += f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
            card_html += f'<div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{g["away"]} @ {g["home"]}</span><span style="color: #888; margin-left: 12px;">Q{g["period"]} {g["clock"]}</span></div>'
            card_html += f'<div><span style="color: #fff; font-size: 1.2em; font-weight: bold;">{g["away_score"]} - {g["home_score"]}</span></div></div>'
            card_html += f'<div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
            card_html += f'<div><span style="color: #aaa;">Edge:</span><span style="color: {border_color}; font-size: 1.3em; font-weight: bold; margin-left: 8px;">{pick}</span><span style="color: #888; margin-left: 8px;">({ml_lead:+d} lead)</span><span style="color: #666; margin-left: 8px;">{pace_label}</span></div>'
            card_html += f'<div><span style="background: {border_color}; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{alignment}/100</span></div></div>'
            card_html += f'<div style="margin-top: 8px;"><span style="color: {conviction_color}; font-weight: bold;">{conviction_text}</span></div>'
            card_html += f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #333; color: #888;">{totals_text}</div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button(f"🎯 {pick} ML", kalshi_url)
            with col2:
                if projected:
                    safe_no, _, _, _ = get_totals_thresholds(projected)
                    st.link_button(f"⬇️ NO {safe_no}", kalshi_totals_url)
                else:
                    st.link_button(f"⬇️ TOTALS", kalshi_totals_url)
            with col3:
                if projected:
                    _, _, safe_yes, _ = get_totals_thresholds(projected)
                    st.link_button(f"⬆️ YES {safe_yes}", kalshi_totals_url)
                else:
                    st.link_button(f"⬆️ TOTALS", kalshi_totals_url)
        else:
            # Build totals display
            if projected:
                safe_no, no_cushion, safe_yes, yes_cushion = get_totals_thresholds(projected)
                # Format cushions with proper signs and labels
                if no_cushion >= 10:
                    no_label = f"🟢 NO {safe_no} (+{no_cushion}) SAFE"
                elif no_cushion >= 5:
                    no_label = f"🟡 NO {safe_no} (+{no_cushion})"
                elif no_cushion >= 0:
                    no_label = f"⚪ NO {safe_no} (+{no_cushion})"
                else:
                    no_label = f"🔴 NO {safe_no} ({no_cushion}) AVOID"
                
                if yes_cushion >= 10:
                    yes_label = f"🟢 YES {safe_yes} (+{yes_cushion}) SAFE"
                elif yes_cushion >= 5:
                    yes_label = f"🟡 YES {safe_yes} (+{yes_cushion})"
                elif yes_cushion >= 0:
                    yes_label = f"⚪ YES {safe_yes} (+{yes_cushion})"
                else:
                    yes_label = f"🔴 YES {safe_yes} ({yes_cushion}) AVOID"
                
                totals_text = f"Proj: {projected} | {no_label} | {yes_label}"
            else:
                totals_text = f"⏳ Totals after {MIN_MINUTES_FOR_PROJECTION} min"
            
            edge_status = "TOO EARLY" if mins < 6 else "TOO CLOSE"
            card_html = '<div style="background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 100%); border: 1px solid #555; border-radius: 10px; padding: 16px; margin: 10px 0;">'
            card_html += f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
            card_html += f'<div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{g["away"]} @ {g["home"]}</span><span style="color: #888; margin-left: 12px;">Q{g["period"]} {g["clock"]}</span></div>'
            card_html += f'<div><span style="color: #fff; font-size: 1.2em; font-weight: bold;">{g["away_score"]} - {g["home_score"]}</span></div></div>'
            card_html += f'<div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
            card_html += f'<div><span style="color: #888;">ML Edge:</span><span style="color: #888; margin-left: 8px;">{edge_status}</span><span style="color: #666; margin-left: 8px;">({lead:+d})</span><span style="color: #666; margin-left: 8px;">{pace_label}</span></div>'
            card_html += '<div><span style="background: #555; color: #aaa; padding: 6px 14px; border-radius: 6px; font-weight: bold;">—/100</span></div></div>'
            card_html += f'<div style="margin-top: 8px;"><span style="color: {conviction_color}; font-weight: bold;">{conviction_text}</span></div>'
            card_html += f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #333; color: #888;">{totals_text}</div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button(f"👀 VIEW ML", kalshi_url)
            with col2:
                if projected:
                    safe_no, _, _, _ = get_totals_thresholds(projected)
                    st.link_button(f"⬇️ NO {safe_no}", kalshi_totals_url)
                else:
                    st.link_button(f"⬇️ TOTALS", kalshi_totals_url)
            with col3:
                if projected:
                    _, _, safe_yes, _ = get_totals_thresholds(projected)
                    st.link_button(f"⬆️ YES {safe_yes}", kalshi_totals_url)
                else:
                    st.link_button(f"⬆️ TOTALS", kalshi_totals_url)
        
        st.markdown("")
    
    st.divider()

# STAR INJURIES
st.subheader("🏥 STAR INJURIES")
star_injuries = []
today_teams = set()
for g in games:
    today_teams.add(g["home"])
    today_teams.add(g["away"])
for star, (team, tier) in STARS.items():
    if team in today_teams and team in injuries:
        if any(star.lower() in p.lower() for p in injuries[team]):
            star_injuries.append({"star": star, "team": team, "tier": tier})
star_injuries.sort(key=lambda x: -x["tier"])
if star_injuries:
    for inj in star_injuries[:6]:
        stars = "⭐" * inj["tier"]
        st.error(f"{stars} **{inj['star']}** — OUT ({inj['team']})")
else:
    st.info("No major star injuries for today's games")
b2b_today = [t for t in rest.get("b2b", set()) if t in today_teams]
if b2b_today:
    st.warning(f"🛏️ **B2B TEAMS:** {', '.join(sorted(b2b_today))}")

st.divider()

# NBA NEWS
st.subheader("📰 NBA NEWS")
news = fetch_news()
if news:
    for article in news[:6]:
        if article["link"]:
            st.markdown(f"**[{article['headline']}]({article['link']})**")
        else:
            st.markdown(f"**{article['headline']}**")
else:
    st.info("No news available")

st.divider()

# PRE-GAME ALIGNMENT
st.subheader("🎯 PRE-GAME ALIGNMENT")
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #4a9eff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
<p style="color: #4a9eff; font-weight: 600; margin: 0 0 6px 0;">📊 ALL SCHEDULED GAMES — FACTOR ALIGNMENT</p>
<p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">
We show the edge — <strong>you make the call</strong>. Higher score = more factors favor that side. Sorted by game time (soonest first).
</p>
</div>
""", unsafe_allow_html=True)

if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None
if "show_bulk_add" not in st.session_state:
    st.session_state.show_bulk_add = False

picks = []
for g in games:
    if g["status"] == "STATUS_FINAL" or g["status"] == "STATUS_IN_PROGRESS":
        continue
    result = calc_edge(g["home"], g["away"], injuries, rest)
    if result:
        result["status"] = g["status"]
        result["period"] = g["period"]
        result["clock"] = g["clock"]
        result["home_score"] = g["home_score"]
        result["away_score"] = g["away_score"]
        result["time"] = g.get("time", "")
        result["datetime"] = g.get("datetime")
        picks.append(result)
    else:
        picks.append({
            "pick": None,
            "opponent": None,
            "edge_score": 50,
            "edge_pts": 0,
            "reasons": ["No clear edge"],
            "home": g["home"],
            "away": g["away"],
            "is_home": None,
            "status": g["status"],
            "period": g["period"],
            "clock": g["clock"],
            "home_score": g["home_score"],
            "away_score": g["away_score"],
            "time": g.get("time", ""),
            "datetime": g.get("datetime")
        })
picks.sort(key=lambda x: x["datetime"] if x["datetime"] else datetime.max.replace(tzinfo=eastern))

if picks:
    for p in picks:
        edge_score = p["edge_score"]
        kalshi_url = build_kalshi_url(p["away"], p["home"])
        
        if p["pick"]:
            reasons_str = " • ".join(p["reasons"])
            game_time = p.get("time", "")
            
            if edge_score >= 75:
                border_color = "#00ff00"
                bg_color = "#0d1f0d"
            elif edge_score >= 60:
                border_color = "#88cc00"
                bg_color = "#1a1f0d"
            else:
                border_color = "#cccc00"
                bg_color = "#1f1f0d"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a1a 0%, {bg_color} 100%); border: 2px solid {border_color}; border-radius: 10px; padding: 16px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: #fff; font-size: 1.1em; font-weight: bold;">{p['away']} @ {p['home']}</span>
                        <span style="color: #888; margin-left: 12px;">{game_time}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {border_color}; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{edge_score}/100</span>
                    </div>
                </div>
                <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: #aaa;">Edge:</span>
                        <span style="color: {border_color}; font-size: 1.3em; font-weight: bold; margin-left: 8px;">{p['pick']}</span>
                    </div>
                    <div style="color: #888; font-size: 0.9em;">
                        {reasons_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"🎯 EDGE: {p['pick']} — BUY ON KALSHI", kalshi_url)
        else:
            game_time = p.get("time", "")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 100%); border: 1px solid #555; border-radius: 10px; padding: 16px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: #fff; font-size: 1.1em; font-weight: bold;">{p['away']} @ {p['home']}</span>
                        <span style="color: #888; margin-left: 12px;">{game_time}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: #555; color: #aaa; padding: 6px 14px; border-radius: 6px; font-weight: bold;">—/100</span>
                    </div>
                </div>
                <div style="margin-top: 12px;">
                    <span style="color: #888;">Edge: TOO CLOSE — No clear advantage</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"👀 VIEW {p['away']} @ {p['home']} ON KALSHI", kalshi_url)
        
        st.markdown("")
else:
    st.info("No scheduled games right now.")

st.divider()

# TODAY'S GAMES
st.subheader("📺 TODAY'S GAMES — 5 Day Record")
for g in games:
    home, away = g["home"], g["away"]
    h_net = TEAM_STATS.get(home, {}).get("net", 0)
    a_net = TEAM_STATS.get(away, {}).get("net", 0)
    h_rec = team_record.get(home, [])
    a_rec = team_record.get(away, [])
    h_display = get_record_display(h_rec)
    a_display = get_record_display(a_rec)
    h_streak = get_streak(h_rec)
    a_streak = get_streak(a_rec)
    if g["status"] == "STATUS_FINAL":
        winner = home if g["home_score"] > g["away_score"] else away
        status = f"✅ {winner} wins"
    elif g["status"] == "STATUS_IN_PROGRESS":
        status = f"🔴 Q{g['period']} {g['clock']}"
    else:
        status = "Scheduled"
    st.markdown(f"**{away}** ({a_net:+.1f}) {a_display} {a_streak} — {g['away_score']} @ {g['home_score']} — **{home}** ({h_net:+.1f}) {h_display} {h_streak} | {status}")

st.divider()

# POSITION TRACKER
st.subheader("📈 ACTIVE POSITIONS")
games_dict = {f"{g['away']}@{g['home']}": g for g in games}
if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        gk = pos['game']
        g = games_dict.get(gk)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        pos_type = pos.get('type', 'ml')
        cost = round(price * contracts / 100, 2)
        potential = round((100 - price) * contracts / 100, 2)
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            mins = get_minutes_played(g['period'], g['clock'], g['status'])
            is_final = g['status'] == "STATUS_FINAL"
            is_live = g['status'] == "STATUS_IN_PROGRESS"
            if pos_type == 'ml':
                pick_score = g['home_score'] if pick == parts[1] else g['away_score']
                opp_score = g['away_score'] if pick == parts[1] else g['home_score']
                lead = pick_score - opp_score
                if is_final:
                    won = pick_score > opp_score
                    label, status_color = ("✅ WON", "success") if won else ("❌ LOST", "error")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif is_live:
                    if lead >= 20 and mins >= 36:
                        label, status_color = "🟢 VERY SAFE", "success"
                    elif lead >= 15:
                        label, status_color = "🟢 CRUISING", "success"
                    elif lead >= 8:
                        label, status_color = "🟢 ON TRACK", "success"
                    elif lead >= 1:
                        label, status_color = "🟡 CLOSE", "warning"
                    elif lead == 0:
                        label, status_color = "🟡 TIED", "warning"
                    elif lead >= -7:
                        label, status_color = "🟠 RISKY", "warning"
                    elif lead >= -14:
                        label, status_color = "🔴 WARNING", "error"
                    else:
                        label, status_color = "🔴 DANGER", "error"
                    pnl = f"Lead: {lead:+d} | Win: +${potential:.2f}"
                else:
                    label, status_color = "⏳ PENDING", "info"
                    pnl = f"Win: +${potential:.2f}"
            else:
                threshold = float(str(pos.get('pick', '230.5')).split()[-1]) if pos.get('pick') else 230.5
                side = 'YES' if 'YES' in str(pos.get('pick', '')).upper() else 'NO'
                total = g['home_score'] + g['away_score']
                if is_final:
                    won = (total > threshold) if side == 'YES' else (total < threshold)
                    label, status_color = ("✅ WON", "success") if won else ("❌ LOST", "error")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif is_live and mins > 0:
                    pace_val = total / mins
                    projected = round(total + pace_val * (48 - mins))
                    if side == 'NO':
                        cushion = threshold - projected
                    else:
                        cushion = projected - threshold
                    if cushion >= 15:
                        label, status_color = "🟢 VERY SAFE", "success"
                    elif cushion >= 8:
                        label, status_color = "🟢 ON TRACK", "success"
                    elif cushion >= 3:
                        label, status_color = "🟡 CLOSE", "warning"
                    elif cushion >= -5:
                        label, status_color = "🟠 RISKY", "warning"
                    else:
                        label, status_color = "🔴 DANGER", "error"
                    pnl = f"Proj: {projected} vs {threshold} ({cushion:+.0f}) | Win: +${potential:.2f}"
                else:
                    label, status_color = "⏳ PENDING", "info"
                    pnl = f"Win: +${potential:.2f}"
            status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
            type_label = "ML" if pos_type == "ml" else "TOTAL"
            if status_color == "success":
                st.success(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
            elif status_color == "error":
                st.error(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
            elif status_color == "warning":
                st.warning(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
            else:
                st.info(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
            st.caption(f"🎯 {type_label}: {pick} | {contracts}x @ {price}¢ | {pnl}")
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
            if st.session_state.editing_position == idx:
                ec1, ec2, ec3 = st.columns(3)
                with ec1: new_type = st.selectbox("Type", ["ml", "totals"], index=0 if pos_type == "ml" else 1, key=f"et_{idx}")
                with ec2: new_price = st.number_input("Price ¢", 1, 99, price, key=f"ep_{idx}")
                with ec3: new_contracts = st.number_input("Contracts", 1, 100, contracts, key=f"ec_{idx}")
                if new_type == "ml":
                    new_pick = st.radio("Pick", [parts[1], parts[0]], index=0 if pick == parts[1] else 1, horizontal=True, key=f"epk_{idx}")
                else:
                    tc1, tc2 = st.columns(2)
                    with tc1: edit_side = st.radio("Side", ["YES", "NO"], horizontal=True, key=f"es_{idx}")
                    with tc2: edit_line = st.selectbox("Line", THRESHOLDS, index=5, key=f"el_{idx}")
                    new_pick = f"{edit_side} {edit_line}"
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save", key=f"sv_{idx}", type="primary", use_container_width=True):
                        st.session_state.positions[idx] = {"game": gk, "type": new_type, "pick": new_pick, "price": new_price, "contracts": new_contracts}
                        save_positions(st.session_state.positions)
                        st.session_state.editing_position = None
                        st.rerun()
                with bc2:
                    if st.button("❌ Cancel", key=f"cn_{idx}", use_container_width=True):
                        st.session_state.editing_position = None
                        st.rerun()
            st.markdown("---")
        else:
            st.markdown(f"{gk} — Game not found")
            if st.button("🗑️", key=f"del_old_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    if st.button("🗑️ Clear All Positions", key="clear_all", use_container_width=True):
        st.session_state.positions = []
        st.session_state.editing_position = None
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No active positions — add picks below")

st.divider()

# ADD POSITION
st.subheader("➕ ADD POSITION")
game_list = [f"{g['away']} @ {g['home']}" for g in games]
game_opts = ["Select..."] + game_list
sel = st.selectbox("Game", game_opts, key="add_game")
if sel != "Select...":
    parts = sel.replace(" @ ", "@").split("@")
    pos_type = st.radio("Type", ["Moneyline", "Totals"], horizontal=True, key="add_type")
    if pos_type == "Moneyline":
        p1, p2, p3 = st.columns(3)
        with p1: add_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True, key="add_pick")
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_ml")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_ml")
        if st.button("✅ ADD ML POSITION", key="add_ml", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "ml", "pick": add_pick, "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()
    else:
        t1, t2 = st.columns(2)
        with t1: side = st.radio("Side", ["YES", "NO"], horizontal=True, key="add_side")
        with t2: line = st.selectbox("Line", THRESHOLDS, index=5, key="add_line")
        p2, p3 = st.columns(2)
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_tot")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_tot")
        if st.button("✅ ADD TOTALS POSITION", key="add_tot", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "totals", "pick": f"{side} {line}", "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()

st.divider()

# MATCH ANALYZER
st.subheader("🔬 MATCH ANALYZER")
all_teams = sorted(TEAM_STATS.keys())
ma1, ma2 = st.columns(2)
with ma1:
    away_team = st.selectbox("Away Team", ["Select..."] + all_teams, key="ma_away")
with ma2:
    home_team = st.selectbox("Home Team", ["Select..."] + all_teams, key="ma_home")
if away_team != "Select..." and home_team != "Select..." and away_team != home_team:
    if st.button("🔍 ANALYZE MATCHUP", type="primary", use_container_width=True):
        h_stats = TEAM_STATS.get(home_team, {})
        a_stats = TEAM_STATS.get(away_team, {})
        st.markdown("---")
        st.markdown(f"### {away_team} @ {home_team}")
        st.markdown("**📈 LAST 5 GAMES**")
        h_rec = team_record.get(home_team, [])
        a_rec = team_record.get(away_team, [])
        f1, f2 = st.columns(2)
        with f1:
            a_wins = a_rec.count("W") if a_rec else 0
            st.markdown(f"**{away_team}:** {get_record_display(a_rec)} ({a_wins}-{5-a_wins}) {get_streak(a_rec)}")
        with f2:
            h_wins = h_rec.count("W") if h_rec else 0
            st.markdown(f"**{home_team}:** {get_record_display(h_rec)} ({h_wins}-{5-h_wins}) {get_streak(h_rec)}")
        st.markdown("---")
        st.markdown("**📊 TEAM COMPARISON**")
        comp1, comp2, comp3 = st.columns(3)
        comp1.metric(f"{away_team} Net", f"{a_stats.get('net', 0):+.1f}")
        comp2.metric("vs", "")
        comp3.metric(f"{home_team} Net", f"{h_stats.get('net', 0):+.1f}")
        result = calc_edge(home_team, away_team, injuries, rest)
        if result:
            st.markdown("---")
            st.markdown("**🏆 FACTOR ANALYSIS**")
            edge_score = result["edge_score"]
            if edge_score >= 75:
                st.success(f"🟢 **75+ EDGE: {result['pick']}** — Edge Score: {edge_score}/100")
            elif edge_score >= 68:
                st.info(f"🟡 **68+ EDGE: {result['pick']}** — Edge Score: {edge_score}/100")
            elif edge_score >= 60:
                st.warning(f"⚪ **60+ EDGE: {result['pick']}** — Edge Score: {edge_score}/100")
            else:
                st.info(f"⚪ **LOW EDGE** — Not enough factors align clearly")
            st.caption("Remember: Edge Score shows factor alignment, NOT win probability.")
elif away_team == home_team and away_team != "Select...":
    st.error("Select two different teams")

st.divider()

# HOW TO USE
with st.expander("📖 HOW TO USE THIS APP"):
    st.markdown("""
    ### What This App Does
    
    **We show the edge — you make the call.** This app displays factor alignment for NBA games, not predictions. Higher scores mean more factors favor one side.
    
    ---
    
    ### Two Views
    
    **🎯 Pre-Game Alignment** — Shows all scheduled games sorted by tip-off time. Edge score based on:
    - Star player injuries (+5 for MVP-tier, +3 for All-Star)
    - Back-to-back fatigue (+4)
    - Rest advantage (+2)
    - Travel fatigue (+2 for cross-country)
    - Net rating gap (+1 to +3)
    - Head-to-head history (+1.5)
    - Pace mismatch (+1.5)
    - Home altitude - Denver (+1.5)
    
    **🔴 Live Edge Monitor** — Shows all live games sorted by alignment. Updates every 24 seconds based on:
    - Current lead size
    - Time remaining
    - Quarter context
    - Pace adjustment (fast games = leads less sticky)
    
    ---
    
    ### Conviction Guide
    
    | Conviction | Meaning |
    |------------|---------|
    | 🟢🟢🟢 VERY HIGH | Q4 final 4 min with 10+ lead |
    | 🟢🟢 HIGH | Q4 with 15+ lead |
    | 🟢 GOOD | Q3 with 12+ lead |
    | 🟡 MEDIUM | Q2 with 10+ lead |
    | 🔴 LOW | Q1 or small lead |
    
    ---
    
    ### Totals Guide
    
    Each live card shows safe thresholds for OVER/UNDER:
    - **NO [threshold]** = Safe UNDER (2 levels above projected)
    - **YES [threshold]** = Safe OVER (2 levels below projected)
    - Green = cushion 10+ (strong)
    - Yellow = cushion 5-9 (decent)
    - Gray = cushion under 5 (risky)
    
    **Note:** Totals projection only appears after 6 minutes of game time.
    
    ---
    
    ### Important Reminders
    
    ⚠️ Edge Score ≠ Win Probability  
    ⚠️ This is not a predictive model  
    ⚠️ Past performance doesn't guarantee results  
    ⚠️ Only risk what you can afford to lose  
    """)

st.caption("⚠️ Educational only. Not financial advice. Edge Score ≠ win probability. v3.7")
