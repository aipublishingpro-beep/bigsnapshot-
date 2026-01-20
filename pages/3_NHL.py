import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import pytz

# ============================================================
# NHL EDGE FINDER v1.1
# Kalshi NHL Moneyline Edge Detection
# BigSnapshot — NHL Market Pressure Engine v1.1 (Charts Enabled)
# ============================================================

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

# ============================================================
# AUTH CHECK
# ============================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

VERSION = "1.1"

# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# NHL TEAMS (UNCHANGED)
# ============================================================

NHL_TEAMS = {
    "ANA": {"name": "Anaheim Ducks", "division": "Pacific"},
    "ARI": {"name": "Arizona Coyotes", "division": "Central"},
    "BOS": {"name": "Boston Bruins", "division": "Atlantic"},
    "BUF": {"name": "Buffalo Sabres", "division": "Atlantic"},
    "CGY": {"name": "Calgary Flames", "division": "Pacific"},
    "CAR": {"name": "Carolina Hurricanes", "division": "Metropolitan"},
    "CHI": {"name": "Chicago Blackhawks", "division": "Central"},
    "COL": {"name": "Colorado Avalanche", "division": "Central"},
    "CBJ": {"name": "Columbus Blue Jackets", "division": "Metropolitan"},
    "DAL": {"name": "Dallas Stars", "division": "Central"},
    "DET": {"name": "Detroit Red Wings", "division": "Atlantic"},
    "EDM": {"name": "Edmonton Oilers", "division": "Pacific"},
    "FLA": {"name": "Florida Panthers", "division": "Atlantic"},
    "LAK": {"name": "Los Angeles Kings", "division": "Pacific"},
    "MIN": {"name": "Minnesota Wild", "division": "Central"},
    "MTL": {"name": "Montreal Canadiens", "division": "Atlantic"},
    "NSH": {"name": "Nashville Predators", "division": "Central"},
    "NJD": {"name": "New Jersey Devils", "division": "Metropolitan"},
    "NYI": {"name": "New York Islanders", "division": "Metropolitan"},
    "NYR": {"name": "New York Rangers", "division": "Metropolitan"},
    "OTT": {"name": "Ottawa Senators", "division": "Atlantic"},
    "PHI": {"name": "Philadelphia Flyers", "division": "Metropolitan"},
    "PIT": {"name": "Pittsburgh Penguins", "division": "Metropolitan"},
    "SJS": {"name": "San Jose Sharks", "division": "Pacific"},
    "SEA": {"name": "Seattle Kraken", "division": "Pacific"},
    "STL": {"name": "St. Louis Blues", "division": "Central"},
    "TBL": {"name": "Tampa Bay Lightning", "division": "Atlantic"},
    "TOR": {"name": "Toronto Maple Leafs", "division": "Atlantic"},
    "VAN": {"name": "Vancouver Canucks", "division": "Pacific"},
    "VGK": {"name": "Vegas Golden Knights", "division": "Pacific"},
    "WSH": {"name": "Washington Capitals", "division": "Metropolitan"},
    "WPG": {"name": "Winnipeg Jets", "division": "Central"},
}

# ============================================================
# MOCK GOALIE DATA (UNCHANGED)
# ============================================================

GOALIES = {
    "COL": {"starter": "Alexandar Georgiev", "starter_sv": 0.912, "backup": "Justus Annunen", "backup_sv": 0.895},
    "WSH": {"starter": "Charlie Lindgren", "starter_sv": 0.908, "backup": "Logan Thompson", "backup_sv": 0.901},
    "SEA": {"starter": "Philipp Grubauer", "starter_sv": 0.905, "backup": "Joey Daccord", "backup_sv": 0.918},
    "PIT": {"starter": "Tristan Jarry", "starter_sv": 0.898, "backup": "Alex Nedeljkovic", "backup_sv": 0.891},
    "FLA": {"starter": "Sergei Bobrovsky", "starter_sv": 0.915, "backup": "Anthony Stolarz", "backup_sv": 0.908},
    "SJS": {"starter": "Mackenzie Blackwood", "starter_sv": 0.902, "backup": "Vitek Vanecek", "backup_sv": 0.888},
    "TOR": {"starter": "Joseph Woll", "starter_sv": 0.921, "backup": "Anthony Stolarz", "backup_sv": 0.910},
    "MIN": {"starter": "Filip Gustavsson", "starter_sv": 0.918, "backup": "Marc-Andre Fleury", "backup_sv": 0.895},
    "VAN": {"starter": "Thatcher Demko", "starter_sv": 0.918, "backup": "Arturs Silovs", "backup_sv": 0.885},
    "NYI": {"starter": "Ilya Sorokin", "starter_sv": 0.922, "backup": "Semyon Varlamov", "backup_sv": 0.905},
    "CGY": {"starter": "Dustin Wolf", "starter_sv": 0.915, "backup": "Dan Vladar", "backup_sv": 0.898},
    "NJD": {"starter": "Jacob Markstrom", "starter_sv": 0.908, "backup": "Nico Daws", "backup_sv": 0.892},
    "VGK": {"starter": "Adin Hill", "starter_sv": 0.912, "backup": "Ilya Samsonov", "backup_sv": 0.895},
    "PHI": {"starter": "Samuel Ersson", "starter_sv": 0.905, "backup": "Ivan Fedotov", "backup_sv": 0.898},
    "ANA": {"starter": "Lukas Dostal", "starter_sv": 0.908, "backup": "John Gibson", "backup_sv": 0.888},
    "NYR": {"starter": "Igor Shesterkin", "starter_sv": 0.928, "backup": "Jonathan Quick", "backup_sv": 0.901},
    "CHI": {"starter": "Petr Mrazek", "starter_sv": 0.902, "backup": "Arvid Soderblom", "backup_sv": 0.888},
    "WPG": {"starter": "Connor Hellebuyck", "starter_sv": 0.925, "backup": "Eric Comrie", "backup_sv": 0.895},
    "BOS": {"starter": "Jeremy Swayman", "starter_sv": 0.918, "backup": "Joonas Korpisalo", "backup_sv": 0.892},
    "DAL": {"starter": "Jake Oettinger", "starter_sv": 0.915, "backup": "Casey DeSmith", "backup_sv": 0.898},
}

# ============================================================
# MOCK GAMES WITH OPEN PRICES (v1.1 - Added for Market Pressure)
# ============================================================

def get_mock_games():
    """Generate mock NHL games with open prices for line movement tracking"""
    games = [
        {
            "game_id": "nhl_20260119_1",
            "away_team": "WSH",
            "home_team": "COL",
            "away_kalshi": 15,
            "home_kalshi": 87,
            "away_open": 18,  # Open price for line movement
            "home_open": 84,
            "game_time": "9:00 PM ET",
            "status": "scheduled",
            "away_record": "23-18-4",
            "home_record": "31-14-2",
            "away_last10": "5-4-1",
            "home_last10": "7-2-1",
            "away_b2b": False,
            "home_b2b": False,
            "away_rest": 2,
            "home_rest": 1,
            "away_pp": 21.5,
            "home_pp": 26.8,
            "away_pk": 78.2,
            "home_pk": 82.5,
            "away_xgf": 2.85,
            "home_xgf": 3.42,
            "away_xga": 3.12,
            "home_xga": 2.65,
            "away_goalie": "starter",
            "home_goalie": "starter",
            "h2h_away": 1,
            "h2h_home": 2,
        },
        {
            "game_id": "nhl_20260119_2",
            "away_team": "PIT",
            "home_team": "SEA",
            "away_kalshi": 77,
            "home_kalshi": 23,
            "away_open": 65,
            "home_open": 35,
            "game_time": "10:00 PM ET",
            "status": "live_2nd",
            "away_record": "25-18-5",
            "home_record": "22-22-3",
            "away_last10": "6-3-1",
            "home_last10": "4-5-1",
            "away_b2b": False,
            "home_b2b": True,
            "away_rest": 3,
            "home_rest": 0,
            "away_pp": 22.8,
            "home_pp": 19.5,
            "away_pk": 80.1,
            "home_pk": 77.8,
            "away_xgf": 3.05,
            "home_xgf": 2.78,
            "away_xga": 2.88,
            "home_xga": 3.15,
            "away_goalie": "starter",
            "home_goalie": "backup",
            "h2h_away": 2,
            "h2h_home": 1,
        },
        {
            "game_id": "nhl_20260119_3",
            "away_team": "SJS",
            "home_team": "FLA",
            "away_kalshi": 40,
            "home_kalshi": 63,
            "away_open": 35,
            "home_open": 67,
            "game_time": "7:00 PM ET",
            "status": "scheduled",
            "away_record": "15-28-6",
            "home_record": "29-16-3",
            "away_last10": "3-6-1",
            "home_last10": "6-3-1",
            "away_b2b": True,
            "home_b2b": False,
            "away_rest": 0,
            "home_rest": 2,
            "away_pp": 17.2,
            "home_pp": 24.5,
            "away_pk": 75.8,
            "home_pk": 81.2,
            "away_xgf": 2.45,
            "home_xgf": 3.28,
            "away_xga": 3.55,
            "home_xga": 2.72,
            "away_goalie": "backup",
            "home_goalie": "starter",
            "h2h_away": 0,
            "h2h_home": 2,
        },
        {
            "game_id": "nhl_20260119_4",
            "away_team": "MIN",
            "home_team": "TOR",
            "away_kalshi": 51,
            "home_kalshi": 51,
            "away_open": 48,
            "home_open": 54,
            "game_time": "7:30 PM ET",
            "status": "scheduled",
            "away_record": "28-16-4",
            "home_record": "28-17-3",
            "away_last10": "7-2-1",
            "home_last10": "6-3-1",
            "away_b2b": False,
            "home_b2b": False,
            "away_rest": 2,
            "home_rest": 2,
            "away_pp": 23.5,
            "home_pp": 25.2,
            "away_pk": 82.8,
            "home_pk": 80.5,
            "away_xgf": 3.18,
            "home_xgf": 3.22,
            "away_xga": 2.75,
            "home_xga": 2.82,
            "away_goalie": "starter",
            "home_goalie": "starter",
            "h2h_away": 1,
            "h2h_home": 1,
        },
        {
            "game_id": "nhl_20260119_5",
            "away_team": "NYI",
            "home_team": "VAN",
            "away_kalshi": 57,
            "home_kalshi": 44,
            "away_open": 52,
            "home_open": 49,
            "game_time": "10:00 PM ET",
            "status": "scheduled",
            "away_record": "24-18-7",
            "home_record": "22-18-8",
            "away_last10": "5-3-2",
            "home_last10": "4-4-2",
            "away_b2b": False,
            "home_b2b": False,
            "away_rest": 1,
            "home_rest": 1,
            "away_pp": 20.8,
            "home_pp": 22.5,
            "away_pk": 84.2,
            "home_pk": 79.8,
            "away_xgf": 2.92,
            "home_xgf": 3.05,
            "away_xga": 2.68,
            "home_xga": 3.02,
            "away_goalie": "starter",
            "home_goalie": "backup",
            "h2h_away": 1,
            "h2h_home": 0,
        },
        {
            "game_id": "nhl_20260119_6",
            "away_team": "NJD",
            "home_team": "CGY",
            "away_kalshi": 52,
            "home_kalshi": 49,
            "away_open": 55,
            "home_open": 46,
            "game_time": "9:00 PM ET",
            "status": "scheduled",
            "away_record": "26-19-5",
            "home_record": "24-18-7",
            "away_last10": "5-4-1",
            "home_last10": "6-3-1",
            "away_b2b": False,
            "home_b2b": False,
            "away_rest": 1,
            "home_rest": 2,
            "away_pp": 24.2,
            "home_pp": 21.8,
            "away_pk": 79.5,
            "home_pk": 81.2,
            "away_xgf": 3.08,
            "home_xgf": 2.95,
            "away_xga": 2.92,
            "home_xga": 2.85,
            "away_goalie": "starter",
            "home_goalie": "starter",
            "h2h_away": 1,
            "h2h_home": 1,
        },
        {
            "game_id": "nhl_20260119_7",
            "away_team": "PHI",
            "home_team": "VGK",
            "away_kalshi": 34,
            "home_kalshi": 66,
            "away_open": 38,
            "home_open": 63,
            "game_time": "10:00 PM ET",
            "status": "scheduled",
            "away_record": "20-22-6",
            "home_record": "30-14-4",
            "away_last10": "4-5-1",
            "home_last10": "8-1-1",
            "away_b2b": True,
            "home_b2b": False,
            "away_rest": 0,
            "home_rest": 3,
            "away_pp": 18.5,
            "home_pp": 25.8,
            "away_pk": 77.2,
            "home_pk": 83.5,
            "away_xgf": 2.72,
            "home_xgf": 3.35,
            "away_xga": 3.18,
            "home_xga": 2.58,
            "away_goalie": "starter",
            "home_goalie": "starter",
            "h2h_away": 0,
            "h2h_home": 2,
        },
        {
            "game_id": "nhl_20260119_8",
            "away_team": "NYR",
            "home_team": "ANA",
            "away_kalshi": 68,
            "home_kalshi": 32,
            "away_open": 62,
            "home_open": 38,
            "game_time": "8:00 PM ET",
            "status": "scheduled",
            "away_record": "27-18-4",
            "home_record": "18-25-5",
            "away_last10": "6-3-1",
            "home_last10": "3-6-1",
            "away_b2b": False,
            "home_b2b": False,
            "away_rest": 2,
            "home_rest": 1,
            "away_pp": 26.2,
            "home_pp": 17.8,
            "away_pk": 81.8,
            "home_pk": 76.5,
            "away_xgf": 3.28,
            "home_xgf": 2.55,
            "away_xga": 2.72,
            "home_xga": 3.32,
            "away_goalie": "starter",
            "home_goalie": "starter",
            "h2h_away": 2,
            "h2h_home": 0,
        },
    ]
    return games

# ============================================================
# MARKET PRESSURE LOGIC (v1.1 - NEW)
# Confirmation / Warning layer only - does NOT affect edge scores
# ============================================================

def calculate_market_pressure(game, team, model_favors_team):
    """
    Calculate Market Pressure based on Kalshi line movement.
    This is a CONFIRMATION / WARNING layer only.
    Does NOT affect edge scores or model output.
    
    Rules:
    - Movement TOWARD model side → Sharp Support (CONFIRMED)
    - No meaningful movement → Neutral (MODEL ONLY)  
    - Movement AGAINST model side → Sharp Resistance (CAUTION)
    - Ignore moves smaller than 8 cents
    """
    MOVEMENT_THRESHOLD = 8  # Ignore moves smaller than this
    
    if team == "away":
        current = game["away_kalshi"]
        open_price = game["away_open"]
    else:
        current = game["home_kalshi"]
        open_price = game["home_open"]
    
    movement = current - open_price  # Positive = price went UP
    
    # Ignore small movements
    if abs(movement) < MOVEMENT_THRESHOLD:
        return {
            "pressure": "→ Neutral",
            "status": "MODEL ONLY",
            "movement": movement,
        }
    
    # Determine if movement confirms or contradicts model
    if model_favors_team:
        # Model likes this team
        if movement > 0:
            # Price went UP = market agrees with model
            return {
                "pressure": "↑ Sharp Support",
                "status": "CONFIRMED",
                "movement": movement,
            }
        else:
            # Price went DOWN = market disagrees with model
            return {
                "pressure": "↓ Sharp Resistance",
                "status": "CAUTION",
                "movement": movement,
            }
    else:
        # Model doesn't favor this team
        if movement < 0:
            # Price dropped on non-favored side = confirms model
            return {
                "pressure": "↑ Sharp Support",
                "status": "CONFIRMED",
                "movement": movement,
            }
        else:
            return {
                "pressure": "→ Neutral",
                "status": "MODEL ONLY",
                "movement": movement,
            }

def generate_line_movement_data(game, team):
    """
    Generate line movement timeline data for charting.
    In production: Replace with real Kalshi API historical data.
    For now: Mock data based on open → current price.
    """
    if team == "away":
        open_price = game["away_open"]
        current = game["away_kalshi"]
    else:
        open_price = game["home_open"]
        current = game["home_kalshi"]
    
    # Generate mock timeline (hourly intervals from open to now)
    # Simulates gradual line movement
    hours = 8  # 8 hours of data
    movement = current - open_price
    
    data = []
    for i in range(hours + 1):
        # Simulate non-linear movement (sharper early if sharp money)
        if abs(movement) >= 8:
            # Sharp movement pattern (early move, then stable)
            progress = min(1.0, (i / hours) * 1.5) if i < hours * 0.6 else 1.0
        else:
            # Gradual/public pattern (linear)
            progress = i / hours
        
        price = open_price + (movement * progress)
        hour = 10 + i  # Start at 10 AM
        time_label = f"{hour}:00" if hour < 12 else f"{hour-12 if hour > 12 else 12}:00 PM"
        
        data.append({
            "time": time_label,
            "hour": i,
            "price": round(price, 1),
        })
    
    return pd.DataFrame(data)

# ============================================================
# EDGE CALCULATION ENGINE (UNCHANGED from v1.0)
# ============================================================

def calculate_goalie_edge(game, team):
    """Calculate goalie matchup edge (-2 to +2)"""
    if team == "away":
        team_code = game["away_team"]
        opp_code = game["home_team"]
        goalie_status = game["away_goalie"]
        opp_goalie_status = game["home_goalie"]
    else:
        team_code = game["home_team"]
        opp_code = game["away_team"]
        goalie_status = game["home_goalie"]
        opp_goalie_status = game["away_goalie"]
    
    team_goalie = GOALIES.get(team_code, {"starter_sv": 0.905, "backup_sv": 0.890})
    opp_goalie = GOALIES.get(opp_code, {"starter_sv": 0.905, "backup_sv": 0.890})
    
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
    """Calculate total edge score for a team (UNCHANGED)"""
    goalie = calculate_goalie_edge(game, team)
    fatigue = calculate_fatigue_edge(game, team)
    home_ice = calculate_home_ice_edge(game, team)
    form = calculate_form_edge(game, team)
    special_teams = calculate_special_teams_edge(game, team)
    xg = calculate_xg_edge(game, team)
    h2h = calculate_h2h_edge(game, team)
    
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

def calculate_model_probability(away_edge, home_edge):
    """Convert edge scores to win probabilities (UNCHANGED)"""
    edge_diff = home_edge - away_edge
    home_prob = 50 + (edge_diff * 5)
    home_prob = max(10, min(90, home_prob))
    away_prob = 100 - home_prob
    return round(away_prob), round(home_prob)

def detect_edge(kalshi_price, model_prob, threshold=8):
    """Detect if there's a betting edge (UNCHANGED)"""
    diff = model_prob - kalshi_price
    if diff >= threshold:
        return {"edge": True, "direction": "BUY", "diff": diff}
    elif diff <= -threshold:
        return {"edge": True, "direction": "SELL", "diff": abs(diff)}
    return {"edge": False, "direction": None, "diff": diff}

# ============================================================
# UI COMPONENTS
# ============================================================

def render_header():
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>🏒 NHL Edge Finder</h1>
        <p style='color: #888; font-size: 0.9rem;'>Kalshi NHL Moneyline Edge Detection | v""" + VERSION + """</p>
    </div>
    """, unsafe_allow_html=True)

def render_edge_badge(edge_info):
    """Render edge indicator badge"""
    if edge_info["edge"]:
        if edge_info["direction"] == "BUY":
            return f"🟢 +{edge_info['diff']:.0f}¢"
        else:
            return f"🔴 +{edge_info['diff']:.0f}¢"
    return "⚪ No Edge"

def render_line_movement_chart(game, team, team_code):
    """Render line movement chart (click-to-expand)"""
    df = generate_line_movement_data(game, team)
    
    st.caption(f"**{team_code} Line Movement** (Open → Current)")
    st.line_chart(df.set_index("time")["price"], height=200)
    st.caption("Chart shows Kalshi price movement over time. Early smooth moves suggest sharp action; late jagged moves suggest public action.")

def render_game_card(game):
    """Render a single game analysis card with Market Pressure"""
    away = game["away_team"]
    home = game["home_team"]
    
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    
    away_model_prob, home_model_prob = calculate_model_probability(
        away_edge["total"], home_edge["total"]
    )
    
    away_edge_info = detect_edge(game["away_kalshi"], away_model_prob)
    home_edge_info = detect_edge(game["home_kalshi"], home_model_prob)
    
    # Market Pressure (v1.1)
    away_model_favors = away_edge_info["diff"] > 0
    home_model_favors = home_edge_info["diff"] > 0
    
    away_pressure = calculate_market_pressure(game, "away", away_model_favors)
    home_pressure = calculate_market_pressure(game, "home", home_model_favors)
    
    # Status indicator
    if "live" in game["status"]:
        status_badge = "🔴 LIVE"
    else:
        status_badge = f"🕐 {game['game_time']}"
    
    # Card styling based on edge
    has_edge = away_edge_info["edge"] or home_edge_info["edge"]
    border_color = "#22c55e" if has_edge else "#333"
    
    with st.container():
        st.markdown(f"""
        <div style='border: 2px solid {border_color}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background: #1a1a1a;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-size: 0.9rem; color: #888;'>{status_badge}</span>
                <span style='font-size: 0.8rem; color: #666;'>NHL</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"### {away}")
            st.caption(f"{NHL_TEAMS[away]['name']}")
            st.caption(f"Record: {game['away_record']} | L10: {game['away_last10']}")
            
            goalie_data = GOALIES.get(away, {})
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
            st.markdown(f"**Model:** {away_model_prob}% / {home_model_prob}%")
        
        with col3:
            st.markdown(f"### {home}")
            st.caption(f"{NHL_TEAMS[home]['name']}")
            st.caption(f"Record: {game['home_record']} | L10: {game['home_last10']}")
            
            goalie_data = GOALIES.get(home, {})
            goalie_type = game["home_goalie"]
            if goalie_type == "starter":
                st.caption(f"🥅 {goalie_data.get('starter', 'TBD')} ({goalie_data.get('starter_sv', 0):.3f})")
            else:
                st.caption(f"🥅 {goalie_data.get('backup', 'TBD')} ⚠️ BACKUP")
            
            if game["home_b2b"]:
                st.caption("⚠️ BACK-TO-BACK")
        
        st.markdown("---")
        
        # Edge signals + Market Pressure (v1.1) - HIGHLIGHTED WITH BUY BUTTONS
        col_a, col_b = st.columns(2)
        
        # Build Kalshi URL for this game
        kalshi_url = f"https://kalshi.com/markets/kxnhl/nhl-regular-season-{away.lower()}-{home.lower()}"
        
        with col_a:
            if away_edge_info["edge"]:
                edge_color = "#ff6600" if away_edge_info["direction"] == "BUY" else "#ff4444"
                st.markdown(f"""
                <div style="background: {edge_color}; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <span style="font-size: 1.3em; font-weight: bold; color: #000;">🎯 {away} +{away_edge_info['diff']:.0f}¢ EDGE</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <a href="{kalshi_url}" target="_blank" style="text-decoration: none;">
                    <button style="background-color:#00aa00; color:white; padding:10px 20px; border:none; border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; width:100%;">
                        BUY {away} ON KALSHI
                    </button>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"**{away}:** ⚪ No Edge")
            st.caption(f"Edge Score: {away_edge['total']:+.2f}")
            st.caption(f"Market Pressure: **{away_pressure['pressure']}**")
            if away_pressure["status"] != "MODEL ONLY":
                st.caption(f"Status: {away_pressure['status']}")
        
        with col_b:
            if home_edge_info["edge"]:
                edge_color = "#ff6600" if home_edge_info["direction"] == "BUY" else "#ff4444"
                st.markdown(f"""
                <div style="background: {edge_color}; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <span style="font-size: 1.3em; font-weight: bold; color: #000;">🎯 {home} +{home_edge_info['diff']:.0f}¢ EDGE</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <a href="{kalshi_url}" target="_blank" style="text-decoration: none;">
                    <button style="background-color:#00aa00; color:white; padding:10px 20px; border:none; border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; width:100%;">
                        BUY {home} ON KALSHI
                    </button>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"**{home}:** ⚪ No Edge")
            st.caption(f"Edge Score: {home_edge['total']:+.2f}")
            st.caption(f"Market Pressure: **{home_pressure['pressure']}**")
            if home_pressure["status"] != "MODEL ONLY":
                st.caption(f"Status: {home_pressure['status']}")
        
        # Line Movement Chart (v1.1 - click to expand)
        with st.expander("📈 View Market Movement"):
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                render_line_movement_chart(game, "away", away)
            with chart_col2:
                render_line_movement_chart(game, "home", home)

def render_edge_summary(games):
    """Render summary of all edges detected with Market Pressure"""
    edges = []
    
    for game in games:
        away = game["away_team"]
        home = game["home_team"]
        
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        
        away_model_prob, home_model_prob = calculate_model_probability(
            away_edge["total"], home_edge["total"]
        )
        
        away_edge_info = detect_edge(game["away_kalshi"], away_model_prob)
        home_edge_info = detect_edge(game["home_kalshi"], home_model_prob)
        
        # Market Pressure
        away_model_favors = away_edge_info["diff"] > 0
        home_model_favors = home_edge_info["diff"] > 0
        
        away_pressure = calculate_market_pressure(game, "away", away_model_favors)
        home_pressure = calculate_market_pressure(game, "home", home_model_favors)
        
        if away_edge_info["edge"]:
            edges.append({
                "game": f"{away} @ {home}",
                "team": away,
                "kalshi": game["away_kalshi"],
                "model": away_model_prob,
                "edge": away_edge_info["diff"],
                "pressure": away_pressure["pressure"],
                "status": away_pressure["status"],
                "time": game["game_time"],
            })
        
        if home_edge_info["edge"]:
            edges.append({
                "game": f"{away} @ {home}",
                "team": home,
                "kalshi": game["home_kalshi"],
                "model": home_model_prob,
                "edge": home_edge_info["diff"],
                "pressure": home_pressure["pressure"],
                "status": home_pressure["status"],
                "time": game["game_time"],
            })
    
    return edges

# ============================================================
# MAIN APP
# ============================================================

def main():
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.page_link("Home.py", label="🏠 Home", use_container_width=True)
        st.divider()
        
        st.markdown("### ⚙️ Settings")
        edge_threshold = st.slider("Edge Threshold (¢)", 5, 15, 8)
        show_all_games = st.checkbox("Show games without edges", value=True)
        
        st.markdown("---")
        st.markdown("### 📈 Market Pressure Guide")
        st.caption("↑ Sharp Support = CONFIRMED")
        st.caption("→ Neutral = MODEL ONLY")
        st.caption("↓ Sharp Resistance = CAUTION")
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown("[Kalshi NHL Markets](https://kalshi.com/?search=nhl)")
        
        st.markdown("---")
        st.caption(f"NHL Edge Finder v{VERSION}")
        st.caption("Data updates every 5 min")
    
    # Main content
    games = get_mock_games()
    
    # ============================================================
    # 🎯 ML PICKS SECTION (NBA-STYLE)
    # ============================================================
    st.subheader("🎯 ML PICKS")
    
    ml_picks = []
    for game in games:
        away = game["away_team"]
        home = game["home_team"]
        
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        
        away_model_prob, home_model_prob = calculate_model_probability(
            away_edge["total"], home_edge["total"]
        )
        
        away_edge_info = detect_edge(game["away_kalshi"], away_model_prob, edge_threshold)
        home_edge_info = detect_edge(game["home_kalshi"], home_model_prob, edge_threshold)
        
        # Build factors list
        def get_factors(game, team):
            factors = []
            if team == "away":
                if game["home_b2b"]: factors.append("🛏️ Opp B2B")
                if game["away_goalie"] == "starter" and game["home_goalie"] == "backup": factors.append("🥅 Goalie Edge")
                if game["away_rest"] > game["home_rest"]: factors.append(f"😴 +{game['away_rest']-game['home_rest']}d Rest")
            else:
                if game["away_b2b"]: factors.append("🛏️ Opp B2B")
                if game["home_goalie"] == "starter" and game["away_goalie"] == "backup": factors.append("🥅 Goalie Edge")
                if game["home_rest"] > game["away_rest"]: factors.append(f"😴 +{game['home_rest']-game['away_rest']}d Rest")
                factors.append("🏠 Home Ice")
            return factors
        
        # Kalshi URL
        kalshi_url = f"https://kalshi.com/?search=nhl+{away.lower()}+{home.lower()}"
        
        if away_edge_info["edge"]:
            score = min(10, 5 + away_edge_info["diff"] / 3)
            ml_picks.append({
                "pick": away,
                "opponent": home,
                "score": round(score, 1),
                "edge_cents": away_edge_info["diff"],
                "factors": get_factors(game, "away"),
                "kalshi_url": kalshi_url,
                "game_time": game["game_time"]
            })
        
        if home_edge_info["edge"]:
            score = min(10, 5 + home_edge_info["diff"] / 3)
            ml_picks.append({
                "pick": home,
                "opponent": away,
                "score": round(score, 1),
                "edge_cents": home_edge_info["diff"],
                "factors": get_factors(game, "home"),
                "kalshi_url": kalshi_url,
                "game_time": game["game_time"]
            })
    
    # Sort by score descending
    ml_picks.sort(key=lambda x: x["score"], reverse=True)
    
    if ml_picks:
        for pick in ml_picks:
            # Color based on score
            if pick["score"] >= 8.0:
                border_color = "#00ff00"
                score_color = "#00ff00"
            elif pick["score"] >= 6.5:
                border_color = "#00aaff"
                score_color = "#00aaff"
            elif pick["score"] >= 5.5:
                border_color = "#ffff00"
                score_color = "#ffff00"
            else:
                border_color = "#888888"
                score_color = "#888888"
            
            factors_str = " • ".join(pick["factors"][:4]) if pick["factors"] else ""
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #0f172a, #020617); padding: 10px 15px; margin-bottom: 6px; border-radius: 8px; border-left: 4px solid {border_color};">
                <div>
                    <span style="font-weight: bold; color: #fff;">{pick['pick']}</span>
                    <span style="color: #666;"> vs {pick['opponent']}</span>
                    <span style="color: {score_color}; font-weight: bold; margin-left: 10px;">{pick['score']}/10</span>
                    <span style="color: #888; font-size: 0.85em; margin-left: 10px;">{factors_str}</span>
                </div>
                <a href="{pick['kalshi_url']}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #16a34a; color: white; padding: 6px 14px; border: none; border-radius: 6px; font-size: 0.85em; font-weight: 600; cursor: pointer;">
                        BUY {pick['pick']}
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        # Add all picks button
        if len(ml_picks) > 1:
            st.markdown(f"""
            <div style="text-align: center; margin-top: 10px;">
                <button style="background: transparent; border: 1px solid #333; color: #888; padding: 8px 20px; border-radius: 6px; cursor: pointer;">
                    ➕ Add {len(ml_picks)} Picks
                </button>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No ML picks at current threshold. Adjust threshold or wait for better edges.")
    
    st.divider()
    
    # Edge summary at top (legacy - can remove if desired)
    edges = render_edge_summary(games)
    
    if edges:
        st.markdown("### 🎯 Active Edges")
        
        # Create DataFrame for cleaner display
        for row in sorted(edges, key=lambda x: -x["edge"]):
            status_color = "🟢" if row["status"] == "CONFIRMED" else "🟡" if row["status"] == "MODEL ONLY" else "🟠"
            st.markdown(
                f"{status_color} **{row['team']}** ({row['game']}) — "
                f"Kalshi: {row['kalshi']}¢ | Model: {row['model']}% | "
                f"Edge: +{row['edge']:.0f}¢ | {row['pressure']} | {row['time']}"
            )
        
        st.markdown("---")
    else:
        st.info("No edges detected at current threshold. Adjust threshold or wait for line movement.")
    
    # All games
    st.markdown("### 🏒 Today's Games")
    
    for game in games:
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        away_model_prob, home_model_prob = calculate_model_probability(
            away_edge["total"], home_edge["total"]
        )
        away_edge_info = detect_edge(game["away_kalshi"], away_model_prob, edge_threshold)
        home_edge_info = detect_edge(game["home_kalshi"], home_model_prob, edge_threshold)
        
        has_edge = away_edge_info["edge"] or home_edge_info["edge"]
        
        if show_all_games or has_edge:
            render_game_card(game)
    
    # How to Use Guide
    st.markdown("---")
    with st.expander("📖 How to Use This App"):
        st.markdown("""
        **Understanding Edge Signals:**
        - **🟢 +X¢** = Model sees value. Kalshi price is lower than model probability suggests.
        - **⚪ No Edge** = Model and market are aligned. No actionable opportunity.
        
        **Understanding Market Pressure:**
        - **↑ Sharp Support** = Line moved TOWARD model pick. Smart money agrees. Status: CONFIRMED
        - **→ Neutral** = Minimal line movement (<8¢). No confirmation either way. Status: MODEL ONLY
        - **↓ Sharp Resistance** = Line moved AGAINST model pick. Proceed with caution. Status: CAUTION
        
        **Reading the Line Movement Chart:**
        - Click "View Market Movement" to expand the chart
        - **Early smooth moves** (first few hours) = Sharp/smart money action
        - **Late jagged moves** (close to game time) = Public/casual money action
        - Chart is for context only — it does NOT affect edge scores
        
        **Key Factors We Analyze:**
        - Goalie matchups (starter vs backup)
        - Back-to-back fatigue and rest days
        - Home ice advantage
        - Recent team form
        - Expected goals metrics
        - Special teams performance
        - Head-to-head history
        
        **Best Practices:**
        1. Prioritize CONFIRMED edges (model + market agree)
        2. Be cautious with CAUTION status (market disagrees with model)
        3. MODEL ONLY edges are valid but unconfirmed
        4. Check goalie status — backup goalies swing NHL games significantly
        5. Back-to-back games are real fatigue factors in hockey
        
        **Timing Tips:**
        - Markets are most inefficient early (overnight, early morning)
        - Edges shrink as game time approaches
        - Goalie confirmations often come day-of — watch for late value
        
        **Important Notes:**
        - Line movement data is based on Kalshi prices
        - This tool identifies opportunities — it does not guarantee outcomes
        - Always check Kalshi market rules before trading
        """)
    
    # Disclaimers
    st.markdown("---")
    st.markdown("""
    <div style='background: #1a1a1a; padding: 1rem; border-radius: 8px; font-size: 0.8rem; color: #666;'>
        <strong>⚠️ Disclaimer:</strong> This tool is for informational purposes only. 
        Past performance does not guarantee future results. All trading involves risk. 
        Not financial advice. Kalshi trading subject to their terms of service.
        Model probabilities are estimates based on historical factors and may not reflect actual outcomes.
        Market Pressure is derived from Kalshi price movement and is for confirmation only.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
