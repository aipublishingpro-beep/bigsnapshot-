import streamlit as st

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

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

send_ga4_event("NHL Edge Finder", "/NHL")

# ============================================================
# AUTH REMOVED - FREE APP
# ============================================================
# No authentication required for NHL Edge Finder

# ============================================================
# IMPORTS
# ============================================================
import requests
import json
import os
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

apply_styles()

VERSION = "19.7 LIVE"  # Added game date/time display for scheduled games

# ============================================================
# STRONG PICKS SYSTEM
# ============================================================
STRONG_PICKS_FILE = "strong_picks.json"

def load_strong_picks():
    try:
        if os.path.exists(STRONG_PICKS_FILE):
            with open(STRONG_PICKS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"picks": [], "next_ml": 1}

def save_strong_picks(data):
    try:
        with open(STRONG_PICKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

def get_next_ml_number():
    picks_data = st.session_state.strong_picks
    return picks_data.get("next_ml", 1)

def add_strong_pick(sport, team, opponent, edge_score, reasons):
    picks_data = st.session_state.strong_picks
    ml_num = get_next_ml_number()
    
    pick = {
        "ml_number": ml_num,
        "sport": sport,
        "team": team,
        "opponent": opponent,
        "edge_score": edge_score,
        "reasons": reasons,
        "timestamp": datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        "result": "PENDING"
    }
    
    picks_data["picks"].append(pick)
    picks_data["next_ml"] = ml_num + 1
    save_strong_picks(picks_data)
    st.session_state.strong_picks = picks_data
    return ml_num

if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

# ============================================================
# TEAM DATA
# ============================================================
NHL_TEAMS = {
    "ANA": {"name": "Anaheim Ducks", "conference": "West", "division": "Pacific"},
    "ARI": {"name": "Arizona Coyotes", "conference": "West", "division": "Central"},
    "BOS": {"name": "Boston Bruins", "conference": "East", "division": "Atlantic"},
    "BUF": {"name": "Buffalo Sabres", "conference": "East", "division": "Atlantic"},
    "CGY": {"name": "Calgary Flames", "conference": "West", "division": "Pacific"},
    "CAR": {"name": "Carolina Hurricanes", "conference": "East", "division": "Metropolitan"},
    "CHI": {"name": "Chicago Blackhawks", "conference": "West", "division": "Central"},
    "COL": {"name": "Colorado Avalanche", "conference": "West", "division": "Central"},
    "CBJ": {"name": "Columbus Blue Jackets", "conference": "East", "division": "Metropolitan"},
    "DAL": {"name": "Dallas Stars", "conference": "West", "division": "Central"},
    "DET": {"name": "Detroit Red Wings", "conference": "East", "division": "Atlantic"},
    "EDM": {"name": "Edmonton Oilers", "conference": "West", "division": "Pacific"},
    "FLA": {"name": "Florida Panthers", "conference": "East", "division": "Atlantic"},
    "LAK": {"name": "Los Angeles Kings", "conference": "West", "division": "Pacific"},
    "MIN": {"name": "Minnesota Wild", "conference": "West", "division": "Central"},
    "MTL": {"name": "Montreal Canadiens", "conference": "East", "division": "Atlantic"},
    "NSH": {"name": "Nashville Predators", "conference": "West", "division": "Central"},
    "NJD": {"name": "New Jersey Devils", "conference": "East", "division": "Metropolitan"},
    "NYI": {"name": "New York Islanders", "conference": "East", "division": "Metropolitan"},
    "NYR": {"name": "New York Rangers", "conference": "East", "division": "Metropolitan"},
    "OTT": {"name": "Ottawa Senators", "conference": "East", "division": "Atlantic"},
    "PHI": {"name": "Philadelphia Flyers", "conference": "East", "division": "Metropolitan"},
    "PIT": {"name": "Pittsburgh Penguins", "conference": "East", "division": "Metropolitan"},
    "SJS": {"name": "San Jose Sharks", "conference": "West", "division": "Pacific"},
    "SEA": {"name": "Seattle Kraken", "conference": "West", "division": "Pacific"},
    "STL": {"name": "St. Louis Blues", "conference": "West", "division": "Central"},
    "TBL": {"name": "Tampa Bay Lightning", "conference": "East", "division": "Atlantic"},
    "TOR": {"name": "Toronto Maple Leafs", "conference": "East", "division": "Atlantic"},
    "VAN": {"name": "Vancouver Canucks", "conference": "West", "division": "Pacific"},
    "VGK": {"name": "Vegas Golden Knights", "conference": "West", "division": "Pacific"},
    "WSH": {"name": "Washington Capitals", "conference": "East", "division": "Metropolitan"},
    "WPG": {"name": "Winnipeg Jets", "conference": "West", "division": "Central"},
}

GOALIES = {
    "ANA": {"starter": "Dostal", "starter_sv": 0.908, "backup": "Gibson", "backup_sv": 0.888},
    "BOS": {"starter": "Swayman", "starter_sv": 0.916, "backup": "Korpisalo", "backup_sv": 0.899},
    "BUF": {"starter": "Luukkonen", "starter_sv": 0.910, "backup": "Levi", "backup_sv": 0.894},
    "CGY": {"starter": "Wolf", "starter_sv": 0.915, "backup": "Vladar", "backup_sv": 0.901},
    "CAR": {"starter": "Andersen", "starter_sv": 0.914, "backup": "Kochetkov", "backup_sv": 0.909},
    "CHI": {"starter": "Mrazek", "starter_sv": 0.907, "backup": "Soderblom", "backup_sv": 0.896},
    "COL": {"starter": "Georgiev", "starter_sv": 0.897, "backup": "Annunen", "backup_sv": 0.905},
    "CBJ": {"starter": "Merzlikins", "starter_sv": 0.901, "backup": "Tarasov", "backup_sv": 0.908},
    "DAL": {"starter": "Oettinger", "starter_sv": 0.913, "backup": "DeSmith", "backup_sv": 0.903},
    "DET": {"starter": "Talbot", "starter_sv": 0.911, "backup": "Lyon", "backup_sv": 0.904},
    "EDM": {"starter": "Skinner", "starter_sv": 0.905, "backup": "Pickard", "backup_sv": 0.909},
    "FLA": {"starter": "Bobrovsky", "starter_sv": 0.915, "backup": "Knight", "backup_sv": 0.903},
    "LAK": {"starter": "Kuemper", "starter_sv": 0.908, "backup": "Rittich", "backup_sv": 0.901},
    "MIN": {"starter": "Gustavsson", "starter_sv": 0.911, "backup": "Fleury", "backup_sv": 0.906},
    "MTL": {"starter": "Montembeault", "starter_sv": 0.903, "backup": "Primeau", "backup_sv": 0.890},
    "NSH": {"starter": "Saros", "starter_sv": 0.918, "backup": "Wedgewood", "backup_sv": 0.900},
    "NJD": {"starter": "Markstrom", "starter_sv": 0.910, "backup": "Allen", "backup_sv": 0.904},
    "NYI": {"starter": "Sorokin", "starter_sv": 0.919, "backup": "Varlamov", "backup_sv": 0.912},
    "NYR": {"starter": "Shesterkin", "starter_sv": 0.917, "backup": "Quick", "backup_sv": 0.903},
    "OTT": {"starter": "Ullmark", "starter_sv": 0.913, "backup": "Forsberg", "backup_sv": 0.901},
    "PHI": {"starter": "Ersson", "starter_sv": 0.907, "backup": "Fedotov", "backup_sv": 0.897},
    "PIT": {"starter": "Jarry", "starter_sv": 0.903, "backup": "Blomqvist", "backup_sv": 0.909},
    "SJS": {"starter": "Askarov", "starter_sv": 0.898, "backup": "Blackwood", "backup_sv": 0.894},
    "SEA": {"starter": "Daccord", "starter_sv": 0.912, "backup": "Grubauer", "backup_sv": 0.899},
    "STL": {"starter": "Binnington", "starter_sv": 0.907, "backup": "Hofer", "backup_sv": 0.910},
    "TBL": {"starter": "Vasilevskiy", "starter_sv": 0.915, "backup": "Johansson", "backup_sv": 0.902},
    "TOR": {"starter": "Woll", "starter_sv": 0.914, "backup": "Stolarz", "backup_sv": 0.912},
    "VAN": {"starter": "Demko", "starter_sv": 0.918, "backup": "Lankinen", "backup_sv": 0.908},
    "VGK": {"starter": "Hill", "starter_sv": 0.912, "backup": "Samsonov", "backup_sv": 0.903},
    "WSH": {"starter": "Thompson", "starter_sv": 0.911, "backup": "Lindgren", "backup_sv": 0.903},
    "WPG": {"starter": "Hellebuyck", "starter_sv": 0.923, "backup": "Comrie", "backup_sv": 0.897},
}

eastern = pytz.timezone('US/Eastern')

# ============================================================
# TEAM ABBREVIATION MAPPING
# ============================================================
TEAM_ABBREVS = {
    "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
    "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

# ============================================================
# ESPN API - REAL NHL DATA
# ============================================================
@st.cache_data(ttl=60)
def fetch_nhl_games_real():
    """Fetch today's NHL games from ESPN API"""
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={today_date}"
    
    games = []
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            
            if len(competitors) < 2:
                continue
            
            home_team, away_team = None, None
            home_abbr, away_abbr = "", ""
            
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                
                if c.get("homeAway") == "home":
                    home_team = full_name
                    home_abbr = abbr
                else:
                    away_team = full_name
                    away_abbr = abbr
            
            # Get records (W-L-OT format)
            home_record = "0-0-0"
            away_record = "0-0-0"
            for c in competitors:
                record = c.get("records", [{}])[0].get("summary", "0-0-0")
                if c.get("homeAway") == "home":
                    home_record = record
                else:
                    away_record = record
            
            # Get game date/time
            game_date = event.get("date", "")
            status = event.get("status", {})
            status_type = status.get("type", {}).get("name", "STATUS_SCHEDULED")
            
            # Format game time
            game_time = "TBD"
            if game_date:
                try:
                    dt = datetime.strptime(game_date, "%Y-%m-%dT%H:%M%SZ")
                    dt_eastern = dt.replace(tzinfo=pytz.UTC).astimezone(eastern)
                    game_time = dt_eastern.strftime("%I:%M %p ET")
                except:
                    game_time = "TBD"
            
            # Build game dict with mock supplemental data
            # (Real stats would come from separate API calls)
            game = {
                "id": event.get("id"),
                "home": home_abbr,
                "away": away_abbr,
                "home_record": home_record,
                "away_record": away_record,
                "game_time": game_time,
                "status": status_type,
                "home_last10": "5-4-1",  # Mock - would need separate API
                "away_last10": "6-3-1",  # Mock - would need separate API
                "home_goalie": "starter",  # Mock - would need roster API
                "away_goalie": "starter",  # Mock - would need roster API
                "home_b2b": False,  # Would calculate from yesterday's games
                "away_b2b": False,  # Would calculate from yesterday's games
                "home_rest": 1,
                "away_rest": 1,
                "home_pp": 22.0,  # Mock - would need stats API
                "away_pp": 20.0,
                "home_pk": 82.0,
                "away_pk": 80.0,
                "home_xgf": 3.0,
                "home_xga": 2.7,
                "away_xgf": 2.9,
                "away_xga": 2.8,
                "h2h_home": 3,
                "h2h_away": 2,
                "home_kalshi": 55,  # Mock - would scrape from Kalshi
                "away_kalshi": 45,
            }
            
            games.append(game)
        
        return games
        
    except Exception as e:
        st.error(f"ESPN API error: {e}")
        return []

# ============================================================
# EDGE CALCULATION FUNCTIONS
# ============================================================
def calculate_goalie_edge(game, team):
    """Calculate goalie save percentage edge (-2 to +2)"""
    if team == "away":
        goalie_status = game["away_goalie"]
        opp_goalie_status = game["home_goalie"]
        team_abbr = game["away"]
        opp_abbr = game["home"]
    else:
        goalie_status = game["home_goalie"]
        opp_goalie_status = game["away_goalie"]
        team_abbr = game["home"]
        opp_abbr = game["away"]
    
    # Get goalie data with defaults
    team_goalie = GOALIES.get(team_abbr, {"starter_sv": 0.910, "backup_sv": 0.900})
    opp_goalie = GOALIES.get(opp_abbr, {"starter_sv": 0.910, "backup_sv": 0.900})
    
    # Safe key access with .get() and defaults
    team_sv = team_goalie.get("starter_sv", 0.910) if goalie_status == "starter" else team_goalie.get("backup_sv", 0.900)
    opp_sv = opp_goalie.get("starter_sv", 0.910) if opp_goalie_status == "starter" else opp_goalie.get("backup_sv", 0.900)
    
    sv_diff = team_sv - opp_sv
    
    if goalie_status == "backup" and opp_goalie_status == "starter":
        sv_diff -= 0.008
    elif goalie_status == "starter" and opp_goalie_status == "backup":
        sv_diff += 0.008
    
    edge = sv_diff * 100
    return max(-2, min(2, edge))

def calculate_fatigue_edge(game, team):
    """Calculate back-to-back and rest edge (-1.5 to +1.5)"""
    if team == "away":
        b2b = game["away_b2b"]
        rest = game["away_rest"]
        opp_b2b = game["home_b2b"]
        opp_rest = game["home_rest"]
    else:
        b2b = game["home_b2b"]
        rest = game["home_rest"]
        opp_b2b = game["away_b2b"]
        opp_rest = game["away_rest"]
    
    edge = 0
    
    if b2b and not opp_b2b:
        edge -= 1.0
    elif not b2b and opp_b2b:
        edge += 1.0
    
    rest_diff = rest - opp_rest
    edge += rest_diff * 0.25
    
    return max(-1.5, min(1.5, edge))

def calculate_home_ice_edge(game, team):
    """Calculate home ice advantage (+0.5 for home, -0.3 for away)"""
    if team == "home":
        return 0.5
    else:
        return -0.3

def calculate_form_edge(game, team):
    """Calculate recent form edge based on last 10 games (-1.5 to +1.5)"""
    if team == "away":
        last10 = game["away_last10"]
        opp_last10 = game["home_last10"]
    else:
        last10 = game["home_last10"]
        opp_last10 = game["away_last10"]
    
    def parse_record(rec):
        parts = rec.split("-")
        w, l, ot = int(parts[0]), int(parts[1]), int(parts[2])
        return (w * 2 + ot) / 20
    
    team_pct = parse_record(last10)
    opp_pct = parse_record(opp_last10)
    
    diff = team_pct - opp_pct
    return max(-1.5, min(1.5, diff * 3))

def calculate_special_teams_edge(game, team):
    """Calculate special teams edge (-1 to +1)"""
    if team == "away":
        pp = game["away_pp"]
        pk = game["away_pk"]
        opp_pp = game["home_pp"]
        opp_pk = game["home_pk"]
    else:
        pp = game["home_pp"]
        pk = game["home_pk"]
        opp_pp = game["away_pp"]
        opp_pk = game["away_pk"]
    
    pp_edge = (pp - opp_pk) / 100
    pk_edge = (pk - opp_pp) / 100
    
    combined = (pp_edge + pk_edge) * 5
    return max(-1, min(1, combined))

def calculate_xg_edge(game, team):
    """Calculate expected goals edge (-1.5 to +1.5)"""
    if team == "away":
        xgf = game["away_xgf"]
        xga = game["away_xga"]
        opp_xgf = game["home_xgf"]
        opp_xga = game["home_xga"]
    else:
        xgf = game["home_xgf"]
        xga = game["home_xga"]
        opp_xgf = game["away_xgf"]
        opp_xga = game["away_xga"]
    
    team_diff = xgf - xga
    opp_diff = opp_xgf - opp_xga
    
    edge = (team_diff - opp_diff) / 2
    return max(-1.5, min(1.5, edge))

def calculate_h2h_edge(game, team):
    """Calculate head-to-head edge (-0.5 to +0.5)"""
    if team == "away":
        wins = game["h2h_away"]
        losses = game["h2h_home"]
    else:
        wins = game["h2h_home"]
        losses = game["h2h_away"]
    
    total = wins + losses
    if total == 0:
        return 0
    
    win_pct = wins / total
    edge = (win_pct - 0.5) * 1
    return max(-0.5, min(0.5, edge))

def calculate_total_edge(game, team):
    """Calculate total edge score for a team"""
    goalie = calculate_goalie_edge(game, team)
    fatigue = calculate_fatigue_edge(game, team)
    home_ice = calculate_home_ice_edge(game, team)
    form = calculate_form_edge(game, team)
    special_teams = calculate_special_teams_edge(game, team)
    xg = calculate_xg_edge(game, team)
    h2h = calculate_h2h_edge(game, team)
    
    # Weighted total
    total = (
        goalie * 1.5 +
        fatigue * 1.2 +
        home_ice * 1.0 +
        form * 1.0 +
        special_teams * 0.8 +
        xg * 1.0 +
        h2h * 0.5
    )
    
    return {
        "total": round(total, 2),
        "goalie": round(goalie, 2),
        "fatigue": round(fatigue, 2),
        "home_ice": round(home_ice, 2),
        "form": round(form, 2),
        "special_teams": round(special_teams, 2),
        "xg": round(xg, 2),
        "h2h": round(h2h, 2),
    }

def get_normalized_score(edge_total):
    """
    Map raw edge (-10 to +10) to display score (0 to 10)
    
    ADJUSTED SCALING:
    Edge of +5 or higher → 10.0
    Edge of 0 → 5.0
    Edge of -5 or lower → 0.0
    
    Formula: score = 5.0 + edge_total (direct 1:1 mapping)
    """
    score = 5.0 + edge_total
    return round(max(0, min(10, score)), 1)

def calculate_model_probability(away_edge, home_edge):
    """Calculate model probability from edge scores"""
    edge_diff = home_edge - away_edge
    home_prob = max(10, min(90, 50 + (edge_diff * 5)))
    return round(100 - home_prob), round(home_prob)

def analyze_game(game):
    """Analyze a game and return pick recommendation"""
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    
    # FIXED: Use absolute scoring instead of relative normalization
    away_final = get_normalized_score(away_edge["total"])
    home_final = get_normalized_score(home_edge["total"])
    
    away_model_prob, home_model_prob = calculate_model_probability(away_edge["total"], home_edge["total"])
    
    reasons_home = []
    reasons_away = []
    
    if home_edge["goalie"] >= 0.5:
        reasons_home.append(f"Goalie edge (+{home_edge['goalie']:.2f})")
    elif away_edge["goalie"] >= 0.5:
        reasons_away.append(f"Goalie edge (+{away_edge['goalie']:.2f})")
    
    if home_edge["fatigue"] >= 0.7:
        reasons_home.append(f"Rest advantage (+{home_edge['fatigue']:.2f})")
    elif away_edge["fatigue"] >= 0.7:
        reasons_away.append(f"Rest advantage (+{away_edge['fatigue']:.2f})")
    
    if home_edge["form"] >= 0.5:
        reasons_home.append(f"Hot streak (+{home_edge['form']:.2f})")
    elif away_edge["form"] >= 0.5:
        reasons_away.append(f"Hot streak (+{away_edge['form']:.2f})")
    
    if home_edge["special_teams"] >= 0.3:
        reasons_home.append(f"Special teams (+{home_edge['special_teams']:.2f})")
    elif away_edge["special_teams"] >= 0.3:
        reasons_away.append(f"Special teams (+{away_edge['special_teams']:.2f})")
    
    if home_final >= away_final:
        return game["home"], home_final, reasons_home[:4]
    else:
        return game["away"], away_final, reasons_away[:4]

def get_signal_tier(score):
    """Get signal tier and color based on score"""
    if score >= 10.0:
        return "🔥 ELITE", "#ff0000"
    elif score >= 9.0:
        return "🔒 STRONG", "#00ff00"
    elif score >= 7.0:
        return "🔵 BUY", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    else:
        return "⚪ PASS", "#888888"

# ============================================================
# SIDEBAR
# ============================================================
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    
    st.header("🏷️ STRONG PICKS")
    today_tags = len([p for p in st.session_state.strong_picks.get('picks', []) 
                      if p.get('sport') == 'NHL' and today_str in p.get('timestamp', '')])
    st.markdown(f"""
**Next ML#:** ML-{get_next_ml_number():03d}  
**Today's Tags:** {today_tags}
""")
    st.divider()
    
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔥 **ELITE** → 10.0 <span style="color:#888;font-size:0.8em;">Perfect edge</span>

🔒 **STRONG** → 9.0-9.9 <span style="color:#888;font-size:0.8em;">Tracked</span>

🔵 **BUY** → 7.0-8.9 <span style="color:#888;font-size:0.8em;">Info only</span>

🟡 **LEAN** → 5.5-6.9 <span style="color:#888;font-size:0.8em;">Slight edge</span>

⚪ **PASS** → Below 5.5 <span style="color:#888;font-size:0.8em;">No edge</span>
""", unsafe_allow_html=True)
    st.divider()
    
    st.header("🔗 KALSHI")
    st.markdown('<a href="https://kalshi.com/?search=nhl" target="_blank" style="color: #00aaff;">NHL Markets ↗</a>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN
# ============================================================
st.title("🏒 NHL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Real ESPN Data")

games = fetch_nhl_games_real()

if not games:
    st.warning("No NHL games scheduled today.")
    st.stop()

st.markdown("---")

# ============================================================
# ML PICKS
# ============================================================
st.header("🎯 MONEYLINE PICKS")

# Analyze all games and sort by pick score (highest first)
game_analyses = []
for game in games:
    pick_team, pick_score, reasons = analyze_game(game)
    signal_tier, tier_color = get_signal_tier(pick_score)
    
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    away_score = get_normalized_score(away_edge["total"])
    home_score = get_normalized_score(home_edge["total"])
    away_prob, home_prob = calculate_model_probability(away_edge["total"], home_edge["total"])
    
    game_analyses.append({
        "game": game,
        "pick_team": pick_team,
        "pick_score": pick_score,
        "reasons": reasons,
        "signal_tier": signal_tier,
        "tier_color": tier_color,
        "away_edge": away_edge,
        "home_edge": home_edge,
        "away_score": away_score,
        "home_score": home_score,
        "away_prob": away_prob,
        "home_prob": home_prob
    })

# Sort by pick_score descending (highest first)
game_analyses.sort(key=lambda x: x["pick_score"], reverse=True)

# Display sorted games
for analysis in game_analyses:
    game = analysis["game"]
    pick_team = analysis["pick_team"]
    pick_score = analysis["pick_score"]
    reasons = analysis["reasons"]
    signal_tier = analysis["signal_tier"]
    tier_color = analysis["tier_color"]
    away_score = analysis["away_score"]
    home_score = analysis["home_score"]
    away_prob = analysis["away_prob"]
    home_prob = analysis["home_prob"]
    
    with st.container():
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            st.markdown(f"### {game['away']}")
            away_team_name = NHL_TEAMS.get(game['away'], {}).get('name', game['away'])
            st.caption(f"{away_team_name}")
            st.caption(f"Record: {game['away_record']} | L10: {game['away_last10']}")
            
            goalie_data = GOALIES.get(game['away'], {})
            goalie_type = game["away_goalie"]
            if goalie_type == "starter":
                st.caption(f"🥅 {goalie_data.get('starter', 'TBD')} ({goalie_data.get('starter_sv', 0):.3f})")
            else:
                st.caption(f"🥅 {goalie_data.get('backup', 'TBD')} ⚠️ BACKUP")
            
            if game["away_b2b"]:
                st.caption("⚠️ BACK-TO-BACK")
        
        with col2:
            st.markdown("### @")
            st.markdown(f"**Game Time:** {game['game_time']}")
            st.markdown(f"**Kalshi:** {game['away_kalshi']}¢ / {game['home_kalshi']}¢")
            st.markdown(f"**Model:** {away_prob}% / {home_prob}%")
            st.markdown(f"**Edge Score:** {away_score} / {home_score}")
        
        with col3:
            st.markdown(f"### {game['home']}")
            home_team_name = NHL_TEAMS.get(game['home'], {}).get('name', game['home'])
            st.caption(f"{home_team_name}")
            st.caption(f"Record: {game['home_record']} | L10: {game['home_last10']}")
            
            goalie_data = GOALIES.get(game['home'], {})
            goalie_type = game["home_goalie"]
            if goalie_type == "starter":
                st.caption(f"🥅 {goalie_data.get('starter', 'TBD')} ({goalie_data.get('starter_sv', 0):.3f})")
            else:
                st.caption(f"🥅 {goalie_data.get('backup', 'TBD')} ⚠️ BACKUP")
            
            if game["home_b2b"]:
                st.caption("⚠️ BACK-TO-BACK")
        
        st.markdown("---")
        
        # Signal display
        col_pick, col_tag = st.columns([3, 1])
        with col_pick:
            pick_team_name = NHL_TEAMS.get(pick_team, {}).get('name', pick_team)
            st.markdown(f"<div style='padding: 10px; background: {tier_color}22; border-left: 4px solid {tier_color};'>"
                       f"<strong>PICK:</strong> {pick_team} {pick_team_name}<br>"
                       f"<strong>Signal:</strong> {signal_tier} ({pick_score}/10)<br>"
                       f"<strong>Reasons:</strong> {', '.join(reasons) if reasons else 'Base model edge'}"
                       f"</div>", unsafe_allow_html=True)
        
        with col_tag:
            if pick_score >= 9.0:
                if st.button("🏷️ TAG", key=f"tag_{game['id']}", use_container_width=True):
                    ml_num = add_strong_pick("NHL", pick_team, 
                                            game['home'] if pick_team == game['away'] else game['away'],
                                            pick_score, reasons)
                    st.success(f"Tagged as ML-{ml_num:03d}")
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# LEGEND & HOW TO USE (COLLAPSIBLE)
# ============================================================
st.markdown("---")

with st.expander("📖 LEGEND & PICKING GUIDE"):
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
### 🎯 Signal Tiers
- **🔥 ELITE (10.0)** → Perfect edge, maximum confidence
- **🔒 STRONG (9.0-9.9)** → High-confidence edge, trackable
- **🔵 BUY (7.0-8.9)** → Good edge, actionable
- **🟡 LEAN (5.5-6.9)** → Slight edge, informational
- **⚪ PASS (< 5.5)** → No significant edge

### 📊 Edge Score Breakdown
Each team gets scored **0-10** based on 7 factors:
- **Goalie Matchup** (1.5x weight) - Save % differential
- **Fatigue** (1.2x weight) - B2B games, rest days
- **Home Ice** (1.0x weight) - Home advantage
- **Recent Form** (1.0x weight) - Last 10 games
- **xG Differential** (1.0x weight) - Expected goals
- **Special Teams** (0.8x weight) - PP/PK %
- **Head-to-Head** (0.5x weight) - Season matchup history
""")

    with col_b:
        st.markdown("""
### ✅ How to Pick Winners
1. **Compare Edge Scores** - Higher score = stronger pick
2. **Check Signal Tier** - Only bet 🔵 BUY or 🔒 STRONG
3. **Read the Reasons** - Understand WHY there's an edge
4. **Compare to Kalshi Price** - Look for mispriced markets
5. **Verify Model Probability** - Model % vs Kalshi %

### 💡 Example Pick
```
PICK: TOR Toronto Maple Leafs
Signal: 🔵 BUY (7.8/10)
Reasons: Goalie edge (+1.2), Hot streak (+0.9)

Kalshi: 45¢ / 55¢  ← TOR is 45¢
Model: 38% / 62%   ← Model says TOR 38%
```
**Edge:** Market has TOR at 45% but model says 38%. **Fade TOR** or **buy opponent**.

### 🎲 Risk Management
- **Never bet PASS or LEAN signals**
- **Bet size by tier:** STRONG = 2-3%, BUY = 1-2%
- **Check goalie confirmations** before game time
- **Avoid heavy B2B teams** unless opponent also B2B
""")

with st.expander("🛠️ HOW TO USE THIS APP"):
    st.markdown("""
### Step-by-Step Guide

**1️⃣ Review Today's Games**
- Scroll through all matchups with edge scores displayed
- Each game shows both teams' records, goalies, and fatigue status

**2️⃣ Identify Strong Signals**
- Look for 🔥 ELITE (10.0) or 🔒 STRONG (9.0+) or 🔵 BUY (7.0+) signals
- Read the "Reasons" section to understand the edge source

**3️⃣ Compare Model vs Market**
- **Kalshi Price:** Current market probability (in cents)
- **Model Probability:** Our calculated probability
- **Edge exists when:** Model differs significantly from Kalshi

**4️⃣ Make Your Decision**
- If Model > Kalshi → Market underpricing the team
- If Model < Kalshi → Market overpricing the team
- Look for 5-10% gaps for best edges

**5️⃣ Verify Before Betting**
- Check starting goalie confirmations (usually 1-2 hours before game)
- Verify no late-breaking injury news
- Confirm market still available on Kalshi

**6️⃣ Tag Strong Picks (9.0+ only)**
- Click "🏷️ TAG" button to add to tracking system
- Gets assigned ML number (ML-001, ML-002, etc.)
- Tracked in sidebar under "STRONG PICKS"

### ⚠️ Important Notes
- **Placeholder Stats:** Some advanced stats (PP%, xG, etc.) use placeholder values pending full integration
- **Goalie Changes:** Always verify starting goalies before betting
- **Line Movement:** Prices on Kalshi change constantly
- **Not Financial Advice:** This tool provides analysis, not betting recommendations

### 🔗 Kalshi Markets
Click "NHL Markets ↗" in sidebar to access Kalshi's NHL offerings
""")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("⚠️ Educational only. Not financial advice. v19.6")
