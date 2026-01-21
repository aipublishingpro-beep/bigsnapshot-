import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import uuid

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

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

TEAM_ABBR_TO_FULL = {v: k for k, v in KALSHI_CODES.items()}

@st.cache_data(ttl=120)
def fetch_kalshi_market(ticker):
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            market = data.get("market", {})
            if market:
                return {
                    "yes_price": market.get("yes_bid", 0),
                    "no_price": market.get("no_bid", 0),
                    "last_price": market.get("last_price", 0),
                    "volume": market.get("volume", 0),
                    "open_interest": market.get("open_interest", 0),
                    "exists": True
                }
        return {"exists": False}
    except:
        return {"exists": False}

@st.cache_data(ttl=300)
def fetch_kalshi_history(ticker):
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}/history"
        params = {"limit": 50}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("history", [])
        return []
    except:
        return []

def calc_market_pressure(ticker, pick_abbr, home_abbr):
    market = fetch_kalshi_market(ticker)
    if not market.get("exists"):
        return None, "NO DATA", "#888888"
    
    history = fetch_kalshi_history(ticker)
    if len(history) < 2:
        return market, "NEUTRAL", "#ffaa00"
    
    recent_prices = [h.get("yes_price", 50) for h in history[:10]]
    older_prices = [h.get("yes_price", 50) for h in history[10:20]] if len(history) > 10 else recent_prices
    
    avg_recent = sum(recent_prices) / len(recent_prices) if recent_prices else 50
    avg_older = sum(older_prices) / len(older_prices) if older_prices else 50
    
    price_move = avg_recent - avg_older
    pick_is_home = pick_abbr == home_abbr
    
    if pick_is_home:
        if price_move > 3: return market, "CONFIRMING", "#00ff00"
        elif price_move < -3: return market, "FADING", "#ff4444"
        else: return market, "NEUTRAL", "#ffaa00"
    else:
        if price_move < -3: return market, "CONFIRMING", "#00ff00"
        elif price_move > 3: return market, "FADING", "#ff4444"
        else: return market, "NEUTRAL", "#ffaa00"

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
    except:
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

with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    st.header("🔗 KALSHI")
    st.caption("NFL Championship Markets")
    st.divider()
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="nfl_auto")
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=30000, key="nfl_refresh")
    st.divider()
    st.caption("v2.4.1")

st.title("🏈 NFL Edge Finder")
st.caption(f"v2.4.1 | {now.strftime('%I:%M:%S %p ET')} | Conference Championships")

games = fetch_nfl_games()
injuries = fetch_nfl_injuries()

st.divider()

st.subheader("🎯 ML PICKS")

# NFC Championship
nfc_ticker = "KXNFLGAME-26JAN26PHIWAS"
nfc_market = fetch_kalshi_market(nfc_ticker)
nfc_exists = nfc_market.get("exists", False)
nfc_score = 7.5
nfc_border = "#00aaff"
nfc_market_data, nfc_pressure, nfc_pressure_color = calc_market_pressure(nfc_ticker, "PHI", "WAS")
nfc_price_info = f" | {nfc_market.get('yes_price', 0)}¢" if nfc_exists else ""

st.markdown(f"""
<div style="display: flex; align-items: center; background: #1a1a2e; border-left: 4px solid {nfc_border}; padding: 12px 16px; margin-bottom: 8px; border-radius: 4px;">
    <div style="flex: 1;">
        <span style="color: #00d4ff; font-size: 0.8em;">NFC CHAMPIONSHIP</span><br>
        <span style="font-weight: bold; color: white;">PHI</span>
        <span style="color: #888;"> @ WAS 🏠</span>
        <span style="color: {nfc_border}; font-weight: bold; margin-left: 8px;">{nfc_score}/10</span>
        <span style="background: {nfc_pressure_color}22; color: {nfc_pressure_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">{nfc_pressure}{nfc_price_info}</span>
    </div>
    <div>
        <a href="https://kalshi.com/markets/{nfc_ticker.lower()}" target="_blank" style="background: {'#00aa00' if nfc_exists else '#666'}; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold;">{'BUY PHI' if nfc_exists else '⏳ PENDING'}</a>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"📈 PHI @ WAS Line Movement", expanded=False):
    if nfc_exists:
        history = fetch_kalshi_history(nfc_ticker)
        if history and len(history) > 1:
            import pandas as pd
            df = pd.DataFrame(history)
            if 'yes_price' in df.columns and 'ts' in df.columns:
                df['time'] = pd.to_datetime(df['ts'], unit='s')
                df = df.sort_values('time')
                st.line_chart(df.set_index('time')['yes_price'], use_container_width=True)
                st.caption(f"Volume: {nfc_market.get('volume', 'N/A')} | OI: {nfc_market.get('open_interest', 'N/A')}")
            else:
                st.info("Chart data unavailable")
        else:
            st.info("No price history available yet")
    else:
        st.info("⏳ Market not live yet")

st.markdown("---")

# AFC Championship
afc_ticker = "KXNFLGAME-26JAN26BUFKC"
afc_market = fetch_kalshi_market(afc_ticker)
afc_exists = afc_market.get("exists", False)
afc_score = 5.5
afc_border = "#ffff00"
afc_market_data, afc_pressure, afc_pressure_color = calc_market_pressure(afc_ticker, "BUF", "KC")
afc_price_info = f" | {afc_market.get('yes_price', 0)}¢" if afc_exists else ""

st.markdown(f"""
<div style="display: flex; align-items: center; background: #1a1a2e; border-left: 4px solid {afc_border}; padding: 12px 16px; margin-bottom: 8px; border-radius: 4px;">
    <div style="flex: 1;">
        <span style="color: #ff6b6b; font-size: 0.8em;">AFC CHAMPIONSHIP</span><br>
        <span style="font-weight: bold; color: white;">BUF</span>
        <span style="color: #888;"> @ KC 🏠</span>
        <span style="color: {afc_border}; font-weight: bold; margin-left: 8px;">{afc_score}/10</span>
        <span style="color: #888; font-size: 0.9em;"> ⚔️ TOSS-UP</span>
        <span style="background: {afc_pressure_color}22; color: {afc_pressure_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">{afc_pressure}{afc_price_info}</span>
    </div>
    <div style="display: flex; gap: 8px;">
        <a href="https://kalshi.com/markets/{afc_ticker.lower()}" target="_blank" style="background: {'#00aa00' if afc_exists else '#666'}; color: white; padding: 8px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 0.9em;">{'BUY BUF' if afc_exists else '⏳'}</a>
        <a href="https://kalshi.com/markets/{afc_ticker.lower()}" target="_blank" style="background: {'#cc0000' if afc_exists else '#666'}; color: white; padding: 8px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 0.9em;">{'BUY KC' if afc_exists else '⏳'}</a>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"📈 BUF @ KC Line Movement", expanded=False):
    if afc_exists:
        history = fetch_kalshi_history(afc_ticker)
        if history and len(history) > 1:
            import pandas as pd
            df = pd.DataFrame(history)
            if 'yes_price' in df.columns and 'ts' in df.columns:
                df['time'] = pd.to_datetime(df['ts'], unit='s')
                df = df.sort_values('time')
                st.line_chart(df.set_index('time')['yes_price'], use_container_width=True)
                st.caption(f"Volume: {afc_market.get('volume', 'N/A')} | OI: {afc_market.get('open_interest', 'N/A')}")
            else:
                st.info("Chart data unavailable")
        else:
            st.info("No price history available yet")
    else:
        st.info("⏳ Market not live yet")

st.divider()
st.markdown("""
<div style="background:linear-gradient(135deg,#4a1942,#2d132c);border-radius:12px;padding:20px;text-align:center;border:1px solid #801336">
    <span style="font-size:2em">🏆</span>
    <h3 style="color:#ffd700;margin:10px 0">Super Bowl LIX</h3>
    <p style="color:#fff;margin:0">February 9, 2025 • Caesars Superdome, New Orleans</p>
    <p style="color:#888;font-size:0.9em;margin-top:5px">FOX • 6:30 PM ET</p>
</div>
""", unsafe_allow_html=True)

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
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** 🏠 {g['home_score']}")
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
    st.caption("Sample field visualization:")
    st.markdown(draw_football_field(35, "BUF", "KC", "BUF", False), unsafe_allow_html=True)

if final_games:
    st.subheader("✅ RECENT FINALS")
    for gid, g in final_games.items():
        winner = g['away_team'] if g['away_score'] > g['home_score'] else g['home_team']
        st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** 🏠 {g['home_score']} — **{winner} WIN**")

st.divider()
st.subheader("🏥 CHAMPIONSHIP TEAM INJURIES")

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

st.divider()
st.caption("⚠️ Entertainment only. Not financial advice. v2.4.1")
