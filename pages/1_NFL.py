import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
from styles import apply_styles
import extra_streamlit_components as stx

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

apply_styles()

# ============================================================
# COOKIE MANAGER FOR PERSISTENT LOGIN
# ============================================================
cookie_manager = stx.CookieManager()

# ============================================================
# SESSION STATE FOR AUTH
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# ============================================================
# CHECK COOKIE FOR PERSISTENT LOGIN
# ============================================================
auth_cookie = cookie_manager.get("bigsnapshot_auth")
if auth_cookie and not st.session_state.authenticated:
    st.session_state.authenticated = True
    st.session_state.user_type = auth_cookie

# ============================================================
# AUTH CHECK
# ============================================================
if not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

VERSION = "2.0"

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button {
        padding: 8px 12px !important;
        font-size: 0.85em !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# TEAM MAPPINGS
# ============================================================
TEAM_ABBREVS = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
}

KALSHI_CODES = {
    "ARI": "ari", "ATL": "atl", "BAL": "bal", "BUF": "buf", "CAR": "car",
    "CHI": "chi", "CIN": "cin", "CLE": "cle", "DAL": "dal", "DEN": "den",
    "DET": "det", "GB": "gb", "HOU": "hou", "IND": "ind", "JAX": "jax",
    "KC": "kc", "LV": "lv", "LAC": "lac", "LAR": "lar", "MIA": "mia",
    "MIN": "min", "NE": "ne", "NO": "no", "NYG": "nyg", "NYJ": "nyj",
    "PHI": "phi", "PIT": "pit", "SF": "sf", "SEA": "sea", "TB": "tb",
    "TEN": "ten", "WAS": "was"
}

DOME_STADIUMS = ["ARI", "ATL", "DAL", "DET", "HOU", "IND", "LV", "LAC", "LAR", "MIN", "NO"]

# ============================================================
# TEAM STATS (Power ratings, win %)
# ============================================================
TEAM_STATS = {
    "ARI": {"pwr": -12.5, "rank": 27, "home_win": 0.42, "away_win": 0.30},
    "ATL": {"pwr": 2.5, "rank": 18, "home_win": 0.55, "away_win": 0.42},
    "BAL": {"pwr": 15.5, "rank": 6, "home_win": 0.72, "away_win": 0.62},
    "BUF": {"pwr": 18.2, "rank": 5, "home_win": 0.78, "away_win": 0.68},
    "CAR": {"pwr": -18.5, "rank": 30, "home_win": 0.35, "away_win": 0.22},
    "CHI": {"pwr": -8.5, "rank": 22, "home_win": 0.45, "away_win": 0.35},
    "CIN": {"pwr": 5.8, "rank": 14, "home_win": 0.58, "away_win": 0.48},
    "CLE": {"pwr": -25.0, "rank": 32, "home_win": 0.38, "away_win": 0.25},
    "DAL": {"pwr": -5.2, "rank": 20, "home_win": 0.52, "away_win": 0.38},
    "DEN": {"pwr": 8.5, "rank": 8, "home_win": 0.65, "away_win": 0.50},
    "DET": {"pwr": 22.5, "rank": 4, "home_win": 0.78, "away_win": 0.68},
    "GB": {"pwr": 12.2, "rank": 10, "home_win": 0.70, "away_win": 0.55},
    "HOU": {"pwr": 16.5, "rank": 7, "home_win": 0.68, "away_win": 0.58},
    "IND": {"pwr": 14.5, "rank": 12, "home_win": 0.55, "away_win": 0.48},
    "JAX": {"pwr": 10.5, "rank": 11, "home_win": 0.55, "away_win": 0.48},
    "KC": {"pwr": 18.5, "rank": 9, "home_win": 0.82, "away_win": 0.72},
    "LV": {"pwr": -10.2, "rank": 25, "home_win": 0.42, "away_win": 0.28},
    "LAC": {"pwr": 11.8, "rank": 3, "home_win": 0.62, "away_win": 0.52},
    "LAR": {"pwr": 24.5, "rank": 5, "home_win": 0.72, "away_win": 0.62},
    "MIA": {"pwr": -2.5, "rank": 16, "home_win": 0.55, "away_win": 0.38},
    "MIN": {"pwr": 8.5, "rank": 13, "home_win": 0.68, "away_win": 0.52},
    "NE": {"pwr": -12.5, "rank": 24, "home_win": 0.42, "away_win": 0.30},
    "NO": {"pwr": -8.8, "rank": 23, "home_win": 0.48, "away_win": 0.35},
    "NYG": {"pwr": -15.5, "rank": 29, "home_win": 0.35, "away_win": 0.22},
    "NYJ": {"pwr": -12.5, "rank": 26, "home_win": 0.42, "away_win": 0.28},
    "PHI": {"pwr": 14.8, "rank": 6, "home_win": 0.75, "away_win": 0.60},
    "PIT": {"pwr": 4.8, "rank": 10, "home_win": 0.62, "away_win": 0.45},
    "SF": {"pwr": 6.5, "rank": 15, "home_win": 0.58, "away_win": 0.48},
    "SEA": {"pwr": 28.5, "rank": 2, "home_win": 0.78, "away_win": 0.68},
    "TB": {"pwr": -3.2, "rank": 19, "home_win": 0.52, "away_win": 0.40},
    "TEN": {"pwr": -14.8, "rank": 28, "home_win": 0.40, "away_win": 0.25},
    "WAS": {"pwr": -4.5, "rank": 21, "home_win": 0.52, "away_win": 0.42}
}

STADIUM_COORDS = {
    "ARI": (33.5277, -112.2626), "ATL": (33.7553, -84.4006), "BAL": (39.2780, -76.6227),
    "BUF": (42.7738, -78.7870), "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167),
    "CIN": (39.0955, -84.5161), "CLE": (41.5061, -81.6995), "DAL": (32.7473, -97.0945),
    "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
    "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3239, -81.6373),
    "KC": (39.0489, -94.4839), "LV": (36.0909, -115.1833), "LAC": (33.9535, -118.3392),
    "LAR": (33.9535, -118.3392), "MIA": (25.9580, -80.2389), "MIN": (44.9737, -93.2577),
    "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8128, -74.0742),
    "NYJ": (40.8128, -74.0742), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158),
    "SF": (37.4032, -121.9698), "SEA": (47.5952, -122.3316), "TB": (27.9759, -82.5033),
    "TEN": (36.1665, -86.7713), "WAS": (38.9076, -76.8645)
}

# ============================================================
# KALSHI URL BUILDER
# ============================================================
def build_kalshi_url(away_abbr, home_abbr):
    eastern = pytz.timezone('US/Eastern')
    today = datetime.now(eastern)
    date_str = today.strftime("%y%b%d").upper()
    away_code = KALSHI_CODES.get(away_abbr, away_abbr.lower())
    home_code = KALSHI_CODES.get(home_abbr, home_abbr.lower())
    ticker = f"KXNFLGAME-{date_str}{away_code.upper()}{home_code.upper()}"
    return f"https://kalshi.com/markets/kxnflgame/{ticker.lower()}"

# ============================================================
# WEATHER API
# ============================================================
@st.cache_data(ttl=1800)
def fetch_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation&wind_speed_unit=mph&temperature_unit=fahrenheit"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data.get("current", {})
        return {
            "temp": current.get("temperature_2m", 70),
            "wind": current.get("wind_speed_10m", 0),
            "precip": current.get("precipitation", 0)
        }
    except:
        return {"temp": 70, "wind": 0, "precip": 0}

def get_weather_for_game(home_abbr):
    if home_abbr in DOME_STADIUMS:
        return {"wind": 0, "precip": 0, "temp": 72, "dome": True, "impact": "none"}
    coords = STADIUM_COORDS.get(home_abbr)
    if not coords:
        return {"wind": 0, "precip": 0, "temp": 70, "dome": False, "impact": "none"}
    weather = fetch_weather(coords[0], coords[1])
    wind, precip, temp = weather.get("wind", 0), weather.get("precip", 0), weather.get("temp", 70)
    if wind >= 20 or precip > 0.5:
        impact = "severe"
    elif wind >= 15 or precip > 0.1:
        impact = "moderate"
    elif wind >= 10:
        impact = "light"
    else:
        impact = "none"
    return {"wind": wind, "precip": precip, "temp": temp, "dome": False, "impact": impact}

# ============================================================
# ESPN API - REAL DATA
# ============================================================
@st.cache_data(ttl=60)
def fetch_nfl_games():
    eastern = pytz.timezone('US/Eastern')
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={today_date}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            home_abbr, away_abbr = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbr = full_name, score, abbr
                else:
                    away_team, away_score, away_abbr = full_name, score, abbr
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_abbr}@{home_abbr}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_abbr": away_abbr, "home_abbr": home_abbr,
                "away_score": away_score, "home_score": home_score,
                "quarter": period, "clock": clock, "status_type": status_type
            }
        return games
    except Exception as e:
        st.error(f"ESPN API error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_nfl_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_abbr = TEAM_ABBREVS.get(team_name, "")
            if not team_abbr:
                continue
            injuries[team_abbr] = []
            for cat in team_data.get("categories", []):
                for player in cat.get("items", []):
                    name = player.get("athlete", {}).get("displayName", "")
                    status = player.get("status", "")
                    pos = player.get("athlete", {}).get("position", {}).get("abbreviation", "")
                    if name:
                        injuries[team_abbr].append({"name": name, "status": status, "pos": pos})
    except:
        pass
    return injuries

# ============================================================
# ML SCORING MODEL - NFL FACTORS
# ============================================================
def calc_ml_score(home_abbr, away_abbr, injuries):
    home = TEAM_STATS.get(home_abbr, {})
    away = TEAM_STATS.get(away_abbr, {})
    weather = get_weather_for_game(home_abbr)
    
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    
    # Factor 1: Power Rating Difference
    home_pwr = home.get('pwr', 0)
    away_pwr = away.get('pwr', 0)
    pwr_diff = home_pwr - away_pwr
    if pwr_diff > 10:
        score_home += 2.0
        reasons_home.append(f"💪 +{pwr_diff:.1f}")
    elif pwr_diff > 5:
        score_home += 1.0
        reasons_home.append(f"💪 +{pwr_diff:.1f}")
    elif pwr_diff < -10:
        score_away += 2.0
        reasons_away.append(f"💪 +{-pwr_diff:.1f}")
    elif pwr_diff < -5:
        score_away += 1.0
        reasons_away.append(f"💪 +{-pwr_diff:.1f}")
    
    # Factor 2: Home Field Advantage
    home_hw = home.get('home_win', 0.5)
    score_home += 1.0
    reasons_home.append(f"🏟️ {int(home_hw*100)}%")
    
    # Factor 3: Team Ranking
    home_rank = home.get('rank', 16)
    away_rank = away.get('rank', 16)
    if home_rank <= 10 and away_rank > 20:
        score_home += 1.5
        reasons_home.append(f"📊 #{home_rank}")
    elif away_rank <= 10 and home_rank > 20:
        score_away += 1.5
        reasons_away.append(f"📊 #{away_rank}")
    
    # Factor 4: Weather Impact (favors home team in bad weather)
    if weather["impact"] == "severe":
        score_home += 1.0
        reasons_home.append(f"🌧️ {int(weather['wind'])}mph")
    elif weather["impact"] == "moderate":
        score_home += 0.5
        reasons_home.append(f"💨 {int(weather['wind'])}mph")
    elif weather["dome"]:
        reasons_home.append("🏠 Dome")
    
    # Factor 5: Key Injuries (QB, RB1)
    key_positions = ["QB", "RB"]
    home_key_out = len([i for i in injuries.get(home_abbr, []) 
                        if 'out' in i.get('status', '').lower() and i.get('pos') in key_positions])
    away_key_out = len([i for i in injuries.get(away_abbr, []) 
                        if 'out' in i.get('status', '').lower() and i.get('pos') in key_positions])
    if away_key_out > home_key_out:
        score_home += 2.0
        reasons_home.append(f"🏥 {away_key_out} key OUT")
    elif home_key_out > away_key_out:
        score_away += 2.0
        reasons_away.append(f"🏥 {home_key_out} key OUT")
    
    # Factor 6: Total Injuries
    home_inj = len([i for i in injuries.get(home_abbr, []) if 'out' in i.get('status', '').lower()])
    away_inj = len([i for i in injuries.get(away_abbr, []) if 'out' in i.get('status', '').lower()])
    if away_inj > home_inj + 3:
        score_home += 1.0
        reasons_home.append(f"🩹 {away_inj} OUT")
    elif home_inj > away_inj + 3:
        score_away += 1.0
        reasons_away.append(f"🩹 {home_inj} OUT")
    
    # Calculate final scores
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    
    if home_final >= away_final:
        return home_abbr, home_final, reasons_home[:4]
    else:
        return away_abbr, away_final, reasons_away[:4]

def get_signal_tier(score):
    if score >= 8.0:
        return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5:
        return "🔵 BUY", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    else:
        return "⚪ TOSS-UP", "#888888"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    
    st.header("📖 ML LEGEND")
    st.markdown("🟢 **STRONG BUY** → 8.0+\n\n🔵 **BUY** → 6.5-7.9\n\n🟡 **LEAN** → 5.5-6.4\n\n⚪ **TOSS-UP** → Below 5.5")
    st.divider()
    
    st.header("🔗 KALSHI")
    st.markdown('<a href="https://kalshi.com/?search=nfl" target="_blank" style="color: #00aaff;">NFL Markets ↗</a>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN
# ============================================================
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)

st.title("🏈 NFL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Real ESPN Data")

games = fetch_nfl_games()
injuries = fetch_nfl_injuries()

if not games:
    st.warning("No NFL games scheduled today.")
    st.stop()

st.divider()

# ============================================================
# 🎯 ML PICKS
# ============================================================
st.subheader("🎯 ML PICKS")

ml_results = []
for game_key, g in games.items():
    away_abbr = g["away_abbr"]
    home_abbr = g["home_abbr"]
    
    pick, score, reasons = calc_ml_score(home_abbr, away_abbr, injuries)
    tier, color = get_signal_tier(score)
    
    opponent = away_abbr if pick == home_abbr else home_abbr
    kalshi_url = build_kalshi_url(away_abbr, home_abbr)
    
    ml_results.append({
        "pick": pick,
        "opponent": opponent,
        "score": score,
        "color": color,
        "reasons": reasons,
        "kalshi_url": kalshi_url,
        "game_key": game_key,
        "status": g["status_type"]
    })

ml_results.sort(key=lambda x: x["score"], reverse=True)

shown = 0
for r in ml_results:
    if r["score"] < 5.5:
        continue
    shown += 1
    reasons_str = " • ".join(r["reasons"]) if r["reasons"] else ""
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #0f172a, #020617); padding: 10px 15px; margin-bottom: 6px; border-radius: 8px; border-left: 4px solid {r['color']};">
        <div>
            <span style="font-weight: bold; color: #fff;">{r['pick']}</span>
            <span style="color: #666;"> vs {r['opponent']}</span>
            <span style="color: {r['color']}; font-weight: bold; margin-left: 10px;">{r['score']}/10</span>
            <span style="color: #888; font-size: 0.85em; margin-left: 10px;">{reasons_str}</span>
        </div>
        <a href="{r['kalshi_url']}" target="_blank" style="text-decoration: none;">
            <button style="background-color: #16a34a; color: white; padding: 6px 14px; border: none; border-radius: 6px; font-size: 0.85em; font-weight: 600; cursor: pointer;">
                BUY {r['pick']}
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

if shown == 0:
    st.info("No strong picks today. All games are close to toss-ups.")

st.divider()

# ============================================================
# 🌤️ WEATHER REPORT
# ============================================================
st.subheader("🌤️ WEATHER REPORT")

teams_today = set()
for g in games.values():
    teams_today.add(g["home_abbr"])

weather_shown = False
cols = st.columns(4)
col_idx = 0
for home_abbr in sorted(teams_today):
    weather = get_weather_for_game(home_abbr)
    if weather["dome"]:
        label = "🏠 Dome"
    elif weather["impact"] != "none":
        label = f"💨 {int(weather['wind'])}mph | {int(weather['temp'])}°F"
        if weather["precip"] > 0:
            label += " | 🌧️"
    else:
        label = f"☀️ {int(weather['temp'])}°F"
    
    with cols[col_idx % 4]:
        impact_color = {"severe": "🔴", "moderate": "🟡", "light": "🟢", "none": "⚪"}.get(weather["impact"], "⚪")
        st.markdown(f"**{home_abbr}** {impact_color}")
        st.caption(label)
    col_idx += 1
    weather_shown = True

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injury_shown = False
cols = st.columns(4)
col_idx = 0
for team in sorted(teams_today):
    team_inj = injuries.get(team, [])
    key_injuries = [i for i in team_inj if 'out' in i.get('status', '').lower()]
    if key_injuries:
        with cols[col_idx % 4]:
            st.markdown(f"**{team}**")
            for inj in key_injuries[:3]:
                pos = inj.get('pos', '')
                st.caption(f"🔴 {inj['name']} ({pos})")
        col_idx += 1
        injury_shown = True

if not injury_shown:
    st.info("✅ No major injuries reported for today's teams")

st.divider()

# ============================================================
# 📺 ALL GAMES
# ============================================================
st.subheader("📺 ALL GAMES")

cols = st.columns(4)
for i, (gk, g) in enumerate(games.items()):
    with cols[i % 4]:
        st.markdown(f"**{g['away_abbr']}** {g['away_score']} @ **{g['home_abbr']}** {g['home_score']}")
        if g['status_type'] == "STATUS_FINAL":
            st.caption("FINAL")
        elif g['quarter'] > 0:
            st.caption(f"Q{g['quarter']} {g['clock']}")
        else:
            st.caption("Scheduled")

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 How to Use This App", expanded=False):
    st.markdown("""
    **What is NFL Edge Finder?**
    
    This tool analyzes NFL games and identifies moneyline betting opportunities on Kalshi prediction markets.
    
    **Understanding the Signals:**
    - **🟢 STRONG BUY (8.0+):** High confidence pick
    - **🔵 BUY (6.5-7.9):** Good edge detected
    - **🟡 LEAN (5.5-6.4):** Slight edge
    - **⚪ TOSS-UP (Below 5.5):** No clear edge
    
    **Key Indicators:**
    - **💪 Power Rating:** Team strength differential
    - **🏟️ Home Field:** Home win percentage
    - **🌧️ Weather:** Wind/rain impact (favors home)
    - **🏥 Injuries:** Key players (QB, RB) out
    """)

st.divider()
st.caption(f"⚠️ Entertainment only. Not financial advice. v{VERSION}")
