import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
from styles import apply_styles, buy_button

st.set_page_config(page_title="NCAA Edge Finder", page_icon="🎓", layout="wide")

# ============================================================
# AUTHENTICATION CHECK
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.switch_page("Home.py")

apply_styles()

# ========== GOOGLE ANALYTICS G4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== MOBILE CSS FIX ==========
st.markdown("""
<style>
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        div[data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; }
        .stButton button { padding: 8px 12px !important; font-size: 14px !important; }
    }
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

POSITIONS_FILE = "ncaa_positions.json"

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

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "ncaa_positions" not in st.session_state:
    st.session_state.ncaa_positions = load_positions()
if "selected_ncaa_pick" not in st.session_state:
    st.session_state.selected_ncaa_pick = None

if st.session_state.auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={int(time.time()) + 30}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

# Conference tiers for strength calculation
POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}

# Team code mapping (common teams - ESPN abbreviation to Kalshi code)
# Kalshi uses lowercase codes like: duke, unc, kansas, etc.
TEAM_CODES = {}  # Will be populated dynamically from ESPN data

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_kalshi_ncaa_url(team1_code, team2_code):
    """Build Kalshi NCAA basketball URL - format: kxncaambgame-{YY}{MMM}{DD}{team1}{team2}"""
    date_str = datetime.now(eastern).strftime("%y%b%d").lower()
    t1 = team1_code.lower().replace(" ", "").replace(".", "").replace("'", "")[:4]
    t2 = team2_code.lower().replace(" ", "").replace(".", "").replace("'", "")[:4]
    ticker = f"KXNCAAMBGAME-{date_str.upper()}{t1.upper()}{t2.upper()}"
    return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"

def fetch_espn_ncaa_scores():
    """Fetch NCAA basketball scores from ESPN API"""
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today_date}&limit=100"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            home_abbrev, away_abbrev = "", ""
            home_rank, away_rank = 0, 0
            home_record, away_record = "", ""
            home_conf, away_conf = "", ""
            
            for c in competitors:
                team_data = c.get("team", {})
                name = team_data.get("displayName", team_data.get("name", ""))
                abbrev = team_data.get("abbreviation", name[:4].upper())
                score = int(c.get("score", 0) or 0)
                rank_obj = c.get("curatedRank", {})
                rank = rank_obj.get("current", 0) if rank_obj else 0
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                
                # Try to get conference
                conf = ""
                for rec in records:
                    if rec.get("type") == "conference":
                        conf = rec.get("name", "")
                        break
                
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbrev = name, score, abbrev
                    home_rank, home_record, home_conf = rank, record, conf
                else:
                    away_team, away_score, away_abbrev = name, score, abbrev
                    away_rank, away_record, away_conf = rank, record, conf
            
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            
            game_key = f"{away_abbrev}@{home_abbrev}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "away_score": away_score, "home_score": home_score,
                "away_rank": away_rank, "home_rank": home_rank,
                "away_record": away_record, "home_record": home_record,
                "away_conf": away_conf, "home_conf": home_conf,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except Exception as e:
        st.error(f"Error fetching ESPN data: {e}")
        return {}

def fetch_yesterday_teams():
    """Fetch teams that played yesterday for B2B detection"""
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={yesterday}&limit=100"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                abbrev = c.get("team", {}).get("abbreviation", "")
                if abbrev: teams.add(abbrev)
        return teams
    except:
        return set()

@st.cache_data(ttl=3600)
def fetch_ap_rankings():
    """Fetch current AP Top 25 rankings"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rankings = {}
        for ranking_group in data.get("rankings", []):
            if ranking_group.get("name") == "AP Top 25":
                for team in ranking_group.get("ranks", []):
                    abbrev = team.get("team", {}).get("abbreviation", "")
                    rank = team.get("current", 0)
                    if abbrev: rankings[abbrev] = rank
                break
        return rankings
    except:
        return {}

def get_conference_tier(conf_name):
    """Return tier based on conference strength"""
    if not conf_name: return 3
    if any(p in conf_name for p in POWER_CONFERENCES): return 1
    if any(h in conf_name for h in HIGH_MAJOR): return 2
    return 3

def get_minutes_played(period, clock, status_type):
    """Calculate minutes played in game"""
    if status_type == "STATUS_FINAL": return 40
    if status_type == "STATUS_HALFTIME": return 20
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        # College basketball: 2 x 20 minute halves
        if period == 1: return 20 - time_left
        elif period == 2: return 20 + (20 - time_left)
        else: return 40 + (period - 2) * 5 + (5 - time_left)  # OT
    except:
        return (period - 1) * 20 if period <= 2 else 40 + (period - 2) * 5

def calc_ncaa_score(home_team, away_team, home_abbrev, away_abbrev, 
                    home_rank, away_rank, home_conf, away_conf,
                    home_record, away_record, yesterday_teams, rankings):
    """Calculate edge score for NCAA matchup - proprietary multi-factor model"""
    sh, sa = 0, 0  # Score for home/away
    rh, ra = [], []  # Reasons for home/away
    
    # 1. HOME COURT ADVANTAGE (1.5x weight - stronger in college)
    sh += 1.5
    rh.append("🏠 Home Court")
    
    # 2. AP RANKING DIFFERENTIAL (1.5x weight)
    h_rank = home_rank if home_rank > 0 else rankings.get(home_abbrev, 0)
    a_rank = away_rank if away_rank > 0 else rankings.get(away_abbrev, 0)
    
    if h_rank > 0 and a_rank == 0:
        sh += 1.5
        rh.append(f"📊 #{h_rank} Ranked")
    elif a_rank > 0 and h_rank == 0:
        sa += 1.5
        ra.append(f"📊 #{a_rank} Ranked")
    elif h_rank > 0 and a_rank > 0:
        if a_rank - h_rank >= 10:
            sh += 1.0
            rh.append(f"📊 #{h_rank} vs #{a_rank}")
        elif h_rank - a_rank >= 10:
            sa += 1.0
            ra.append(f"📊 #{a_rank} vs #{h_rank}")
    
    # 3. CONFERENCE STRENGTH (1.2x weight)
    h_tier = get_conference_tier(home_conf)
    a_tier = get_conference_tier(away_conf)
    if h_tier < a_tier:  # Lower tier = stronger
        sh += 0.8
        rh.append("🏆 Power Conf")
    elif a_tier < h_tier:
        sa += 0.8
        ra.append("🏆 Power Conf")
    
    # 4. BACK-TO-BACK FATIGUE (1.0x weight - rare in college)
    home_b2b = home_abbrev in yesterday_teams
    away_b2b = away_abbrev in yesterday_teams
    if away_b2b and not home_b2b:
        sh += 1.0
        rh.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        sa += 1.0
        ra.append("🛏️ Opp B2B")
    
    # 5. RECORD ANALYSIS (1.2x weight)
    try:
        h_wins, h_losses = map(int, home_record.split("-")[:2]) if home_record else (0, 0)
        a_wins, a_losses = map(int, away_record.split("-")[:2]) if away_record else (0, 0)
        h_pct = h_wins / (h_wins + h_losses) if (h_wins + h_losses) > 0 else 0.5
        a_pct = a_wins / (a_wins + a_losses) if (a_wins + a_losses) > 0 else 0.5
        
        if h_pct - a_pct > 0.20:
            sh += 1.0
            rh.append(f"📈 {home_record}")
        elif a_pct - h_pct > 0.20:
            sa += 1.0
            ra.append(f"📈 {away_record}")
    except:
        pass
    
    # 6. RANKED VS UNRANKED BONUS
    if h_rank > 0 and h_rank <= 10 and a_rank == 0:
        sh += 1.0
        rh.append("🔝 Top 10")
    elif a_rank > 0 and a_rank <= 10 and h_rank == 0:
        sa += 1.0
        ra.append("🔝 Top 10")
    
    # Calculate final scores
    total = sh + sa
    hf = round((sh / total) * 10, 1) if total > 0 else 5.0
    af = round((sa / total) * 10, 1) if total > 0 else 5.0
    
    if hf >= af:
        return home_abbrev, home_team, hf, rh[:4], h_rank
    else:
        return away_abbrev, away_team, af, ra[:4], a_rank

def get_signal_tier(score):
    """STRICT TIER SYSTEM - Only 10.0 = STRONG BUY (tracked)"""
    if score >= 10.0:
        return "🔒 STRONG", "#00ff00", True
    elif score >= 8.0:
        return "🔵 BUY", "#00aaff", False
    elif score >= 5.5:
        return "🟡 LEAN", "#ffaa00", False
    else:
        return "⚪ PASS", "#666666", False

# FETCH DATA
games = fetch_espn_ncaa_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
rankings = fetch_ap_rankings()
now = datetime.now(eastern)

# Filter yesterday teams to only include today's teams
today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams.intersection(today_teams)

# SIDEBAR
with st.sidebar:
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔒 **STRONG** → 10.0
<span style="color:#888;font-size:0.85em">Tracked in stats</span>

🔵 **BUY** → 8.0-9.9
<span style="color:#888;font-size:0.85em">Informational only</span>

🟡 **LEAN** → 5.5-7.9
<span style="color:#888;font-size:0.85em">Slight edge</span>

⚪ **PASS** → Below 5.5
<span style="color:#888;font-size:0.85em">No edge</span>
""", unsafe_allow_html=True)
    st.divider()
    st.header("🎓 NCAA FACTORS")
    st.markdown("""
<span style="color:#888;font-size:0.85em">
• Home Court (1.5x)<br>
• AP Rankings<br>
• Conference Tier<br>
• Win % Differential<br>
• Back-to-Back<br>
• Ranked vs Unranked
</span>
""", unsafe_allow_html=True)
    st.divider()
    st.caption("v1.0 NCAA EDGE")

# TITLE
st.title("🎓 NCAA EDGE FINDER")
st.caption("College Basketball Edge Detection | v1.0")

# STATS SUMMARY
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Today's Games", len(games))
with col2:
    ranked_games = sum(1 for g in games.values() if g['home_rank'] > 0 or g['away_rank'] > 0)
    st.metric("Ranked Matchups", ranked_games)
with col3:
    st.metric("B2B Teams", len(yesterday_teams))

st.divider()

# LIVE GAMES
live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}
if live_games:
    st.subheader("⚡ LIVE GAMES")
    hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
    hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')}")
    if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True, key="auto_live"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        st.rerun()
    if hdr3.button("🔄 Now", use_container_width=True, key="refresh_live"):
        st.rerun()
    
    for gk, g in live_games.items():
        half, clock = g['period'], g['clock']
        diff = abs(g['home_score'] - g['away_score'])
        mins = get_minutes_played(half, clock, g['status_type'])
        pace = round(g['total'] / mins, 2) if mins > 0 else 0
        proj = round(pace * 40) if mins > 0 else 0
        
        # OT check
        if half >= 3:
            state, clr = "OT", "#ff0000"
        elif half == 2 and diff <= 8:
            state, clr = "CLOSE", "#ffaa00"
        else:
            state, clr = "LIVE", "#44ff44"
        
        # Format rankings
        away_display = f"#{g['away_rank']} " if g['away_rank'] > 0 else ""
        home_display = f"#{g['home_rank']} " if g['home_rank'] > 0 else ""
        half_label = "H1" if half == 1 else "H2" if half == 2 else f"OT{half-2}"
        
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:12px;border-radius:10px;border:2px solid {clr};margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <b style="color:#fff;font-size:1.1em">{escape_html(away_display)}{escape_html(g['away_abbrev'])} {g['away_score']} @ {escape_html(home_display)}{escape_html(g['home_abbrev'])} {g['home_score']}</b>
                <div><span style="color:{clr};font-weight:bold">{half_label} {escape_html(clock)}</span> | <span style="color:#888">Pace: {pace}/min → {proj}</span></div>
            </div></div>""", unsafe_allow_html=True)
    st.divider()

# ML PICKS - COMPACT DESIGN
st.subheader("🎯 ML PICKS")

if games:
    ml_results = []
    for gk, g in games.items():
        try:
            pick_abbrev, pick_name, score, reasons, pick_rank = calc_ncaa_score(
                g["home_team"], g["away_team"],
                g["home_abbrev"], g["away_abbrev"],
                g["home_rank"], g["away_rank"],
                g["home_conf"], g["away_conf"],
                g["home_record"], g["away_record"],
                yesterday_teams, rankings
            )
            tier, color, is_tracked = get_signal_tier(score)
            is_home = pick_abbrev == g["home_abbrev"]
            opp_abbrev = g["away_abbrev"] if is_home else g["home_abbrev"]
            opp_rank = g["away_rank"] if is_home else g["home_rank"]
            
            ml_results.append({
                "pick_abbrev": pick_abbrev, "pick_name": pick_name,
                "opp_abbrev": opp_abbrev, "pick_rank": pick_rank, "opp_rank": opp_rank,
                "score": score, "color": color, "tier": tier, "reasons": reasons,
                "is_home": is_home, "away_abbrev": g["away_abbrev"], "home_abbrev": g["home_abbrev"],
                "is_tracked": is_tracked, "game_key": gk
            })
        except Exception as e:
            continue
    
    ml_results.sort(key=lambda x: x["score"], reverse=True)
    
    for r in ml_results:
        if r["score"] < 5.5:
            continue
        
        kalshi_url = build_kalshi_ncaa_url(r["away_abbrev"], r["home_abbrev"])
        reasons_safe = [escape_html(reason) for reason in r["reasons"][:3]]
        reasons_str = " · ".join(reasons_safe)
        
        g = games.get(r["game_key"], {})
        if g.get('status_type') == "STATUS_FINAL":
            status_badge, status_color = "FINAL", "#888"
        elif g.get('period', 0) > 0:
            half_label = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}"
            status_badge = f"{half_label} {escape_html(g.get('clock', ''))}"
            status_color = "#ff4444"
        else:
            status_badge, status_color = "PRE", "#00ff00"
        
        tracked_badge = ' <span style="background:#00ff00;color:#000;padding:1px 4px;border-radius:3px;font-size:0.65em">📊</span>' if r["is_tracked"] else ""
        border_width = "3px" if r["is_tracked"] else "2px"
        
        pick_display = f"#{r['pick_rank']} " if r['pick_rank'] > 0 else ""
        opp_display = f"#{r['opp_rank']} " if r['opp_rank'] > 0 else ""
        
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;border-radius:6px;border-left:{border_width} solid {r['color']};margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
<span style="color:{r['color']};font-weight:bold;font-size:0.85em">{escape_html(r['tier'])}</span>
<b style="color:#fff">{escape_html(pick_display)}{escape_html(r['pick_abbrev'])}</b>
<span style="color:#555">v {escape_html(opp_display)}{escape_html(r['opp_abbrev'])}</span>
<span style="color:#38bdf8;font-weight:bold">{r['score']}</span>{tracked_badge}
<span style="color:{status_color};font-size:0.75em">{status_badge}</span>
</div>
<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:4px 10px;border-radius:4px;font-size:0.75em;font-weight:bold;text-decoration:none">BUY</a>
</div>
<div style="color:#666;font-size:0.75em;margin:-2px 0 6px 14px">{reasons_str}</div>""", unsafe_allow_html=True)
    
    # Add STRONG picks to tracker
    scheduled_strong = [r for r in ml_results if r["is_tracked"] and games.get(r["game_key"], {}).get('status_type') == "STATUS_SCHEDULED"]
    if scheduled_strong:
        if st.button(f"➕ Add {len(scheduled_strong)} STRONG Picks to Tracker", use_container_width=True, key="add_ncaa_picks"):
            added = 0
            for r in scheduled_strong:
                if not any(p.get('game') == r['game_key'] and p.get('pick') == r['pick_abbrev'] for p in st.session_state.ncaa_positions):
                    st.session_state.ncaa_positions.append({
                        "game": r['game_key'], "type": "ml", 
                        "pick": r['pick_abbrev'], "pick_name": r['pick_name'],
                        "price": 50, "contracts": 1, "tracked": True
                    })
                    added += 1
            if added:
                save_positions(st.session_state.ncaa_positions)
                st.rerun()
else:
    st.info("No games today — check back later!")

st.divider()

# AP TOP 25 RANKINGS
st.subheader("📊 AP TOP 25")
st.caption("Current rankings from AP Poll")

if rankings:
    sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
    
    rc1, rc2 = st.columns(2)
    for i, (abbrev, rank) in enumerate(sorted_rankings[:25]):
        with rc1 if i < 13 else rc2:
            if rank <= 5:
                clr = "#00ff00"
            elif rank <= 10:
                clr = "#88ff00"
            elif rank <= 15:
                clr = "#ffff00"
            else:
                clr = "#ffaa00"
            
            st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:5px 8px;margin-bottom:2px;border-radius:4px;border-left:2px solid {clr}">
                <div style="display:flex;align-items:center;gap:8px">
                    <span style="color:{clr};font-weight:bold;width:24px">#{rank}</span>
                    <span style="color:#fff;font-weight:bold">{escape_html(abbrev)}</span>
                </div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("Rankings unavailable")

st.divider()

# B2B TRACKER
if yesterday_teams:
    st.subheader("🛏️ BACK-TO-BACK TEAMS")
    st.caption("Teams that played yesterday (rare in college)")
    b2b_cols = st.columns(4)
    for i, team in enumerate(sorted(yesterday_teams)):
        with b2b_cols[i % 4]:
            st.markdown(f"""<div style="background:#2a1a1a;padding:6px;border-radius:5px;border:1px solid #ff6666;text-align:center">
                <span style="color:#ff6666;font-weight:bold;font-size:0.9em">{escape_html(team)}</span> <span style="color:#888;font-size:0.8em">B2B</span>
            </div>""", unsafe_allow_html=True)
    st.divider()

# ACTIVE POSITIONS
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.ncaa_positions:
    for idx, pos in enumerate(st.session_state.ncaa_positions):
        gk = pos['game']
        g = games.get(gk)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        cost = round(price * contracts / 100, 2)
        potential = round((100 - price) * contracts / 100, 2)
        is_tracked_pos = pos.get('tracked', False)
        
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            pick_score = g['home_score'] if pick == parts[1] else g['away_score']
            opp_score = g['away_score'] if pick == parts[1] else g['home_score']
            lead = pick_score - opp_score
            is_final = g['status_type'] == "STATUS_FINAL"
            
            if is_final:
                won = pick_score > opp_score
                label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
            elif g['period'] > 0:
                if lead >= 10:
                    label, clr = "🟢 CRUISING", "#00ff00"
                elif lead >= 0:
                    label, clr = "🟡 CLOSE", "#ffff00"
                else:
                    label, clr = "🔴 BEHIND", "#ff0000"
                pnl = f"Win: +${potential:.2f}"
            else:
                label, clr = "⏳ PENDING", "#888"
                pnl = f"Win: +${potential:.2f}"
            
            half_label = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}" if g['period'] > 2 else ""
            status = "FINAL" if is_final else f"{half_label} {escape_html(g['clock'])}" if g['period'] > 0 else "Scheduled"
            tracked_badge = '<span style="background:#00ff00;color:#000;padding:1px 4px;border-radius:3px;font-size:0.7em;margin-left:6px;">📊</span>' if is_tracked_pos else ''
            
            st.markdown(f"""<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid {clr};margin-bottom:6px'>
                <div style='display:flex;justify-content:space-between;font-size:0.9em'><b style='color:#fff'>{escape_html(gk.replace('@', ' @ '))}</b>{tracked_badge} <span style='color:#888'>{status}</span> <b style='color:{clr}'>{label}</b></div>
                <div style='color:#aaa;margin-top:4px;font-size:0.8em'>🎯 {escape_html(pick)} | {contracts}x @ {price}¢ | Lead: {lead:+d} | {pnl}</div></div>""", unsafe_allow_html=True)
            
            kalshi_url = build_kalshi_ncaa_url(parts[0], parts[1])
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<a href='{kalshi_url}' target='_blank' style='color:#38bdf8;font-size:0.8em'>🔗 Trade</a>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_ncaa_{idx}"):
                    st.session_state.ncaa_positions.pop(idx)
                    save_positions(st.session_state.ncaa_positions)
                    st.rerun()
else:
    st.info("No active positions")

st.divider()

# ALL GAMES - COMPACT
st.subheader("📺 ALL GAMES")
st.caption(f"{len(games)} games today")

if games:
    for gk, g in sorted(games.items()):
        away_display = f"#{g['away_rank']} " if g['away_rank'] > 0 else ""
        home_display = f"#{g['home_rank']} " if g['home_rank'] > 0 else ""
        
        if g['status_type'] == "STATUS_FINAL":
            winner = g['home_abbrev'] if g['home_score'] > g['away_score'] else g['away_abbrev']
            status, clr = f"✅ {escape_html(winner)}", "#44ff44"
        elif g['period'] > 0:
            half_label = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}"
            status, clr = f"🔴 {half_label} {escape_html(g['clock'])}", "#ff4444"
        else:
            status, clr = "📅", "#888"
        
        st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#0f172a;padding:6px 10px;margin-bottom:3px;border-radius:5px;border-left:2px solid {clr};font-size:0.9em">
            <div><b style="color:#fff">{escape_html(away_display)}{escape_html(g['away_abbrev'])}</b> {g['away_score']} @ <b style="color:#fff">{escape_html(home_display)}{escape_html(g['home_abbrev'])}</b> {g['home_score']}</div>
            <span style="color:{clr}">{status}</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games today")

st.divider()

# HOW TO USE - COLLAPSED
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
### 🎓 **Getting Started**

**NCAA Edge Finder** detects mispricings in Kalshi college basketball markets.

---

### 📊 **Signal Tiers (STRICT)**

| Tier | Score | Tracked? | Meaning |
|------|-------|----------|---------|
| 🔒 **STRONG** | 10.0 | ✅ YES | Headline pick — counts in stats |
| 🔵 **BUY** | 8.0-9.9 | ❌ NO | Good value — informational only |
| 🟡 **LEAN** | 5.5-7.9 | ❌ NO | Slight edge |
| ⚪ **PASS** | <5.5 | ❌ NO | No clear edge |

---

### 🏀 **Key NCAA Factors**

- **Home Court** — Bigger impact in college (student sections!)
- **AP Rankings** — Ranked vs unranked matters
- **Conference Strength** — Power 5 vs mid-major
- **Win %** — Record differential
- **Back-to-Back** — Rare but impactful

---

### ⚠️ **College Basketball Differences**

1. **More variance** — Upsets happen more often
2. **Home court stronger** — 1.5x vs 1.0x in NBA
3. **Less data** — No advanced stats
4. **350+ teams** — Kalshi covers major matchups

---

### 🔗 **Trading**

Click **BUY** buttons to go directly to Kalshi markets.

---

*Built for Kalshi. v1.0*
""")

st.divider()
st.caption("⚠️ Educational only. Not financial advice. v1.0 NCAA EDGE")
st.caption("📧 Contact: william@bigsnapshot.com")
