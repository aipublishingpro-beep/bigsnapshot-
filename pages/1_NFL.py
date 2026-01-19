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

# ========== HIDE STREAMLIT STUFF ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

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
st.caption("v2.2.0 — Conference Championships Preview")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="nfl_auto")
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=30000, key="nfl_refresh")
    
    st.divider()
    st.markdown("### ⚡ LiveState Legend")
    st.caption("🔴 MAX — 3-7¢ swings")
    st.caption("🟠 ELEVATED — 1-4¢ swings")
    st.caption("🟢 NORMAL — Stable pricing")
    
    st.divider()
    st.markdown("### 🎯 ML Signal Legend")
    st.caption("🟢 STRONG → 8.0+")
    st.caption("🔵 BUY → 6.5-7.9")
    st.caption("🟡 LEAN → 5.5-6.4")

games = fetch_nfl_games()
injuries = fetch_nfl_injuries()

# ========== NFC CHAMPIONSHIP ANALYSIS ==========
st.divider()

# NFC Game Card
st.markdown("""
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:20px;margin-bottom:20px;border:1px solid #0f3460">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px">
        <span style="color:#00d4ff;font-weight:bold">NFC Championship</span>
        <span style="color:#888">Sun, Jan 26 • 3:00 PM ET</span>
    </div>
    <h2 style="color:#fff;margin:0 0 10px 0">Philadelphia Eagles @ Washington Commanders</h2>
    <div style="color:#888;font-size:0.9em">FOX | 🌡️ 38°F | 💨 8mph</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**DVOA:**")
    st.caption("PHI +22.8% vs WAS +5.2%")
with col2:
    st.markdown("**Defense Rank:**")
    st.caption("PHI #2 vs WAS #18")
with col3:
    st.markdown("**Edge:**")
    st.success("🦅 PHI favored")

st.markdown("---")
st.markdown("✈️ **PHI:** Saquon 2,000+ rush yds, #1 rushing attack, Hurts playoff proven")
st.markdown("🏠 **WAS:** Jayden Daniels ROY candidate, home playoff game, defense improving")

# NFC BUY buttons with market check
nfc_ticker = "KXNFLGAME-26JAN26PHIWAS"
nfc_market_exists = check_kalshi_market_exists(nfc_ticker)

col1, col2 = st.columns(2)
with col1:
    if nfc_market_exists:
        st.link_button("🎯 BUY PHI", f"https://kalshi.com/markets/{nfc_ticker.lower()}", use_container_width=True)
        st.caption(f"✅ {nfc_ticker}")
    else:
        st.warning("⏳ PHI — Market not live yet")
        st.caption(f"{nfc_ticker}")
with col2:
    if nfc_market_exists:
        st.link_button("🎯 BUY WAS", f"https://kalshi.com/markets/{nfc_ticker.lower()}", use_container_width=True)
        st.caption(f"✅ {nfc_ticker}")
    else:
        st.warning("⏳ WAS — Market not live yet")
        st.caption(f"{nfc_ticker}")

st.divider()

# ========== AFC CHAMPIONSHIP ANALYSIS ==========

# AFC Game Card
st.markdown("""
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:20px;margin-bottom:20px;border:1px solid #0f3460">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px">
        <span style="color:#ff6b6b;font-weight:bold">AFC Championship</span>
        <span style="color:#888">Sun, Jan 26 • 6:30 PM ET</span>
    </div>
    <h2 style="color:#fff;margin:0 0 10px 0">Buffalo Bills @ Kansas City Chiefs</h2>
    <div style="color:#888;font-size:0.9em">CBS | 🌡️ 28°F | 💨 12mph</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**DVOA:**")
    st.caption("BUF +28.4% vs KC +19.6%")
with col2:
    st.markdown("**Defense Rank:**")
    st.caption("BUF #1 vs KC #8")
with col3:
    st.markdown("**Edge:**")
    st.info("⚔️ TOSS-UP")

st.markdown("---")
st.markdown("✈️ **BUF:** Josh Allen MVP candidate, #1 defense, 0-4 vs Mahomes in playoffs")
st.markdown("🏠 **KC:** Mahomes 3x SB champ, Arrowhead home-field, 4-0 vs Allen")

# AFC BUY buttons with market check
afc_ticker = "KXNFLGAME-26JAN26BUFKC"
afc_market_exists = check_kalshi_market_exists(afc_ticker)

col1, col2 = st.columns(2)
with col1:
    if afc_market_exists:
        st.link_button("🎯 BUY BUF", f"https://kalshi.com/markets/{afc_ticker.lower()}", use_container_width=True)
        st.caption(f"✅ {afc_ticker}")
    else:
        st.warning("⏳ BUF — Market not live yet")
        st.caption(f"{afc_ticker}")
with col2:
    if afc_market_exists:
        st.link_button("🎯 BUY KC", f"https://kalshi.com/markets/{afc_ticker.lower()}", use_container_width=True)
        st.caption(f"✅ {afc_ticker}")
    else:
        st.warning("⏳ KC — Market not live yet")
        st.caption(f"{afc_ticker}")

# ========== SUPER BOWL INFO ==========
st.divider()
st.markdown("""
<div style="background:linear-gradient(135deg,#4a1942,#2d132c);border-radius:12px;padding:20px;text-align:center;border:1px solid #801336">
    <span style="font-size:2em">🏆</span>
    <h3 style="color:#ffd700;margin:10px 0">Super Bowl LIX</h3>
    <p style="color:#fff;margin:0">February 9, 2026 • Caesars Superdome, New Orleans</p>
    <p style="color:#888;font-size:0.9em;margin-top:5px">FOX • 6:30 PM ET</p>
</div>
""", unsafe_allow_html=True)

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
    st.info("🕐 No live games right now — Conference Championships are Sunday, Jan 26")
    
    # Show sample field for visual appeal
    st.caption("Sample field visualization (active during live games):")
    st.markdown(draw_football_field(35, "BUF", "KC", "BUF", False), unsafe_allow_html=True)

if final_games:
    st.subheader("✅ RECENT FINALS")
    for gid, g in final_games.items():
        winner = g['away_team'] if g['away_score'] > g['home_score'] else g['home_team']
        st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** {g['home_score']} — **{winner} WIN**")

# ========== INJURY REPORT ==========
st.divider()
st.subheader("🚑 CHAMPIONSHIP TEAM INJURIES")

champ_teams = ["Philadelphia Eagles", "Washington Commanders", "Buffalo Bills", "Kansas City Chiefs"]
cols = st.columns(4)
for i, team in enumerate(champ_teams):
    with cols[i]:
        team_injuries = injuries.get(team, [])
        st.markdown(f"**{KALSHI_CODES.get(team, team[:3])}**")
        if team_injuries:
            for inj in team_injuries[:4]:
                status_color = "🔴" if inj['status'].lower() == 'out' else "🟡"
                st.caption(f"{status_color} {inj['name']} ({inj['position']})")
        else:
            st.caption("✅ No major injuries")

# ========== KEY MATCHUP FACTORS ==========
st.divider()
st.subheader("🔑 KEY MATCHUP FACTORS")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**NFC: PHI @ WAS**")
    st.markdown("""
    - 🏃 PHI rushing attack vs WAS run defense
    - 🌟 Saquon Barkley workload management
    - 🏠 Commanders home playoff energy
    - ❄️ Cold weather favors rushing teams
    - 📊 PHI 2-0 vs WAS this season
    """)
with col2:
    st.markdown("**AFC: BUF @ KC**")
    st.markdown("""
    - 🧊 Allen's 0-4 playoff record vs Mahomes
    - 🏠 Arrowhead Stadium noise factor
    - 🛡️ BUF #1 defense vs KC offense
    - ❄️ Extreme cold expected (20s)
    - 🔄 KC's 3-peat pursuit
    """)

# ========== EDGE FINDER ANALYSIS ==========
st.divider()
st.subheader("📊 10-FACTOR EDGE ANALYSIS")

# NFC Analysis
st.markdown("**NFC CHAMPIONSHIP — PHI @ WAS**")
nfc_factors = {
    "Home Field": ("WAS +1", "🏠"),
    "Rest Days": ("EVEN", "😴"),
    "DVOA Differential": ("PHI +17.6%", "📈"),
    "Defensive Rank": ("PHI #2 vs #18", "🛡️"),
    "Injuries Impact": ("PHI healthier", "🚑"),
    "Weather": ("Neutral", "🌡️"),
    "Momentum": ("Both hot", "🔥"),
    "Playoff Experience": ("PHI edge", "🏆"),
    "H2H This Season": ("PHI 2-0", "⚔️"),
    "Public Money": ("PHI heavy", "💰")
}

cols = st.columns(5)
for i, (factor, (value, emoji)) in enumerate(nfc_factors.items()):
    with cols[i % 5]:
        st.caption(f"{emoji} {factor}")
        st.caption(value)

st.success("**NFC EDGE: PHI 7.5/10** — Strong favorite based on DVOA and defensive advantage")

st.markdown("---")

# AFC Analysis  
st.markdown("**AFC CHAMPIONSHIP — BUF @ KC**")
afc_factors = {
    "Home Field": ("KC +1", "🏠"),
    "Rest Days": ("EVEN", "😴"),
    "DVOA Differential": ("BUF +8.8%", "📈"),
    "Defensive Rank": ("BUF #1 vs #8", "🛡️"),
    "Injuries Impact": ("Slight KC edge", "🚑"),
    "Weather": ("Extreme cold", "🌡️"),
    "Momentum": ("Both hot", "🔥"),
    "Playoff Experience": ("KC edge (Mahomes)", "🏆"),
    "H2H History": ("KC 4-0 playoffs", "⚔️"),
    "Public Money": ("Split", "💰")
}

cols = st.columns(5)
for i, (factor, (value, emoji)) in enumerate(afc_factors.items()):
    with cols[i % 5]:
        st.caption(f"{emoji} {factor}")
        st.caption(value)

st.info("**AFC EDGE: TOSS-UP 5.5/10** — BUF better team on paper, but Mahomes factor + home field")

# ========== FOOTER ==========
st.divider()
st.subheader("📖 How to Use")
st.markdown("""
**Market Status:**
- ✅ Market is LIVE — click to trade on Kalshi
- ⏳ Market not live yet — typically opens 2-3 days before game

**When Games Go Live:** Football field visualization, real-time scores, down & distance, red zone alerts

**Questions?** aipublishingpro@gmail.com
""")

st.caption("⚠️ Educational analysis only. Not financial advice. v2.2.0")
