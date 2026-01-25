import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

# ============================================================
# AUTH - Use shared auth module
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="nfl_refresh")

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

send_ga4_event("NFL Edge Finder", "/NFL")

import requests
import json
import os
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "19.0"

# ============================================================
# TEAM DATA
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

TEAM_STATS = {
    "ARI": {"net": -12.5, "pace": 24.2, "home_pct": 0.42, "tier": "weak"},
    "ATL": {"net": 2.5, "pace": 25.8, "home_pct": 0.55, "tier": "mid"},
    "BAL": {"net": 15.5, "pace": 27.2, "home_pct": 0.72, "tier": "elite"},
    "BUF": {"net": 18.2, "pace": 26.5, "home_pct": 0.78, "tier": "elite"},
    "CAR": {"net": -18.5, "pace": 21.5, "home_pct": 0.35, "tier": "weak"},
    "CHI": {"net": -8.5, "pace": 22.8, "home_pct": 0.45, "tier": "weak"},
    "CIN": {"net": 5.8, "pace": 25.2, "home_pct": 0.58, "tier": "good"},
    "CLE": {"net": -25.0, "pace": 20.5, "home_pct": 0.38, "tier": "weak"},
    "DAL": {"net": -5.2, "pace": 24.0, "home_pct": 0.52, "tier": "mid"},
    "DEN": {"net": 8.5, "pace": 23.8, "home_pct": 0.65, "tier": "good"},
    "DET": {"net": 22.5, "pace": 28.5, "home_pct": 0.78, "tier": "elite"},
    "GB": {"net": 12.2, "pace": 25.5, "home_pct": 0.70, "tier": "elite"},
    "HOU": {"net": 10.5, "pace": 24.8, "home_pct": 0.68, "tier": "good"},
    "IND": {"net": -2.5, "pace": 23.5, "home_pct": 0.55, "tier": "mid"},
    "JAX": {"net": -8.5, "pace": 22.2, "home_pct": 0.45, "tier": "weak"},
    "KC": {"net": 18.5, "pace": 26.8, "home_pct": 0.82, "tier": "elite"},
    "LV": {"net": -10.2, "pace": 22.5, "home_pct": 0.42, "tier": "weak"},
    "LAC": {"net": 11.8, "pace": 24.5, "home_pct": 0.62, "tier": "good"},
    "LAR": {"net": 8.5, "pace": 25.0, "home_pct": 0.62, "tier": "good"},
    "MIA": {"net": -2.5, "pace": 26.0, "home_pct": 0.55, "tier": "mid"},
    "MIN": {"net": 12.5, "pace": 25.2, "home_pct": 0.68, "tier": "elite"},
    "NE": {"net": -12.5, "pace": 21.8, "home_pct": 0.42, "tier": "weak"},
    "NO": {"net": -8.8, "pace": 23.0, "home_pct": 0.48, "tier": "weak"},
    "NYG": {"net": -15.5, "pace": 21.2, "home_pct": 0.35, "tier": "weak"},
    "NYJ": {"net": -6.5, "pace": 22.5, "home_pct": 0.45, "tier": "weak"},
    "PHI": {"net": 14.8, "pace": 26.2, "home_pct": 0.75, "tier": "elite"},
    "PIT": {"net": 4.8, "pace": 23.8, "home_pct": 0.62, "tier": "mid"},
    "SF": {"net": -4.5, "pace": 24.5, "home_pct": 0.52, "tier": "mid"},
    "SEA": {"net": 6.5, "pace": 25.0, "home_pct": 0.62, "tier": "good"},
    "TB": {"net": 5.8, "pace": 24.8, "home_pct": 0.58, "tier": "good"},
    "TEN": {"net": -14.8, "pace": 21.5, "home_pct": 0.40, "tier": "weak"},
    "WAS": {"net": 8.5, "pace": 25.5, "home_pct": 0.62, "tier": "good"},
}

STAR_PLAYERS = {
    "BAL": ["Lamar Jackson", "Derrick Henry"],
    "BUF": ["Josh Allen", "James Cook"],
    "KC": ["Patrick Mahomes", "Travis Kelce"],
    "DET": ["Jared Goff", "Amon-Ra St. Brown", "Jahmyr Gibbs"],
    "PHI": ["Jalen Hurts", "Saquon Barkley", "AJ Brown"],
    "MIN": ["Sam Darnold", "Justin Jefferson"],
    "GB": ["Jordan Love", "Josh Jacobs"],
    "SF": ["Brock Purdy", "Christian McCaffrey"],
    "DAL": ["Dak Prescott", "CeeDee Lamb"],
    "MIA": ["Tua Tagovailoa", "Tyreek Hill"],
    "CIN": ["Joe Burrow", "Ja'Marr Chase"],
    "LAC": ["Justin Herbert", "JK Dobbins"],
    "HOU": ["CJ Stroud", "Nico Collins"],
    "DEN": ["Bo Nix", "Javonte Williams"],
    "SEA": ["Geno Smith", "DK Metcalf"],
    "TB": ["Baker Mayfield", "Mike Evans"],
    "LAR": ["Matthew Stafford", "Puka Nacua"],
    "WAS": ["Jayden Daniels", "Terry McLaurin"],
    "ATL": ["Kirk Cousins", "Bijan Robinson"],
    "PIT": ["Russell Wilson", "Najee Harris"],
    "IND": ["Anthony Richardson", "Jonathan Taylor"],
    "ARI": ["Kyler Murray", "Marvin Harrison Jr"],
    "CHI": ["Caleb Williams", "DJ Moore"],
    "JAX": ["Trevor Lawrence", "Travis Etienne"],
    "NYJ": ["Aaron Rodgers", "Breece Hall"],
    "LV": ["Aidan O'Connell", "Brock Bowers"],
    "NE": ["Drake Maye", "Rhamondre Stevenson"],
    "NYG": ["Daniel Jones", "Malik Nabers"],
    "NO": ["Derek Carr", "Alvin Kamara"],
    "CAR": ["Bryce Young", "Chuba Hubbard"],
    "CLE": ["Deshaun Watson", "Nick Chubb"],
    "TEN": ["Will Levis", "Tony Pollard"],
}

STAR_TIERS = {
    "Patrick Mahomes": 3, "Josh Allen": 3, "Lamar Jackson": 3, "Jalen Hurts": 3, "Joe Burrow": 3,
    "Travis Kelce": 2, "Tyreek Hill": 2, "Justin Jefferson": 2, "CeeDee Lamb": 2, "Ja'Marr Chase": 2,
    "Derrick Henry": 2, "Saquon Barkley": 2, "Christian McCaffrey": 2,
    "AJ Brown": 2, "Amon-Ra St. Brown": 2, "DK Metcalf": 2, "Puka Nacua": 2,
    "Justin Herbert": 2, "CJ Stroud": 2, "Jayden Daniels": 2, "Jared Goff": 2,
    "Brock Purdy": 1, "Jordan Love": 1, "Dak Prescott": 1, "Tua Tagovailoa": 1,
    "Matthew Stafford": 1, "Baker Mayfield": 1, "Geno Smith": 1, "Kirk Cousins": 1,
}

# NFL totals thresholds (different from NBA)
THRESHOLDS = [37.5, 40.5, 43.5, 45.5, 47.5, 49.5, 51.5, 54.5, 57.5]

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=30)
def fetch_games():
    """Fetch today's games from ESPN"""
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={today}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        
        # If no games today, check upcoming week
        if not data.get("events"):
            for days_ahead in range(1, 8):
                future_date = (datetime.now(eastern) + timedelta(days=days_ahead)).strftime('%Y%m%d')
                url2 = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={future_date}"
                try:
                    resp2 = requests.get(url2, timeout=5)
                    data2 = resp2.json()
                    if data2.get("events"):
                        data = data2
                        break
                except:
                    continue
        
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team = abbr
                    home_score = score
                else:
                    away_team = abbr
                    away_score = score
            
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            
            # Calculate minutes played (NFL: 15 min quarters)
            minutes_played = 0
            if period > 0:
                completed_quarters = (period - 1) * 15
                if clock:
                    try:
                        parts = clock.split(":")
                        mins_left = int(parts[0])
                        minutes_played = completed_quarters + (15 - mins_left)
                    except:
                        minutes_played = completed_quarters
            
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
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, "")
            if not team_key:
                continue
            injuries[team_key] = []
            for cat in team_data.get("categories", []):
                for player in cat.get("items", []):
                    athlete = player.get("athlete", {})
                    name = athlete.get("displayName", "")
                    status = player.get("status", "")
                    pos = athlete.get("position", {}).get("abbreviation", "")
                    if name:
                        injuries[team_key].append({"name": name, "status": status, "pos": pos})
        return injuries
    except:
        return {}

# ============================================================
# EDGE CALCULATION
# ============================================================
def calc_pregame_edge(away, home, injuries):
    """Calculate pre-game edge score (50 = neutral, higher = home favored)"""
    home_pts, away_pts = 0, 0
    factors_home, factors_away = [], []
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    # Star injuries
    home_injuries = injuries.get(home, [])
    away_injuries = injuries.get(away, [])
    home_stars = STAR_PLAYERS.get(home, [])
    away_stars = STAR_PLAYERS.get(away, [])
    
    home_out_names = [str(inj.get("name", "")).lower() for inj in home_injuries 
                      if "OUT" in str(inj.get("status", "")).upper()]
    away_out_names = [str(inj.get("name", "")).lower() for inj in away_injuries 
                      if "OUT" in str(inj.get("status", "")).upper()]
    
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
    if net_gap >= 20:
        home_pts += 4
        factors_home.append("📊 Net +20")
    elif net_gap >= 12:
        home_pts += 2.5
        factors_home.append("📊 Net +12")
    elif net_gap >= 6:
        home_pts += 1.5
        factors_home.append("📊 Net +6")
    elif net_gap <= -20:
        away_pts += 4
        factors_away.append("📊 Net +20")
    elif net_gap <= -12:
        away_pts += 2.5
        factors_away.append("📊 Net +12")
    elif net_gap <= -6:
        away_pts += 1.5
        factors_away.append("📊 Net +6")
    
    # Home field (NFL home field = ~2.5 pts)
    home_pts += 2.5
    factors_home.append("🏟️ Home")
    
    # Elite road team vs weak home
    if away_stats.get("tier") == "elite" and home_stats.get("tier") == "weak":
        away_pts += 2
        factors_away.append("🛫 Elite Road")
    
    # Base score with net rating influence
    base = 50 + (net_gap * 1.2)
    base = max(25, min(75, base))
    
    score = base + home_pts - away_pts
    score = max(10, min(90, score))
    
    if score >= 50:
        return home, int(score), factors_home
    else:
        return away, int(100 - score), factors_away

def calc_live_edge(game, injuries):
    """Calculate live edge based on current score"""
    away, home = game['away'], game['home']
    away_score, home_score = game['away_score'], game['home_score']
    period = game['period']
    minutes = game['minutes_played']
    total = game['total_score']
    
    lead = home_score - away_score
    
    pick, pregame_score, factors = calc_pregame_edge(away, home, injuries)
    
    # Calculate pace (pts per minute)
    pace = round(total / minutes, 2) if minutes > 0 else 0
    # NFL pace labels (different thresholds than NBA)
    pace_label = "🔥 FAST" if pace > 1.0 else "⚖️ AVG" if pace > 0.7 else "🐢 SLOW"
    
    # Live adjustments
    live_adj = 0
    
    # Lead factor (NFL leads are more meaningful)
    if abs(lead) >= 21:
        live_adj = 30 if lead > 0 else -30
    elif abs(lead) >= 14:
        live_adj = 22 if lead > 0 else -22
    elif abs(lead) >= 10:
        live_adj = 15 if lead > 0 else -15
    elif abs(lead) >= 7:
        live_adj = 10 if lead > 0 else -10
    elif abs(lead) >= 3:
        live_adj = 5 if lead > 0 else -5
    
    # Quarter context
    if period == 4:
        if abs(lead) >= 14:
            live_adj += 20 if lead > 0 else -20
        elif abs(lead) >= 7:
            live_adj += 12 if lead > 0 else -12
    elif period == 3 and abs(lead) >= 14:
        live_adj += 8 if lead > 0 else -8
    
    final_score = pregame_score + live_adj if pick == home else (100 - pregame_score) + live_adj
    final_score = max(10, min(95, final_score))
    
    if lead > 0:
        live_pick = home
    elif lead < 0:
        live_pick = away
    else:
        live_pick = pick
    
    # Project total (60 min game)
    if minutes >= 8:
        proj_total = round((total / minutes) * 60)
    else:
        proj_total = 46
    
    return {
        "pick": live_pick,
        "score": int(final_score),
        "lead": lead,
        "pace": pace,
        "pace_label": pace_label,
        "proj_total": proj_total,
        "factors": factors
    }

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(away, home):
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnflgame/nfl-regular-season-games?ticker=KXNFLGAME-{today}{away}{home}"

def get_kalshi_totals_link(away, home):
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnflo/nfl-total-game-points?ticker=KXNFLO-{today}-{away}{home}"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 NFL EDGE GUIDE")
    st.markdown("""
### Score Guide

| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best bets |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |
| **<50** | ⚪ WEAK | Skip |

---

### Injury Impact

| Stars | Impact |
|-------|--------|
| ⭐⭐⭐ | QB/RB1 = +5 |
| ⭐⭐ | WR1/TE1 = +3 |
| ⭐ | Starter = +1 |

---

### Pace Guide

| Pace | Label | Action |
|------|-------|--------|
| <0.7 | 🐢 SLOW | Buy NO |
| 0.7-1.0 | ⚖️ AVG | Wait |
| >1.0 | 🔥 FAST | Buy YES |

---

*We show the edge — you make the call.*
""")
    st.divider()
    st.caption(f"v{VERSION} NFL EDGE")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()

# Get today's teams
today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

# Separate games
live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']
final_games = [g for g in games if g['status'] == 'STATUS_FINAL']

# ============================================================
# UI HEADER
# ============================================================
st.title("🏈 NFL EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 30s")

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
    if team not in today_teams:
        continue
    for inj in team_injuries:
        name = inj.get("name", "")
        status = str(inj.get("status", "")).upper()
        
        if "OUT" in status or "DOUBT" in status:
            tier = 0
            for star_name, star_tier in STAR_TIERS.items():
                if star_name.lower() in name.lower():
                    tier = star_tier
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
    st.markdown("*Real-time edge updates every 30 seconds.*")
    
    live_with_edge = []
    for g in live_games:
        edge = calc_live_edge(g, injuries)
        live_with_edge.append((g, edge))
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)
    
    for g, edge in live_with_edge:
        mins = g['minutes_played']
        
        if mins < 8:
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
        
        safe_no = edge['proj_total'] + 6
        safe_yes = edge['proj_total'] - 4
        
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
            <div style="color: #aaa; font-size: 0.9em; margin-bottom: 10px;">
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
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            st.link_button(f"⬇️ NO {safe_no}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button(f"⬆️ YES {safe_yes}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        
        st.markdown("---")
else:
    st.info("🕐 No live games right now. NFL games typically on Sun/Mon/Thu.")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals in live games")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [8, 15, 20, 30], index=0, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

cush_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < cush_min or mins <= 0:
        continue
    pace = total / mins
    remaining_min = max(60 - mins, 1)
    projected_final = round(total + pace * remaining_min)
    
    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected_final), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 1, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected_final
    else:
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected_final), 0)
        safe_idx = max(base_idx - 1, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected_final - safe_line
    
    if cushion < 4:
        continue
    
    if cush_side == "NO":
        if pace < 0.7:
            pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 0.85:
            pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else:
            pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 1.0:
            pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 0.85:
            pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else:
            pace_status, pace_color = "❌ SLOW", "#ff0000"
    
    cush_results.append({
        'away': g['away'], 'home': g['home'],
        'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        st.markdown(f"""<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']}">
        <b style="color:#fff">{r['away']} @ {r['home']}</b> 
        <span style="color:#888">Q{r['period']} {r['clock']} • {r['total']}pts/{r['mins']:.0f}min</span>
        <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
        <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:8px">🎯 {r['safe_line']}</span>
        <span style="color:#00ff00;font-weight:bold;margin-left:8px">+{r['cushion']:.0f}</span>
        <span style="color:{r['pace_color']};margin-left:8px">{r['pace_status']}</span>
        </div>""", unsafe_allow_html=True)
        st.link_button(f"BUY {cush_side} {r['safe_line']}", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
else:
    st.info(f"No {cush_side} opportunities with 4+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for live games")

pace_data = []
for g in live_games:
    mins = g['minutes_played']
    if mins >= 8:
        pace = round(g['total_score'] / mins, 2)
        pace_data.append({
            "away": g['away'], "home": g['home'],
            "pace": pace, "proj": round(pace * 60),
            "total": g['total_score'], "mins": mins,
            "period": g['period'], "clock": g['clock']
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 0.7:
            lbl, clr = "🐢 SLOW", "#00ff00"
            rec_side, rec_line = "NO", THRESHOLDS[min(next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1) + 1, len(THRESHOLDS)-1)]
        elif p['pace'] < 0.85:
            lbl, clr = "⚖️ AVG", "#ffff00"
            rec_side, rec_line = None, None
        elif p['pace'] < 1.0:
            lbl, clr = "🔥 FAST", "#ff8800"
            rec_side, rec_line = "YES", THRESHOLDS[max(next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 1, 0)]
        else:
            lbl, clr = "🚀 SHOOTOUT", "#ff0000"
            rec_side, rec_line = "YES", THRESHOLDS[max(next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 1, 0)]
        
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr}">
        <b style="color:#fff">{p['away']} @ {p['home']}</b>
        <span style="color:#666;margin-left:10px">Q{p['period']} {p['clock']}</span>
        <span style="color:#888;margin-left:10px">{p['total']}pts/{p['mins']:.0f}min</span>
        <span style="color:{clr};font-weight:bold;margin-left:10px">{p['pace']:.2f}/min {lbl}</span>
        <span style="color:#888;margin-left:10px">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>""", unsafe_allow_html=True)
        
        if rec_side and rec_line:
            st.link_button(f"BUY {rec_side} {rec_line}", get_kalshi_totals_link(p['away'], p['home']), use_container_width=True)
else:
    st.info("No games with 8+ minutes played yet")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT
# ============================================================
if scheduled_games:
    st.subheader("🎯 PRE-GAME ALIGNMENT")
    st.markdown("*Look for **70+** scores with multiple factors.*")
    
    games_with_edge = []
    for g in scheduled_games:
        pick, score, factors = calc_pregame_edge(g['away'], g['home'], injuries)
        games_with_edge.append((g, pick, score, factors))
    games_with_edge.sort(key=lambda x: x[2], reverse=True)
    
    for g, pick, score, factors in games_with_edge:
        if score >= 70:
            score_color = "#22c55e"
            tier = "🟢 STRONG"
            border_color = "#22c55e"
        elif score >= 60:
            score_color = "#22c55e"
            tier = "🟢 GOOD"
            border_color = "#22c55e"
        elif score >= 50:
            score_color = "#eab308"
            tier = "🟡 MODERATE"
            border_color = "#eab308"
        else:
            score_color = "#888"
            tier = "⚪ WEAK"
            border_color = "#444"
        
        st.markdown(f"""
        <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #fff; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: {score_color}; font-weight: 600;">{tier} {score}/100</span>
            </div>
            <div style="color: #888; font-size: 0.85em; margin-top: 4px;">
                Edge: <strong style="color: #fff;">{pick}</strong> • {' • '.join(factors[:3]) if factors else 'No strong factors'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button(f"🎯 BUY {pick}", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE", expanded=False):
    st.markdown("""
### Edge Score Guide

| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best opportunities |
| **60-69** | 🟢 GOOD | Worth considering |
| **50-59** | 🟡 MODERATE | Wait for live |
| **<50** | ⚪ WEAK | Skip |

---

### NFL Pace Guide

| Pace | Label | Action |
|------|-------|--------|
| <0.7 | 🐢 SLOW | Buy NO |
| 0.7-0.85 | ⚖️ AVG | Wait |
| 0.85-1.0 | 🔥 FAST | Buy YES |
| >1.0 | 🚀 SHOOTOUT | Buy YES |

---

### Cushion Scanner

- **+6+** = Very safe threshold
- **+4-5** = Safe threshold
- **<+4** = Not shown (risky)

---

⚠️ Edge Score ≠ Win Probability  
⚠️ Only risk what you can afford to lose
""")

st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
