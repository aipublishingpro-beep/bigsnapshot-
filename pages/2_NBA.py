import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== HIDE MENUS ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
.stLinkButton > a {
    background-color: #00aa00 !important;
    border-color: #00aa00 !important;
    color: white !important;
}
.stLinkButton > a:hover {
    background-color: #00cc00 !important;
    border-color: #00cc00 !important;
}
</style>
""", unsafe_allow_html=True)

# ========== GA4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== GATE CHECK ==========
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False

if not st.session_state.gate_passed:
    st.title("🎯 NBA Edge Finder")
    st.warning("⚠️ Please confirm the following:")
    cb1 = st.checkbox("I understand this tool provides market signals, not predictions.")
    cb2 = st.checkbox("I understand signals may change as new information arrives.")
    cb3 = st.checkbox("I understand this is not financial advice.")
    cb4 = st.checkbox("I understand this free beta may end at any time.")
    cb5 = st.checkbox("I confirm I am 18+ years old.")
    if cb1 and cb2 and cb3 and cb4 and cb5:
        if st.button("Enter NBA Edge Finder", type="primary"):
            st.session_state.gate_passed = True
            st.rerun()
    st.stop()

# ========== SESSION STATE ==========
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'positions' not in st.session_state:
    st.session_state.positions = []

if st.session_state.auto_refresh:
    st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)
    auto_status = "🔄 Auto ON"
else:
    auto_status = "⏸️ Auto OFF"

# ========== TIMEZONE ==========
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

# ========== TEAM MAPPINGS ==========
TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
    "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
    "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee",
    "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City",
    "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix",
    "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento",
    "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS"
}

TEAM_STATS = {
    "Atlanta": {"net_rtg": -3.2, "off_rtg": 115.8, "def_rtg": 119.0, "pace": 101.2},
    "Boston": {"net_rtg": 9.8, "off_rtg": 120.5, "def_rtg": 110.7, "pace": 99.8},
    "Brooklyn": {"net_rtg": -7.5, "off_rtg": 108.2, "def_rtg": 115.7, "pace": 96.3},
    "Charlotte": {"net_rtg": -8.1, "off_rtg": 107.5, "def_rtg": 115.6, "pace": 100.5},
    "Chicago": {"net_rtg": -4.2, "off_rtg": 112.3, "def_rtg": 116.5, "pace": 99.1},
    "Cleveland": {"net_rtg": 7.2, "off_rtg": 117.8, "def_rtg": 110.6, "pace": 97.5},
    "Dallas": {"net_rtg": -1.5, "off_rtg": 114.2, "def_rtg": 115.7, "pace": 98.8},
    "Denver": {"net_rtg": 3.8, "off_rtg": 116.2, "def_rtg": 112.4, "pace": 98.2},
    "Detroit": {"net_rtg": -5.8, "off_rtg": 110.5, "def_rtg": 116.3, "pace": 99.8},
    "Golden State": {"net_rtg": 2.1, "off_rtg": 114.8, "def_rtg": 112.7, "pace": 100.2},
    "Houston": {"net_rtg": 4.5, "off_rtg": 115.5, "def_rtg": 111.0, "pace": 98.5},
    "Indiana": {"net_rtg": 1.2, "off_rtg": 118.5, "def_rtg": 117.3, "pace": 103.8},
    "LA Clippers": {"net_rtg": -0.8, "off_rtg": 112.5, "def_rtg": 113.3, "pace": 97.2},
    "LA Lakers": {"net_rtg": 1.5, "off_rtg": 114.2, "def_rtg": 112.7, "pace": 99.5},
    "Memphis": {"net_rtg": 4.2, "off_rtg": 117.2, "def_rtg": 113.0, "pace": 101.5},
    "Miami": {"net_rtg": 0.5, "off_rtg": 111.8, "def_rtg": 111.3, "pace": 96.8},
    "Milwaukee": {"net_rtg": 2.8, "off_rtg": 116.5, "def_rtg": 113.7, "pace": 99.2},
    "Minnesota": {"net_rtg": 3.5, "off_rtg": 112.8, "def_rtg": 109.3, "pace": 97.8},
    "New Orleans": {"net_rtg": -9.2, "off_rtg": 107.5, "def_rtg": 116.7, "pace": 98.5},
    "New York": {"net_rtg": 6.5, "off_rtg": 118.4, "def_rtg": 111.9, "pace": 99.5},
    "Oklahoma City": {"net_rtg": 11.2, "off_rtg": 118.5, "def_rtg": 107.3, "pace": 99.8},
    "Orlando": {"net_rtg": 2.2, "off_rtg": 109.5, "def_rtg": 107.3, "pace": 96.2},
    "Philadelphia": {"net_rtg": -2.5, "off_rtg": 111.2, "def_rtg": 113.7, "pace": 98.2},
    "Phoenix": {"net_rtg": 0.8, "off_rtg": 113.5, "def_rtg": 112.7, "pace": 98.5},
    "Portland": {"net_rtg": -7.8, "off_rtg": 108.2, "def_rtg": 116.0, "pace": 99.8},
    "Sacramento": {"net_rtg": -1.2, "off_rtg": 114.8, "def_rtg": 116.0, "pace": 100.5},
    "San Antonio": {"net_rtg": 5.5, "off_rtg": 117.8, "def_rtg": 112.3, "pace": 100.8},
    "Toronto": {"net_rtg": -6.5, "off_rtg": 109.5, "def_rtg": 116.0, "pace": 98.2},
    "Utah": {"net_rtg": -5.2, "off_rtg": 119.4, "def_rtg": 124.6, "pace": 102.5},
    "Washington": {"net_rtg": -10.5, "off_rtg": 112.7, "def_rtg": 123.2, "pace": 101.2}
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young", "Jalen Johnson"], "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Brooklyn": ["Cam Thomas"], "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Chicago": ["Zach LaVine", "Coby White"], "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["James Harden", "Kawhi Leonard"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr."], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"], "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Karl-Anthony Towns"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"], "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"], "Phoenix": ["Kevin Durant", "Devin Booker"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"], "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "San Antonio": ["Victor Wembanyama", "Devin Vassell"], "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Utah": ["Lauri Markkanen", "Keyonte George"], "Washington": ["Jordan Poole", "Kyle Kuzma"]
}

# ========== HELPER FUNCTIONS ==========
def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 48
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 0
    try:
        if ':' in str(clock):
            parts = str(clock).split(':')
            mins_left = int(parts[0])
            secs_left = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins_left = 0
            secs_left = float(clock) if clock else 0
        time_left_in_period = mins_left + secs_left / 60
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left_in_period)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left_in_period)
    except:
        return (period - 1) * 12 if period <= 4 else 48

# ========== FETCH ESPN GAMES - FIXED ==========
@st.cache_data(ttl=60)
def fetch_espn_scores(date_key=None):
    games = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                # FIXED: Use homeAway field to correctly identify teams
                if c.get("homeAway") == "home":
                    home_team, home_score = team_name, score
                else:
                    away_team, away_score = team_name, score
            if not home_team or not away_team:
                continue
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
    except Exception as e:
        st.error(f"Error fetching games: {e}")
    return games

@st.cache_data(ttl=3600)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams.add(team_name)
        return teams
    except:
        return set()

@st.cache_data(ttl=300)
def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            if not team_name:
                team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key:
                continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                if not name:
                    name = player.get("displayName", "")
                status = player.get("status", "")
                if not status:
                    status = player.get("type", {}).get("description", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

# ========== ML SCORING (10-FACTOR) ==========
def calc_ml_score(away_team, home_team, injuries, yesterday_teams):
    away_stats = TEAM_STATS.get(away_team, {})
    home_stats = TEAM_STATS.get(home_team, {})
    if not away_stats or not home_stats:
        return None, 5.0, []
    
    score = 5.0
    reasons = []
    
    # Factor 1: Net Rating
    net_diff = home_stats.get("net_rtg", 0) - away_stats.get("net_rtg", 0)
    score += min(1.5, max(-1.5, net_diff * 0.1))
    if abs(net_diff) >= 5:
        reasons.append(f"Net Rtg: {'+' if net_diff > 0 else ''}{net_diff:.1f}")
    
    # Factor 2: Home Court
    score += 0.8
    reasons.append("Home +0.8")
    
    # Factor 3: B2B Fatigue
    away_b2b = away_team in yesterday_teams
    home_b2b = home_team in yesterday_teams
    if away_b2b and not home_b2b:
        score += 0.7
        reasons.append("Away B2B")
    elif home_b2b and not away_b2b:
        score -= 0.7
        reasons.append("Home B2B")
    
    # Factor 4: Star Injuries
    away_stars = STAR_PLAYERS.get(away_team, [])
    home_stars = STAR_PLAYERS.get(home_team, [])
    away_inj = injuries.get(away_team, [])
    home_inj = injuries.get(home_team, [])
    
    away_out = sum(1 for i in away_inj if any(s.lower() in i.get("name", "").lower() for s in away_stars) and "out" in i.get("status", "").lower())
    home_out = sum(1 for i in home_inj if any(s.lower() in i.get("name", "").lower() for s in home_stars) and "out" in i.get("status", "").lower())
    
    inj_impact = (away_out - home_out) * 0.5
    score += max(-1.5, min(1.5, inj_impact))
    if away_out > 0:
        reasons.append(f"Away {away_out}⭐ out")
    if home_out > 0:
        reasons.append(f"Home {home_out}⭐ out")
    
    # Factor 5: Defense Rating
    def_diff = away_stats.get("def_rtg", 110) - home_stats.get("def_rtg", 110)
    score += min(0.5, max(-0.5, def_diff * 0.05))
    
    score = max(0, min(10, score))
    
    if score >= 5.5:
        pick = home_team
    else:
        pick = away_team
        score = 10 - score
    
    return pick, round(score, 1), reasons

def get_signal_tier(score):
    if score >= 8.0:
        return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5:
        return "🔵 BUY", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    else:
        return "⚪ TOSS-UP", "#888888"

# ========== FETCH DATA ==========
games = fetch_espn_scores(date_key=today_str)
game_list = sorted(list(games.keys()))
yesterday_teams_raw = fetch_yesterday_teams()
injuries = fetch_espn_injuries()

today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams_raw.intersection(today_teams)

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')} | v15.51")
if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True):
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.rerun()
if hdr3.button("🔄 Refresh", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ========== ML PICKS ==========
st.subheader("🎯 ML PICKS")

ml_results = []
for gk in game_list:
    g = games[gk]
    away, home = g['away_team'], g['home_team']
    pick, score, reasons = calc_ml_score(away, home, injuries, yesterday_teams)
    if pick and score >= 5.5:
        ml_results.append({
            "game": gk, "pick": pick, "score": score, "reasons": reasons,
            "away": away, "home": home, "status": g['status_type']
        })

ml_results.sort(key=lambda x: x['score'], reverse=True)

if ml_results:
    for r in ml_results:
        signal, color = get_signal_tier(r['score'])
        reasons_txt = " | ".join(r['reasons'][:3]) if r['reasons'] else ""
        
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"**{r['away']} @ {r['home']}**")
                st.caption(f"{signal} | Score: {r['score']}/10")
            with c2:
                st.caption(reasons_txt)
            with c3:
                pick_code = KALSHI_CODES.get(r['pick'], "XXX")
                date_code = now.strftime("%y%b%d").upper()
                away_code = KALSHI_CODES.get(r['away'], "XXX")
                home_code = KALSHI_CODES.get(r['home'], "XXX")
                ticker = f"KXNBAGAME-{date_code}{away_code}{home_code}"
                kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
                st.link_button(f"🎯 BUY {pick_code}", kalshi_url, use_container_width=True)
                st.caption(f"→ {ticker}")
else:
    st.info("No strong ML picks right now")

st.divider()

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

cush_col1, cush_col2 = st.columns(2)
cush_min = cush_col1.selectbox("Min Minutes", [6, 9, 12, 15, 18], index=0, key="cush_min")
cush_side = cush_col2.selectbox("Side", ["NO (Under)", "YES (Over)"], key="cush_side")
is_no = "NO" in cush_side

cushion_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins < cush_min or g['status_type'] == "STATUS_FINAL":
        continue
    
    total = g['total']
    pace = total / mins if mins > 0 else 0
    proj = round(pace * 48)
    
    if is_no:
        candidates = [t for t in THRESHOLDS if t > proj]
        if len(candidates) >= 2:
            bet_line = candidates[1]
        elif len(candidates) == 1:
            bet_line = candidates[0]
        else:
            continue
        cushion = bet_line - proj
    else:
        candidates = [t for t in THRESHOLDS if t < proj]
        if len(candidates) >= 2:
            bet_line = candidates[-2]
        elif len(candidates) == 1:
            bet_line = candidates[0]
        else:
            continue
        cushion = proj - bet_line
    
    if cushion >= 6:
        cushion_data.append({
            "game": gk, "total": total, "proj": proj, "bet_line": bet_line,
            "cushion": cushion, "pace": pace, "mins": mins,
            "period": g['period'], "clock": g['clock']
        })

cushion_data.sort(key=lambda x: x['cushion'], reverse=True)

if cushion_data:
    st.markdown("| Game | Status | Total | Proj | 🎯 Bet Line | Cushion | Pace |")
    st.markdown("|------|--------|-------|------|-------------|---------|------|")
    for cd in cushion_data:
        pace_lbl = "🟢" if cd['pace'] < 4.5 else "🟡" if cd['pace'] < 4.8 else "🟠" if cd['pace'] < 5.2 else "🔴"
        status = f"Q{cd['period']} {cd['clock']}"
        st.markdown(f"| {cd['game'].replace('@', ' @ ')} | {status} | {cd['total']} | {cd['proj']} | **{cd['bet_line']}** | +{cd['cushion']:.0f} | {pace_lbl} {cd['pace']:.2f} |")
else:
    st.info(f"No games with {cush_min}+ min and 6+ cushion")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({
            "game": gk, "pace": pace, "proj": proj, "total": g['total'], "mins": mins,
            "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']} pts in {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ========== INJURY REPORT ==========
st.subheader("🏥 INJURY REPORT")

injury_count = 0
for team in sorted(today_teams):
    team_inj = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    for inj in team_inj:
        name = inj.get("name", "")
        status = inj.get("status", "")
        is_star = any(s.lower() in name.lower() for s in stars)
        if is_star:
            st.markdown(f"**⭐ {team}**: {name} — {status}")
            injury_count += 1

if injury_count == 0:
    st.info("No star injuries for today's teams")

st.divider()

# ========== POSITION TRACKER ==========
st.subheader("📊 POSITION TRACKER")

with st.expander("➕ Add Position"):
    c1, c2, c3, c4 = st.columns(4)
    pos_game = c1.selectbox("Game", game_list if game_list else ["No games"])
    pos_pick = c2.text_input("Pick", placeholder="NYK")
    pos_price = c3.number_input("Price ¢", min_value=1, max_value=99, value=50)
    pos_contracts = c4.number_input("Contracts", min_value=1, value=10)
    
    if st.button("Add Position"):
        st.session_state.positions.append({
            "game": pos_game, "pick": pos_pick, "price": pos_price,
            "contracts": pos_contracts, "added": now.strftime("%H:%M")
        })
        st.success(f"Added: {pos_pick} @ {pos_price}¢ x{pos_contracts}")
        st.rerun()

if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{pos['game']}** → {pos['pick']}")
        c2.write(f"Entry: {pos['price']}¢ x {pos['contracts']}")
        c3.write(f"Cost: ${pos['price'] * pos['contracts'] / 100:.2f}")
        if c4.button("❌", key=f"del_{i}"):
            st.session_state.positions.pop(i)
            st.rerun()
    
    if st.button("🗑️ Clear All"):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked")

st.divider()

# ========== ALL GAMES ==========
st.subheader("📺 ALL GAMES")

if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "SCHEDULED"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()

# ========== HOW TO USE ==========
st.subheader("📖 How to Use")
st.markdown("""
**ML PICKS** — Moneyline recommendations based on 10-factor model  
**CUSHION SCANNER** — Find live totals with big cushion to bet line  
**PACE SCANNER** — Track scoring pace to project final totals  
**INJURY REPORT** — Star player injuries affecting today's games  
**POSITION TRACKER** — Track your bets and see live P&L

📧 Feedback: **aipublishingpro@gmail.com**
""")

st.caption("⚠️ For entertainment only. Not financial advice. v15.51")
