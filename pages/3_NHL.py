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

VERSION = "18.5"  # Fixed scoring normalization bug

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
# MOCK DATA GENERATION
# ============================================================
def fetch_mock_nhl_games():
    """Generate realistic mock NHL games for testing"""
    teams = list(NHL_TEAMS.keys())
    games = []
    
    for i in range(6):
        home = teams[i * 2]
        away = teams[i * 2 + 1]
        
        # Random records
        home_w, home_l, home_ot = 25 + i, 15 - i, 5
        away_w, away_l, away_ot = 20 + i, 20 - i, 6
        
        game = {
            "id": f"mock_{i}",
            "home": home,
            "away": away,
            "home_record": f"{home_w}-{home_l}-{home_ot}",
            "away_record": f"{away_w}-{away_l}-{away_ot}",
            "home_last10": f"{7-i}-{2+i}-1",
            "away_last10": f"{6-i}-{3+i}-1",
            "home_goalie": "starter",
            "away_goalie": "starter" if i % 2 == 0 else "backup",
            "home_b2b": i % 3 == 0,
            "away_b2b": i % 4 == 0,
            "home_rest": 1 if i % 3 == 0 else 2,
            "away_rest": 1 if i % 4 == 0 else 2,
            "home_pp": 22.0 + i,
            "away_pp": 20.0 + i,
            "home_pk": 82.0 - i,
            "away_pk": 80.0 - i,
            "home_xgf": 3.1 + (i * 0.1),
            "home_xga": 2.7 - (i * 0.1),
            "away_xgf": 2.9 + (i * 0.1),
            "away_xga": 2.8 - (i * 0.1),
            "h2h_home": 3,
            "h2h_away": 2,
            "home_kalshi": 55,
            "away_kalshi": 45,
        }
        games.append(game)
    
    return games

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
    
    team_goalie = GOALIES.get(team_abbr, {})
    opp_goalie = GOALIES.get(opp_abbr, {})
    
    team_sv = team_goalie["starter_sv"] if goalie_status == "starter" else team_goalie["backup_sv"]
    opp_sv = opp_goalie["starter_sv"] if opp_goalie_status == "starter" else opp_goalie["backup_sv"]
    
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
    Map raw edge score (-10 to +10) to display score (0 to 10)
    
    FIXED SCORING - No longer forces both teams to sum to 10
    
    Edge of +8 or higher → 10.0
    Edge of 0 → 5.0
    Edge of -8 or lower → 0.0
    """
    score = 5.0 + (edge_total / 1.6)
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
    if score >= 9.0:
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
🔒 **STRONG** → 9.0+ <span style="color:#888;font-size:0.8em;">Tracked</span>

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
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Mock Data (Testing)")

games = fetch_mock_nhl_games()

if not games:
    st.warning("No NHL games scheduled today.")
    st.stop()

st.markdown("---")

# ============================================================
# ML PICKS
# ============================================================
st.header("🎯 MONEYLINE PICKS")

for game in games:
    pick_team, pick_score, reasons = analyze_game(game)
    signal_tier, tier_color = get_signal_tier(pick_score)
    
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    away_score = get_normalized_score(away_edge["total"])
    home_score = get_normalized_score(home_edge["total"])
    away_prob, home_prob = calculate_model_probability(away_edge["total"], home_edge["total"])
    
    with st.container():
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            st.markdown(f"### {game['away']}")
            st.caption(f"{NHL_TEAMS[game['away']]['name']}")
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
            st.markdown(f"**Kalshi:** {game['away_kalshi']}¢ / {game['home_kalshi']}¢")
            st.markdown(f"**Model:** {away_prob}% / {home_prob}%")
            st.markdown(f"**Edge Score:** {away_score} / {home_score}")
        
        with col3:
            st.markdown(f"### {game['home']}")
            st.caption(f"{NHL_TEAMS[game['home']]['name']}")
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
            st.markdown(f"<div style='padding: 10px; background: {tier_color}22; border-left: 4px solid {tier_color};'>"
                       f"<strong>PICK:</strong> {pick_team} {NHL_TEAMS[pick_team]['name']}<br>"
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
# FOOTER
# ============================================================
st.markdown("---")
st.caption("NHL Edge Finder • Kalshi Contract Analysis")
st.caption("⚠️ Currently using mock data for testing. Real ESPN API integration pending.")
