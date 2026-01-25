import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=30000, key="nfl_refresh")

import requests
import json
import base64
import hashlib
import time
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.backends import default_backend
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "19.1"

# ============================================================
# KALSHI API AUTH (uses st.secrets - keys stay private)
# ============================================================
def get_kalshi_headers(method, path):
    """Generate authenticated headers for Kalshi API"""
    try:
        api_key = st.secrets.get("KALSHI_API_KEY", "")
        private_key_pem = st.secrets.get("KALSHI_PRIVATE_KEY", "")
        
        if not api_key or not private_key_pem:
            return None
        
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method + path
        
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )
        
        signature = private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        sig_b64 = base64.b64encode(signature).decode()
        
        return {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def fetch_kalshi_nfl_spreads():
    """Fetch NFL spread markets from Kalshi"""
    try:
        path = "/trade-api/v2/markets?series_ticker=KXNFLGAME&status=open&limit=100"
        headers = get_kalshi_headers("GET", path)
        
        if not headers:
            return {}
        
        url = f"https://trading-api.kalshi.com{path}"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return {}
        
        data = resp.json()
        markets = data.get("markets", [])
        
        prices = {}
        for m in markets:
            ticker = m.get("ticker", "")
            title = m.get("title", "")
            yes_ask = m.get("yes_ask", 0) or m.get("last_price", 0) or 0
            
            # Extract team from title (e.g., "Chiefs to beat Bills")
            if " to beat " in title.lower():
                team = title.split(" to beat ")[0].strip()
                prices[team] = yes_ask
            elif " vs " in title:
                # Try to parse from ticker
                prices[ticker] = yes_ask
        
        return prices
    except Exception as e:
        return {}

# ============================================================
# VEGAS LINES (Conference Championships - Jan 26, 2026)
# ============================================================
VEGAS_LINES = {
    "AFC Championship": {
        "favorite": "KC",
        "underdog": "BUF",
        "spread": -1.5,
        "fav_implied": 52,
        "dog_implied": 48
    },
    "NFC Championship": {
        "favorite": "PHI",
        "underdog": "WAS",
        "spread": -6,
        "fav_implied": 70,
        "dog_implied": 30
    }
}

TEAM_FULL_NAMES = {
    "KC": "Chiefs", "BUF": "Bills", "PHI": "Eagles", "WAS": "Commanders",
    "DET": "Lions", "LAR": "Rams", "BAL": "Ravens", "HOU": "Texans",
    "SF": "49ers", "GB": "Packers", "MIN": "Vikings", "TB": "Buccaneers"
}

# ============================================================
# SPREAD EDGE CALCULATION
# ============================================================
def calc_spread_edges(kalshi_prices, vegas_lines, min_gap=5):
    """Find edges where Kalshi price < Vegas implied %"""
    edges = []
    
    for game_name, line in vegas_lines.items():
        fav = line["favorite"]
        dog = line["underdog"]
        fav_name = TEAM_FULL_NAMES.get(fav, fav)
        dog_name = TEAM_FULL_NAMES.get(dog, dog)
        
        # Check favorite
        fav_kalshi = kalshi_prices.get(fav_name, kalshi_prices.get(fav, 0))
        if fav_kalshi > 0:
            fav_gap = line["fav_implied"] - fav_kalshi
            if fav_gap >= min_gap:
                edges.append({
                    "game": game_name,
                    "team": fav,
                    "team_name": fav_name,
                    "side": "favorite",
                    "spread": line["spread"],
                    "vegas_implied": line["fav_implied"],
                    "kalshi_price": fav_kalshi,
                    "gap": fav_gap
                })
        
        # Check underdog
        dog_kalshi = kalshi_prices.get(dog_name, kalshi_prices.get(dog, 0))
        if dog_kalshi > 0:
            dog_gap = line["dog_implied"] - dog_kalshi
            if dog_gap >= min_gap:
                edges.append({
                    "game": game_name,
                    "team": dog,
                    "team_name": dog_name,
                    "side": "underdog",
                    "spread": f"+{abs(line['spread'])}",
                    "vegas_implied": line["dog_implied"],
                    "kalshi_price": dog_kalshi,
                    "gap": dog_gap
                })
    
    edges.sort(key=lambda x: x["gap"], reverse=True)
    return edges

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
    "ARI": {"net": -12.5, "tier": "weak"}, "ATL": {"net": 2.5, "tier": "mid"},
    "BAL": {"net": 15.5, "tier": "elite"}, "BUF": {"net": 18.2, "tier": "elite"},
    "CAR": {"net": -18.5, "tier": "weak"}, "CHI": {"net": -8.5, "tier": "weak"},
    "CIN": {"net": 5.8, "tier": "good"}, "CLE": {"net": -25.0, "tier": "weak"},
    "DAL": {"net": -5.2, "tier": "mid"}, "DEN": {"net": 8.5, "tier": "good"},
    "DET": {"net": 22.5, "tier": "elite"}, "GB": {"net": 12.2, "tier": "elite"},
    "HOU": {"net": 10.5, "tier": "good"}, "IND": {"net": -2.5, "tier": "mid"},
    "JAX": {"net": -8.5, "tier": "weak"}, "KC": {"net": 18.5, "tier": "elite"},
    "LV": {"net": -10.2, "tier": "weak"}, "LAC": {"net": 11.8, "tier": "good"},
    "LAR": {"net": 8.5, "tier": "good"}, "MIA": {"net": -2.5, "tier": "mid"},
    "MIN": {"net": 12.5, "tier": "elite"}, "NE": {"net": -12.5, "tier": "weak"},
    "NO": {"net": -8.8, "tier": "weak"}, "NYG": {"net": -15.5, "tier": "weak"},
    "NYJ": {"net": -6.5, "tier": "weak"}, "PHI": {"net": 14.8, "tier": "elite"},
    "PIT": {"net": 4.8, "tier": "mid"}, "SF": {"net": -4.5, "tier": "mid"},
    "SEA": {"net": 6.5, "tier": "good"}, "TB": {"net": 5.8, "tier": "good"},
    "TEN": {"net": -14.8, "tier": "weak"}, "WAS": {"net": 8.5, "tier": "good"},
}

THRESHOLDS = [37.5, 40.5, 43.5, 45.5, 47.5, 49.5, 51.5, 54.5, 57.5]

# ============================================================
# ESPN FETCH
# ============================================================
@st.cache_data(ttl=30)
def fetch_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={today}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        
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
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, "")
            if not team_key: continue
            injuries[team_key] = []
            for cat in team_data.get("categories", []):
                for player in cat.get("items", []):
                    name = player.get("athlete", {}).get("displayName", "")
                    status = player.get("status", "")
                    if name:
                        injuries[team_key].append({"name": name, "status": status})
        return injuries
    except:
        return {}

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(away, home):
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnflgame/nfl-games?ticker=KXNFLGAME-{today}{away}{home}"

def get_kalshi_totals_link(away, home):
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnflo/nfl-total-game-points?ticker=KXNFLO-{today}-{away}{home}"

# ============================================================
# LIVE EDGE CALCULATION
# ============================================================
def calc_live_edge(game, injuries):
    away, home = game['away'], game['home']
    lead = game['home_score'] - game['away_score']
    minutes = game['minutes_played']
    total = game['total_score']
    period = game['period']
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    net_gap = home_stats.get("net", 0) - away_stats.get("net", 0)
    
    base = 50 + (net_gap * 1.2) + 2.5
    base = max(25, min(75, base))
    
    live_adj = 0
    if abs(lead) >= 21: live_adj = 30 if lead > 0 else -30
    elif abs(lead) >= 14: live_adj = 22 if lead > 0 else -22
    elif abs(lead) >= 10: live_adj = 15 if lead > 0 else -15
    elif abs(lead) >= 7: live_adj = 10 if lead > 0 else -10
    
    if period == 4 and abs(lead) >= 14: live_adj += 20 if lead > 0 else -20
    
    score = base + live_adj
    score = max(10, min(95, score))
    
    pace = round(total / minutes, 2) if minutes > 0 else 0
    pace_label = "🔥 FAST" if pace > 1.0 else "⚖️ AVG" if pace > 0.7 else "🐢 SLOW"
    
    live_pick = home if lead > 0 else away if lead < 0 else home
    proj_total = round((total / minutes) * 60) if minutes >= 8 else 46
    
    return {
        "pick": live_pick, "score": int(score), "lead": lead,
        "pace": pace, "pace_label": pace_label, "proj_total": proj_total
    }

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 NFL EDGE GUIDE")
    st.markdown("""
### Spread Edge
| GAP | Signal |
|-----|--------|
| **+7¢+** | 🟢 STRONG BUY |
| **+5-6¢** | 🟢 BUY |
| **<+5¢** | Not shown |

### Live Edge
| Score | Action |
|-------|--------|
| **70+** | 🟢 STRONG |
| **60-69** | 🟢 GOOD |
| **<60** | Wait |
""")
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# FETCH ALL DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()
kalshi_prices = fetch_kalshi_nfl_spreads()

live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']

# ============================================================
# HEADER
# ============================================================
st.title("🏈 NFL EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 30s")

c1, c2, c3 = st.columns(3)
c1.metric("Games Today", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Kalshi API", "✅" if kalshi_prices else "⚠️ Manual")

st.divider()

# ============================================================
# 💰 SPREAD EDGE — KALSHI vs VEGAS (ONLY SHOWS EDGES)
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #0d4a0d 0%, #1a5a1a 100%); padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
    <h2 style="color: #4ade80; margin: 0;">💰 SPREAD EDGE — Kalshi vs Vegas</h2>
    <p style="color: #888; margin: 5px 0 0 0;">Only showing mispriced markets (GAP ≥ 5¢)</p>
</div>
""", unsafe_allow_html=True)

# Calculate edges
edges = calc_spread_edges(kalshi_prices, VEGAS_LINES, min_gap=5)

if edges:
    for edge in edges:
        gap_color = "#22c55e" if edge["gap"] >= 7 else "#4ade80"
        signal = "🟢 STRONG BUY" if edge["gap"] >= 7 else "🟢 BUY"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid {gap_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #fff; font-size: 1.2em; font-weight: 700;">{edge['team']} ({edge['team_name']})</span>
                    <span style="color: #888; margin-left: 10px;">{edge['game']}</span>
                </div>
                <span style="color: {gap_color}; font-weight: 700; font-size: 1.1em;">{signal}</span>
            </div>
            <div style="display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap;">
                <div style="background: #333; padding: 8px 12px; border-radius: 6px;">
                    <span style="color: #888;">Vegas:</span> 
                    <span style="color: #fff; font-weight: 600;">{edge['spread']} ({edge['vegas_implied']}%)</span>
                </div>
                <div style="background: #333; padding: 8px 12px; border-radius: 6px;">
                    <span style="color: #888;">Kalshi:</span> 
                    <span style="color: #fff; font-weight: 600;">{edge['kalshi_price']}¢</span>
                </div>
                <div style="background: {gap_color}22; padding: 8px 12px; border-radius: 6px; border: 1px solid {gap_color};">
                    <span style="color: {gap_color}; font-weight: 700;">GAP: +{edge['gap']}¢</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button(f"🎯 BUY {edge['team']} on Kalshi", get_kalshi_ml_link(edge['team'], edge['team']), use_container_width=True)
        st.markdown("")

elif kalshi_prices:
    st.info("⚪ No mispriced markets right now (all GAPs < 5¢). Check back closer to game time.")
else:
    # Manual fallback if API fails
    st.warning("⚠️ Kalshi API not connected. Showing manual comparison.")
    
    st.markdown("### Conference Championships")
    
    for game_name, line in VEGAS_LINES.items():
        fav = line["favorite"]
        dog = line["underdog"]
        
        st.markdown(f"""
        <div style="background: #1e1e2e; padding: 14px; border-radius: 10px; margin-bottom: 10px;">
            <div style="color: #fff; font-weight: 600; margin-bottom: 8px;">{game_name}: {fav} vs {dog}</div>
            <div style="color: #888;">Vegas: <span style="color: #fff;">{fav} {line['spread']} ({line['fav_implied']}%)</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fav_price = st.number_input(f"{fav} Kalshi ¢", 0, 99, 0, key=f"fav_{game_name}")
        with col2:
            dog_price = st.number_input(f"{dog} Kalshi ¢", 0, 99, 0, key=f"dog_{game_name}")
        
        if fav_price > 0:
            fav_gap = line["fav_implied"] - fav_price
            if fav_gap >= 5:
                st.success(f"🟢 {fav} GAP: +{fav_gap}¢ — BUY")
            else:
                st.caption(f"⚪ {fav} GAP: {fav_gap}¢ — No edge")
        
        if dog_price > 0:
            dog_gap = line["dog_implied"] - dog_price
            if dog_gap >= 5:
                st.success(f"🟢 {dog} GAP: +{dog_gap}¢ — BUY")
            else:
                st.caption(f"⚪ {dog} GAP: {dog_gap}¢ — No edge")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    
    for g in live_games:
        edge = calc_live_edge(g, injuries)
        mins = g['minutes_played']
        
        if mins < 8:
            status_label, status_color = "⏳ TOO EARLY", "#888"
        elif edge['score'] >= 70:
            status_label, status_color = f"🟢 STRONG {edge['score']}", "#22c55e"
        elif edge['score'] >= 60:
            status_label, status_color = f"🟢 GOOD {edge['score']}", "#22c55e"
        else:
            status_label, status_color = f"🟡 {edge['score']}", "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        safe_no = edge['proj_total'] + 6
        safe_yes = edge['proj_total'] - 4
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
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
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
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
cush_min = cs1.selectbox("Min minutes", [8, 15, 20, 30], index=0)
cush_side = cs2.selectbox("Side", ["NO", "YES"])

cush_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < cush_min or mins <= 0: continue
    
    pace = total / mins
    remaining = max(60 - mins, 1)
    projected = round(total + pace * remaining)
    
    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 1, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected
    else:
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected), 0)
        safe_idx = max(base_idx - 1, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected - safe_line
    
    if cushion < 4: continue
    
    pace_ok = (cush_side == "NO" and pace < 0.85) or (cush_side == "YES" and pace > 0.85)
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
    st.info(f"No {cush_side} opportunities with 4+ cushion yet")

st.divider()

# ============================================================
# 📅 SCHEDULED GAMES
# ============================================================
if scheduled_games:
    st.subheader("📅 SCHEDULED GAMES")
    for g in scheduled_games:
        st.markdown(f"""
        <div style="background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <span style="color: #fff; font-weight: 600;">{g['away']} @ {g['home']}</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
