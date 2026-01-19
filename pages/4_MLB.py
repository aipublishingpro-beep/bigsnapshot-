import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ============================================================
# MLB EDGE FINDER v1.0
# Pitcher Matchup + Market Lag Model
# Pregame Moneyline & Full-Game Totals
# ============================================================

st.set_page_config(page_title="MLB Edge Finder", page_icon="⚾", layout="wide")

VERSION = "1.0"

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
# MLB TEAMS
# ============================================================

MLB_TEAMS = {
    "ARI": {"name": "Arizona Diamondbacks", "league": "NL", "division": "West"},
    "ATL": {"name": "Atlanta Braves", "league": "NL", "division": "East"},
    "BAL": {"name": "Baltimore Orioles", "league": "AL", "division": "East"},
    "BOS": {"name": "Boston Red Sox", "league": "AL", "division": "East"},
    "CHC": {"name": "Chicago Cubs", "league": "NL", "division": "Central"},
    "CHW": {"name": "Chicago White Sox", "league": "AL", "division": "Central"},
    "CIN": {"name": "Cincinnati Reds", "league": "NL", "division": "Central"},
    "CLE": {"name": "Cleveland Guardians", "league": "AL", "division": "Central"},
    "COL": {"name": "Colorado Rockies", "league": "NL", "division": "West"},
    "DET": {"name": "Detroit Tigers", "league": "AL", "division": "Central"},
    "HOU": {"name": "Houston Astros", "league": "AL", "division": "West"},
    "KC": {"name": "Kansas City Royals", "league": "AL", "division": "Central"},
    "LAA": {"name": "Los Angeles Angels", "league": "AL", "division": "West"},
    "LAD": {"name": "Los Angeles Dodgers", "league": "NL", "division": "West"},
    "MIA": {"name": "Miami Marlins", "league": "NL", "division": "East"},
    "MIL": {"name": "Milwaukee Brewers", "league": "NL", "division": "Central"},
    "MIN": {"name": "Minnesota Twins", "league": "AL", "division": "Central"},
    "NYM": {"name": "New York Mets", "league": "NL", "division": "East"},
    "NYY": {"name": "New York Yankees", "league": "AL", "division": "East"},
    "OAK": {"name": "Oakland Athletics", "league": "AL", "division": "West"},
    "PHI": {"name": "Philadelphia Phillies", "league": "NL", "division": "East"},
    "PIT": {"name": "Pittsburgh Pirates", "league": "NL", "division": "Central"},
    "SD": {"name": "San Diego Padres", "league": "NL", "division": "West"},
    "SF": {"name": "San Francisco Giants", "league": "NL", "division": "West"},
    "SEA": {"name": "Seattle Mariners", "league": "AL", "division": "West"},
    "STL": {"name": "St. Louis Cardinals", "league": "NL", "division": "Central"},
    "TB": {"name": "Tampa Bay Rays", "league": "AL", "division": "East"},
    "TEX": {"name": "Texas Rangers", "league": "AL", "division": "West"},
    "TOR": {"name": "Toronto Blue Jays", "league": "AL", "division": "East"},
    "WSH": {"name": "Washington Nationals", "league": "NL", "division": "East"},
}

# ============================================================
# PARK FACTORS (Run Environment)
# ============================================================

PARK_FACTORS = {
    "COL": 1.38,  # Coors Field - extreme hitter's park
    "CIN": 1.08,
    "TEX": 1.06,
    "BOS": 1.05,  # Fenway
    "PHI": 1.04,
    "CHC": 1.03,  # Wrigley (wind dependent)
    "BAL": 1.02,
    "MIL": 1.01,
    "ATL": 1.00,
    "LAD": 0.99,
    "ARI": 0.99,
    "NYY": 0.99,
    "MIN": 0.98,
    "CHW": 0.98,
    "HOU": 0.97,
    "CLE": 0.97,
    "TOR": 0.97,
    "KC": 0.96,
    "DET": 0.96,
    "STL": 0.96,
    "WSH": 0.95,
    "PIT": 0.95,
    "LAA": 0.95,
    "NYM": 0.94,
    "SD": 0.93,
    "TB": 0.93,
    "SF": 0.92,
    "SEA": 0.91,
    "MIA": 0.90,
    "OAK": 0.90,
}

# ============================================================
# MOCK PITCHER DATA
# ============================================================

PITCHERS = {
    "Gerrit Cole": {"team": "NYY", "hand": "R", "era": 3.12, "fip": 3.05, "k9": 11.2, "bb9": 2.1, "hr9": 1.0, "last5_era": 2.85},
    "Corbin Burnes": {"team": "BAL", "hand": "R", "era": 2.92, "fip": 3.15, "k9": 10.8, "bb9": 2.0, "hr9": 0.9, "last5_era": 2.65},
    "Zack Wheeler": {"team": "PHI", "hand": "R", "era": 3.01, "fip": 2.88, "k9": 10.5, "bb9": 1.8, "hr9": 0.8, "last5_era": 2.90},
    "Spencer Strider": {"team": "ATL", "hand": "R", "era": 3.25, "fip": 3.10, "k9": 12.5, "bb9": 2.5, "hr9": 1.1, "last5_era": 3.45},
    "Logan Webb": {"team": "SF", "hand": "R", "era": 3.15, "fip": 3.35, "k9": 7.8, "bb9": 1.9, "hr9": 0.7, "last5_era": 2.88},
    "Framber Valdez": {"team": "HOU", "hand": "L", "era": 3.22, "fip": 3.45, "k9": 8.2, "bb9": 2.8, "hr9": 0.6, "last5_era": 3.10},
    "Blake Snell": {"team": "LAD", "hand": "L", "era": 3.38, "fip": 3.20, "k9": 11.8, "bb9": 4.2, "hr9": 0.9, "last5_era": 2.55},
    "Tarik Skubal": {"team": "DET", "hand": "L", "era": 2.85, "fip": 2.92, "k9": 10.2, "bb9": 1.5, "hr9": 0.8, "last5_era": 2.40},
    "Yoshinobu Yamamoto": {"team": "LAD", "hand": "R", "era": 3.05, "fip": 3.12, "k9": 9.8, "bb9": 2.0, "hr9": 1.0, "last5_era": 3.20},
    "Dylan Cease": {"team": "SD", "hand": "R", "era": 3.45, "fip": 3.55, "k9": 11.0, "bb9": 3.5, "hr9": 1.0, "last5_era": 3.85},
    "Tyler Glasnow": {"team": "LAD", "hand": "R", "era": 3.10, "fip": 2.95, "k9": 12.0, "bb9": 2.8, "hr9": 0.9, "last5_era": 2.75},
    "Chris Sale": {"team": "ATL", "hand": "L", "era": 2.95, "fip": 3.08, "k9": 10.5, "bb9": 2.0, "hr9": 1.0, "last5_era": 2.60},
    "Seth Lugo": {"team": "KC", "hand": "R", "era": 3.35, "fip": 3.50, "k9": 8.5, "bb9": 2.2, "hr9": 1.1, "last5_era": 3.65},
    "Sonny Gray": {"team": "STL", "hand": "R", "era": 3.28, "fip": 3.40, "k9": 9.2, "bb9": 2.5, "hr9": 0.9, "last5_era": 3.50},
    "Joe Ryan": {"team": "MIN", "hand": "R", "era": 3.55, "fip": 3.65, "k9": 9.0, "bb9": 1.8, "hr9": 1.3, "last5_era": 4.10},
    "Ranger Suarez": {"team": "PHI", "hand": "L", "era": 3.15, "fip": 3.30, "k9": 7.5, "bb9": 2.2, "hr9": 0.8, "last5_era": 2.95},
}

# ============================================================
# MOCK GAMES
# ============================================================

def get_mock_games():
    """Generate mock MLB games"""
    games = [
        {
            "game_id": "mlb_001",
            "away_team": "NYY",
            "home_team": "BOS",
            "away_pitcher": "Gerrit Cole",
            "home_pitcher": "None Listed",
            "away_kalshi": 58,
            "home_kalshi": 44,
            "total_line": 8.5,
            "over_kalshi": 52,
            "under_kalshi": 50,
            "game_time": "7:10 PM ET",
            "away_last10": "7-3",
            "home_last10": "5-5",
            "away_vs_rhp": ".265",
            "home_vs_rhp": ".248",
            "away_bullpen_inn": 8.2,
            "home_bullpen_inn": 12.1,
            "weather": {"wind_mph": 12, "wind_dir": "Out to CF", "temp": 72},
            "open_away": 55,
            "open_home": 47,
        },
        {
            "game_id": "mlb_002",
            "away_team": "LAD",
            "home_team": "SF",
            "away_pitcher": "Tyler Glasnow",
            "home_pitcher": "Logan Webb",
            "away_kalshi": 62,
            "home_kalshi": 40,
            "total_line": 7.0,
            "over_kalshi": 45,
            "under_kalshi": 57,
            "game_time": "9:45 PM ET",
            "away_last10": "8-2",
            "home_last10": "6-4",
            "away_vs_rhp": ".272",
            "home_vs_rhp": ".255",
            "away_bullpen_inn": 5.1,
            "home_bullpen_inn": 7.2,
            "weather": {"wind_mph": 8, "wind_dir": "In from LF", "temp": 58},
            "open_away": 60,
            "open_home": 42,
        },
        {
            "game_id": "mlb_003",
            "away_team": "ATL",
            "home_team": "PHI",
            "away_pitcher": "Chris Sale",
            "home_pitcher": "Zack Wheeler",
            "away_kalshi": 48,
            "home_kalshi": 54,
            "total_line": 7.5,
            "over_kalshi": 48,
            "under_kalshi": 54,
            "game_time": "6:40 PM ET",
            "away_last10": "6-4",
            "home_last10": "7-3",
            "away_vs_rhp": ".258",
            "home_vs_lhp": ".242",
            "away_bullpen_inn": 9.0,
            "home_bullpen_inn": 6.2,
            "weather": {"wind_mph": 5, "wind_dir": "Calm", "temp": 68},
            "open_away": 46,
            "open_home": 56,
        },
        {
            "game_id": "mlb_004",
            "away_team": "HOU",
            "home_team": "TEX",
            "away_pitcher": "Framber Valdez",
            "home_pitcher": "None Listed",
            "away_kalshi": 55,
            "home_kalshi": 47,
            "total_line": 8.0,
            "over_kalshi": 55,
            "under_kalshi": 47,
            "game_time": "8:05 PM ET",
            "away_last10": "6-4",
            "home_last10": "4-6",
            "away_vs_rhp": ".262",
            "home_vs_lhp": ".238",
            "away_bullpen_inn": 7.1,
            "home_bullpen_inn": 14.2,
            "weather": {"wind_mph": 0, "wind_dir": "Dome", "temp": 72},
            "open_away": 52,
            "open_home": 50,
        },
        {
            "game_id": "mlb_005",
            "away_team": "SD",
            "home_team": "COL",
            "away_pitcher": "Dylan Cease",
            "home_pitcher": "None Listed",
            "away_kalshi": 65,
            "home_kalshi": 37,
            "total_line": 11.5,
            "over_kalshi": 58,
            "under_kalshi": 44,
            "game_time": "8:40 PM ET",
            "away_last10": "5-5",
            "home_last10": "3-7",
            "away_vs_rhp": ".255",
            "home_vs_rhp": ".268",
            "away_bullpen_inn": 10.0,
            "home_bullpen_inn": 11.2,
            "weather": {"wind_mph": 15, "wind_dir": "Out to RF", "temp": 78},
            "open_away": 62,
            "open_home": 40,
        },
        {
            "game_id": "mlb_006",
            "away_team": "DET",
            "home_team": "MIN",
            "away_pitcher": "Tarik Skubal",
            "home_pitcher": "Joe Ryan",
            "away_kalshi": 52,
            "home_kalshi": 50,
            "total_line": 8.0,
            "over_kalshi": 50,
            "under_kalshi": 52,
            "game_time": "7:40 PM ET",
            "away_last10": "7-3",
            "home_last10": "5-5",
            "away_vs_rhp": ".248",
            "home_vs_lhp": ".235",
            "away_bullpen_inn": 4.2,
            "home_bullpen_inn": 9.1,
            "weather": {"wind_mph": 6, "wind_dir": "In", "temp": 65},
            "open_away": 48,
            "open_home": 54,
        },
    ]
    return games

# ============================================================
# EDGE CALCULATION ENGINE
# ============================================================

def calculate_pitcher_quality_score(pitcher_name):
    """Calculate pitcher quality score (0-10 scale)"""
    if pitcher_name == "None Listed" or pitcher_name not in PITCHERS:
        return 4.0  # Unknown pitcher penalty
    
    p = PITCHERS[pitcher_name]
    
    # Lower ERA/FIP = better
    era_score = max(0, 10 - (p["era"] - 2.0) * 2)
    fip_score = max(0, 10 - (p["fip"] - 2.0) * 2)
    
    # Higher K/9 = better
    k_score = min(10, p["k9"] / 1.2)
    
    # Lower BB/9 = better
    bb_score = max(0, 10 - p["bb9"] * 2)
    
    # Lower HR/9 = better
    hr_score = max(0, 10 - p["hr9"] * 5)
    
    # Weighted blend
    quality = (era_score * 0.25 + fip_score * 0.25 + k_score * 0.2 + bb_score * 0.15 + hr_score * 0.15)
    
    return round(quality, 2)

def calculate_pitcher_form_score(pitcher_name):
    """Calculate recent form score based on last 5 starts"""
    if pitcher_name == "None Listed" or pitcher_name not in PITCHERS:
        return 5.0
    
    p = PITCHERS[pitcher_name]
    season_era = p["era"]
    recent_era = p["last5_era"]
    
    # Positive if pitching better recently
    diff = season_era - recent_era
    form_score = 5.0 + (diff * 2)
    
    return round(max(0, min(10, form_score)), 2)

def calculate_bullpen_risk(innings_last_3_days):
    """Calculate bullpen fatigue risk"""
    if innings_last_3_days < 6:
        return "LOW"
    elif innings_last_3_days < 10:
        return "MED"
    else:
        return "HIGH"

def calculate_park_adjustment(home_team):
    """Get park factor adjustment"""
    return PARK_FACTORS.get(home_team, 1.0)

def calculate_weather_impact(weather):
    """Calculate weather impact on totals"""
    wind_mph = weather.get("wind_mph", 0)
    wind_dir = weather.get("wind_dir", "")
    
    if "Dome" in wind_dir:
        return {"impact": "NEUTRAL", "note": "Dome - no weather impact"}
    
    if wind_mph < 10:
        return {"impact": "NEUTRAL", "note": "Light wind - minimal impact"}
    
    if "Out" in wind_dir:
        return {"impact": "OVER", "note": f"{wind_mph} mph out - favors hitters"}
    elif "In" in wind_dir:
        return {"impact": "UNDER", "note": f"{wind_mph} mph in - suppresses runs"}
    else:
        return {"impact": "NEUTRAL", "note": f"{wind_mph} mph - mixed impact"}

def calculate_market_movement(current_price, open_price):
    """Detect market movement direction"""
    diff = current_price - open_price
    if diff >= 5:
        return {"direction": "STEAM", "diff": diff, "note": "Sharp money detected"}
    elif diff <= -5:
        return {"direction": "FADE", "diff": diff, "note": "Public side - potential fade"}
    else:
        return {"direction": "STABLE", "diff": diff, "note": "Minimal movement"}

def calculate_total_edge(game, side):
    """Calculate total edge score for a team"""
    if side == "away":
        pitcher = game["away_pitcher"]
        opp_pitcher = game["home_pitcher"]
        bullpen_inn = game["away_bullpen_inn"]
        opp_bullpen_inn = game["home_bullpen_inn"]
        last10 = game["away_last10"]
    else:
        pitcher = game["home_pitcher"]
        opp_pitcher = game["away_pitcher"]
        bullpen_inn = game["home_bullpen_inn"]
        opp_bullpen_inn = game["away_bullpen_inn"]
        last10 = game["home_last10"]
        
    # Factor 1: Pitcher Quality (2.0x weight)
    pitcher_quality = calculate_pitcher_quality_score(pitcher)
    opp_pitcher_quality = calculate_pitcher_quality_score(opp_pitcher)
    pitcher_edge = (pitcher_quality - opp_pitcher_quality) * 2.0
    
    # Factor 2: Pitcher Recent Form (1.5x weight)
    pitcher_form = calculate_pitcher_form_score(pitcher)
    opp_pitcher_form = calculate_pitcher_form_score(opp_pitcher)
    form_edge = (pitcher_form - opp_pitcher_form) * 1.5
    
    # Factor 3: Bullpen Fatigue (1.2x weight)
    bullpen_risk = calculate_bullpen_risk(bullpen_inn)
    opp_bullpen_risk = calculate_bullpen_risk(opp_bullpen_inn)
    bullpen_scores = {"LOW": 2, "MED": 0, "HIGH": -2}
    bullpen_edge = (bullpen_scores[bullpen_risk] - bullpen_scores[opp_bullpen_risk]) * 1.2
    
    # Factor 4: Offensive Form (0.8x weight)
    wins = int(last10.split("-")[0])
    form_pct = wins / 10
    offense_edge = (form_pct - 0.5) * 10 * 0.8
    
    # Factor 5: Park Factor (1.0x weight) - only for home team
    if side == "home":
        park = calculate_park_adjustment(game["home_team"])
        park_edge = (park - 1.0) * 5  # Slight home boost in hitter's parks
    else:
        park_edge = 0
    
    # Total edge
    total = pitcher_edge + form_edge + bullpen_edge + offense_edge + park_edge
    
    return {
        "total": round(total, 2),
        "pitcher_quality": round(pitcher_quality, 2),
        "pitcher_form": round(pitcher_form, 2),
        "bullpen_risk": bullpen_risk,
        "offense_form": round(offense_edge, 2),
        "park_edge": round(park_edge, 2),
    }

def determine_edge_label(edge_score, kalshi_diff):
    """Determine edge label: STRONG / LEAN / PASS"""
    if edge_score >= 8 and kalshi_diff >= 8:
        return "STRONG"
    elif edge_score >= 4 and kalshi_diff >= 5:
        return "LEAN"
    else:
        return "PASS"

def calculate_model_probability(away_edge, home_edge):
    """Convert edge scores to implied probabilities"""
    edge_diff = home_edge - away_edge
    home_prob = 50 + (edge_diff * 2)
    home_prob = max(15, min(85, home_prob))
    away_prob = 100 - home_prob
    return round(away_prob), round(home_prob)

# ============================================================
# UI COMPONENTS
# ============================================================

def render_header():
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>MLB Edge Finder</h1>
        <p style='color: #888; font-size: 0.9rem;'>Pitcher Matchup + Market Lag Model | v{VERSION}</p>
    </div>
    """, unsafe_allow_html=True)

def render_game_card(game):
    """Render a single game analysis card"""
    away = game["away_team"]
    home = game["home_team"]
    
    away_edge = calculate_total_edge(game, "away")
    home_edge = calculate_total_edge(game, "home")
    
    away_model, home_model = calculate_model_probability(away_edge["total"], home_edge["total"])
    
    # Market movement
    away_movement = calculate_market_movement(game["away_kalshi"], game["open_away"])
    home_movement = calculate_market_movement(game["home_kalshi"], game["open_home"])
    
    # Weather
    weather_impact = calculate_weather_impact(game["weather"])
    
    # Park factor
    park_factor = calculate_park_adjustment(home)
    
    # Edge labels
    away_kalshi_diff = away_model - game["away_kalshi"]
    home_kalshi_diff = home_model - game["home_kalshi"]
    
    away_label = determine_edge_label(away_edge["total"], away_kalshi_diff)
    home_label = determine_edge_label(home_edge["total"], home_kalshi_diff)
    
    # Card border color
    has_edge = away_label != "PASS" or home_label != "PASS"
    border_color = "#22c55e" if has_edge else "#333"
    
    with st.container():
        st.markdown(f"""
        <div style='border: 2px solid {border_color}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background: #0e1117;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span style='color: #888;'>{game['game_time']}</span>
                <span style='color: #666;'>MLB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Pitchers prominently displayed
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"### {away}")
            st.caption(MLB_TEAMS[away]["name"])
            st.markdown(f"**{game['away_pitcher']}**")
            if game['away_pitcher'] in PITCHERS:
                p = PITCHERS[game['away_pitcher']]
                st.caption(f"ERA: {p['era']} | FIP: {p['fip']} | K/9: {p['k9']}")
                st.caption(f"Last 5: {p['last5_era']} ERA")
            else:
                st.caption("Pitcher TBD")
            st.caption(f"Last 10: {game['away_last10']}")
            st.caption(f"Bullpen Risk: **{away_edge['bullpen_risk']}**")
        
        with col2:
            st.markdown("### VS")
            st.markdown(f"**Kalshi:** {game['away_kalshi']}c / {game['home_kalshi']}c")
            st.markdown(f"**Model:** {away_model}% / {home_model}%")
            st.caption(f"Total: {game['total_line']}")
        
        with col3:
            st.markdown(f"### {home}")
            st.caption(MLB_TEAMS[home]["name"])
            st.markdown(f"**{game['home_pitcher']}**")
            if game['home_pitcher'] in PITCHERS:
                p = PITCHERS[game['home_pitcher']]
                st.caption(f"ERA: {p['era']} | FIP: {p['fip']} | K/9: {p['k9']}")
                st.caption(f"Last 5: {p['last5_era']} ERA")
            else:
                st.caption("Pitcher TBD")
            st.caption(f"Last 10: {game['home_last10']}")
            st.caption(f"Bullpen Risk: **{home_edge['bullpen_risk']}**")
        
        st.markdown("---")
        
        # Edge Labels
        col_a, col_b = st.columns(2)
        
        with col_a:
            label_color = "#22c55e" if away_label == "STRONG" else "#fbbf24" if away_label == "LEAN" else "#666"
            st.markdown(f"**{away}:** <span style='color:{label_color}'>{away_label}</span>", unsafe_allow_html=True)
            st.caption(f"Edge Score: {away_edge['total']:+.1f}")
            if away_movement["direction"] != "STABLE":
                st.caption(f"Market: {away_movement['note']}")
        
        with col_b:
            label_color = "#22c55e" if home_label == "STRONG" else "#fbbf24" if home_label == "LEAN" else "#666"
            st.markdown(f"**{home}:** <span style='color:{label_color}'>{home_label}</span>", unsafe_allow_html=True)
            st.caption(f"Edge Score: {home_edge['total']:+.1f}")
            if home_movement["direction"] != "STABLE":
                st.caption(f"Market: {home_movement['note']}")
        
        # Context bar
        context_items = []
        if park_factor >= 1.05:
            context_items.append(f"Park: Hitter-friendly ({park_factor:.2f})")
        elif park_factor <= 0.95:
            context_items.append(f"Park: Pitcher-friendly ({park_factor:.2f})")
        
        if weather_impact["impact"] != "NEUTRAL":
            context_items.append(f"Weather: {weather_impact['note']}")
        
        if context_items:
            st.caption(" | ".join(context_items))

def render_edge_summary(games):
    """Render summary of actionable edges"""
    edges = []
    
    for game in games:
        away = game["away_team"]
        home = game["home_team"]
        
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        
        away_model, home_model = calculate_model_probability(away_edge["total"], home_edge["total"])
        
        away_diff = away_model - game["away_kalshi"]
        home_diff = home_model - game["home_kalshi"]
        
        away_label = determine_edge_label(away_edge["total"], away_diff)
        home_label = determine_edge_label(home_edge["total"], home_diff)
        
        if away_label in ["STRONG", "LEAN"]:
            edges.append({
                "matchup": f"{away} @ {home}",
                "pick": away,
                "pitcher": game["away_pitcher"],
                "label": away_label,
                "kalshi": game["away_kalshi"],
                "model": away_model,
                "edge": away_diff,
                "time": game["game_time"],
            })
        
        if home_label in ["STRONG", "LEAN"]:
            edges.append({
                "matchup": f"{away} @ {home}",
                "pick": home,
                "pitcher": game["home_pitcher"],
                "label": home_label,
                "kalshi": game["home_kalshi"],
                "model": home_model,
                "edge": home_diff,
                "time": game["game_time"],
            })
    
    return edges

# ============================================================
# MAIN APP
# ============================================================

def main():
    render_header()
    
    # Timezone
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        show_all = st.checkbox("Show all games", value=True)
        
        st.markdown("---")
        st.markdown("### Factor Weights")
        st.caption("Pitcher Quality: 2.0x")
        st.caption("Pitcher Form: 1.5x")
        st.caption("Bullpen Fatigue: 1.2x")
        st.caption("Handedness: 1.0x")
        st.caption("Park Factor: 1.0x")
        st.caption("Offensive Form: 0.8x")
        st.caption("Weather: 0.5x")
        
        st.markdown("---")
        st.markdown("[Kalshi MLB Markets](https://kalshi.com/?search=mlb)")
        
        st.markdown("---")
        st.caption(f"v{VERSION}")
        st.caption(f"{now.strftime('%I:%M %p ET')}")
    
    # Get games
    games = get_mock_games()
    
    # Edge summary
    edges = render_edge_summary(games)
    
    if edges:
        st.markdown("### Actionable Edges")
        
        for e in sorted(edges, key=lambda x: -abs(x["edge"])):
            label_color = "#22c55e" if e["label"] == "STRONG" else "#fbbf24"
            st.markdown(
                f"<span style='color:{label_color}'>{e['label']}</span> **{e['pick']}** ({e['matchup']}) — "
                f"{e['pitcher']} | Kalshi: {e['kalshi']}c | Model: {e['model']}% | +{e['edge']:.0f}c edge | {e['time']}",
                unsafe_allow_html=True
            )
        
        st.markdown("---")
    else:
        st.info("No actionable edges detected. Check back closer to game time.")
    
    # All games
    st.markdown("### Today's Games")
    
    for game in games:
        away_edge = calculate_total_edge(game, "away")
        home_edge = calculate_total_edge(game, "home")
        away_model, home_model = calculate_model_probability(away_edge["total"], home_edge["total"])
        away_diff = away_model - game["away_kalshi"]
        home_diff = home_model - game["home_kalshi"]
        away_label = determine_edge_label(away_edge["total"], away_diff)
        home_label = determine_edge_label(home_edge["total"], home_diff)
        
        has_edge = away_label != "PASS" or home_label != "PASS"
        
        if show_all or has_edge:
            render_game_card(game)
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style='background: #1a1a1a; padding: 1rem; border-radius: 8px; font-size: 0.8rem; color: #666;'>
        <strong>Disclaimer:</strong> This tool is for informational and educational purposes only. 
        Past performance does not guarantee future results. All trading involves risk of loss.
        This is not financial advice. Model outputs are estimates based on historical factors.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
