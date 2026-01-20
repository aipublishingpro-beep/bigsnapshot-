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
# NHL TEAMS
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
# GOALIE DATA
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
# MOCK GAMES DATA
# ============================================================

def get_mock_games():
    games = [
        {
            "game_id": "nhl_20260119_1",
            "away_team": "WSH", "home_team": "COL",
            "away_kalshi": 15, "home_kalshi": 87,
            "away_open": 18, "home_open": 84,
            "game_time": "9:00 PM ET", "status": "scheduled",
            "away_record": "23-18-4", "home_record": "31-14-2",
            "away_last10": "5-4-1", "home_last10": "7-2-1",
            "away_b2b": False, "home_b2b": False,
            "away_rest": 2, "home_rest": 1,
            "away_pp": 21.5, "home_pp": 26.8,
            "away_pk": 78.2, "home_pk": 82.5,
            "away_xgf": 2.85, "home_xgf": 3.42,
            "away_xga": 3.12, "home_xga": 2.65,
            "away_goalie": "starter", "home_goalie": "starter",
            "h2h_away": 1, "h2h_home": 2,
        },
        {
            "game_id": "nhl_20260119_2",
            "away_team": "PIT", "home_team": "SEA",
            "away_kalshi": 77, "home_kalshi": 23,
            "away_open": 65, "home_open": 35,
            "game_time": "10:00 PM ET", "status": "live_2nd",
            "away_record": "25-18-5", "home_record": "22-22-3",
            "away_last10": "6-3-1", "home_last10": "4-5-1",
            "away_b2b": False, "home_b2b": True,
            "away_rest": 3, "home_rest": 0,
            "away_pp": 22.8, "home_pp": 19.5,
            "away_pk": 80.1, "home_pk": 77.8,
            "away_xgf": 3.05, "home_xgf": 2.78,
            "away_xga": 2.88, "home_xga": 3.15,
            "away_goalie": "starter", "home_goalie": "backup",
            "h2h_away": 2, "h2h_home": 1,
        },
        {
            "game_id": "nhl_20260119_3",
            "away_team": "SJS", "home_team": "FLA",
            "away_kalshi": 40, "home_kalshi": 63,
            "away_open": 35, "home_open": 67,
            "game_time": "7:00 PM ET", "status": "scheduled",
            "away_record": "15-28-6", "home_record": "29-16-3",
            "away_last10": "3-6-1", "home_last10": "6-3-1",
            "away_b2b": True, "home_b2b": False,
            "away_rest": 0, "home_rest": 2,
            "away_pp": 17.2, "home_pp": 24.5,
            "away_pk": 75.8, "home_pk": 81.2,
            "away_xgf": 2.45, "home_xgf": 3.28,
            "away_xga": 3.55, "home_xga": 2.72,
            "away_goalie": "backup", "home_goalie": "starter",
            "h2h_away": 0, "h2h_home": 2,
        },
        {
            "game_id": "nhl_20260119_4",
            "away_team": "MIN", "home_team": "TOR",
            "away_kalshi": 51, "home_kalshi": 51,
            "away_open": 48, "home_open": 54,
            "game_time": "7:30 PM ET", "status": "scheduled",
            "away_record": "28-16-4", "home_record": "28-17-3",
            "away_last10": "7-2-1", "home_last10": "6-3-1",
            "away_b2b": False, "home_b2b": False,
            "away_rest": 2, "home_rest": 2,
            "away_pp": 23.5, "home_pp": 25.2,
            "away_pk": 82.8, "home_pk": 80.5,
            "away_xgf": 3.18, "home_xgf": 3.22,
            "away_xga": 2.75, "home_xga": 2.82,
            "away_goalie": "starter", "home_goalie": "starter",
            "h2h_away": 1, "h2h_home": 1,
        },
    ]
    return games

# ============================================================
# MARKET PRESSURE LOGIC
# ============================================================

def calculate_market_pressure(game, team, model_favors_team):
    MOVEMENT_THRESHOLD = 8
    if team == "away":
        current = game["away_kalshi"]
        open_price = game["away_open"]
    else:
        current = game["home_kalshi"]
        open_price = game["home_open"]
    
    movement = current - open_price
    
    if abs(movement) < MOVEMENT_THRESHOLD:
        return {"pressure": "→ Neutral", "status": "MODEL ONLY", "movement": movement}
    
    if model_favors_team:
        if movement > 0:
            return {"pressure": "↑ Sharp Support", "status": "CONFIRMED", "movement": movement}
        else:
            return {"pressure": "↓ Sharp Resistance", "status": "CAUTION", "movement": movement}
    else:
        if movement < 0:
            return {"pressure": "↑ Sharp Support", "status": "CONFIRMED", "movement": movement}
        else:
            return {"pressure": "→ Neutral", "status": "MODEL ONLY", "movement": movement}

def generate_line_movement_data(game, team):
    if team == "away":
        open_price = game["away_open"]
        current = game["away_kalshi"]
    else:
        open_price = game["home_open"]
        current = game["home_kalshi"]
    
    hours = 8
    movement = current - open_price
    data = []
    for i in range(hours + 1):
        if abs(movement) >= 8:
            progress = min(1.0, (i / hours) * 1.5) if i < hours * 0.6 else 1.0
        else:
            progress = i / hours
        price = open_price + (movement * progress)
        hour = 10 + i
        time_label = f"{hour}:00" if hour < 12 else f"{hour-12 if hour > 12 else 12}:00 PM"
        data.append({"time": time_label, "hour": i, "price": round(price, 1)})
    return pd.DataFrame(data)

# ============================================================
# EDGE CALCULATION
# ============================================================

def calculate_goalie_edge(game, team):
    if team == "away":
        team_code, opp_code = game["away_team"], game["home_team"]
        goalie_status, opp_goalie_status = game["away_goalie"], game["home_goalie"]
    else:
        team_code, opp_code = game["home_team"], game["away_team"]
        goalie_status, opp_goalie_status = game["home_goalie"], game["away_goalie"]
    
    team_goalie = GOALIES.get(team_code, {"starter_sv": 0.905, "backup_sv": 0.890})
    opp_goalie = GOALIES.get(opp_code, {"starter_sv": 0.905, "backup_sv": 0.890})
    
    team_sv = team_goalie["starter_sv"] if goalie_status == "starter" else team_goalie["backup_sv"]
    opp_sv = opp_goalie["starter_sv"] if opp_goalie_status == "starter" else opp_goalie["backup_sv"]
    
    sv_diff = team_sv - opp_sv
    if goalie_status == "backup" and opp_goalie_status == "starter":
        sv_diff -= 0.008
    elif goalie_status == "starter" and opp_goalie_status == "backup":
        sv_diff += 0.008
    
    return max(-2, min(2, sv_diff * 100))

def calculate_fatigue_edge(game, team):
    if team == "away":
        b2b, rest, opp_b2b, opp_rest = game["away_b2b"], game["away_rest"], game["home_b2b"], game["home_rest"]
    else:
        b2b, rest, opp_b2b, opp_rest = game["home_b2b"], game["home_rest"], game["away_b2b"], game["away_rest"]
    
    edge = 0
    if b2b and not opp_b2b:
        edge -= 1.0
    elif not b2b and opp_b2b:
        edge += 1.0
    edge += (rest - opp_rest) * 0.25
    return max(-1.5, min(1.5, edge))

def calculate_home_ice_edge(game, team):
    return 0.5 if team == "home" else -0.3

def calculate_form_edge(game, team):
    if team == "away":
        last10, opp_last10 = game["away_last10"], game["home_last10"]
    else:
        last10, opp_last10 = game["home_last10"], game["away_last10"]
    
    def parse_record(rec):
        parts = rec.split("-")
        w, l, ot = int(parts[0]), int(parts[1]), int(parts[2])
        return (w * 2 + ot) / 20
    
    diff = parse_record(last10) - parse_record(opp_last10)
    return max(-1.5, min(1.5, diff * 3))

def calculate_special_teams_edge(game, team):
    if team == "away":
        pp, pk, opp_pp, opp_pk = game["away_pp"], game["away_pk"], game["home_pp"], game["home_pk"]
    else:
        pp, pk, opp_pp, opp_pk = game["home_pp"], game["home_pk"], game["away_pp"], game["away_pk"]
    
    combined = ((pp - opp_pk) / 100 + (pk - opp_pp) / 100) * 5
    return max(-1, min(1, combined))

def calculate_xg_edge(game, team):
    if team == "away":
        xgf, xga, opp_xgf, opp_xga = game["away_xgf"], game["away_xga"], game["home_xgf"], game["home_xga"]
    else:
        xgf, xga, opp_xgf, opp_xga = game["home_xgf"], game["home_xga"], game["away_xgf"], game["away_xga"]
    
    edge = ((xgf - xga) - (opp_xgf - opp_xga)) / 2
    return max(-1.5, min(1.5, edge))

def calculate_h2h_edge(game, team):
    if team == "away":
        wins, losses = game["h2h_away"], game["h2h_home"]
    else:
        wins, losses = game["h2h_home"], game["h2h_away"]
    
    total = wins + losses
    if total == 0:
        return 0
    return max(-0.5, min(0.5, (wins / total - 0.5)))

def calculate_total_edge(game, team):
    goalie = calculate_goalie_edge(game, team)
    fatigue = calculate_fatigue_edge(game, team)
    home_ice = calculate_home_ice_edge(game, team)
    form = calculate_form_edge(game, team)
    special_teams = calculate_special_teams_edge(game, team)
    xg = calculate_xg_edge(game, team)
    h2h = calculate_h2h_edge(game, team)
    
    total = goalie * 1.5 + fatigue * 1.2 + home_ice * 1.0 + form * 1.0 + special_teams * 0.8 + xg * 1.0 + h2h * 0.5
    
    return {
        "total": round(total, 2), "goalie": round(goalie, 2), "fatigue": round(fatigue, 2),
        "home_ice": round(home_ice, 2), "form": round(form, 2), "special_teams": round(special_teams, 2),
        "xg": round(xg, 2), "h2h": round(h2h, 2),
    }

def calculate_model_probability(away_edge, home_edge):
    edge_diff = home_edge - away_edge
    home_prob = max(10, min(90, 50 + (edge_diff * 5)))
    return round(100 - home_prob), round(home_prob)

def detect_edge(kalshi_price, model_prob, threshold=8):
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
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>🏒 NHL Edge Finder</h1>
        <p style='color: #888;'>Kalshi NHL Moneyline Edge Detection | v{VERSION}</p>
    </div>
    """, unsafe_allow_html=True)

def render_edge_badge(edge_info):
    if edge_info["edge"]:
        if edge_info["direction"] == "BUY":
            return f"🟢 +{edge_info['diff']:.0f}¢"
        else:
            return f"🔴 +{edge_info['diff']:.0f}¢"
    return "⚪ No Edge"

def render_game_card(game, edge_threshold):
    away, home = game["away_team"], game["home_team"]
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    away_model_prob, home_model_prob = calculate_model_probability(away_edge["total"], home_edge["total"])
    away_edge_info = detect_edge(game["away_kalshi"], away_model_prob, edge_threshold)
    home_edge_info = detect_edge(game["home_kalshi"], home_model_prob, edge_threshold)
    
    away_pressure = calculate_market_pressure(game, "away", away_edge_info["diff"] > 0)
    home_pressure = calculate_market_pressure(game, "home", home_edge_info["diff"] > 0)
    
    status_badge = "🔴 LIVE" if "live" in game["status"] else f"🕐 {game['game_time']}"
    has_edge = away_edge_info["edge"] or home_edge_info["edge"]
    border_color = "#22c55e" if has_edge else "#333"
    
    st.markdown(f"<div style='border: 2px solid {border_color}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background: #1a1a1a;'><span style='color: #888;'>{status_badge}</span></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.markdown(f"### {away}")
        st.caption(f"{NHL_TEAMS[away]['name']} | {game['away_record']}")
        if game["away_b2b"]:
            st.caption("⚠️ BACK-TO-BACK")
    with col2:
        st.markdown("### @")
        st.markdown(f"**Kalshi:** {game['away_kalshi']}¢ / {game['home_kalshi']}¢")
        st.markdown(f"**Model:** {away_model_prob}% / {home_model_prob}%")
    with col3:
        st.markdown(f"### {home}")
        st.caption(f"{NHL_TEAMS[home]['name']} | {game['home_record']}")
        if game["home_b2b"]:
            st.caption("⚠️ BACK-TO-BACK")
    
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**{away}:** {render_edge_badge(away_edge_info)}")
        st.caption(f"Market Pressure: **{away_pressure['pressure']}** | {away_pressure['status']}")
    with col_b:
        st.markdown(f"**{home}:** {render_edge_badge(home_edge_info)}")
        st.caption(f"Market Pressure: **{home_pressure['pressure']}** | {home_pressure['status']}")

# ============================================================
# MAIN APP
# ============================================================

def main():
    render_header()
    
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
        st.markdown("[Kalshi NHL Markets](https://kalshi.com/?search=nhl)")
        st.caption(f"NHL Edge Finder v{VERSION}")
    
    games = get_mock_games()
    
    st.markdown("### 🏒 Today's Games")
    for game in games:
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        away_model_prob, home_model_prob = calculate_model_probability(away_edge["total"], home_edge["total"])
        away_edge_info = detect_edge(game["away_kalshi"], away_model_prob, edge_threshold)
        home_edge_info = detect_edge(game["home_kalshi"], home_model_prob, edge_threshold)
        
        has_edge = away_edge_info["edge"] or home_edge_info["edge"]
        if show_all_games or has_edge:
            render_game_card(game, edge_threshold)
    
    st.markdown("---")
    st.caption("⚠️ Disclaimer: For informational purposes only. Not financial advice.")

if __name__ == "__main__":
    main()
