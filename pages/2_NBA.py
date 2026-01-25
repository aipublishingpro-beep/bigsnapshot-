import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# ============================================================
# AUTH - Use shared auth module
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 24 seconds (1 possession)
st_autorefresh(interval=24000, key="datarefresh")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NBA Edge Finder", "/NBA")

import requests
import json
import os
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "5.1"
LEAGUE_AVG_TOTAL = 225  # NBA league average total

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
    """Fetch today's games from ESPN"""
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
            
            # Calculate minutes played
            minutes_played = 0
            if period > 0:
                if period <= 4:
                    completed_quarters = (period - 1) * 12
                    if clock:
                        try:
                            if ":" in clock:
                                # Format: "11:23" or "1:45"
                                parts = clock.split(":")
                                mins_left = int(parts[0])
                                secs_left = float(parts[1]) if len(parts) > 1 else 0
                            else:
                                # Format: "23.7" (under 1 minute, just seconds)
                                mins_left = 0
                                secs_left = float(clock)
                            minutes_played = completed_quarters + (12 - mins_left - secs_left/60)
                        except:
                            minutes_played = completed_quarters
                else:
                    # Overtime
                    minutes_played = 48 + (period - 4) * 5
            
            games.append({
                "away": away_team,
                "home": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "status": status,
                "period": period,
                "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    """Fetch injury data from ESPN"""
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
    """Fetch teams that played yesterday (for B2B detection)"""
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
    """Extract OUT/DOUBT player names from injury data"""
    names = []
    for inj in team_injuries:
        if isinstance(inj, dict):
            status = str(inj.get("status", "")).upper()
            if "OUT" in status or "DOUBT" in status:
                names.append(inj.get("name", "").lower())
        elif isinstance(inj, str):
            names.append(inj.lower())
    return names

def calc_pregame_edge(away, home, injuries, b2b_teams):
    """Calculate pre-game edge score (50 = neutral, higher = home favored)"""
    home_pts, away_pts = 0, 0
    factors_home, factors_away = [], []
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    # B2B fatigue
    if away in b2b_teams:
        home_pts += 3
        factors_home.append("😴 Away B2B +3")
    if home in b2b_teams:
        away_pts += 2
        factors_away.append("😴 Home B2B +2")
    
    # Injury impact
    home_injuries = injuries.get(home, [])
    away_injuries = injuries.get(away, [])
    home_stars = STAR_PLAYERS.get(home, [])
    away_stars = STAR_PLAYERS.get(away, [])
    
    home_out_names = get_injury_names(home_injuries)
    away_out_names = get_injury_names(away_injuries)
    
    for star in home_stars:
        if any(star.lower() in name for name in home_out_names):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            away_pts += pts
            factors_away.append(f"🏥 {star.split()[-1]} OUT +{pts}")
    
    for star in away_stars:
        if any(star.lower() in name for name in away_out_names):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            home_pts += pts
            factors_home.append(f"🏥 {star.split()[-1]} OUT +{pts}")
    
    # Net rating gap
    home_net = home_stats.get("net", 0)
    away_net = away_stats.get("net", 0)
    net_gap = home_net - away_net
    if net_gap >= 10:
        home_pts += 3
        factors_home.append("📊 Net +10")
    elif net_gap >= 5:
        home_pts += 1.5
        factors_home.append("📊 Net +5")
    elif net_gap <= -10:
        away_pts += 3
        factors_away.append("📊 Net +10")
    elif net_gap <= -5:
        away_pts += 1.5
        factors_away.append("📊 Net +5")
    
    # Home court
    home_pts += 2.5
    factors_home.append("🏠 Home +2.5")
    
    # Elite vs weak
    if away_stats.get("tier") == "elite" and home_stats.get("tier") == "weak":
        away_pts += 2
        factors_away.append("🛫 Elite Road +2")
    
    # Calculate final score
    base = 50 + (net_gap * 1.5)
    base = max(30, min(70, base))
    
    score = base + home_pts - away_pts
    score = max(15, min(85, score))
    
    if score >= 50:
        return home, int(score), factors_home
    else:
        return away, int(100 - score), factors_away

def calc_live_edge(game, injuries, b2b_teams):
    """Calculate live edge based on current score"""
    away, home = game['away'], game['home']
    away_score, home_score = game['away_score'], game['home_score']
    period = game['period']
    mins = game['minutes_played']
    total = game['total_score']
    
    lead = home_score - away_score
    
    pick, pregame_score, factors = calc_pregame_edge(away, home, injuries, b2b_teams)
    
    # PROJECTION FIX - Blend with league average early in game
    if mins >= 8:
        pace = total / mins
        # Weight increases as game progresses (full weight at 24 min)
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
    pace_label = "🔥 FAST" if pace_val > 5.0 else "⚖️ AVG" if pace_val > 4.2 else "🐢 SLOW"
    
    # Live adjustments based on lead
    live_adj = 0
    if abs(lead) >= 20:
        live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15:
        live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10:
        live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5:
        live_adj = 6 if lead > 0 else -6
    
    # Period adjustments
    if period == 4:
        if abs(lead) >= 10:
            live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5:
            live_adj += 8 if lead > 0 else -8
    elif period == 3 and abs(lead) >= 12:
        live_adj += 6 if lead > 0 else -6
    
    final_score = pregame_score + live_adj if pick == home else (100 - pregame_score) + live_adj
    final_score = max(15, min(92, final_score))
    
    if lead > 0:
        live_pick = home
    elif lead < 0:
        live_pick = away
    else:
        live_pick = pick
    
    return {
        "pick": live_pick,
        "score": int(final_score),
        "lead": lead,
        "pace": pace_val,
        "pace_label": pace_label,
        "proj_total": proj_total,
        "factors": factors
    }

# ============================================================
# KALSHI LINK
# ============================================================
# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(away, home):
    """Build correct Kalshi ML market URL"""
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    ticker = f"kxnbagame-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker}"

def get_kalshi_totals_link(away, home):
    """Build correct Kalshi totals market URL"""
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    ticker = f"kxnbatotal-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/kxnbatotal/pro-basketball-total-points/{ticker}"

# ============================================================
# SIDEBAR LEGEND
# ============================================================
with st.sidebar:
    st.header("📖 NBA EDGE GUIDE")
    st.markdown("""
### Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best bets |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |
| **<50** | ⚪ WEAK | Skip |

---
### Injury Tiers
| Tier | Impact | Example |
|------|--------|---------|
| ⭐⭐⭐ | +5 pts | Jokic, SGA |
| ⭐⭐ | +3 pts | Brunson |
| ⭐ | +1 pt | Role player |

---
### Pace Guide
| Pace | Label | Totals |
|------|-------|--------|
| <4.2 | 🐢 SLOW | NO |
| 4.2-4.8 | ⚖️ AVG | Wait |
| 4.8-5.2 | 🔥 FAST | YES |
| >5.2 | 🚀 SHOOTOUT | YES |

---
### How to Trade
1. Check projection
2. Click TOTALS
3. Pick threshold on Kalshi
""")
    st.divider()
    st.caption(f"v{VERSION} NBA EDGE")

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
# UI HEADER
# ============================================================
st.title("🏀 NBA EDGE FINDER")
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
                <div style="color:#fff;font-weight:bold">{stars} {inj['name']} 🔥</div>
                <div style="color:{status_color};font-size:0.85em">{inj['status']} • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No major star injuries for today's games")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.markdown("*Real-time edge updates every 24 seconds.*")
    
    live_with_edge = []
    for g in live_games:
        edge = calc_live_edge(g, injuries, b2b_teams)
        live_with_edge.append((g, edge))
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)
    
    for g, edge in live_with_edge:
        mins = g['minutes_played']
        
        if mins < 6:
            status_label = "⏳ TOO EARLY"
            status_color = "#888"
        elif abs(edge['lead']) < 3:
            status_label = "⚖️ TOO CLOSE"
            status_color = "#ffa500"
        elif edge['score'] >= 70:
            status_label = f"🟢 STRONG {edge['score']}/100"
            status_color = "#22c55e"
        elif edge['score'] >= 60:
            status_label = f"🟢 GOOD {edge['score']}/100"
            status_color = "#22c55e"
        else:
            status_label = f"🟡 {edge['score']}/100"
            status_color = "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        proj = edge['proj_total']
        
        # Totals recommendation based on pace
        if edge['pace'] < 4.2:
            totals_rec = "NO (Under)"
            totals_color = "#22c55e"
            totals_note = f"Pick threshold ABOVE {proj}"
        elif edge['pace'] > 4.8:
            totals_rec = "YES (Over)"
            totals_color = "#f97316"
            totals_note = f"Pick threshold BELOW {proj}"
        else:
            totals_rec = "WAIT"
            totals_color = "#888"
            totals_note = "Pace too neutral"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b; font-size: 0.9em;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #fff; font-size: 1.4em; font-weight: 700;">{g['away_score']} - {g['home_score']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; font-size: 0.9em;">
                Edge: <strong style="color: #fff;">{leader}</strong> ({lead_display}) • {edge['pace_label']} ({edge['pace']:.2f}/min)
            </div>
            <div style="color: #888; font-size: 0.85em; margin-top: 6px;">
                Proj: <b style="color:#fff">{proj}</b> | 
                Totals: <b style="color:{totals_color}">{totals_rec}</b> — {totals_note}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            st.link_button(f"⬇️ BUY NO", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button(f"⬆️ BUY YES", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        
        st.markdown("---")
else:
    st.info("🕐 No live games right now. Check back when games tip off!")

st.divider()

# ============================================================
# 🎯 PROJECTION SCANNER (was Cushion Scanner)
# ============================================================
st.subheader("🎯 PROJECTION SCANNER")
st.caption("Track projected totals - pick your threshold on Kalshi")

proj_min = st.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="proj_min")

proj_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < proj_min or mins <= 0: continue
    
    pace = total / mins
    
    # Use blended projection
    if mins >= 8:
        weight = min(1.0, (mins - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        projected_final = round(blended_pace * 48)
    else:
        projected_final = round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 48) * 0.7)) * 48)
    projected_final = max(185, min(265, projected_final))
    
    if pace < 4.2:
        pace_status, pace_color, rec = "🐢 SLOW", "#00ff00", "Lean NO (Under)"
    elif pace < 4.8:
        pace_status, pace_color, rec = "⚖️ AVG", "#ffff00", "Wait"
    elif pace < 5.2:
        pace_status, pace_color, rec = "🔥 FAST", "#ff8800", "Lean YES (Over)"
    else:
        pace_status, pace_color, rec = "🚀 SHOOTOUT", "#ff0000", "Lean YES (Over)"
    
    proj_results.append({
        'away': g['away'], 'home': g['home'],
        'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'rec': rec,
        'period': g['period'], 'clock': g['clock']
    })

proj_results.sort(key=lambda x: x['pace'])

if proj_results:
    for r in proj_results:
        st.markdown(f"""<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']}">
        <b style="color:#fff">{r['away']} @ {r['home']}</b> 
        <span style="color:#888">Q{r['period']} {r['clock']} • {r['total']}pts/{r['mins']:.0f}min</span>
        <span style="color:{r['pace_color']};font-weight:bold;margin-left:8px">{r['pace']:.2f}/min {r['pace_status']}</span>
        <span style="color:#888;margin-left:8px">Proj: <b style="color:#fff">{r['projected']}</b></span>
        <span style="color:#aaa;margin-left:8px">→ {r['rec']}</span>
        </div>""", unsafe_allow_html=True)
        
        b1, b2 = st.columns(2)
        with b1:
            st.link_button(f"⬇️ BUY NO (above {r['projected']})", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
        with b2:
            st.link_button(f"⬆️ BUY YES (below {r['projected']})", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
else:
    st.info(f"No games with {proj_min}+ minutes played yet")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT
# ============================================================
if scheduled_games:
    st.subheader("🎯 PRE-GAME ALIGNMENT")
    st.markdown("*Look for **70+** scores with multiple factors.*")
    
    games_with_edge = []
    for g in scheduled_games:
        pick, score, factors = calc_pregame_edge(g['away'], g['home'], injuries, b2b_teams)
        games_with_edge.append((g, pick, score, factors))
    games_with_edge.sort(key=lambda x: x[2], reverse=True)
    
    for g, pick, score, factors in games_with_edge:
        if score >= 70:
            score_color, tier, border_color = "#22c55e", "🟢 STRONG", "#22c55e"
        elif score >= 60:
            score_color, tier, border_color = "#22c55e", "🟢 GOOD", "#22c55e"
        elif score >= 50:
            score_color, tier, border_color = "#eab308", "🟡 MODERATE", "#eab308"
        else:
            score_color, tier, border_color = "#888", "⚪ WEAK", "#444"
        
        b2b_away = "😴" if g['away'] in b2b_teams else ""
        b2b_home = "😴" if g['home'] in b2b_teams else ""
        
        st.markdown(f"""
        <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #fff; font-weight: 600;">{b2b_away}{g['away']} @ {g['home']}{b2b_home}</span>
                <span style="color: {score_color}; font-weight: 600;">{tier} {score}/100</span>
            </div>
            <div style="color: #888; font-size: 0.85em; margin-top: 4px;">
                Edge: <strong style="color: #fff;">{pick}</strong> • {' • '.join(factors[:3]) if factors else 'No strong factors'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button(f"🎯 BUY {pick} ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
## 🏀 NBA EDGE FINDER GUIDE

### What This App Does
Finds betting edges for NBA games on Kalshi prediction markets. Tracks live scores, calculates projections, and recommends ML picks and totals directions.

---

### 🏥 INJURY REPORT
Shows star players who are OUT or DOUBTFUL for today's games.
- ⭐⭐⭐ = MVP-level (Jokic, SGA, Giannis) — huge impact
- ⭐⭐ = All-Star level (Brunson, Mitchell) — big impact  
- ⭐ = Quality starter — moderate impact

**How to use:** If a star is OUT, the opposing team gets an edge boost.

---

### 🔴 LIVE EDGE MONITOR
Real-time tracking of games in progress. Updates every 24 seconds.

**Edge Score (0-100):**
| Score | Label | What to Do |
|-------|-------|------------|
| 70+ | 🟢 STRONG | Best opportunities |
| 60-69 | 🟢 GOOD | Worth considering |
| 50-59 | 🟡 MODERATE | Wait for bigger lead |
| <50 | ⚪ WEAK | Skip |

**Pace Label:**
| Pace | Label | Totals Direction |
|------|-------|------------------|
| <4.2 pts/min | 🐢 SLOW | Buy NO (Under) |
| 4.2-4.8 | ⚖️ AVG | Wait |
| 4.8-5.2 | 🔥 FAST | Buy YES (Over) |
| >5.2 | 🚀 SHOOTOUT | Buy YES (Over) |

**Projected Total:** Our estimate of final combined score based on current pace blended with league average (225).

**Totals Recommendation:**
- **NO (Under)** = Game is slow, pick a threshold ABOVE the projection
- **YES (Over)** = Game is fast, pick a threshold BELOW the projection
- **WAIT** = Pace is neutral, don't bet totals yet

**Buttons:**
- 🎯 ML = Moneyline (who wins)
- ⬇️ BUY NO = Opens Kalshi totals page, pick threshold ABOVE projection
- ⬆️ BUY YES = Opens Kalshi totals page, pick threshold BELOW projection

---

### 🎯 PROJECTION SCANNER
Quick view of all live games with pace and projection data.

**How to read:**
- `5.43/min 🔥 FAST` = Scoring pace per minute
- `Proj: 261` = Projected final total
- `→ Lean YES (Over)` = Recommended direction

**How to trade:**
1. Find a game with clear pace direction (SLOW or FAST)
2. Note the projection number
3. Click BUY NO or BUY YES
4. On Kalshi, pick a threshold with cushion:
   - For NO: pick threshold 5-10 points ABOVE projection
   - For YES: pick threshold 5-10 points BELOW projection

---

### 🎯 PRE-GAME ALIGNMENT
Shows scheduled games ranked by edge strength BEFORE tip-off.

**Factors that boost edge:**
- 😴 Back-to-back (B2B) = Team played yesterday, fatigued
- 🏥 Star injuries = Key player OUT
- 📊 Net rating gap = Better team by stats
- 🏠 Home court = +2.5 boost

**How to use:** Look for 70+ scores with multiple factors aligned.

---

### ⚠️ IMPORTANT REMINDERS
- Edge Score ≠ Win Probability
- Projection is an ESTIMATE, not a guarantee
- Always pick thresholds with CUSHION (5-10 pts buffer)
- Only risk what you can afford to lose
- This is educational, not financial advice
""")

st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
