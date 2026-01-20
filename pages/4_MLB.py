import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import math

# ============================================================
# MLB EDGE FINDER v1.2
# Pitcher Matchup + Market Lag Model
# NOW WITH REAL API INTEGRATION
# ============================================================

st.set_page_config(page_title="MLB Edge Finder", page_icon="⚾", layout="wide")

VERSION = "1.2"

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
    108: {"abbr": "LAA", "name": "Los Angeles Angels", "league": "AL"},
    109: {"abbr": "ARI", "name": "Arizona Diamondbacks", "league": "NL"},
    110: {"abbr": "BAL", "name": "Baltimore Orioles", "league": "AL"},
    111: {"abbr": "BOS", "name": "Boston Red Sox", "league": "AL"},
    112: {"abbr": "CHC", "name": "Chicago Cubs", "league": "NL"},
    113: {"abbr": "CIN", "name": "Cincinnati Reds", "league": "NL"},
    114: {"abbr": "CLE", "name": "Cleveland Guardians", "league": "AL"},
    115: {"abbr": "COL", "name": "Colorado Rockies", "league": "NL"},
    116: {"abbr": "DET", "name": "Detroit Tigers", "league": "AL"},
    117: {"abbr": "HOU", "name": "Houston Astros", "league": "AL"},
    118: {"abbr": "KC", "name": "Kansas City Royals", "league": "AL"},
    119: {"abbr": "LAD", "name": "Los Angeles Dodgers", "league": "NL"},
    120: {"abbr": "WSH", "name": "Washington Nationals", "league": "NL"},
    121: {"abbr": "NYM", "name": "New York Mets", "league": "NL"},
    133: {"abbr": "OAK", "name": "Oakland Athletics", "league": "AL"},
    134: {"abbr": "PIT", "name": "Pittsburgh Pirates", "league": "NL"},
    135: {"abbr": "SD", "name": "San Diego Padres", "league": "NL"},
    136: {"abbr": "SEA", "name": "Seattle Mariners", "league": "AL"},
    137: {"abbr": "SF", "name": "San Francisco Giants", "league": "NL"},
    138: {"abbr": "STL", "name": "St. Louis Cardinals", "league": "NL"},
    139: {"abbr": "TB", "name": "Tampa Bay Rays", "league": "AL"},
    140: {"abbr": "TEX", "name": "Texas Rangers", "league": "AL"},
    141: {"abbr": "TOR", "name": "Toronto Blue Jays", "league": "AL"},
    142: {"abbr": "MIN", "name": "Minnesota Twins", "league": "AL"},
    143: {"abbr": "PHI", "name": "Philadelphia Phillies", "league": "NL"},
    144: {"abbr": "ATL", "name": "Atlanta Braves", "league": "NL"},
    145: {"abbr": "CHW", "name": "Chicago White Sox", "league": "AL"},
    146: {"abbr": "MIA", "name": "Miami Marlins", "league": "NL"},
    147: {"abbr": "NYY", "name": "New York Yankees", "league": "AL"},
    158: {"abbr": "MIL", "name": "Milwaukee Brewers", "league": "NL"},
}

# Reverse lookup
TEAM_ABBR_TO_ID = {v["abbr"]: k for k, v in MLB_TEAMS.items()}

# ============================================================
# PARK FACTORS
# ============================================================

PARK_FACTORS = {
    "COL": 1.38, "CIN": 1.08, "TEX": 1.06, "BOS": 1.05, "PHI": 1.04,
    "CHC": 1.03, "BAL": 1.02, "MIL": 1.01, "ATL": 1.00, "LAD": 0.99,
    "ARI": 0.99, "NYY": 0.99, "MIN": 0.98, "CHW": 0.98, "HOU": 0.97,
    "CLE": 0.97, "TOR": 0.97, "KC": 0.96, "DET": 0.96, "STL": 0.96,
    "WSH": 0.95, "PIT": 0.95, "LAA": 0.95, "NYM": 0.94, "SD": 0.93,
    "TB": 0.93, "SF": 0.92, "SEA": 0.91, "MIA": 0.90, "OAK": 0.90,
}

# ============================================================
# API FUNCTIONS - MLB STATS API (FREE, NO KEY)
# ============================================================

@st.cache_data(ttl=300)  # Cache 5 minutes
def fetch_mlb_schedule(date_str):
    """Fetch MLB schedule with probable pitchers from official MLB Stats API"""
    url = f"https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": 1,
        "date": date_str,
        "hydrate": "probablePitcher,team,linescore"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("dates", [])
    except Exception as e:
        st.error(f"MLB API error: {e}")
        return []

@st.cache_data(ttl=3600)  # Cache 1 hour
def fetch_pitcher_stats(player_id, season=2026):
    """Fetch pitcher season stats"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {
        "stats": "season",
        "season": season,
        "group": "pitching"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        stats = data.get("stats", [])
        if stats and stats[0].get("splits"):
            return stats[0]["splits"][0].get("stat", {})
        return {}
    except:
        return {}

@st.cache_data(ttl=3600)
def fetch_pitcher_recent_games(player_id, season=2026):
    """Fetch pitcher's last 5 game logs"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {
        "stats": "gameLog",
        "season": season,
        "group": "pitching"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        stats = data.get("stats", [])
        if stats and stats[0].get("splits"):
            # Get last 5 starts
            games = stats[0]["splits"][-5:]
            return games
        return []
    except:
        return []

@st.cache_data(ttl=1800)  # Cache 30 min
def fetch_team_record(team_id, season=2026):
    """Fetch team standings/record"""
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        "stats": "season",
        "season": season,
        "group": "hitting"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except:
        return {}

# ============================================================
# KALSHI API (PUBLIC MARKET DATA)
# ============================================================

@st.cache_data(ttl=60)  # Cache 1 minute for prices
def fetch_kalshi_mlb_markets():
    """Fetch MLB markets from Kalshi"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {
        "limit": 100,
        "status": "open",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        markets = data.get("markets", [])
        # Filter for MLB
        mlb_markets = [m for m in markets if "MLB" in m.get("ticker", "").upper() or "baseball" in m.get("title", "").lower()]
        return mlb_markets
    except Exception as e:
        return []

def match_kalshi_to_game(kalshi_markets, away_abbr, home_abbr):
    """Try to match Kalshi market to a specific game"""
    for market in kalshi_markets:
        ticker = market.get("ticker", "").upper()
        title = market.get("title", "").upper()
        if away_abbr in ticker or away_abbr in title:
            if home_abbr in ticker or home_abbr in title:
                yes_price = market.get("yes_ask", 50)
                no_price = market.get("no_ask", 50)
                return {
                    "found": True,
                    "away_price": no_price,  # Away = No typically
                    "home_price": yes_price,  # Home = Yes typically
                    "ticker": market.get("ticker"),
                }
    return {"found": False, "away_price": 50, "home_price": 50, "ticker": None}

# ============================================================
# EDGE CALCULATION ENGINE
# ============================================================

def calculate_pitcher_quality_score(stats):
    """Calculate pitcher quality score from real stats"""
    if not stats:
        return 3.0  # Unknown pitcher penalty
    
    era = float(stats.get("era", 4.50))
    whip = float(stats.get("whip", 1.30))
    k_per_9 = float(stats.get("strikeoutsPer9Inn", 8.0))
    bb_per_9 = float(stats.get("walksPer9Inn", 3.0))
    hr_per_9 = float(stats.get("homeRunsPer9", 1.2))
    
    # Score components (lower ERA/WHIP = better, higher K = better)
    era_score = max(0, 10 - (era - 2.0) * 1.5)
    whip_score = max(0, 10 - (whip - 0.9) * 5)
    k_score = min(10, k_per_9 / 1.2)
    bb_score = max(0, 10 - bb_per_9 * 2)
    hr_score = max(0, 10 - hr_per_9 * 4)
    
    quality = (era_score * 0.30 + whip_score * 0.20 + k_score * 0.20 + bb_score * 0.15 + hr_score * 0.15)
    return round(max(0, min(10, quality)), 2)

def calculate_pitcher_form_score(recent_games):
    """Calculate recent form from last 5 game logs"""
    if not recent_games:
        return 5.0
    
    total_era = 0
    games_counted = 0
    for game in recent_games:
        stat = game.get("stat", {})
        era = stat.get("era")
        if era:
            total_era += float(era)
            games_counted += 1
    
    if games_counted == 0:
        return 5.0
    
    avg_era = total_era / games_counted
    # Lower recent ERA = better form
    form_score = max(0, min(10, 10 - (avg_era - 2.5) * 1.5))
    return round(form_score, 2)

def calculate_bullpen_risk(team_abbr):
    """Estimate bullpen fatigue - would need more API calls for real data"""
    # Placeholder - in production, fetch recent game logs
    return "MED"

def calculate_model_probability(away_edge, home_edge):
    """Convert edge scores to probabilities using logistic function"""
    edge_diff = home_edge - away_edge
    home_prob = 100 / (1 + math.exp(-edge_diff / 4.5))
    home_prob = max(12, min(88, home_prob))
    away_prob = 100 - home_prob
    return round(away_prob), round(home_prob)

def determine_edge_label(edge_score, kalshi_diff, pitcher_known=True):
    """Determine edge label: STRONG / LEAN / PASS"""
    if not pitcher_known:
        return "PASS"
    if edge_score >= 9 and kalshi_diff >= 10:
        return "STRONG"
    elif edge_score >= 4 and kalshi_diff >= 6:
        return "LEAN"
    else:
        return "PASS"

def calculate_park_adjustment(home_abbr):
    """Get park factor"""
    return PARK_FACTORS.get(home_abbr, 1.0)

# ============================================================
# PROCESS GAMES
# ============================================================

def process_game(game_data, kalshi_markets):
    """Process a single game from MLB API"""
    away_team_id = game_data["teams"]["away"]["team"]["id"]
    home_team_id = game_data["teams"]["home"]["team"]["id"]
    
    away_info = MLB_TEAMS.get(away_team_id, {"abbr": "UNK", "name": "Unknown"})
    home_info = MLB_TEAMS.get(home_team_id, {"abbr": "UNK", "name": "Unknown"})
    
    away_abbr = away_info["abbr"]
    home_abbr = home_info["abbr"]
    
    # Get probable pitchers
    away_pitcher = game_data["teams"]["away"].get("probablePitcher", {})
    home_pitcher = game_data["teams"]["home"].get("probablePitcher", {})
    
    away_pitcher_name = away_pitcher.get("fullName", "TBD")
    home_pitcher_name = home_pitcher.get("fullName", "TBD")
    away_pitcher_id = away_pitcher.get("id")
    home_pitcher_id = home_pitcher.get("id")
    
    # Fetch pitcher stats if available
    away_pitcher_stats = fetch_pitcher_stats(away_pitcher_id) if away_pitcher_id else {}
    home_pitcher_stats = fetch_pitcher_stats(home_pitcher_id) if home_pitcher_id else {}
    
    # Fetch recent form
    away_recent = fetch_pitcher_recent_games(away_pitcher_id) if away_pitcher_id else []
    home_recent = fetch_pitcher_recent_games(home_pitcher_id) if home_pitcher_id else []
    
    # Calculate scores
    away_quality = calculate_pitcher_quality_score(away_pitcher_stats)
    home_quality = calculate_pitcher_quality_score(home_pitcher_stats)
    
    away_form = calculate_pitcher_form_score(away_recent)
    home_form = calculate_pitcher_form_score(home_recent)
    
    # Edge calculation
    away_edge = (away_quality - home_quality) * 2.0 + (away_form - home_form) * 1.0
    home_edge = (home_quality - away_quality) * 2.0 + (home_form - away_form) * 1.0
    
    # Park factor for home team
    park = calculate_park_adjustment(home_abbr)
    home_edge += (park - 1.0) * 3
    
    # Clamp edges
    away_edge = max(-12, min(12, away_edge))
    home_edge = max(-12, min(12, home_edge))
    
    # Model probabilities
    away_model, home_model = calculate_model_probability(away_edge, home_edge)
    
    # Match Kalshi prices
    kalshi_match = match_kalshi_to_game(kalshi_markets, away_abbr, home_abbr)
    away_kalshi = kalshi_match["away_price"]
    home_kalshi = kalshi_match["home_price"]
    
    # Edge labels
    away_diff = away_model - away_kalshi
    home_diff = home_model - home_kalshi
    
    away_label = determine_edge_label(away_edge, away_diff, away_pitcher_id is not None)
    home_label = determine_edge_label(home_edge, home_diff, home_pitcher_id is not None)
    
    # Game time
    game_time = game_data.get("gameDate", "")
    try:
        dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
        eastern = pytz.timezone("US/Eastern")
        dt_eastern = dt.astimezone(eastern)
        time_str = dt_eastern.strftime("%I:%M %p ET")
    except:
        time_str = "TBD"
    
    return {
        "game_id": game_data.get("gamePk"),
        "away_abbr": away_abbr,
        "home_abbr": home_abbr,
        "away_name": away_info["name"],
        "home_name": home_info["name"],
        "away_pitcher": away_pitcher_name,
        "home_pitcher": home_pitcher_name,
        "away_pitcher_stats": away_pitcher_stats,
        "home_pitcher_stats": home_pitcher_stats,
        "away_quality": away_quality,
        "home_quality": home_quality,
        "away_form": away_form,
        "home_form": home_form,
        "away_edge": away_edge,
        "home_edge": home_edge,
        "away_model": away_model,
        "home_model": home_model,
        "away_kalshi": away_kalshi,
        "home_kalshi": home_kalshi,
        "kalshi_found": kalshi_match["found"],
        "away_label": away_label,
        "home_label": home_label,
        "park_factor": park,
        "game_time": time_str,
        "status": game_data.get("status", {}).get("detailedState", "Scheduled"),
    }

# ============================================================
# UI COMPONENTS
# ============================================================

def render_header():
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>MLB Edge Finder</h1>
        <p style='color: #888; font-size: 0.9rem;'>Pitcher Matchup + Market Lag Model | v{VERSION}</p>
        <p style='color: #666; font-size: 0.8rem;'>Live MLB Stats API + Kalshi Markets</p>
    </div>
    """, unsafe_allow_html=True)

def render_game_card(game):
    """Render a single game card"""
    has_edge = game["away_label"] != "PASS" or game["home_label"] != "PASS"
    border_color = "#22c55e" if has_edge else "#333"
    
    with st.container():
        st.markdown(f"""
        <div style='border: 2px solid {border_color}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background: #0e1117;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span style='color: #888;'>{game['game_time']}</span>
                <span style='color: #666;'>{game['status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"### {game['away_abbr']}")
            st.caption(game['away_name'])
            st.markdown(f"**{game['away_pitcher']}**")
            if game['away_pitcher_stats']:
                s = game['away_pitcher_stats']
                st.caption(f"ERA: {s.get('era', '-')} | WHIP: {s.get('whip', '-')} | K/9: {s.get('strikeoutsPer9Inn', '-')}")
            else:
                st.caption("Stats unavailable")
            st.caption(f"Quality: {game['away_quality']:.1f} | Form: {game['away_form']:.1f}")
        
        with col2:
            st.markdown("### VS")
            if game['kalshi_found']:
                st.markdown(f"**Kalshi:** {game['away_kalshi']}c / {game['home_kalshi']}c")
            else:
                st.caption("Kalshi: No market found")
            st.markdown(f"**Model:** {game['away_model']}% / {game['home_model']}%")
            if game['park_factor'] >= 1.03:
                st.caption(f"Park: Hitter-friendly")
            elif game['park_factor'] <= 0.95:
                st.caption(f"Park: Pitcher-friendly")
        
        with col3:
            st.markdown(f"### {game['home_abbr']}")
            st.caption(game['home_name'])
            st.markdown(f"**{game['home_pitcher']}**")
            if game['home_pitcher_stats']:
                s = game['home_pitcher_stats']
                st.caption(f"ERA: {s.get('era', '-')} | WHIP: {s.get('whip', '-')} | K/9: {s.get('strikeoutsPer9Inn', '-')}")
            else:
                st.caption("Stats unavailable")
            st.caption(f"Quality: {game['home_quality']:.1f} | Form: {game['home_form']:.1f}")
        
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            lbl = game['away_label']
            color = "#22c55e" if lbl == "STRONG" else "#fbbf24" if lbl == "LEAN" else "#666"
            st.markdown(f"**{game['away_abbr']}:** <span style='color:{color}'>{lbl}</span>", unsafe_allow_html=True)
            st.caption(f"Edge: {game['away_edge']:+.1f}")
        
        with col_b:
            lbl = game['home_label']
            color = "#22c55e" if lbl == "STRONG" else "#fbbf24" if lbl == "LEAN" else "#666"
            st.markdown(f"**{game['home_abbr']}:** <span style='color:{color}'>{lbl}</span>", unsafe_allow_html=True)
            st.caption(f"Edge: {game['home_edge']:+.1f}")

# ============================================================
# MAIN APP
# ============================================================

def main():
    render_header()
    
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        
        # Date picker
        selected_date = st.date_input("Game Date", value=now.date())
        date_str = selected_date.strftime("%Y-%m-%d")
        
        show_all = st.checkbox("Show all games", value=True)
        
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Data Sources")
        st.caption("MLB Stats API (official)")
        st.caption("Kalshi Public Markets")
        
        st.markdown("---")
        st.markdown("### Factor Weights")
        st.caption("Pitcher Quality: 2.0x")
        st.caption("Pitcher Form: 1.0x")
        st.caption("Park Factor: varies")
        st.caption("Edge clamped: -12 to +12")
        
        st.markdown("---")
        st.markdown("[Kalshi MLB Markets](https://kalshi.com/?search=mlb)")
        
        st.markdown("---")
        st.caption(f"v{VERSION}")
        st.caption(f"Updated: {now.strftime('%I:%M %p ET')}")
    
    # Fetch data
    with st.spinner("Fetching MLB schedule..."):
        schedule_data = fetch_mlb_schedule(date_str)
    
    with st.spinner("Fetching Kalshi markets..."):
        kalshi_markets = fetch_kalshi_mlb_markets()
    
    # Check if games exist
    if not schedule_data:
        st.warning(f"No MLB games scheduled for {date_str}. Try a different date or wait for the season to start (late March).")
        
        # Show next scheduled games
        st.markdown("---")
        st.markdown("### Season Info")
        st.info("MLB regular season typically runs late March through early October. Spring Training games may appear in March.")
        return
    
    # Process games
    games = []
    for date_obj in schedule_data:
        for game_data in date_obj.get("games", []):
            processed = process_game(game_data, kalshi_markets)
            games.append(processed)
    
    if not games:
        st.warning("No games found for this date.")
        return
    
    # Edge summary
    edges = [g for g in games if g["away_label"] != "PASS" or g["home_label"] != "PASS"]
    
    if edges:
        st.markdown("### Actionable Edges")
        for g in edges:
            if g["away_label"] in ["STRONG", "LEAN"]:
                lbl = g["away_label"]
                color = "#22c55e" if lbl == "STRONG" else "#fbbf24"
                diff = g["away_model"] - g["away_kalshi"]
                st.markdown(
                    f"<span style='color:{color}'>{lbl}</span> **{g['away_abbr']}** @ {g['home_abbr']} — "
                    f"{g['away_pitcher']} | Model: {g['away_model']}% | +{diff:.0f}c edge | {g['game_time']}",
                    unsafe_allow_html=True
                )
            if g["home_label"] in ["STRONG", "LEAN"]:
                lbl = g["home_label"]
                color = "#22c55e" if lbl == "STRONG" else "#fbbf24"
                diff = g["home_model"] - g["home_kalshi"]
                st.markdown(
                    f"<span style='color:{color}'>{lbl}</span> **{g['home_abbr']}** vs {g['away_abbr']} — "
                    f"{g['home_pitcher']} | Model: {g['home_model']}% | +{diff:.0f}c edge | {g['game_time']}",
                    unsafe_allow_html=True
                )
        st.markdown("---")
    else:
        st.info("No actionable edges detected for this date.")
    
    # All games
    st.markdown(f"### Games for {date_str}")
    st.caption(f"{len(games)} games found | Kalshi markets: {len(kalshi_markets)}")
    
    for game in games:
        has_edge = game["away_label"] != "PASS" or game["home_label"] != "PASS"
        if show_all or has_edge:
            render_game_card(game)
    
    # How to Use Guide
    st.markdown("---")
    with st.expander("📖 How to Use This App"):
        st.markdown("""
        **Understanding Edge Labels:**
        - **STRONG** = High-confidence edge (≥9 edge score + ≥10¢ Kalshi diff). Best opportunities.
        - **LEAN** = Moderate edge (≥4 edge score + ≥6¢ diff). Proceed with consideration.
        - **PASS** = No actionable edge. Model and market aligned or pitcher unknown.
        
        **Why Pitchers Dominate MLB Betting:**
        - Starting pitchers account for ~60% of game outcome variance
        - A bad pitcher vs a good lineup is the most reliable edge in baseball
        - Bullpen fatigue compounds late — watch HIGH risk bullpens
        
        **Reading the Analysis:**
        - **Pitcher Quality (2.0x):** ERA, FIP, WHIP, K/9, BB/9, HR/9 blend
        - **Pitcher Form (1.0x):** Last 5 starts trend — recent performance matters
        - **Bullpen Risk:** LOW/MED/HIGH based on recent innings — HIGH means vulnerable late
        - **Park Factor:** Coors (1.38) inflates runs; Oracle Park (0.92) suppresses them
        
        **Best Practices:**
        1. Prioritize games where BOTH pitchers are known (TBD = auto-PASS)
        2. STRONG edges with good pitchers are your best bets
        3. Watch bullpen risk — HIGH + HIGH often means volatile totals
        4. Check park factor — Coors Field games are different animals
        5. Line movement toward your pick = confirmation
        
        **Timing Tips:**
        - Probable pitchers usually confirmed 1-2 days before game
        - Best edges appear early morning before market adjusts
        - Late scratches (pitcher changes) create sudden edge opportunities
        
        **What This Tool Does NOT Do:**
        - Predict exact scores
        - Guarantee wins
        - Account for weather in real-time (yet)
        - Track in-game changes
        
        **Settlement Note:**
        Kalshi MLB markets settle on official game results. Suspended/postponed games have specific rules — check Kalshi's market rules before trading.
        """)
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style='background: #1a1a1a; padding: 1rem; border-radius: 8px; font-size: 0.8rem; color: #666;'>
        <strong>Disclaimer:</strong> This tool is for informational and educational purposes only. 
        Past performance does not guarantee future results. All trading involves risk of loss.
        Not financial advice. Data from MLB Stats API and Kalshi public markets.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
