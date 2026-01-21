import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

apply_styles()

# ============================================================
# AUTH CHECK
# ============================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
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
# TEAM MAPPINGS
# ============================================================
TEAM_ABBREVS = {
    "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
    "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

KALSHI_CODES = {
    "ANA": "ana", "ARI": "ari", "BOS": "bos", "BUF": "buf", "CGY": "cgy",
    "CAR": "car", "CHI": "chi", "COL": "col", "CBJ": "cbj", "DAL": "dal",
    "DET": "det", "EDM": "edm", "FLA": "fla", "LAK": "lak", "MIN": "min",
    "MTL": "mtl", "NSH": "nsh", "NJD": "njd", "NYI": "nyi", "NYR": "nyr",
    "OTT": "ott", "PHI": "phi", "PIT": "pit", "SJS": "sjs", "SEA": "sea",
    "STL": "stl", "TBL": "tbl", "TOR": "tor", "UTA": "uta", "VAN": "van",
    "VGK": "vgk", "WSH": "wsh", "WPG": "wpg"
}

# ============================================================
# TEAM STATS (Updated Jan 2026 - update periodically)
# ============================================================
TEAM_STATS = {
    "ANA": {"win_pct": 0.380, "home_win_pct": 0.420, "goals_for": 2.65, "goals_against": 3.35, "pp_pct": 17.8, "pk_pct": 76.5},
    "BOS": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.10, "goals_against": 2.70, "pp_pct": 22.5, "pk_pct": 82.0},
    "BUF": {"win_pct": 0.450, "home_win_pct": 0.500, "goals_for": 2.85, "goals_against": 3.05, "pp_pct": 19.5, "pk_pct": 78.5},
    "CGY": {"win_pct": 0.520, "home_win_pct": 0.580, "goals_for": 2.95, "goals_against": 2.85, "pp_pct": 21.8, "pk_pct": 81.2},
    "CAR": {"win_pct": 0.600, "home_win_pct": 0.680, "goals_for": 3.25, "goals_against": 2.55, "pp_pct": 24.2, "pk_pct": 84.5},
    "CHI": {"win_pct": 0.350, "home_win_pct": 0.400, "goals_for": 2.55, "goals_against": 3.45, "pp_pct": 16.5, "pk_pct": 75.0},
    "COL": {"win_pct": 0.620, "home_win_pct": 0.720, "goals_for": 3.42, "goals_against": 2.65, "pp_pct": 26.8, "pk_pct": 82.5},
    "CBJ": {"win_pct": 0.400, "home_win_pct": 0.450, "goals_for": 2.70, "goals_against": 3.25, "pp_pct": 18.2, "pk_pct": 77.0},
    "DAL": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.05, "goals_against": 2.65, "pp_pct": 23.5, "pk_pct": 83.0},
    "DET": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.90, "goals_against": 2.95, "pp_pct": 20.5, "pk_pct": 79.5},
    "EDM": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.35, "goals_against": 2.85, "pp_pct": 28.5, "pk_pct": 80.5},
    "FLA": {"win_pct": 0.600, "home_win_pct": 0.680, "goals_for": 3.28, "goals_against": 2.72, "pp_pct": 24.5, "pk_pct": 81.2},
    "LAK": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 2.95, "goals_against": 2.78, "pp_pct": 21.0, "pk_pct": 80.0},
    "MIN": {"win_pct": 0.560, "home_win_pct": 0.640, "goals_for": 3.18, "goals_against": 2.75, "pp_pct": 23.5, "pk_pct": 82.8},
    "MTL": {"win_pct": 0.420, "home_win_pct": 0.480, "goals_for": 2.75, "goals_against": 3.15, "pp_pct": 18.8, "pk_pct": 77.5},
    "NSH": {"win_pct": 0.480, "home_win_pct": 0.550, "goals_for": 2.82, "goals_against": 2.92, "pp_pct": 19.8, "pk_pct": 79.0},
    "NJD": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 3.08, "goals_against": 2.92, "pp_pct": 24.2, "pk_pct": 79.5},
    "NYI": {"win_pct": 0.500, "home_win_pct": 0.560, "goals_for": 2.92, "goals_against": 2.88, "pp_pct": 20.8, "pk_pct": 84.2},
    "NYR": {"win_pct": 0.560, "home_win_pct": 0.620, "goals_for": 3.28, "goals_against": 2.72, "pp_pct": 26.2, "pk_pct": 81.8},
    "OTT": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.95, "goals_against": 3.05, "pp_pct": 21.5, "pk_pct": 78.0},
    "PHI": {"win_pct": 0.440, "home_win_pct": 0.500, "goals_for": 2.72, "goals_against": 3.18, "pp_pct": 18.5, "pk_pct": 77.2},
    "PIT": {"win_pct": 0.520, "home_win_pct": 0.580, "goals_for": 3.05, "goals_against": 2.88, "pp_pct": 22.8, "pk_pct": 80.1},
    "SJS": {"win_pct": 0.320, "home_win_pct": 0.380, "goals_for": 2.45, "goals_against": 3.55, "pp_pct": 17.2, "pk_pct": 75.8},
    "SEA": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.78, "goals_against": 3.05, "pp_pct": 19.5, "pk_pct": 77.8},
    "STL": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.88, "goals_against": 2.98, "pp_pct": 20.2, "pk_pct": 78.5},
    "TBL": {"win_pct": 0.560, "home_win_pct": 0.620, "goals_for": 3.15, "goals_against": 2.82, "pp_pct": 25.5, "pk_pct": 81.5},
    "TOR": {"win_pct": 0.580, "home_win_pct": 0.660, "goals_for": 3.22, "goals_against": 2.82, "pp_pct": 25.2, "pk_pct": 80.5},
    "UTA": {"win_pct": 0.420, "home_win_pct": 0.480, "goals_for": 2.68, "goals_against": 3.12, "pp_pct": 18.0, "pk_pct": 76.5},
    "VAN": {"win_pct": 0.500, "home_win_pct": 0.560, "goals_for": 3.05, "goals_against": 3.02, "pp_pct": 22.5, "pk_pct": 79.8},
    "VGK": {"win_pct": 0.600, "home_win_pct": 0.700, "goals_for": 3.35, "goals_against": 2.58, "pp_pct": 25.8, "pk_pct": 83.5},
    "WPG": {"win_pct": 0.620, "home_win_pct": 0.700, "goals_for": 3.38, "goals_against": 2.55, "pp_pct": 24.8, "pk_pct": 82.5},
    "WSH": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 3.02, "goals_against": 2.88, "pp_pct": 21.5, "pk_pct": 78.2},
}

# ============================================================
# KALSHI URL BUILDER
# ============================================================
def build_kalshi_url(away_abbr, home_abbr):
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    away_code = KALSHI_CODES.get(away_abbr, away_abbr.lower())
    home_code = KALSHI_CODES.get(home_abbr, home_abbr.lower())
    ticker = f"KXNHLGAME-{date_str}{away_code.upper()}{home_code.upper()}"
    return f"https://kalshi.com/markets/kxnhlgame/{ticker.lower()}"

# ============================================================
# ESPN API - REAL DATA
# ============================================================
@st.cache_data(ttl=60)
def fetch_nhl_games():
    eastern = pytz.timezone('US/Eastern')
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={today_date}"
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
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except Exception as e:
        st.error(f"ESPN API error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    eastern = pytz.timezone('US/Eastern')
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, "")
                if abbr:
                    teams.add(abbr)
        return teams
    except:
        return set()

@st.cache_data(ttl=300)
def fetch_nhl_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries"
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
                    if name:
                        injuries[team_abbr].append({"name": name, "status": status})
    except:
        pass
    return injuries

# ============================================================
# ML SCORING MODEL - 10 FACTORS
# ============================================================
def calc_ml_score(home_abbr, away_abbr, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_abbr, {})
    away = TEAM_STATS.get(away_abbr, {})
    
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    
    home_b2b = home_abbr in yesterday_teams
    away_b2b = away_abbr in yesterday_teams
    if away_b2b and not home_b2b:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    
    home_win = home.get('win_pct', 0.5)
    away_win = away.get('win_pct', 0.5)
    if home_win - away_win > 0.10:
        score_home += 1.0
        reasons_home.append(f"📊 {int(home_win*100)}% W")
    elif away_win - home_win > 0.10:
        score_away += 1.0
        reasons_away.append(f"📊 {int(away_win*100)}% W")
    
    score_home += 1.0
    home_hw = home.get('home_win_pct', 0.55)
    reasons_home.append(f"🏠 {int(home_hw*100)}%")
    
    home_gf = home.get('goals_for', 2.8)
    away_gf = away.get('goals_for', 2.8)
    if home_gf - away_gf > 0.3:
        score_home += 1.0
        reasons_home.append(f"🥅 {home_gf:.2f} GF")
    elif away_gf - home_gf > 0.3:
        score_away += 1.0
        reasons_away.append(f"🥅 {away_gf:.2f} GF")
    
    home_ga = home.get('goals_against', 2.9)
    away_ga = away.get('goals_against', 2.9)
    if away_ga - home_ga > 0.3:
        score_home += 1.0
        reasons_home.append(f"🛡️ {home_ga:.2f} GA")
    elif home_ga - away_ga > 0.3:
        score_away += 1.0
        reasons_away.append(f"🛡️ {away_ga:.2f} GA")
    
    home_pp = home.get('pp_pct', 20)
    away_pp = away.get('pp_pct', 20)
    if home_pp - away_pp > 4:
        score_home += 0.5
        reasons_home.append(f"⚡ {home_pp:.1f}% PP")
    elif away_pp - home_pp > 4:
        score_away += 0.5
        reasons_away.append(f"⚡ {away_pp:.1f}% PP")
    
    home_pk = home.get('pk_pct', 80)
    away_pk = away.get('pk_pct', 80)
    if home_pk - away_pk > 3:
        score_home += 0.5
        reasons_home.append(f"🚫 {home_pk:.1f}% PK")
    elif away_pk - home_pk > 3:
        score_away += 0.5
        reasons_away.append(f"🚫 {away_pk:.1f}% PK")
    
    home_inj = len([i for i in injuries.get(home_abbr, []) if 'out' in i.get('status', '').lower()])
    away_inj = len([i for i in injuries.get(away_abbr, []) if 'out' in i.get('status', '').lower()])
    if away_inj > home_inj + 1:
        score_home += 1.5
        reasons_home.append(f"🏥 {away_inj} OUT")
    elif home_inj > away_inj + 1:
        score_away += 1.5
        reasons_away.append(f"🏥 {home_inj} OUT")
    
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
    st.markdown("[NHL Markets](https://kalshi.com/?search=nhl)")
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN
# ============================================================
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)

st.title("🏒 NHL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Real ESPN Data")

games = fetch_nhl_games()
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_nhl_injuries()

if not games:
    st.warning("No NHL games scheduled today.")
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
    
    pick, score, reasons = calc_ml_score(home_abbr, away_abbr, yesterday_teams, injuries)
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
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

teams_today = set()
for g in games.values():
    teams_today.add(g["away_abbr"])
    teams_today.add(g["home_abbr"])

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
                st.caption(f"🔴 {inj['name']}")
        col_idx += 1
        injury_shown = True

if not injury_shown:
    st.info("✅ No major injuries reported for today's teams")

b2b_today = yesterday_teams.intersection(teams_today)
if b2b_today:
    st.info(f"📅 **Back-to-Back**: {', '.join(sorted(b2b_today))}")

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
        elif g['period'] > 0:
            st.caption(f"P{g['period']} {g['clock']}")
        else:
            st.caption("Scheduled")

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 How to Use This App", expanded=False):
    st.markdown("""
    **What is NHL Edge Finder?**
    
    This tool analyzes NHL games and identifies moneyline betting opportunities on Kalshi prediction markets.
    
    **Understanding the Signals:**
    - **🟢 STRONG BUY (8.0+):** High confidence pick
    - **🔵 BUY (6.5-7.9):** Good edge detected
    - **🟡 LEAN (5.5-6.4):** Slight edge
    - **⚪ TOSS-UP (Below 5.5):** No clear edge
    
    **Key Indicators:**
    - **🛏️ Opp B2B:** Opponent playing back-to-back games
    - **🏠 Home Ice:** Home team advantage percentage
    - **🏥 Injuries:** Key players out for opponent
    """)

st.divider()
st.caption(f"⚠️ Entertainment only. Not financial advice. v{VERSION}")
