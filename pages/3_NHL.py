import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# ============================================================
# NHL EDGE FINDER v1.0
# Kalshi NHL Moneyline Edge Detection
# ============================================================

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

# Version tracking
VERSION = "1.0"

# ============================================================
# MOCK DATA - Replace with real APIs later
# ============================================================

# NHL Teams
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

# Mock goalie data
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

def get_mock_games():
    """Generate mock NHL games for today"""
    games = [
        {
            "game_id": "nhl_20260119_1",
            "away_team": "WSH",
            "home_team": "COL",
            "away_kalshi": 15,
            "home_kalshi": 87,
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
# EDGE CALCULATION ENGINE
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
    
    # Get save percentages
    team_sv = team_goalie["starter_sv"] if goalie_status == "starter" else team_goalie["backup_sv"]
    opp_sv = opp_goalie["starter_sv"] if opp_goalie_status == "starter" else opp_goalie["backup_sv"]
    
    # Calculate edge based on save % differential
    sv_diff = team_sv - opp_sv
    
    # Bonus/penalty for backup vs starter
    if goalie_status == "backup" and opp_goalie_status == "starter":
        sv_diff -= 0.008  # Penalty for using backup vs starter
    elif goalie_status == "starter" and opp_goalie_status == "backup":
        sv_diff += 0.008  # Bonus for starter vs backup
    
    # Scale to -2 to +2
    edge = sv_diff * 100  # Convert to points scale
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
    
    # Back-to-back penalty
    if b2b and not opp_b2b:
        edge -= 1.0
    elif not b2b and opp_b2b:
        edge += 1.0
    
    # Rest advantage
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
    
    # Parse last 10 record (W-L-OT)
    def parse_record(rec):
        parts = rec.split("-")
        w, l, ot = int(parts[0]), int(parts[1]), int(parts[2])
        return (w * 2 + ot) / 20  # Points percentage
    
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
    
    # PP vs opponent PK
    pp_edge = (pp - opp_pk) / 100
    # PK vs opponent PP
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
    
    # Team's xG differential vs opponent's
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
    
    # Weights
    total = (
        goalie * 1.5 +      # Goalie is huge in NHL
        fatigue * 1.2 +     # B2B matters
        home_ice * 1.0 +    # Home ice solid
        form * 1.0 +        # Recent form
        special_teams * 0.8 + # Special teams
        xg * 1.0 +          # Expected goals
        h2h * 0.5           # H2H minor factor
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
    """Convert edge scores to win probabilities"""
    edge_diff = home_edge - away_edge
    
    # Sigmoid-like conversion
    # Base is 50-50, adjusted by edge differential
    home_prob = 50 + (edge_diff * 5)
    home_prob = max(10, min(90, home_prob))
    away_prob = 100 - home_prob
    
    return round(away_prob), round(home_prob)

def detect_edge(kalshi_price, model_prob, threshold=8):
    """Detect if there's a betting edge"""
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
            return f"🟢 BUY EDGE +{edge_info['diff']:.0f}¢"
        else:
            return f"🔴 SELL EDGE +{edge_info['diff']:.0f}¢"
    return "⚪ No Edge"

def render_game_card(game):
    """Render a single game analysis card"""
    away = game["away_team"]
    home = game["home_team"]
    
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    
    away_model_prob, home_model_prob = calculate_model_probability(
        away_edge["total"], home_edge["total"]
    )
    
    away_edge_info = detect_edge(game["away_kalshi"], away_model_prob)
    home_edge_info = detect_edge(game["home_kalshi"], home_model_prob)
    
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
            st.markdown(f"### {away} @ ")
            st.caption(f"{NHL_TEAMS[away]['name']}")
            st.caption(f"Record: {game['away_record']}")
            st.caption(f"Last 10: {game['away_last10']}")
            
            # Goalie info
            goalie_data = GOALIES.get(away, {})
            goalie_type = game["away_goalie"]
            if goalie_type == "starter":
                st.caption(f"🥅 {goalie_data.get('starter', 'TBD')} ({goalie_data.get('starter_sv', 0):.3f})")
            else:
                st.caption(f"🥅 {goalie_data.get('backup', 'TBD')} ({goalie_data.get('backup_sv', 0):.3f}) ⚠️ BACKUP")
            
            if game["away_b2b"]:
                st.caption("⚠️ BACK-TO-BACK")
        
        with col2:
            st.markdown("### VS")
            st.markdown(f"**Kalshi:** {game['away_kalshi']}¢ / {game['home_kalshi']}¢")
            st.markdown(f"**Model:** {away_model_prob}% / {home_model_prob}%")
        
        with col3:
            st.markdown(f"### {home}")
            st.caption(f"{NHL_TEAMS[home]['name']}")
            st.caption(f"Record: {game['home_record']}")
            st.caption(f"Last 10: {game['home_last10']}")
            
            # Goalie info
            goalie_data = GOALIES.get(home, {})
            goalie_type = game["home_goalie"]
            if goalie_type == "starter":
                st.caption(f"🥅 {goalie_data.get('starter', 'TBD')} ({goalie_data.get('starter_sv', 0):.3f})")
            else:
                st.caption(f"🥅 {goalie_data.get('backup', 'TBD')} ({goalie_data.get('backup_sv', 0):.3f}) ⚠️ BACKUP")
            
            if game["home_b2b"]:
                st.caption("⚠️ BACK-TO-BACK")
        
        st.markdown("---")
        
        # Edge signals
        col_a, col_b = st.columns(2)
        with col_a:
            badge = render_edge_badge(away_edge_info)
            st.markdown(f"**{away}:** {badge}")
            st.caption(f"Edge Score: {away_edge['total']:+.2f}")
        
        with col_b:
            badge = render_edge_badge(home_edge_info)
            st.markdown(f"**{home}:** {badge}")
            st.caption(f"Edge Score: {home_edge['total']:+.2f}")
        
        # Factor breakdown expander
        with st.expander("📊 Factor Breakdown"):
            fcol1, fcol2 = st.columns(2)
            
            with fcol1:
                st.markdown(f"**{away} Factors:**")
                st.caption(f"🥅 Goalie: {away_edge['goalie']:+.2f}")
                st.caption(f"😴 Fatigue: {away_edge['fatigue']:+.2f}")
                st.caption(f"🏠 Home Ice: {away_edge['home_ice']:+.2f}")
                st.caption(f"📈 Form: {away_edge['form']:+.2f}")
                st.caption(f"⚡ Special Teams: {away_edge['special_teams']:+.2f}")
                st.caption(f"📊 xG: {away_edge['xg']:+.2f}")
                st.caption(f"🔄 H2H: {away_edge['h2h']:+.2f}")
            
            with fcol2:
                st.markdown(f"**{home} Factors:**")
                st.caption(f"🥅 Goalie: {home_edge['goalie']:+.2f}")
                st.caption(f"😴 Fatigue: {home_edge['fatigue']:+.2f}")
                st.caption(f"🏠 Home Ice: {home_edge['home_ice']:+.2f}")
                st.caption(f"📈 Form: {home_edge['form']:+.2f}")
                st.caption(f"⚡ Special Teams: {home_edge['special_teams']:+.2f}")
                st.caption(f"📊 xG: {home_edge['xg']:+.2f}")
                st.caption(f"🔄 H2H: {home_edge['h2h']:+.2f}")

def render_edge_summary(games):
    """Render summary of all edges detected"""
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
        
        if away_edge_info["edge"]:
            edges.append({
                "game": f"{away} @ {home}",
                "team": away,
                "direction": away_edge_info["direction"],
                "kalshi": game["away_kalshi"],
                "model": away_model_prob,
                "edge": away_edge_info["diff"],
                "time": game["game_time"],
            })
        
        if home_edge_info["edge"]:
            edges.append({
                "game": f"{away} @ {home}",
                "team": home,
                "direction": home_edge_info["direction"],
                "kalshi": game["home_kalshi"],
                "model": home_model_prob,
                "edge": home_edge_info["diff"],
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
        st.markdown("### ⚙️ Settings")
        edge_threshold = st.slider("Edge Threshold (¢)", 5, 15, 8)
        show_all_games = st.checkbox("Show games without edges", value=True)
        
        st.markdown("---")
        st.markdown("### 📊 Factors Weighted")
        st.caption("🥅 Goalie Matchup: 1.5x")
        st.caption("😴 Fatigue/Rest: 1.2x")
        st.caption("🏠 Home Ice: 1.0x")
        st.caption("📈 Recent Form: 1.0x")
        st.caption("📊 Expected Goals: 1.0x")
        st.caption("⚡ Special Teams: 0.8x")
        st.caption("🔄 Head-to-Head: 0.5x")
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown("[Kalshi NHL Markets](https://kalshi.com/?search=nhl)")
        
        st.markdown("---")
        st.caption(f"NHL Edge Finder v{VERSION}")
        st.caption("Data updates every 5 min")
    
    # Main content
    games = get_mock_games()
    
    # Edge summary at top
    edges = render_edge_summary(games)
    
    if edges:
        st.markdown("### 🎯 Active Edges")
        
        edge_df = pd.DataFrame(edges)
        edge_df = edge_df.sort_values("edge", ascending=False)
        
        for _, row in edge_df.iterrows():
            emoji = "🟢" if row["direction"] == "BUY" else "🔴"
            st.markdown(
                f"{emoji} **{row['team']}** ({row['game']}) — "
                f"{row['direction']} @ {row['kalshi']}¢ | "
                f"Model: {row['model']}% | Edge: +{row['edge']:.0f}¢ | {row['time']}"
            )
        
        st.markdown("---")
    else:
        st.info("No edges detected at current threshold. Adjust threshold or wait for line movement.")
    
    # All games
    st.markdown("### 🏒 Today's Games")
    
    for game in games:
        # Check if game has edge
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
    
    # Disclaimers
    st.markdown("---")
    st.markdown("""
    <div style='background: #1a1a1a; padding: 1rem; border-radius: 8px; font-size: 0.8rem; color: #666;'>
        <strong>⚠️ Disclaimer:</strong> This tool is for informational purposes only. 
        Past performance does not guarantee future results. All trading involves risk. 
        Not financial advice. Kalshi trading subject to their terms of service.
        Model probabilities are estimates based on historical factors and may not reflect actual outcomes.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
