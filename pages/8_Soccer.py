import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Soccer Edge Finder", page_icon="⚽", layout="wide")

# ============================================================
# AUTH - Use shared auth module
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="soccer_refresh")

eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)

VERSION = "1.0"

# ============================================================
# LEAGUES
# ============================================================
LEAGUES = {
    "EPL": {"name": "Premier League", "code": "eng.1", "color": "#3d195b"},
    "LALIGA": {"name": "La Liga", "code": "esp.1", "color": "#ee8707"},
    "BUNDESLIGA": {"name": "Bundesliga", "code": "ger.1", "color": "#d20515"},
    "SERIEA": {"name": "Serie A", "code": "ita.1", "color": "#024494"},
    "LIGUE1": {"name": "Ligue 1", "code": "fra.1", "color": "#091c3e"},
    "MLS": {"name": "MLS", "code": "usa.1", "color": "#000000"},
    "UCL": {"name": "Champions League", "code": "uefa.champions", "color": "#0a1128"},
}

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=30)
def fetch_soccer_games(league_code):
    """Fetch games from ESPN API"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def parse_games(data, league_key):
    """Parse ESPN data into game objects"""
    games = []
    if not data or 'events' not in data:
        return games
    
    for event in data.get('events', []):
        try:
            comp = event.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            home = None
            away = None
            for c in competitors:
                if c.get('homeAway') == 'home':
                    home = c
                else:
                    away = c
            
            if not home or not away:
                home, away = competitors[0], competitors[1]
            
            home_team = home.get('team', {}).get('displayName', 'Unknown')
            away_team = away.get('team', {}).get('displayName', 'Unknown')
            home_score = int(home.get('score', 0) or 0)
            away_score = int(away.get('score', 0) or 0)
            
            status = event.get('status', {}).get('type', {}).get('name', 'STATUS_SCHEDULED')
            clock = event.get('status', {}).get('displayClock', '')
            period = event.get('status', {}).get('period', 0)
            
            game_date_str = event.get('date', '')
            game_time = None
            if game_date_str:
                try:
                    game_time = datetime.fromisoformat(game_date_str.replace('Z', '+00:00')).astimezone(eastern)
                except:
                    pass
            
            games.append({
                'away': away_team,
                'home': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'status': status,
                'clock': clock,
                'period': period,
                'game_time': game_time,
                'league': league_key
            })
        except:
            continue
    
    return games

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_link(league_key):
    """Return Kalshi soccer page"""
    return "https://kalshi.com/sports/soccer"

# ============================================================
# UI
# ============================================================
st.title("⚽ SOCCER EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 30s")

# Refresh buttons
col1, col2, col3 = st.columns([6, 1, 1])
with col1:
    st.write("")
with col2:
    if st.button("🔄 Refresh", use_container_width=True, key="refresh_data"):
        st.cache_data.clear()
        st.rerun()
with col3:
    if st.button("🗑️ Clear", use_container_width=True, key="clear_cache"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ============================================================
# LEAGUE SELECTOR
# ============================================================
selected_league = st.selectbox(
    "Select League",
    options=list(LEAGUES.keys()),
    format_func=lambda x: LEAGUES[x]["name"],
    key="league_selector"
)

league_info = LEAGUES[selected_league]
league_code = league_info["code"]

st.markdown(f"### {league_info['name']}")

# ============================================================
# FETCH & DISPLAY GAMES
# ============================================================
data = fetch_soccer_games(league_code)
games = parse_games(data, selected_league)

if not games:
    st.info(f"No {league_info['name']} games scheduled right now.")
else:
    live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
    scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']
    final_games = [g for g in games if g['status'] == 'STATUS_FINAL']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Live", len(live_games))
    c2.metric("Scheduled", len(scheduled_games))
    c3.metric("Final", len(final_games))
    
    st.divider()
    
    # LIVE GAMES
    if live_games:
        st.subheader("🔴 LIVE MATCHES")
        for g in live_games:
            st.markdown(f"""
            <div style="background:#1e1e2e;padding:14px;border-radius:8px;margin-bottom:8px;border-left:3px solid #22c55e">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                    <span style="color:#fff;font-weight:600">{g['away']} @ {g['home']}</span>
                    <span style="color:#22c55e">⚽ {g['clock']} • {g['period']}'</span>
                </div>
                <div style="color:#fff;font-size:1.2em;font-weight:700">{g['away_score']} - {g['home_score']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.link_button(f"Trade on Kalshi", get_kalshi_link(selected_league), use_container_width=True)
        
        st.divider()
    
    # SCHEDULED GAMES
    if scheduled_games:
        st.subheader("📅 UPCOMING MATCHES")
        for g in scheduled_games:
            time_str = g['game_time'].strftime('%I:%M %p ET') if g['game_time'] else 'TBD'
            st.markdown(f"""
            <div style="background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:6px">
                <div style="color:#fff;font-weight:600">{g['away']} @ {g['home']}</div>
                <div style="color:#888;font-size:0.9em">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.link_button(f"Trade on Kalshi", get_kalshi_link(selected_league), use_container_width=True)
        
        st.divider()
    
    # FINAL GAMES
    if final_games:
        st.subheader("✅ FINAL RESULTS")
        cols = st.columns(3)
        for i, g in enumerate(final_games):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:#1a1a2e;padding:10px;border-radius:6px;margin-bottom:6px">
                    <div style="color:#aaa;font-size:0.85em">{g['away']} @ {g['home']}</div>
                    <div style="color:#fff;font-weight:600">{g['away_score']} - {g['home_score']}</div>
                </div>
                """, unsafe_allow_html=True)

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
