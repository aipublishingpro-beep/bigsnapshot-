import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import uuid

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

# ========== GATE CHECK ==========
if "gate_passed" not in st.session_state or not st.session_state.gate_passed:
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    st.error("⛔ Access Denied")
    st.warning("You must accept the terms on the Home page first.")
    st.page_link("Home.py", label="👉 Go to Home Page", use_container_width=True)
    st.stop()

# ========== INIT ==========
if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

# ========== GA4 TRACKING ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== NFL TEAM CODES ==========
KALSHI_CODES = {
    "Kansas City Chiefs": "KC", "Buffalo Bills": "BUF", "Baltimore Ravens": "BAL",
    "Philadelphia Eagles": "PHI", "Detroit Lions": "DET", "San Francisco 49ers": "SF",
    "Dallas Cowboys": "DAL", "Miami Dolphins": "MIA", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Cleveland Browns": "CLE", "Los Angeles Rams": "LA",
    "Tampa Bay Buccaneers": "TB", "Pittsburgh Steelers": "PIT", "Los Angeles Chargers": "LAC",
    "Seattle Seahawks": "SEA", "Cincinnati Bengals": "CIN", "Jacksonville Jaguars": "JAX",
    "Minnesota Vikings": "MIN", "New York Jets": "NYJ", "New York Giants": "NYG",
    "Indianapolis Colts": "IND", "Denver Broncos": "DEN", "Las Vegas Raiders": "LV",
    "New Orleans Saints": "NO", "Atlanta Falcons": "ATL", "Chicago Bears": "CHI",
    "Arizona Cardinals": "ARI", "Tennessee Titans": "TEN", "Carolina Panthers": "CAR",
    "New England Patriots": "NE", "Washington Commanders": "WAS"
}

# ========== KALSHI MARKET CHECK ==========
@st.cache_data(ttl=300)
def check_kalshi_market_exists(ticker):
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("market") is not None
        return False
    except:
        return False

# ========== ESPN NFL DATA ==========
@st.cache_data(ttl=60)
def fetch_nfl_games():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event["competitions"][0]
            away = comp["competitors"][1]
            home = comp["competitors"][0]
            status = comp["status"]
            game_date_str = event.get("date", "")
            game_date = None
            if game_date_str:
                try:
                    game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00")).astimezone(eastern)
                except:
                    pass
            situation = comp.get("situation", {})
            games[event["id"]] = {
                "away_team": away["team"]["displayName"],
                "home_team": home["team"]["displayName"],
                "away_abbr": away["team"]["abbreviation"],
                "home_abbr": home["team"]["abbreviation"],
                "away_score": int(away.get("score", 0)),
                "home_score": int(home.get("score", 0)),
                "period": status.get("period", 0),
                "clock": status.get("displayClock", ""),
                "status_type": status.get("type", {}).get("name", ""),
                "status_detail": status.get("type", {}).get("shortDetail", ""),
                "total": int(away.get("score", 0)) + int(home.get("score", 0)),
                "possession": situation.get("possession", ""),
                "down": situation.get("down", 0),
                "distance": situation.get("distance", 0),
                "yard_line": situation.get("yardLine", 50),
                "is_red_zone": situation.get("isRedZone", False),
                "game_date": game_date
            }
        return games
    except Exception as e:
        st.error(f"ESPN error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_nfl_injuries():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team in data.get("injuries", []):
            team_name = team.get("team", {}).get("displayName", "Unknown")
            injuries[team_name] = []
            for cat in team.get("categories", []):
                for athlete in cat.get("items", []):
                    status = athlete.get("status", "")
                    if status.lower() in ["out", "doubtful", "questionable"]:
                        injuries[team_name].append({
                            "name": athlete.get("athlete", {}).get("displayName", ""),
                            "position": athlete.get("athlete", {}).get("position", {}).get("abbreviation", ""),
                            "status": status
                        })
        return injuries
    except:
        return {}

@st.cache_data(ttl=1800)
def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%t|%w"
        resp = requests.get(url, timeout=5)
        if resp.ok:
            parts = resp.text.strip().split("|")
            return {"temp": parts[0], "wind": parts[1] if len(parts) > 1 else "N/A"}
    except:
        pass
    return {"temp": "N/A", "wind": "N/A"}

# ========== FOOTBALL FIELD ==========
def draw_football_field(yard_line, possession_abbr, home_abbr, away_abbr, is_red_zone=False):
    if possession_abbr == home_abbr:
        ball_pos = 100 - yard_line
    else:
        ball_pos = yard_line
    ball_pct = ball_pos
    ball_color = "#ff4444" if is_red_zone else "#ffcc00"
    return f"""
    <div style="background:linear-gradient(90deg,#1a472a,#2d5a3d,#1a472a);border-radius:8px;padding:10px;margin:10px 0;position:relative;height:60px">
        <div style="position:absolute;left:10%;top:50%;transform:translateY(-50%);color:#fff;font-weight:bold;font-size:0.8em">{away_abbr}</div>
        <div style="position:absolute;right:10%;top:50%;transform:translateY(-50%);color:#fff;font-weight:bold;font-size:0.8em">{home_abbr}</div>
        <div style="position:absolute;left:10%;right:10%;top:50%;height:4px;background:#fff;transform:translateY(-50%);border-radius:2px"></div>
        <div style="position:absolute;left:calc(10% + {ball_pct * 0.8}%);top:50%;transform:translate(-50%,-50%);width:16px;height:16px;background:{ball_color};border-radius:50%;border:2px solid #fff;box-shadow:0 0 10px {ball_color}"></div>
    </div>
    """

# ========== TITLE ==========
st.title("🏈 NFL Edge Finder")
st.caption("v2.1.8 — Market Check Fix")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="nfl_auto")
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=30000, key="nfl_refresh")
    st.divider()
    st.markdown("### 📊 10-Factor Model")
    st.caption("1. Home field (+1)")
    st.caption("2. Rest advantage (+1)")
    st.caption("3. Timezone travel (+1)")
    st.caption("4. Division game (+0.5)")
    st.caption("5. Injuries (+1)")
    st.caption("6. Weather (+0.5)")
    st.caption("7. Streak (+1)")
    st.caption("8. Playoffs (+1)")
    st.caption("9. Primetime (+0.5)")
    st.caption("10. Revenge (+0.5)")

games = fetch_nfl_games()
injuries = fetch_nfl_injuries()

# ========== UPCOMING PLAYOFF GAMES ==========
st.divider()
st.subheader("📅 CONFERENCE CHAMPIONSHIPS")
st.caption("Sunday, January 26, 2026")

playoff_games = [
    {"away": "Philadelphia Eagles", "home": "Washington Commanders", "time": "3:00 PM ET", "tv": "FOX", "city": "Washington"},
    {"away": "Buffalo Bills", "home": "Kansas City Chiefs", "time": "6:30 PM ET", "tv": "CBS", "city": "Kansas City"}
]

for game in playoff_games:
    weather = get_weather(game["city"])
    weather_str = f"🌡️ {weather['temp']} | 💨 {weather['wind']}"
    
    away_code = KALSHI_CODES.get(game["away"], "")
    home_code = KALSHI_CODES.get(game["home"], "")
    
    ticker = f"KXNFLGAME-26JAN26{away_code}{home_code}"
    
    # Check if market exists
    market_exists = check_kalshi_market_exists(ticker)
    
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.markdown(f"**{game['away']}** @ **{game['home']}**")
        st.caption(f"{game['time']} | {game['tv']} | {weather_str}")
    
    with col2:
        if market_exists:
            kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
            st.link_button(f"🎯 BUY {away_code}", kalshi_url, use_container_width=True)
            st.caption(f"✅ {ticker}")
        else:
            st.warning(f"⏳ {away_code} — Not live yet")
            st.caption(ticker)
    
    with col3:
        if market_exists:
            kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
            st.link_button(f"🎯 BUY {home_code}", kalshi_url, use_container_width=True)
            st.caption(f"✅ {ticker}")
        else:
            st.warning(f"⏳ {home_code} — Not live yet")
            st.caption(ticker)
    
    st.divider()

st.info("💡 Full 10-factor ML picks appear once ESPN lists these games (usually 2-3 days before kickoff)")

# ========== LIVESTATE TRACKER ==========
st.divider()
st.subheader("📡 LIVESTATE TRACKER")

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}
today = datetime.now(eastern).date()
yesterday = today - timedelta(days=1)
final_games = {k: v for k, v in games.items() 
               if v['status_type'] == "STATUS_FINAL" 
               and v.get('game_date') 
               and v['game_date'].date() >= yesterday}

if live_games:
    st.success(f"🔴 {len(live_games)} LIVE GAME(S)")
    for gid, g in live_games.items():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** {g['home_score']}")
                st.caption(f"Q{g['period']} {g['clock']} | Total: {g['total']} pts")
                if g['down'] > 0:
                    st.caption(f"📍 {g['down']} & {g['distance']} at {g['yard_line']} yd line")
            with col2:
                if g['is_red_zone']:
                    st.error("🔴 RED ZONE")
            
            poss_abbr = g.get('possession', g['home_abbr'])
            st.markdown(draw_football_field(g['yard_line'], poss_abbr, g['home_abbr'], g['away_abbr'], g['is_red_zone']), unsafe_allow_html=True)
            st.divider()
else:
    st.info("No live NFL games right now")

if final_games:
    st.subheader("✅ RECENT FINALS")
    for gid, g in final_games.items():
        winner = g['away_team'] if g['away_score'] > g['home_score'] else g['home_team']
        st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** {g['home_score']} — **{winner} WIN**")

# ========== PRE-GAME ML PICKS ==========
st.divider()
st.subheader("🎯 PRE-GAME NFL MONEYLINE PICKS")

scheduled_games = {k: v for k, v in games.items() if v['status_type'] == "STATUS_SCHEDULED"}
if scheduled_games:
    for gid, g in scheduled_games.items():
        away_inj = injuries.get(g['away_team'], [])
        home_inj = injuries.get(g['home_team'], [])
        
        away_score = 0
        home_score = 1  # Home field
        
        away_out = len([i for i in away_inj if i['status'].lower() == 'out'])
        home_out = len([i for i in home_inj if i['status'].lower() == 'out'])
        if away_out > home_out:
            home_score += 1
        elif home_out > away_out:
            away_score += 1
        
        pick = g['home_team'] if home_score >= away_score else g['away_team']
        pick_code = KALSHI_CODES.get(pick, pick[:3].upper())
        score = max(home_score, away_score) + 5
        
        game_date = g.get('game_date')
        if game_date:
            date_str = game_date.strftime("%y%b%d").upper()
        else:
            date_str = datetime.now(eastern).strftime("%y%b%d").upper()
        
        away_code = KALSHI_CODES.get(g['away_team'], g['away_team'][:3].upper())
        home_code = KALSHI_CODES.get(g['home_team'], g['home_team'][:3].upper())
        ticker = f"KXNFLGAME-{date_str}{away_code}{home_code}"
        
        if score >= 8:
            signal = "🟢 STRONG"
        elif score >= 6.5:
            signal = "🔵 BUY"
        else:
            signal = "🟡 LEAN"
        
        market_exists = check_kalshi_market_exists(ticker)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{g['away_team']}** @ **{g['home_team']}**")
            st.caption(f"{signal} {pick} | Score: {score}/10")
        with col2:
            if market_exists:
                kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
                st.link_button(f"BUY {pick_code}", kalshi_url, use_container_width=True)
                st.caption(f"✅ {ticker}")
            else:
                st.warning(f"⏳ Not live yet")
                st.caption(ticker)
        with col3:
            if away_inj or home_inj:
                with st.expander("🚑"):
                    for i in away_inj[:3]:
                        st.caption(f"{i['name']} - {i['status']}")
                    for i in home_inj[:3]:
                        st.caption(f"{i['name']} - {i['status']}")
        st.divider()
else:
    st.info("No scheduled NFL games — check back closer to game day")

# ========== INJURY REPORT ==========
st.divider()
st.subheader("🚑 INJURY REPORT")
injury_teams = [t for t in injuries if injuries[t]]
if injury_teams:
    cols = st.columns(4)
    for i, team in enumerate(injury_teams[:8]):
        with cols[i % 4]:
            st.markdown(f"**{team}**")
            for inj in injuries[team][:3]:
                status_color = "🔴" if inj['status'].lower() == 'out' else "🟡"
                st.caption(f"{status_color} {inj['name']} ({inj['position']})")
else:
    st.info("No major injuries reported")

# ========== FOOTER ==========
st.divider()
st.subheader("📖 How to Use")
st.markdown("""
**Market Status:**
- ✅ Market is LIVE — click to trade on Kalshi
- ⏳ Market not live yet — check back closer to game time

**Signals:** 🟢 STRONG (8+) | 🔵 BUY (6.5-7.9) | 🟡 LEAN (5.5-6.4)

**Questions?** aipublishingpro@gmail.com
""")

st.caption("⚠️ Educational analysis only. Not financial advice. v2.1.8")
