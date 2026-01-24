import streamlit as st

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# ============================================================
# GA4 ANALYTICS - SERVER-SIDE
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

from auth import require_auth
require_auth()

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ============================================================
# TEAM DATA - NET RATINGS, PACE, HOME WIN %
# ============================================================
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
    "Golden State": {"net": 3.5, "pace": 100.2, "home_pct": 0.65, "tier": "good"},
    "Houston": {"net": 1.2, "pace": 101.5, "home_pct": 0.55, "tier": "mid"},
    "Indiana": {"net": 2.8, "pace": 103.5, "home_pct": 0.58, "tier": "mid"},
    "LA Clippers": {"net": 1.5, "pace": 98.0, "home_pct": 0.55, "tier": "mid"},
    "LA Lakers": {"net": 2.2, "pace": 99.5, "home_pct": 0.58, "tier": "mid"},
    "Memphis": {"net": 4.5, "pace": 100.8, "home_pct": 0.68, "tier": "good"},
    "Miami": {"net": 3.8, "pace": 97.5, "home_pct": 0.65, "tier": "good"},
    "Milwaukee": {"net": 5.2, "pace": 99.2, "home_pct": 0.70, "tier": "good"},
    "Minnesota": {"net": 7.5, "pace": 98.8, "home_pct": 0.72, "tier": "elite"},
    "New Orleans": {"net": 1.8, "pace": 100.0, "home_pct": 0.55, "tier": "mid"},
    "New York": {"net": 6.2, "pace": 98.5, "home_pct": 0.68, "tier": "good"},
    "Oklahoma City": {"net": 12.5, "pace": 99.8, "home_pct": 0.82, "tier": "elite"},
    "Orlando": {"net": 3.2, "pace": 97.0, "home_pct": 0.62, "tier": "good"},
    "Philadelphia": {"net": 2.5, "pace": 98.2, "home_pct": 0.58, "tier": "mid"},
    "Phoenix": {"net": 2.0, "pace": 99.0, "home_pct": 0.60, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 99.5, "home_pct": 0.40, "tier": "weak"},
    "Sacramento": {"net": 0.8, "pace": 101.2, "home_pct": 0.55, "tier": "mid"},
    "San Antonio": {"net": -4.8, "pace": 100.5, "home_pct": 0.42, "tier": "weak"},
    "Toronto": {"net": -1.5, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Utah": {"net": -7.5, "pace": 100.2, "home_pct": 0.35, "tier": "weak"},
    "Washington": {"net": -6.2, "pace": 101.0, "home_pct": 0.38, "tier": "weak"}
}

# Star players by tier (3=MVP, 2=All-Star, 1=Key)
STARS = {
    "Nikola Jokic": ("Denver", 3), "Shai Gilgeous-Alexander": ("Oklahoma City", 3),
    "Giannis Antetokounmpo": ("Milwaukee", 3), "Luka Doncic": ("Dallas", 3),
    "Joel Embiid": ("Philadelphia", 3), "Jayson Tatum": ("Boston", 3),
    "Stephen Curry": ("Golden State", 3), "Kevin Durant": ("Phoenix", 3),
    "LeBron James": ("LA Lakers", 3), "Anthony Edwards": ("Minnesota", 3),
    "Ja Morant": ("Memphis", 3), "Donovan Mitchell": ("Cleveland", 3),
    "Trae Young": ("Atlanta", 3), "Devin Booker": ("Phoenix", 3),
    "Jaylen Brown": ("Boston", 2), "Anthony Davis": ("LA Lakers", 2),
    "Damian Lillard": ("Milwaukee", 2), "Kyrie Irving": ("Dallas", 2),
    "Jimmy Butler": ("Miami", 2), "Bam Adebayo": ("Miami", 2),
    "Tyrese Haliburton": ("Indiana", 2), "De'Aaron Fox": ("Sacramento", 2),
    "Jalen Brunson": ("New York", 2), "Chet Holmgren": ("Oklahoma City", 2),
    "Paolo Banchero": ("Orlando", 2), "Franz Wagner": ("Orlando", 2),
    "Victor Wembanyama": ("San Antonio", 2), "Evan Mobley": ("Cleveland", 2),
    "Zion Williamson": ("New Orleans", 2), "LaMelo Ball": ("Charlotte", 2),
    "Cade Cunningham": ("Detroit", 2), "Tyrese Maxey": ("Philadelphia", 2),
}

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

# ============================================================
# ESPN DATA FETCHERS
# ============================================================
@st.cache_data(ttl=120)
def fetch_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        data = requests.get(url, timeout=10).json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home, away = None, None
            for c in competitors:
                name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home = {"team": name, "score": score}
                else:
                    away = {"team": name, "score": score}
            status = event.get("status", {})
            games.append({
                "home": home["team"], "away": away["team"],
                "home_score": home["score"], "away_score": away["score"],
                "status": status.get("type", {}).get("name", ""),
                "period": status.get("period", 0),
                "clock": status.get("displayClock", "")
            })
        return games
    except:
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    injuries = {}
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", timeout=10).json()
        for team_data in data.get("injuries", []):
            team = TEAM_ABBREVS.get(team_data.get("displayName", ""), "")
            if not team: continue
            injuries[team] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "").upper()
                if name and "OUT" in status:
                    injuries[team].append(name)
        return injuries
    except:
        return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    """Get teams that played yesterday and day before"""
    rest = {"b2b": set(), "rested": set()}
    try:
        for days_ago in [1, 2, 3]:
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                for c in event.get("competitions", [{}])[0].get("competitors", []):
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if team:
                        if days_ago == 1:
                            rest["b2b"].add(team)
                        elif days_ago >= 2 and team not in rest["b2b"]:
                            rest["rested"].add(team)
        return rest
    except:
        return {"b2b": set(), "rested": set()}

# ============================================================
# EDGE CALCULATION - NEW 10-FACTOR MODEL
# ============================================================
def calc_edge(home, away, injuries, rest):
    """
    Returns: (pick, probability, edge_pts, reasons)
    """
    home_pts, away_pts = 0, 0
    home_reasons, away_reasons = [], []
    
    h_stats = TEAM_STATS.get(home, {})
    a_stats = TEAM_STATS.get(away, {})
    h_net = h_stats.get("net", 0)
    a_net = a_stats.get("net", 0)
    
    # ========== TIER 1: HIGH IMPACT ==========
    
    # 1. STAR OUT (+5 pts) - Opponent missing star
    home_out = injuries.get(home, [])
    away_out = injuries.get(away, [])
    
    for star, (team, tier) in STARS.items():
        if team == home and any(star.lower() in p.lower() for p in home_out):
            if tier == 3:
                away_pts += 5
                away_reasons.append(f"🔥 {star.split()[-1]} OUT")
            elif tier == 2:
                away_pts += 3
                away_reasons.append(f"⭐ {star.split()[-1]} OUT")
        if team == away and any(star.lower() in p.lower() for p in away_out):
            if tier == 3:
                home_pts += 5
                home_reasons.append(f"🔥 {star.split()[-1]} OUT")
            elif tier == 2:
                home_pts += 3
                home_reasons.append(f"⭐ {star.split()[-1]} OUT")
    
    # 2. REST ADVANTAGE (+4 pts) - Rested vs B2B
    h_b2b = home in rest.get("b2b", set())
    a_b2b = away in rest.get("b2b", set())
    h_rested = home in rest.get("rested", set())
    a_rested = away in rest.get("rested", set())
    
    if a_b2b and not h_b2b:
        home_pts += 4
        home_reasons.append("🛏️ Opp B2B")
    elif h_b2b and not a_b2b:
        away_pts += 4
        away_reasons.append("🛏️ Opp B2B")
    
    if h_rested and a_b2b:
        home_pts += 2
        home_reasons.append("💪 Rested")
    elif a_rested and h_b2b:
        away_pts += 2
        away_reasons.append("💪 Rested")
    
    # 3. NET RATING GAP (+3 pts if 15+, +2 if 10+, +1 if 5+)
    net_gap = h_net - a_net
    if net_gap >= 15:
        home_pts += 3
        home_reasons.append(f"📊 Net +{net_gap:.0f}")
    elif net_gap >= 10:
        home_pts += 2
        home_reasons.append(f"📊 Net +{net_gap:.0f}")
    elif net_gap >= 5:
        home_pts += 1
        home_reasons.append(f"📊 Net +{net_gap:.0f}")
    elif net_gap <= -15:
        away_pts += 3
        away_reasons.append(f"📊 Net +{-net_gap:.0f}")
    elif net_gap <= -10:
        away_pts += 2
        away_reasons.append(f"📊 Net +{-net_gap:.0f}")
    elif net_gap <= -5:
        away_pts += 1
        away_reasons.append(f"📊 Net +{-net_gap:.0f}")
    
    # ========== TIER 2: MEDIUM IMPACT ==========
    
    # 4. DENVER ALTITUDE (+1.5 pts home only)
    if home == "Denver":
        home_pts += 1.5
        home_reasons.append("🏔️ Altitude")
    
    # 5. PACE MISMATCH (+1.5 pts) - Fast team vs slow team
    h_pace = h_stats.get("pace", 99)
    a_pace = a_stats.get("pace", 99)
    if h_pace >= 101 and a_pace <= 98:
        home_pts += 1.5
        home_reasons.append("⚡ Pace edge")
    elif a_pace >= 101 and h_pace <= 98:
        away_pts += 1.5
        away_reasons.append("⚡ Pace edge")
    
    # ========== TIER 3: SITUATIONAL ==========
    
    # 6. FADE WEAK HOME (+1 pt) - Elite road team vs weak home team
    h_tier = h_stats.get("tier", "mid")
    a_tier = a_stats.get("tier", "mid")
    
    if h_tier == "weak" and a_tier in ["elite", "good"]:
        away_pts += 1.5
        away_reasons.append("🎯 Fade weak home")
    
    # 7. FADE HOME BIAS (+1 pt) - Strong road team underpriced
    if a_tier == "elite" and h_tier != "elite":
        away_pts += 1
        away_reasons.append("💰 Road value")
    
    # ========== CALCULATE PROBABILITY ==========
    
    # Base probability from net rating (rough conversion)
    # Net rating gap of 10 ≈ 70% win prob for better team
    base_prob = 50 + (net_gap * 1.5)  # Each net pt = ~1.5% win prob
    base_prob = max(25, min(85, base_prob))  # Cap at 25-85%
    
    # Adjust for edge points
    total_pts = home_pts + away_pts
    if total_pts > 0:
        if home_pts > away_pts:
            edge_boost = (home_pts / total_pts) * 15  # Up to 15% boost
            home_prob = min(90, base_prob + edge_boost)
            pick = home
            prob = home_prob
            reasons = home_reasons
            edge = home_pts - away_pts
        else:
            edge_boost = (away_pts / total_pts) * 15
            away_prob = min(90, (100 - base_prob) + edge_boost)
            pick = away
            prob = away_prob
            reasons = away_reasons
            edge = away_pts - home_pts
    else:
        # No clear edge
        if base_prob >= 55:
            pick, prob, reasons, edge = home, base_prob, ["📊 Better team"], 0
        elif base_prob <= 45:
            pick, prob, reasons, edge = away, 100 - base_prob, ["📊 Better team"], 0
        else:
            return None  # Toss-up, no pick
    
    return {
        "pick": pick,
        "opponent": away if pick == home else home,
        "prob": round(prob),
        "edge_pts": round(edge, 1),
        "reasons": reasons[:4],
        "home": home,
        "away": away,
        "is_home": pick == home
    }

def build_kalshi_url(away, home):
    a_code = KALSHI_CODES.get(away, "XXX")
    h_code = KALSHI_CODES.get(home, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/kxnbagame/kxnbagame-{date_str}{a_code}{h_code}"

# ============================================================
# UI
# ============================================================
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v2.0 • {now.strftime('%b %d, %Y %I:%M %p ET')} • New 10-Factor Model")

# Fetch data
games = fetch_games()
injuries = fetch_injuries()
rest = fetch_rest_days()

# Stats row
c1, c2, c3 = st.columns(3)
c1.metric("Today's Games", len(games))
c2.metric("B2B Teams", len(rest.get("b2b", set())))
c3.metric("Rested Teams", len(rest.get("rested", set())))

st.divider()

# ============================================================
# 🏥 INJURY ALERTS
# ============================================================
st.subheader("🏥 STAR INJURIES")

star_injuries = []
today_teams = set()
for g in games:
    today_teams.add(g["home"])
    today_teams.add(g["away"])

for star, (team, tier) in STARS.items():
    if team in today_teams and team in injuries:
        if any(star.lower() in p.lower() for p in injuries[team]):
            star_injuries.append({"star": star, "team": team, "tier": tier})

star_injuries.sort(key=lambda x: -x["tier"])

if star_injuries:
    cols = st.columns(min(3, len(star_injuries)))
    for i, inj in enumerate(star_injuries[:6]):
        with cols[i % 3]:
            stars = "⭐" * inj["tier"]
            st.markdown(f"""<div style="background:#1a1a2e;padding:12px;border-radius:8px;border-left:4px solid #ff4444;margin-bottom:8px">
                <div style="color:#fff;font-weight:bold">{stars} {inj['star']}</div>
                <div style="color:#ff4444;font-size:0.9em">OUT • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No major star injuries for today's games")

# B2B Alert
if rest.get("b2b"):
    b2b_today = [t for t in rest["b2b"] if t in today_teams]
    if b2b_today:
        st.markdown(f"""<div style="background:#1a2a3a;padding:12px;border-radius:8px;margin-top:10px">
            <span style="color:#f59e0b;font-weight:bold">🛏️ B2B TEAMS:</span> 
            <span style="color:#fff">{", ".join(sorted(b2b_today))}</span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ============================================================
# 🎯 ML PICKS - EDGE BASED
# ============================================================
st.subheader("🎯 ML PICKS")
st.caption("Only showing picks with 60%+ probability")

picks = []
for g in games:
    if g["status"] == "STATUS_FINAL":
        continue
    result = calc_edge(g["home"], g["away"], injuries, rest)
    if result and result["prob"] >= 60:
        result["status"] = g["status"]
        result["period"] = g["period"]
        result["clock"] = g["clock"]
        result["home_score"] = g["home_score"]
        result["away_score"] = g["away_score"]
        picks.append(result)

picks.sort(key=lambda x: (-x["prob"], -x["edge_pts"]))

if picks:
    for p in picks:
        prob = p["prob"]
        buy_under = prob - 8  # Recommended max price
        reasons_str = " • ".join(p["reasons"])
        kalshi_url = build_kalshi_url(p["away"], p["home"])
        
        # Color based on probability
        if prob >= 75:
            border = "#00ff00"
            tier = "🔒 STRONG"
        elif prob >= 68:
            border = "#38bdf8"
            tier = "🔵 BUY"
        else:
            border = "#f59e0b"
            tier = "🟡 LEAN"
        
        # Live status
        if p["status"] == "STATUS_IN_PROGRESS":
            pick_score = p["home_score"] if p["is_home"] else p["away_score"]
            opp_score = p["away_score"] if p["is_home"] else p["home_score"]
            lead = pick_score - opp_score
            live_html = f'<span style="background:#dc2626;padding:2px 8px;border-radius:4px;color:#fff;font-size:0.8em;margin-left:8px">🔴 Q{p["period"]} {p["clock"]} ({lead:+d})</span>'
        else:
            live_html = ""
        
        st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#1e293b);padding:14px 18px;border-radius:10px;border-left:4px solid {border};margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                <div>
                    <span style="background:{border}22;color:{border};padding:4px 10px;border-radius:4px;font-weight:bold;font-size:0.85em">{tier}</span>
                    <span style="color:#fff;font-weight:bold;font-size:1.2em;margin-left:12px">{p['pick']}</span>
                    <span style="color:#666"> vs {p['opponent']}</span>
                    {live_html}
                </div>
                <a href="{kalshi_url}" target="_blank" style="background:linear-gradient(135deg,#16a34a,#15803d);color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold">BUY {p['pick']}</a>
            </div>
            <div style="margin-top:10px;display:flex;gap:20px;flex-wrap:wrap;align-items:center">
                <div style="background:#1e3a5f;padding:8px 14px;border-radius:6px">
                    <span style="color:#888;font-size:0.85em">Model:</span>
                    <span style="color:#00ff00;font-weight:bold;font-size:1.1em"> {prob}%</span>
                </div>
                <div style="background:#1e3a5f;padding:8px 14px;border-radius:6px">
                    <span style="color:#888;font-size:0.85em">Buy under:</span>
                    <span style="color:#f59e0b;font-weight:bold;font-size:1.1em"> {buy_under}¢</span>
                </div>
                <div style="color:#9ca3af;font-size:0.9em">{reasons_str}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("""<div style="background:#0f172a;padding:12px;border-radius:8px;margin-top:15px">
        <span style="color:#f59e0b">💡 TIP:</span>
        <span style="color:#ccc"> Only buy if Kalshi price is BELOW the "Buy under" price. That's your edge.</span>
    </div>""", unsafe_allow_html=True)
else:
    st.info("No high-confidence picks right now. Check back closer to game time.")

st.divider()

# ============================================================
# 📺 ALL GAMES
# ============================================================
st.subheader("📺 ALL GAMES")

for g in games:
    home, away = g["home"], g["away"]
    h_net = TEAM_STATS.get(home, {}).get("net", 0)
    a_net = TEAM_STATS.get(away, {}).get("net", 0)
    
    if g["status"] == "STATUS_FINAL":
        winner = home if g["home_score"] > g["away_score"] else away
        status_html = f'<span style="color:#22c55e">✅ {winner} wins</span>'
    elif g["status"] == "STATUS_IN_PROGRESS":
        status_html = f'<span style="color:#ef4444">🔴 Q{g["period"]} {g["clock"]}</span>'
    else:
        status_html = '<span style="color:#666">Scheduled</span>'
    
    st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#0f172a;padding:10px 14px;margin-bottom:4px;border-radius:6px">
        <div>
            <span style="color:#fff;font-weight:bold">{away}</span>
            <span style="color:#666"> ({a_net:+.1f})</span>
            <span style="color:#888"> {g['away_score']} @ </span>
            <span style="color:#fff;font-weight:bold">{home}</span>
            <span style="color:#666"> ({h_net:+.1f})</span>
            <span style="color:#888"> {g['home_score']}</span>
        </div>
        {status_html}
    </div>""", unsafe_allow_html=True)

st.divider()

# ============================================================
# 📖 METHODOLOGY
# ============================================================
with st.expander("📖 How This Works"):
    st.markdown("""
**NEW 10-FACTOR MODEL**

| Tier | Factor | Points |
|------|--------|--------|
| 1 | Star OUT (MVP) | +5 |
| 1 | Star OUT (All-Star) | +3 |
| 1 | Rest Advantage (vs B2B) | +4 |
| 1 | Extra Rest Bonus | +2 |
| 1 | Net Rating Gap (15+) | +3 |
| 1 | Net Rating Gap (10+) | +2 |
| 2 | Denver Altitude | +1.5 |
| 2 | Pace Mismatch | +1.5 |
| 3 | Fade Weak Home | +1.5 |
| 3 | Road Value (elite road) | +1 |

**THE FILTER:**
- Only shows picks with 60%+ model probability
- "Buy under" = Model probability - 8¢ (that's your edge)
- Example: 70% model → Buy under 62¢

**WHY THIS WORKS:**
- Kalshi is slow to price in injuries
- Public overvalues home court
- Rest is the #1 underpriced factor in NBA
""")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals opportunities in live games")

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

def get_minutes_played(period, clock, status):
    if status == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except: return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def build_kalshi_totals_url(away, home):
    a_code = KALSHI_CODES.get(away, "XXX")
    h_code = KALSHI_CODES.get(home, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/kxnbatotal/kxnbatotal-{date_str}{a_code}{h_code}"

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

cush_results = []
for g in games:
    total = g['home_score'] + g['away_score']
    mins = get_minutes_played(g['period'], g['clock'], g['status'])
    if g['status'] == "STATUS_FINAL": continue
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
    
    if cush_side == "NO":
        if pace < 4.5: pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 5.1: pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ SLOW", "#ff0000"
    
    cush_results.append({
        'home': g['home'], 'away': g['away'], 'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        kalshi_url = build_kalshi_totals_url(r['away'], r['home'])
        btn_color = "#00aa00" if cush_side == "NO" else "#cc6600"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <b style="color:#fff">{r['away']} @ {r['home']}</b>
            <span style="color:#888">Q{r['period']} {r['clock']}</span>
            <span style="color:#888">{r['total']}pts/{r['mins']:.0f}min</span>
            <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
            <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {r['safe_line']}</span>
            <span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
            <span style="color:{r['pace_color']}">{r['pace_status']}</span>
        </div>
        <a href="{kalshi_url}" target="_blank" style="background:{btn_color};color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY {cush_side} {r['safe_line']}</a>
        </div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for all live games")

pace_data = []
for g in games:
    total = g['home_score'] + g['away_score']
    mins = get_minutes_played(g['period'], g['clock'], g['status'])
    if mins >= 6:
        pace = round(total / mins, 2)
        pace_data.append({
            "home": g['home'], "away": g['away'], "pace": pace, "proj": round(pace * 48),
            "total": total, "mins": mins, "period": g['period'], "clock": g['clock'],
            "final": g['status'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        kalshi_url = build_kalshi_totals_url(p['away'], p['home'])
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
            base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1)
            safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#00aa00;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY NO {rec_line}</a>' if not p['final'] else ""
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
            btn_html = ""
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#cc6600;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#cc0000;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <b style="color:#fff">{p['away']} @ {p['home']}</b>
            <span style="color:#666">{status}</span>
            <span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span>
            <span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span>
            <span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>
        <div>{btn_html}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ============================================================
# 📈 POSITION TRACKER
# ============================================================
st.subheader("📈 ACTIVE POSITIONS")

import json
import os

POSITIONS_FILE = "nba_positions.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except: pass

if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None

# Build games dict for lookup
games_dict = {f"{g['away']}@{g['home']}": g for g in games}

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        gk = pos['game']
        g = games_dict.get(gk)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        pos_type = pos.get('type', 'ml')
        cost = round(price * contracts / 100, 2)
        potential = round((100 - price) * contracts / 100, 2)
        
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            
            if pos_type == 'ml':
                pick_score = g['home_score'] if pick == parts[1] else g['away_score']
                opp_score = g['away_score'] if pick == parts[1] else g['home_score']
                lead = pick_score - opp_score
            else:
                pick_score = g['home_score'] + g['away_score']
                lead = 0
            
            is_final = g['status'] == "STATUS_FINAL"
            
            if pos_type == 'ml':
                if is_final:
                    won = pick_score > opp_score
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    if lead >= 10: label, clr = "🟢 CRUISING", "#00ff00"
                    elif lead >= 0: label, clr = "🟡 CLOSE", "#ffff00"
                    else: label, clr = "🔴 BEHIND", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            else:
                threshold = float(str(pos.get('pick', '230.5')).split()[-1]) if pos.get('pick') else 230.5
                side = 'YES' if 'YES' in str(pos.get('pick', '')).upper() else 'NO'
                total = g['home_score'] + g['away_score']
                if is_final:
                    won = (total > threshold) if side == 'YES' else (total < threshold)
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    mins = get_minutes_played(g['period'], g['clock'], g['status'])
                    pace_val = total / mins if mins > 0 else 0
                    if side == 'NO':
                        if pace_val < 4.5: label, clr = "🟢 SAFE", "#00ff00"
                        elif pace_val < 4.8: label, clr = "🟡 WARNING", "#ffff00"
                        else: label, clr = "🔴 DANGER", "#ff0000"
                    else:
                        if pace_val > 5.2: label, clr = "🟢 SAFE", "#00ff00"
                        elif pace_val > 4.8: label, clr = "🟡 WARNING", "#ffff00"
                        else: label, clr = "🔴 DANGER", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            
            status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
            type_label = "ML" if pos_type == "ml" else "TOTAL"
            
            st.markdown(f"""<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid {clr};margin-bottom:6px'>
                <div style='display:flex;justify-content:space-between'><b style='color:#fff'>{gk.replace('@', ' @ ')}</b> <span style='color:#888'>{status}</span> <b style='color:{clr}'>{label}</b></div>
                <div style='color:#aaa;margin-top:4px;font-size:0.85em'>🎯 {type_label}: {pick} | {contracts}x @ {price}¢ | {pnl}</div></div>""", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
            
            if st.session_state.editing_position == idx:
                ec1, ec2, ec3 = st.columns(3)
                with ec1: new_type = st.selectbox("Type", ["ml", "totals"], index=0 if pos_type == "ml" else 1, key=f"et_{idx}")
                with ec2: new_price = st.number_input("Price ¢", 1, 99, price, key=f"ep_{idx}")
                with ec3: new_contracts = st.number_input("Contracts", 1, 100, contracts, key=f"ec_{idx}")
                if new_type == "ml":
                    new_pick = st.radio("Pick", [parts[1], parts[0]], index=0 if pick == parts[1] else 1, horizontal=True, key=f"epk_{idx}")
                else:
                    tc1, tc2 = st.columns(2)
                    with tc1: side = st.radio("Side", ["YES", "NO"], horizontal=True, key=f"es_{idx}")
                    with tc2: line = st.selectbox("Line", THRESHOLDS, index=5, key=f"el_{idx}")
                    new_pick = f"{side} {line}"
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save", key=f"sv_{idx}", type="primary", use_container_width=True):
                        st.session_state.positions[idx] = {"game": gk, "type": new_type, "pick": new_pick, "price": new_price, "contracts": new_contracts}
                        save_positions(st.session_state.positions)
                        st.session_state.editing_position = None
                        st.rerun()
                with bc2:
                    if st.button("❌ Cancel", key=f"cn_{idx}", use_container_width=True):
                        st.session_state.editing_position = None
                        st.rerun()
        else:
            st.markdown(f"<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid #888;margin-bottom:6px;color:#888'>{gk} — Game not found</div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_old_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("🗑️ Clear All Positions", key="clear_all", use_container_width=True):
        st.session_state.positions = []
        st.session_state.editing_position = None
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No active positions — add picks below")

st.divider()

# ============================================================
# ➕ ADD POSITION
# ============================================================
st.subheader("➕ ADD POSITION")

game_list = [f"{g['away']} @ {g['home']}" for g in games]
game_opts = ["Select..."] + game_list

sel = st.selectbox("Game", game_opts, key="add_game")

if sel != "Select...":
    parts = sel.replace(" @ ", "@").split("@")
    pos_type = st.radio("Type", ["Moneyline", "Totals"], horizontal=True, key="add_type")
    
    if pos_type == "Moneyline":
        p1, p2, p3 = st.columns(3)
        with p1: add_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True, key="add_pick")
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_ml")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_ml")
        if st.button("✅ ADD ML POSITION", key="add_ml", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "ml", "pick": add_pick, "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()
    else:
        t1, t2 = st.columns(2)
        with t1: side = st.radio("Side", ["YES", "NO"], horizontal=True, key="add_side")
        with t2: line = st.selectbox("Line", THRESHOLDS, index=5, key="add_line")
        p2, p3 = st.columns(2)
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_tot")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_tot")
        if st.button("✅ ADD TOTALS POSITION", key="add_tot", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "totals", "pick": f"{side} {line}", "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()

st.divider()
st.caption("⚠️ Educational only. Not financial advice. v2.0")
