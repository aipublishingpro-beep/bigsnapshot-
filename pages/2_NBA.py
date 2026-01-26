import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

# ============================================================
# AUTH
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 24 seconds
st_autorefresh(interval=24000, key="datarefresh")

# ============================================================
# GA4 ANALYTICS
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "7.0"
LEAGUE_AVG_TOTAL = 225

# ============================================================
# INITIALIZE SESSION STATE FOR POSITION TRACKER
# ============================================================
if 'positions' not in st.session_state:
    st.session_state.positions = []

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
    "Atlanta": {"net": -3.2, "pace": 100.5, "home_pct": 0.52, "tier": "weak"},
    "Boston": {"net": 11.2, "pace": 99.8, "home_pct": 0.78, "tier": "elite"},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "home_pct": 0.42, "tier": "weak"},
    "Charlotte": {"net": -6.8, "pace": 99.5, "home_pct": 0.38, "tier": "weak"},
    "Chicago": {"net": -2.1, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Cleveland": {"net": 8.5, "pace": 97.2, "home_pct": 0.75, "tier": "elite"},
    "Dallas": {"net": 4.2, "pace": 99.0, "home_pct": 0.62, "tier": "good"},
    "Denver": {"net": 5.8, "pace": 98.5, "home_pct": 0.72, "tier": "good"},
    "Detroit": {"net": -8.2, "pace": 97.8, "home_pct": 0.32, "tier": "weak"},
    "Golden State": {"net": 2.5, "pace": 100.2, "home_pct": 0.58, "tier": "mid"},
    "Houston": {"net": -1.5, "pace": 99.5, "home_pct": 0.55, "tier": "mid"},
    "Indiana": {"net": 3.8, "pace": 102.5, "home_pct": 0.58, "tier": "good"},
    "LA Clippers": {"net": 1.2, "pace": 97.8, "home_pct": 0.52, "tier": "mid"},
    "LA Lakers": {"net": 2.8, "pace": 98.5, "home_pct": 0.62, "tier": "mid"},
    "Memphis": {"net": 1.5, "pace": 99.8, "home_pct": 0.55, "tier": "mid"},
    "Miami": {"net": 0.5, "pace": 97.2, "home_pct": 0.58, "tier": "mid"},
    "Milwaukee": {"net": 4.5, "pace": 98.8, "home_pct": 0.65, "tier": "good"},
    "Minnesota": {"net": 5.2, "pace": 98.2, "home_pct": 0.68, "tier": "good"},
    "New Orleans": {"net": -2.8, "pace": 99.0, "home_pct": 0.48, "tier": "weak"},
    "New York": {"net": 6.8, "pace": 97.5, "home_pct": 0.72, "tier": "good"},
    "Oklahoma City": {"net": 9.5, "pace": 98.8, "home_pct": 0.78, "tier": "elite"},
    "Orlando": {"net": 2.2, "pace": 96.8, "home_pct": 0.58, "tier": "mid"},
    "Philadelphia": {"net": 1.8, "pace": 97.5, "home_pct": 0.55, "tier": "mid"},
    "Phoenix": {"net": 0.8, "pace": 98.2, "home_pct": 0.52, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 98.8, "home_pct": 0.42, "tier": "weak"},
    "Sacramento": {"net": -1.2, "pace": 100.5, "home_pct": 0.52, "tier": "mid"},
    "San Antonio": {"net": -8.5, "pace": 99.2, "home_pct": 0.35, "tier": "weak"},
    "Toronto": {"net": -3.8, "pace": 97.8, "home_pct": 0.45, "tier": "weak"},
    "Utah": {"net": -6.2, "pace": 98.5, "home_pct": 0.38, "tier": "weak"},
    "Washington": {"net": -9.5, "pace": 100.8, "home_pct": 0.28, "tier": "weak"},
}

STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns", "Mikal Bridges"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Golden State": ["Stephen Curry", "Draymond Green"],
    "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "LA Clippers": ["Kawhi Leonard", "James Harden"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Houston": ["Jalen Green", "Alperen Sengun"],
    "Atlanta": ["Trae Young", "Dejounte Murray"],
    "Chicago": ["Zach LaVine", "Coby White"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"],
    "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Brooklyn": ["Cam Thomas", "Mikal Bridges"],
    "San Antonio": ["Victor Wembanyama", "Devin Vassell"],
    "Utah": ["Lauri Markkanen", "Collin Sexton"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"],
    "Washington": ["Jordan Poole", "Kyle Kuzma"],
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3,
    "Luka Doncic": 3, "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3,
    "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3,
    "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2, "Jimmy Butler": 2,
    "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2,
    "Trae Young": 2, "Zion Williamson": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2,
    "Jalen Brunson": 2, "Chet Holmgren": 2, "Paolo Banchero": 2, "Franz Wagner": 2,
    "Victor Wembanyama": 2, "Evan Mobley": 2, "LaMelo Ball": 2, "Cade Cunningham": 2,
    "Tyrese Maxey": 2, "Bam Adebayo": 2, "Karl-Anthony Towns": 2,
}

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=30)
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
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
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
                if period <= 4:
                    completed_quarters = (period - 1) * 12
                    if clock:
                        try:
                            if ":" in clock:
                                parts = clock.split(":")
                                mins_left = int(parts[0])
                                secs_left = float(parts[1]) if len(parts) > 1 else 0
                            else:
                                mins_left = 0
                                secs_left = float(clock)
                            minutes_played = completed_quarters + (12 - mins_left - secs_left/60)
                        except:
                            minutes_played = completed_quarters
                else:
                    minutes_played = 48 + (period - 4) * 5
            
            games.append({
                "away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played, "total_score": home_score + away_score
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
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
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
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
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_injury_names(team_injuries):
    names = []
    for inj in team_injuries:
        if isinstance(inj, dict):
            status = str(inj.get("status", "")).upper()
            if "OUT" in status or "DOUBT" in status:
                names.append(inj.get("name", "").lower())
        elif isinstance(inj, str):
            names.append(inj.lower())
    return names

def calc_live_edge(game, injuries, b2b_teams):
    away, home = game['away'], game['home']
    away_score, home_score = game['away_score'], game['home_score']
    period = game['period']
    mins = game['minutes_played']
    total = game['total_score']
    
    lead = home_score - away_score
    
    # Base from net rating
    home_net = TEAM_STATS.get(home, {}).get("net", 0)
    away_net = TEAM_STATS.get(away, {}).get("net", 0)
    base = 50 + ((home_net - away_net) * 1.5) + 2.5  # home court
    
    # B2B
    if away in b2b_teams: base += 3
    if home in b2b_teams: base -= 2
    
    # Injuries
    home_out = get_injury_names(injuries.get(home, []))
    away_out = get_injury_names(injuries.get(away, []))
    for star in STAR_PLAYERS.get(home, []):
        if any(star.lower() in n for n in home_out):
            base -= STAR_TIERS.get(star, 1) * 2
    for star in STAR_PLAYERS.get(away, []):
        if any(star.lower() in n for n in away_out):
            base += STAR_TIERS.get(star, 1) * 2
    
    # Projection
    if mins >= 8:
        pace = total / mins
        weight = min(1.0, (mins - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        proj_total = round(blended_pace * 48)
        proj_total = max(185, min(265, proj_total))
    elif mins >= 6:
        pace = total / mins
        proj_total = round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 48) * 0.7)) * 48)
        proj_total = max(185, min(265, proj_total))
    else:
        pace = 0
        proj_total = LEAGUE_AVG_TOTAL
    
    pace_val = round(total / mins, 2) if mins > 0 else 0
    pace_label = "🚀 SHOOTOUT" if pace_val > 5.2 else "🔥 FAST" if pace_val > 4.8 else "⚖️ AVG" if pace_val > 4.2 else "🐢 SLOW"
    
    # Live adjustments
    live_adj = 0
    if abs(lead) >= 20: live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15: live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10: live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5: live_adj = 6 if lead > 0 else -6
    
    if period == 4:
        if abs(lead) >= 10: live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5: live_adj += 8 if lead > 0 else -8
    elif period == 3 and abs(lead) >= 12:
        live_adj += 6 if lead > 0 else -6
    
    final_score = base + live_adj
    final_score = max(15, min(92, final_score))
    
    if lead > 0: live_pick = home
    elif lead < 0: live_pick = away
    else: live_pick = home if base >= 50 else away
    
    # Cushion calculation
    cushion_under = proj_total + 8
    cushion_over = proj_total - 8
    
    return {
        "pick": live_pick, "score": int(final_score), "lead": lead,
        "pace": pace_val, "pace_label": pace_label, "proj_total": proj_total,
        "cushion_under": cushion_under, "cushion_over": cushion_over
    }

def calc_pregame_edge(away, home, injuries, b2b_teams):
    home_net = TEAM_STATS.get(home, {}).get("net", 0)
    away_net = TEAM_STATS.get(away, {}).get("net", 0)
    base = 50 + ((home_net - away_net) * 1.5) + 2.5
    
    if away in b2b_teams: base += 3
    if home in b2b_teams: base -= 2
    
    home_out = get_injury_names(injuries.get(home, []))
    away_out = get_injury_names(injuries.get(away, []))
    for star in STAR_PLAYERS.get(home, []):
        if any(star.lower() in n for n in home_out):
            base -= STAR_TIERS.get(star, 1) * 2
    for star in STAR_PLAYERS.get(away, []):
        if any(star.lower() in n for n in away_out):
            base += STAR_TIERS.get(star, 1) * 2
    
    base = max(15, min(85, base))
    pick = home if base >= 50 else away
    score = int(base) if base >= 50 else int(100 - base)
    
    return pick, score

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{date_str}{away_code}{home_code}"

def get_kalshi_totals_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbatotal/pro-basketball-total-points/kxnbatotal-{date_str}{away_code}{home_code}"

def get_kalshi_spread_link(away, home, line=1.5):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    if line > 0:
        return f"https://kalshi.com/markets/kxnbasprd/pro-basketball-spread/kxnbasprd-{date_str}{home_code}{away_code}ovr{abs(line)}"
    else:
        return f"https://kalshi.com/markets/kxnbasprd/pro-basketball-spread/kxnbasprd-{date_str}{away_code}{home_code}ovr{abs(line)}"

# ============================================================
# POSITION TRACKER FUNCTIONS
# ============================================================
def add_position(game_key, pick, bet_type, link):
    pos = {"game": game_key, "pick": pick, "type": bet_type, "link": link, "id": str(uuid.uuid4())[:8]}
    st.session_state.positions.append(pos)

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

def clear_all_positions():
    st.session_state.positions = []

# ============================================================
# SIDEBAR LEGEND
# ============================================================
with st.sidebar:
    st.header("📖 BIGSNAPSHOT EDGE GUIDE")
    st.markdown("""
### Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best edge |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |
| **<50** | ⚪ WEAK | Skip |

---
### Injury Tiers
| Tier | Impact | Example |
|------|--------|---------|
| ⭐⭐⭐ | Major | Jokic, SGA |
| ⭐⭐ | Big | Brunson |
| ⭐ | Moderate | Role player |

---
### Pace Guide
| Pace | Label | Totals |
|------|-------|--------|
| <4.2 | 🐢 SLOW | BUY NO |
| 4.2-4.8 | ⚖️ AVG | Wait |
| 4.8-5.2 | 🔥 FAST | BUY YES |
| >5.2 | 🚀 SHOOTOUT | BUY YES |

---
### Cushion Rule
Always add **8 pts** buffer to projection for safer threshold picks.
""")
    st.divider()
    st.caption(f"v{VERSION} BIGSNAPSHOT")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# ============================================================
# HEADER
# ============================================================
st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 24s")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams: continue
    for inj in team_injuries:
        name = inj.get("name", "") if isinstance(inj, dict) else str(inj)
        status = str(inj.get("status", "")).upper() if isinstance(inj, dict) else "OUT"
        if "OUT" in status or "DOUBT" in status:
            tier = STAR_TIERS.get(name, 0)
            if tier == 0:
                for star_name in STAR_TIERS:
                    if star_name.lower() in name.lower():
                        tier = STAR_TIERS[star_name]
                        break
            if tier > 0:
                injured_stars.append({"name": name, "team": team, "status": "OUT" if "OUT" in status else "DOUBT", "tier": tier})

injured_stars.sort(key=lambda x: (-x['tier'], x['team']))

if injured_stars:
    cols = st.columns(3)
    for i, inj in enumerate(injured_stars):
        with cols[i % 3]:
            stars = "⭐" * inj['tier']
            status_color = "#ff4444" if inj['status'] == "OUT" else "#ffaa00"
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#2a1a2a);padding:10px;border-radius:6px;border-left:3px solid {status_color};margin-bottom:6px">
                <div style="color:#fff;font-weight:bold">{stars} {inj['name']}</div>
                <div style="color:{status_color};font-size:0.85em">{inj['status']} • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No major star injuries for today's games")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR (MAIN VISUAL)
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.caption("Real-time updates every 24 seconds • Click ➕ to track positions")
    
    live_with_edge = [(g, calc_live_edge(g, injuries, b2b_teams)) for g in live_games]
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)
    
    for g, edge in live_with_edge:
        mins = g['minutes_played']
        game_key = f"{g['away']}@{g['home']}"
        
        if mins < 6:
            status_label, status_color = "⏳ TOO EARLY", "#888"
        elif abs(edge['lead']) < 3:
            status_label, status_color = "⚖️ TOO CLOSE", "#ffa500"
        elif edge['score'] >= 70:
            status_label, status_color = f"🟢 STRONG {edge['score']}", "#22c55e"
        elif edge['score'] >= 60:
            status_label, status_color = f"🟢 GOOD {edge['score']}", "#22c55e"
        else:
            status_label, status_color = f"🟡 {edge['score']}", "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        # Totals recommendation
        if edge['pace'] < 4.2:
            totals_rec = f"BUY NO above {edge['cushion_under']}"
            totals_color = "#22c55e"
        elif edge['pace'] > 4.8:
            totals_rec = f"BUY YES below {edge['cushion_over']}"
            totals_color = "#f97316"
        else:
            totals_rec = "WAIT - pace neutral"
            totals_color = "#888"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 8px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b; font-size: 0.9em;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #fff; font-size: 1.4em; font-weight: 700;">{g['away_score']} - {g['home_score']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; font-size: 0.9em;">
                Edge: <strong style="color: #fff;">{leader}</strong> ({lead_display}) • {edge['pace_label']} ({edge['pace']:.2f}/min) • Proj: <b>{edge['proj_total']}</b>
            </div>
            <div style="color: {totals_color}; font-size: 0.85em; margin-top: 6px;">
                📊 {totals_rec}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Buttons row
        bc1, bc2, bc3, bc4, bc5, bc6 = st.columns(6)
        with bc1:
            st.link_button("🎯 ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            st.link_button("+1.5", get_kalshi_spread_link(g['away'], g['home'], 1.5), use_container_width=True)
        with bc3:
            st.link_button("-1.5", get_kalshi_spread_link(g['away'], g['home'], -1.5), use_container_width=True)
        with bc4:
            st.link_button("⬇️ NO", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc5:
            st.link_button("⬆️ YES", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc6:
            if st.button("➕ Track", key=f"add_live_{game_key}"):
                add_position(game_key, edge['pick'], "ML", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()
        
        st.markdown("---")
else:
    st.info("🕐 No live games right now. Check back when games tip off!")

st.divider()

# ============================================================
# 📊 POSITION TRACKER
# ============================================================
st.subheader("📊 POSITION TRACKER")

if st.session_state.positions:
    for pos in st.session_state.positions:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 1])
        with pc1:
            st.write(f"**{pos['game']}**")
        with pc2:
            st.write(f"{pos['pick']} ({pos['type']})")
        with pc3:
            st.link_button("🔗 Buy", pos['link'], use_container_width=True)
        with pc4:
            if st.button("❌", key=f"del_{pos['id']}"):
                remove_position(pos['id'])
                st.rerun()
    
    if st.button("🗑️ Clear All Positions"):
        clear_all_positions()
        st.rerun()
else:
    st.caption("No positions tracked. Click ➕ Track on any game to add.")

st.divider()

# ============================================================
# 🎯 PACE SCANNER (SEPARATE VISUAL)
# ============================================================
st.subheader("🎯 PACE SCANNER")
st.caption("Track projected totals with cushion recommendations")

proj_min = st.selectbox("Min minutes played", [6, 9, 12, 15, 18], index=0, key="proj_min")

proj_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < proj_min or mins <= 0: continue
    
    edge = calc_live_edge(g, injuries, b2b_teams)
    proj_results.append({
        'away': g['away'], 'home': g['home'],
        'total': total, 'mins': mins, 'pace': edge['pace'],
        'pace_label': edge['pace_label'],
        'proj': edge['proj_total'],
        'cushion_under': edge['cushion_under'],
        'cushion_over': edge['cushion_over'],
        'period': g['period'], 'clock': g['clock']
    })

proj_results.sort(key=lambda x: x['pace'])

if proj_results:
    for r in proj_results:
        if r['pace'] < 4.2:
            pace_color, rec = "#00ff00", f"🐢 SLOW → BUY NO above {r['cushion_under']}"
        elif r['pace'] < 4.8:
            pace_color, rec = "#ffff00", "⚖️ AVG → WAIT"
        elif r['pace'] < 5.2:
            pace_color, rec = "#ff8800", f"🔥 FAST → BUY YES below {r['cushion_over']}"
        else:
            pace_color, rec = "#ff0000", f"🚀 SHOOTOUT → BUY YES below {r['cushion_over']}"
        
        st.markdown(f"""<div style="background:#0f172a;padding:12px 14px;margin-bottom:8px;border-radius:8px;border-left:4px solid {pace_color}">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <b style="color:#fff;font-size:1.05em">{r['away']} @ {r['home']}</b>
            <span style="color:#888">Q{r['period']} {r['clock']}</span>
        </div>
        <div style="color:#aaa;margin-top:6px">
            {r['total']} pts in {r['mins']:.0f} min • <span style="color:{pace_color};font-weight:bold">{r['pace']:.2f}/min {r['pace_label']}</span> • Proj: <b style="color:#fff">{r['proj']}</b>
        </div>
        <div style="color:{pace_color};margin-top:6px;font-weight:600">
            {rec}
        </div>
        </div>""", unsafe_allow_html=True)
        
        b1, b2, b3 = st.columns(3)
        with b1:
            st.link_button(f"⬇️ BUY NO (>{r['cushion_under']})", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
        with b2:
            st.link_button(f"⬆️ BUY YES (<{r['cushion_over']})", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
        with b3:
            game_key = f"{r['away']}@{r['home']}"
            if st.button("➕ Track", key=f"add_pace_{game_key}"):
                add_position(game_key, "Totals", "TOTAL", get_kalshi_totals_link(r['away'], r['home']))
                st.rerun()
else:
    st.info(f"No games with {proj_min}+ minutes played yet")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT (DE-EMPHASIZED)
# ============================================================
if scheduled_games:
    with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=False):
        st.caption("⚠️ Pre-game picks are speculative. Live edges are more reliable.")
        
        games_with_edge = [(g, *calc_pregame_edge(g['away'], g['home'], injuries, b2b_teams)) for g in scheduled_games]
        games_with_edge.sort(key=lambda x: x[2], reverse=True)
        
        for g, pick, score in games_with_edge:
            if score >= 70:
                score_color, border_color = "#22c55e", "#22c55e"
            elif score >= 60:
                score_color, border_color = "#22c55e", "#22c55e"
            elif score >= 50:
                score_color, border_color = "#eab308", "#eab308"
            else:
                score_color, border_color = "#888", "#444"
            
            b2b_away = "😴" if g['away'] in b2b_teams else ""
            b2b_home = "😴" if g['home'] in b2b_teams else ""
            game_key = f"{g['away']}@{g['home']}"
            
            st.markdown(f"""
            <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #fff; font-weight: 600;">{b2b_away}{g['away']} @ {g['home']}{b2b_home}</span>
                    <span style="color: {score_color}; font-weight: 600;">{score}/100 → {pick}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(6)
            cols[0].link_button(f"🎯 {pick}", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
            cols[1].link_button("+1.5", get_kalshi_spread_link(g['away'], g['home'], 1.5), use_container_width=True)
            cols[2].link_button("-1.5", get_kalshi_spread_link(g['away'], g['home'], -1.5), use_container_width=True)
            cols[3].link_button("Over", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
            cols[4].link_button("Under", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
            if cols[5].button("➕", key=f"add_pre_{game_key}"):
                add_position(game_key, pick, "ML", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE BIGSNAPSHOT NBA EDGE FINDER", expanded=False):
    st.markdown(f"""
## 🏀 BIGSNAPSHOT NBA EDGE FINDER v{VERSION}

### Focus: LIVE EDGES
Pre-game picks are speculative. **Real edges appear during live games** when:
- Market hasn't adjusted to the score yet
- Pace tells you where totals are heading
- Lead + quarter = high confidence

---

### 🔴 LIVE EDGE MONITOR
| Score | Label | Action |
|-------|-------|--------|
| 70+ | 🟢 STRONG | Best edge |
| 60-69 | 🟢 GOOD | Worth it |
| 50-59 | 🟡 MODERATE | Wait |
| <50 | ⚪ WEAK | Skip |

**Wait for 6+ minutes** before trusting the edge.

---

### 🎯 PACE SCANNER (Totals)
| Pace | Label | Action |
|------|-------|--------|
| <4.2 | 🐢 SLOW | BUY NO above cushion |
| 4.2-4.8 | ⚖️ AVG | WAIT |
| 4.8-5.2 | 🔥 FAST | BUY YES below cushion |
| >5.2 | 🚀 SHOOTOUT | BUY YES below cushion |

**Cushion = 8 points buffer** for safer threshold picks.

---

### 📊 POSITION TRACKER
- Click ➕ Track to add any pick
- Direct Kalshi buy links
- Clear all when done

---

### ⚠️ REMEMBER
- Edge Score ≠ Win Probability
- Only risk what you can afford
- Educational only, not financial advice

**Stay small. Stay quiet. Win.**
""")

st.caption(f"⚠️ Educational only. Not financial advice. BigSnapshot v{VERSION}")
st.caption("Stay small. Stay quiet. Win.")
