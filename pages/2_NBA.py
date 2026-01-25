import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="nba_refresh")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "6.0"

# ============================================================
# TEAM DATA
# ============================================================
TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"net": -3.2, "pace": 100.5, "tier": "weak"},
    "Boston": {"net": 11.2, "pace": 99.8, "tier": "elite"},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "tier": "weak"},
    "Charlotte": {"net": -6.8, "pace": 99.5, "tier": "weak"},
    "Chicago": {"net": -2.1, "pace": 98.8, "tier": "weak"},
    "Cleveland": {"net": 8.5, "pace": 97.2, "tier": "elite"},
    "Dallas": {"net": 4.2, "pace": 99.0, "tier": "good"},
    "Denver": {"net": 5.8, "pace": 98.5, "tier": "good"},
    "Detroit": {"net": -8.2, "pace": 97.8, "tier": "weak"},
    "Golden State": {"net": 3.5, "pace": 100.2, "tier": "good"},
    "Houston": {"net": 2.8, "pace": 98.0, "tier": "mid"},
    "Indiana": {"net": 1.5, "pace": 102.5, "tier": "mid"},
    "LA Clippers": {"net": 1.2, "pace": 97.5, "tier": "mid"},
    "LA Lakers": {"net": 3.8, "pace": 99.2, "tier": "good"},
    "Memphis": {"net": 2.5, "pace": 100.8, "tier": "mid"},
    "Miami": {"net": 1.8, "pace": 96.8, "tier": "mid"},
    "Milwaukee": {"net": 4.5, "pace": 99.5, "tier": "good"},
    "Minnesota": {"net": 6.2, "pace": 98.2, "tier": "good"},
    "New Orleans": {"net": -1.5, "pace": 99.8, "tier": "weak"},
    "New York": {"net": 5.8, "pace": 97.5, "tier": "good"},
    "Oklahoma City": {"net": 9.8, "pace": 98.8, "tier": "elite"},
    "Orlando": {"net": 3.2, "pace": 96.5, "tier": "mid"},
    "Philadelphia": {"net": 2.5, "pace": 97.8, "tier": "mid"},
    "Phoenix": {"net": 1.8, "pace": 98.5, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 99.0, "tier": "weak"},
    "Sacramento": {"net": -0.5, "pace": 100.5, "tier": "mid"},
    "San Antonio": {"net": -7.5, "pace": 99.8, "tier": "weak"},
    "Toronto": {"net": -2.8, "pace": 98.5, "tier": "weak"},
    "Utah": {"net": -6.2, "pace": 100.2, "tier": "weak"},
    "Washington": {"net": -9.5, "pace": 101.5, "tier": "weak"},
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3,
    "Joel Embiid": 3, "Jayson Tatum": 3, "Stephen Curry": 3, "Kevin Durant": 3, "LeBron James": 3,
    "Anthony Edwards": 3, "Ja Morant": 3, "Donovan Mitchell": 3, "Jaylen Brown": 2, "Anthony Davis": 2,
    "Damian Lillard": 2, "Kyrie Irving": 2, "Jimmy Butler": 2, "Jalen Brunson": 2, "Tyrese Maxey": 2,
}

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

# ============================================================
# ESPN FETCH
# ============================================================
@st.cache_data(ttl=24)
def fetch_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            
            for c in competitors:
                team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), c.get("team", {}).get("displayName", ""))
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            
            minutes_played = 0
            if period > 0:
                completed = (period - 1) * 12
                if clock:
                    try:
                        mins_left = int(clock.split(":")[0])
                        minutes_played = completed + (12 - mins_left)
                    except:
                        minutes_played = completed
            
            games.append({
                "away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score
            })
        return games
    except:
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key: continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
        return injuries
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            for comp in event.get("competitions", []):
                for c in comp.get("competitors", []):
                    team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if team_name: teams.add(team_name)
        return teams
    except:
        return set()

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(team):
    team_map = {
        "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
        "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
        "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
        "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
        "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
        "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
        "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
        "Utah": "UTA", "Washington": "WAS"
    }
    abbrev = team_map.get(team, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnba/nba-regular-season-games?ticker=KXNBA-{today}-{abbrev}"

def get_kalshi_totals_link(away, home):
    team_map = {
        "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
        "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
        "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
        "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
        "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
        "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
        "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
        "Utah": "UTA", "Washington": "WAS"
    }
    away_abbrev = team_map.get(away, "")
    home_abbrev = team_map.get(home, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnbao/nba-total-regular-season-game-points?ticker=KXNBAO-{today}-{away_abbrev}{home_abbrev}"

# ============================================================
# LIVE EDGE CALCULATION
# ============================================================
def calc_live_edge(game, injuries, b2b_teams):
    away, home = game['away'], game['home']
    lead = game['home_score'] - game['away_score']
    minutes = game['minutes_played']
    total = game['total_score']
    period = game['period']
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    net_gap = home_stats.get("net", 0) - away_stats.get("net", 0)
    
    base = 50 + (net_gap * 1.5)
    base = max(25, min(75, base))
    
    if away in b2b_teams: base += 4
    if home in b2b_teams: base -= 4
    
    live_adj = 0
    if abs(lead) >= 20: live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15: live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10: live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5: live_adj = 6 if lead > 0 else -6
    
    if period == 4 and abs(lead) >= 10: live_adj += 15 if lead > 0 else -15
    
    score = base + live_adj
    score = max(10, min(95, score))
    
    pace = round(total / minutes, 2) if minutes > 0 else 0
    pace_label = "🔥 FAST" if pace > 5.0 else "⚖️ AVG" if pace > 4.2 else "🐢 SLOW"
    
    live_pick = home if lead > 0 else away if lead < 0 else home
    proj_total = round((total / minutes) * 48) if minutes >= 6 else 220
    
    return {
        "pick": live_pick, "score": int(score), "lead": lead,
        "pace": pace, "pace_label": pace_label, "proj_total": proj_total
    }

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 NBA EDGE GUIDE")
    st.markdown("""
### Live Edge
| Score | Action |
|-------|--------|
| **70+** | 🟢 STRONG |
| **60-69** | 🟢 GOOD |
| **<60** | Wait |

### Pace
| Pace | Label |
|------|-------|
| <4.2 | 🐢 SLOW |
| 4.2-5.0 | ⚖️ AVG |
| >5.0 | 🔥 FAST |

### Cushion
| Cushion | Safety |
|---------|--------|
| **+15** | 🟢 SAFE |
| **+10** | 🟡 OK |
| **<+10** | ⚠️ RISKY |
""")
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# FETCH ALL DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']

# ============================================================
# HEADER
# ============================================================
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 24s")

c1, c2, c3 = st.columns(3)
c1.metric("Games Today", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("B2B Teams", len(b2b_teams & today_teams))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams: continue
    for inj in team_injuries:
        name = inj.get("name", "")
        status = str(inj.get("status", "")).upper()
        if "OUT" in status or "DOUBT" in status:
            tier = STAR_TIERS.get(name, 0)
            if tier > 0:
                injured_stars.append({"name": name, "team": team, "status": "OUT" if "OUT" in status else "DOUBT", "tier": tier})

injured_stars.sort(key=lambda x: -x['tier'])

if injured_stars:
    cols = st.columns(3)
    for i, inj in enumerate(injured_stars):
        with cols[i % 3]:
            stars = "⭐" * inj['tier']
            color = "#ff4444" if inj['status'] == "OUT" else "#ffaa00"
            st.markdown(f"""<div style="background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid {color};margin-bottom:6px">
                <div style="color:#fff;font-weight:bold">{stars} {inj['name']}</div>
                <div style="color:{color};font-size:0.85em">{inj['status']} • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)

b2b_today = b2b_teams & today_teams
if b2b_today:
    st.markdown(f"**🏨 B2B Teams:** {', '.join(sorted(b2b_today))}")

if not injured_stars and not b2b_today:
    st.info("No major injuries or B2B teams today")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    
    for g in live_games:
        edge = calc_live_edge(g, injuries, b2b_teams)
        mins = g['minutes_played']
        
        if mins < 6:
            status_label, status_color = "⏳ TOO EARLY", "#888"
        elif edge['score'] >= 70:
            status_label, status_color = f"🟢 STRONG {edge['score']}", "#22c55e"
        elif edge['score'] >= 60:
            status_label, status_color = f"🟢 GOOD {edge['score']}", "#22c55e"
        else:
            status_label, status_color = f"🟡 {edge['score']}", "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        safe_no = edge['proj_total'] + 12
        safe_yes = edge['proj_total'] - 8
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="color: #fff; font-size: 1.4em; font-weight: 700;">{g['away_score']} - {g['home_score']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; margin-bottom: 10px;">
                Edge: <strong style="color: #fff;">{leader}</strong> ({lead_display}) {edge['pace_label']}
            </div>
            <div style="background: #333; border-radius: 8px; padding: 10px;">
                <span style="color: #888;">Proj: {edge['proj_total']}</span> | 
                <span style="color: #22c55e;">NO {safe_no}</span> | 
                <span style="color: #f97316;">YES {safe_yes}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(edge['pick']), use_container_width=True)
        with bc2:
            st.link_button(f"⬇️ NO {safe_no}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button(f"⬆️ YES {safe_yes}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
else:
    st.info("🕐 No live games right now.")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15], index=0)
cush_side = cs2.selectbox("Side", ["NO", "YES"])

cush_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < cush_min or mins <= 0: continue
    
    pace = total / mins
    remaining = max(48 - mins, 1)
    projected = round(total + pace * remaining)
    
    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected
    else:
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected), 0)
        safe_idx = max(base_idx - 2, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected - safe_line
    
    if cushion < 6: continue
    
    pace_ok = (cush_side == "NO" and pace < 4.5) or (cush_side == "YES" and pace > 4.8)
    pace_color = "#00ff00" if pace_ok else "#ff8800"
    
    cush_results.append({
        'away': g['away'], 'home': g['home'], 'total': total, 'mins': mins,
        'pace': pace, 'pace_color': pace_color, 'projected': projected,
        'cushion': cushion, 'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

if cush_results:
    for r in cush_results:
        st.markdown(f"""<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']}">
        <b style="color:#fff">{r['away']} @ {r['home']}</b> 
        <span style="color:#888">Q{r['period']} • Proj: {r['projected']}</span>
        <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:8px">🎯 {r['safe_line']}</span>
        <span style="color:#00ff00;font-weight:bold;margin-left:8px">+{r['cushion']:.0f}</span>
        </div>""", unsafe_allow_html=True)
        st.link_button(f"BUY {cush_side} {r['safe_line']}", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")

pace_data = []
for g in live_games:
    mins = g['minutes_played']
    if mins >= 6:
        pace = round(g['total_score'] / mins, 2)
        pace_data.append({
            "away": g['away'], "home": g['home'],
            "pace": pace, "proj": round(pace * 48),
            "total": g['total_score'], "mins": mins,
            "period": g['period'], "clock": g['clock']
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.2:
            lbl, clr = "🐢 SLOW", "#00ff00"
        elif p['pace'] < 4.8:
            lbl, clr = "⚖️ AVG", "#ffff00"
        elif p['pace'] < 5.2:
            lbl, clr = "🔥 FAST", "#ff8800"
        else:
            lbl, clr = "🚀 SHOOTOUT", "#ff0000"
        
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr}">
        <b style="color:#fff">{p['away']} @ {p['home']}</b>
        <span style="color:#666;margin-left:10px">Q{p['period']} {p['clock']}</span>
        <span style="color:{clr};font-weight:bold;margin-left:10px">{p['pace']}/min {lbl}</span>
        <span style="color:#888;margin-left:10px">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ============================================================
# 📅 SCHEDULED GAMES
# ============================================================
if scheduled_games:
    st.subheader("📅 SCHEDULED GAMES")
    for g in scheduled_games:
        home_stats = TEAM_STATS.get(g['home'], {})
        away_stats = TEAM_STATS.get(g['away'], {})
        home_net = home_stats.get("net", 0)
        away_net = away_stats.get("net", 0)
        
        st.markdown(f"""
        <div style="background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <span style="color: #fff; font-weight: 600;">{g['away']} @ {g['home']}</span>
            <span style="color: #888; margin-left: 15px;">Net: {g['home']} ({home_net:+.1f}) vs {g['away']} ({away_net:+.1f})</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
