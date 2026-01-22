import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
from styles import apply_styles, buy_button
import extra_streamlit_components as stx

st.set_page_config(page_title="NCAA Edge Finder", page_icon="🎓", layout="wide")

apply_styles()

# ============================================================
# COOKIE MANAGER FOR PERSISTENT LOGIN
# ============================================================
cookie_manager = stx.CookieManager()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

auth_cookie = cookie_manager.get("bigsnapshot_auth")
if auth_cookie and not st.session_state.authenticated:
    st.session_state.authenticated = True
    st.session_state.user_type = auth_cookie

if not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

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

if st.session_state.auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={int(time.time()) + 30}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

# Conference tiers
POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}

def normalize_abbrev(abbrev):
    if not abbrev: return ""
    return abbrev.upper().strip()

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_kalshi_ncaa_url(team1_code, team2_code):
    try:
        if not team1_code or not team2_code: return None
        date_str = datetime.now(eastern).strftime("%y%b%d").upper()
        t1 = ''.join(c for c in team1_code.upper() if c.isalpha())[:4]
        t2 = ''.join(c for c in team2_code.upper() if c.isalpha())[:4]
        if len(t1) < 2 or len(t2) < 2: return None
        ticker = f"KXNCAAMBGAME-{date_str}{t1}{t2}"
        return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"
    except: return None

def get_buy_button_html(kalshi_url, label="BUY"):
    if kalshi_url:
        return f'<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:4px 10px;border-radius:4px;font-size:0.75em;font-weight:bold;text-decoration:none">{label}</a>'
    return f'<span style="background:#444;color:#888;padding:4px 10px;border-radius:4px;font-size:0.75em">Market N/A</span>'

def fetch_espn_ncaa_scores():
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
            home_record, away_record = "", ""
            home_conf, away_conf = "", ""
            
            for c in competitors:
                team_data = c.get("team", {})
                name = team_data.get("displayName", team_data.get("name", ""))
                abbrev = normalize_abbrev(team_data.get("abbreviation", name[:4]))
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                conf = ""
                for rec in records:
                    if rec.get("type") == "conference":
                        conf = rec.get("name", "")
                        break
                
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbrev = name, score, abbrev
                    home_record, home_conf = record, conf
                else:
                    away_team, away_score, away_abbrev = name, score, abbrev
                    away_record, away_conf = record, conf
            
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            
            game_key = f"{away_abbrev}@{home_abbrev}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "away_score": away_score, "home_score": home_score,
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
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={yesterday}&limit=100"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                abbrev = normalize_abbrev(c.get("team", {}).get("abbreviation", ""))
                if abbrev: teams.add(abbrev)
        return teams
    except: return set()

@st.cache_data(ttl=3600)
def fetch_ap_rankings():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rankings = {}
        for ranking_group in data.get("rankings", []):
            if ranking_group.get("name") == "AP Top 25":
                for team in ranking_group.get("ranks", []):
                    abbrev = normalize_abbrev(team.get("team", {}).get("abbreviation", ""))
                    rank = team.get("current", 0)
                    if abbrev and 1 <= rank <= 25:
                        rankings[abbrev] = rank
                break
        return rankings
    except: return {}

@st.cache_data(ttl=3600)
def fetch_team_streaks():
    streaks = {}
    try:
        dates = [(datetime.now(eastern) - timedelta(days=i)).strftime('%Y%m%d') for i in range(1, 14)]
        team_results = {}
        for date in dates:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date}&limit=100"
            resp = requests.get(url, timeout=8)
            data = resp.json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                for c in competitors:
                    abbrev = normalize_abbrev(c.get("team", {}).get("abbreviation", ""))
                    won = c.get("winner", False)
                    if abbrev:
                        if abbrev not in team_results: team_results[abbrev] = []
                        team_results[abbrev].append({"date": date, "won": won})
        for team, results in team_results.items():
            results.sort(key=lambda x: x['date'], reverse=True)
            if not results: continue
            streak = 0
            streak_type = results[0]['won']
            for r in results:
                if r['won'] == streak_type: streak += 1
                else: break
            streaks[team] = streak if streak_type else -streak
    except: pass
    return streaks

@st.cache_data(ttl=3600)
def fetch_team_home_away_splits():
    """Fetch home/away win rates for teams (last 14 days of data)"""
    splits = {}
    try:
        dates = [(datetime.now(eastern) - timedelta(days=i)).strftime('%Y%m%d') for i in range(1, 30)]
        for date in dates[:14]:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date}&limit=100"
            resp = requests.get(url, timeout=8)
            data = resp.json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                for c in competitors:
                    abbrev = normalize_abbrev(c.get("team", {}).get("abbreviation", ""))
                    won = c.get("winner", False)
                    is_home = c.get("homeAway") == "home"
                    if abbrev:
                        if abbrev not in splits:
                            splits[abbrev] = {"home_w": 0, "home_l": 0, "away_w": 0, "away_l": 0}
                        if is_home:
                            if won: splits[abbrev]["home_w"] += 1
                            else: splits[abbrev]["home_l"] += 1
                        else:
                            if won: splits[abbrev]["away_w"] += 1
                            else: splits[abbrev]["away_l"] += 1
    except: pass
    return splits

@st.cache_data(ttl=1800)
def fetch_cbb_news():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/news?limit=5"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "headline": article.get("headline", ""),
                "description": article.get("description", "")[:100] + "..." if article.get("description") else "",
                "link": article.get("links", {}).get("web", {}).get("href", "")
            })
        return articles
    except: return []

def get_conference_tier(conf_name):
    if not conf_name: return 3
    if any(p in conf_name for p in POWER_CONFERENCES): return 1
    if any(h in conf_name for h in HIGH_MAJOR): return 2
    return 3

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 40
    if status_type == "STATUS_HALFTIME": return 20
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period == 1: return 20 - time_left
        elif period == 2: return 20 + (20 - time_left)
        else: return 40 + (period - 2) * 5 + (5 - time_left)
    except:
        return (period - 1) * 20 if period <= 2 else 40 + (period - 2) * 5

# ============================================================
# ENGINE 1: MARKET EDGE ENGINE (EXISTING)
# Factors: Home court, AP rank, Conference tier, Record, B2B
# Output: Edge Score (0-10) + Tier
# ============================================================
def market_edge_engine(g, yesterday_teams, ap_rankings):
    """
    MARKET EDGE ENGINE - Evaluates market-based factors
    INDEPENDENT from Team Strength Analyzer
    """
    home_abbrev = g["home_abbrev"]
    away_abbrev = g["away_abbrev"]
    home_team = g["home_team"]
    away_team = g["away_team"]
    home_conf = g.get("home_conf", "")
    away_conf = g.get("away_conf", "")
    home_record = g.get("home_record", "")
    away_record = g.get("away_record", "")
    
    sh, sa = 0, 0
    rh, ra = [], []
    
    home_ap = ap_rankings.get(home_abbrev, 0)
    away_ap = ap_rankings.get(away_abbrev, 0)
    
    # 1. HOME COURT (1.5x)
    sh += 1.5
    rh.append("🏠 Home")
    
    # 2. AP RANKING (1.5x)
    if home_ap > 0 and away_ap == 0:
        sh += 1.5
        rh.append(f"📊 #{home_ap}")
    elif away_ap > 0 and home_ap == 0:
        sa += 1.5
        ra.append(f"📊 #{away_ap}")
    elif home_ap > 0 and away_ap > 0:
        if away_ap - home_ap >= 10:
            sh += 1.0
            rh.append(f"📊 #{home_ap}v#{away_ap}")
        elif home_ap - away_ap >= 10:
            sa += 1.0
            ra.append(f"📊 #{away_ap}v#{home_ap}")
    
    # 3. CONFERENCE TIER (0.8x)
    h_tier = get_conference_tier(home_conf)
    a_tier = get_conference_tier(away_conf)
    if h_tier < a_tier:
        sh += 0.8
        rh.append("🏆 Power")
    elif a_tier < h_tier:
        sa += 0.8
        ra.append("🏆 Power")
    
    # 4. B2B (1.0x)
    home_b2b = home_abbrev in yesterday_teams
    away_b2b = away_abbrev in yesterday_teams
    if away_b2b and not home_b2b:
        sh += 1.0
        rh.append("🛏️ OppB2B")
    elif home_b2b and not away_b2b:
        sa += 1.0
        ra.append("🛏️ OppB2B")
    
    # 5. RECORD (1.0x)
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
    except: pass
    
    # 6. TOP 10 BONUS (1.0x)
    if home_ap > 0 and home_ap <= 10 and away_ap == 0:
        sh += 1.0
        rh.append("🔝 Top10")
    elif away_ap > 0 and away_ap <= 10 and home_ap == 0:
        sa += 1.0
        ra.append("🔝 Top10")
    
    total = sh + sa
    hf = round((sh / total) * 10, 1) if total > 0 else 5.0
    af = round((sa / total) * 10, 1) if total > 0 else 5.0
    
    if hf >= af:
        return {
            "pick": home_abbrev, "pick_name": home_team,
            "pick_ap": home_ap, "opp": away_abbrev, "opp_ap": away_ap,
            "score": hf, "reasons": rh[:4], "is_home": True
        }
    else:
        return {
            "pick": away_abbrev, "pick_name": away_team,
            "pick_ap": away_ap, "opp": home_abbrev, "opp_ap": home_ap,
            "score": af, "reasons": ra[:4], "is_home": False
        }

def get_market_tier(score):
    """Market Engine tier assignment"""
    if score >= 9.8: return "🔒 STRONG", "#00ff00", True
    elif score >= 8.0: return "🔵 BUY", "#00aaff", False
    elif score >= 5.5: return "🟡 LEAN", "#ffaa00", False
    else: return "⚪ PASS", "#666666", False

# ============================================================
# ENGINE 2: TEAM STRENGTH ANALYZER (NEW)
# Factors: Recent form, Home/Away splits, Strength rating, Fatigue
# Output: Pick + Confidence (CONFIDENT / SLIGHT / NO EDGE)
# ============================================================
def team_strength_analyzer(g, streaks, splits, yesterday_teams, ap_rankings):
    """
    TEAM STRENGTH ANALYZER - Evaluates team performance factors
    INDEPENDENT from Market Edge Engine
    """
    home_abbrev = g["home_abbrev"]
    away_abbrev = g["away_abbrev"]
    
    sh, sa = 0, 0  # Strength scores
    
    # 1. RECENT FORM (streak-based)
    home_streak = streaks.get(home_abbrev, 0)
    away_streak = streaks.get(away_abbrev, 0)
    
    if home_streak >= 5: sh += 2.0
    elif home_streak >= 3: sh += 1.0
    elif home_streak <= -4: sa += 1.5
    elif home_streak <= -2: sa += 0.5
    
    if away_streak >= 5: sa += 2.0
    elif away_streak >= 3: sa += 1.0
    elif away_streak <= -4: sh += 1.5
    elif away_streak <= -2: sh += 0.5
    
    # 2. HOME/AWAY SPLITS
    home_split = splits.get(home_abbrev, {})
    away_split = splits.get(away_abbrev, {})
    
    # Home team's home record
    home_hw = home_split.get("home_w", 0)
    home_hl = home_split.get("home_l", 0)
    home_home_pct = home_hw / (home_hw + home_hl) if (home_hw + home_hl) >= 3 else 0.5
    
    # Away team's away record
    away_aw = away_split.get("away_w", 0)
    away_al = away_split.get("away_l", 0)
    away_away_pct = away_aw / (away_aw + away_al) if (away_aw + away_al) >= 3 else 0.5
    
    if home_home_pct >= 0.75: sh += 1.5
    elif home_home_pct >= 0.60: sh += 0.75
    
    if away_away_pct >= 0.75: sa += 1.5
    elif away_away_pct >= 0.60: sa += 0.75
    elif away_away_pct <= 0.33: sh += 1.0
    
    # 3. STRENGTH RATING (AP rank as proxy)
    home_ap = ap_rankings.get(home_abbrev, 0)
    away_ap = ap_rankings.get(away_abbrev, 0)
    
    if home_ap > 0 and home_ap <= 5: sh += 2.0
    elif home_ap > 0 and home_ap <= 15: sh += 1.0
    elif home_ap > 0: sh += 0.5
    
    if away_ap > 0 and away_ap <= 5: sa += 2.0
    elif away_ap > 0 and away_ap <= 15: sa += 1.0
    elif away_ap > 0: sa += 0.5
    
    # 4. FATIGUE DENSITY (B2B + recent games)
    home_b2b = home_abbrev in yesterday_teams
    away_b2b = away_abbrev in yesterday_teams
    
    if home_b2b: sa += 1.5
    if away_b2b: sh += 1.5
    
    # Calculate edge and confidence
    edge = sh - sa
    
    if edge >= 3.0:
        return {"pick": home_abbrev, "confidence": "CONFIDENT", "edge": round(edge, 1), "is_home": True}
    elif edge >= 1.5:
        return {"pick": home_abbrev, "confidence": "SLIGHT", "edge": round(edge, 1), "is_home": True}
    elif edge <= -3.0:
        return {"pick": away_abbrev, "confidence": "CONFIDENT", "edge": round(abs(edge), 1), "is_home": False}
    elif edge <= -1.5:
        return {"pick": away_abbrev, "confidence": "SLIGHT", "edge": round(abs(edge), 1), "is_home": False}
    else:
        # No clear edge - pick higher rated team but NO EDGE confidence
        if sh >= sa:
            return {"pick": home_abbrev, "confidence": "NO EDGE", "edge": round(edge, 1), "is_home": True}
        else:
            return {"pick": away_abbrev, "confidence": "NO EDGE", "edge": round(abs(edge), 1), "is_home": False}

# ============================================================
# UNIFIED ENGINE: COMBINE AT DECISION LAYER ONLY
# ============================================================
def get_final_signal(market_result, analyzer_result):
    """
    FINAL SIGNAL LOGIC - Combines both engines at decision layer
    NEVER blends scores mathematically
    """
    market_tier, market_color, market_tracked = get_market_tier(market_result["score"])
    analyzer_conf = analyzer_result["confidence"]
    
    # Check agreement
    engines_agree = market_result["pick"] == analyzer_result["pick"]
    
    # STRONG+ = STRONG + CONFIDENT + agreement
    if "STRONG" in market_tier and analyzer_conf == "CONFIDENT" and engines_agree:
        return {
            "final_tier": "🔒 STRONG+",
            "final_color": "#00ff00",
            "is_tracked": True,
            "engines_agree": True,
            "agreement_icon": "🧠"
        }
    
    # STRONG = STRONG only (no dual confirmation)
    elif "STRONG" in market_tier:
        return {
            "final_tier": "🔒 STRONG",
            "final_color": "#00ff00",
            "is_tracked": True,
            "engines_agree": engines_agree,
            "agreement_icon": "🧠" if engines_agree else "⚠️"
        }
    
    # BUY = BUY + CONFIDENT
    elif "BUY" in market_tier and analyzer_conf == "CONFIDENT" and engines_agree:
        return {
            "final_tier": "🔵 BUY",
            "final_color": "#00aaff",
            "is_tracked": False,
            "engines_agree": True,
            "agreement_icon": "🧠"
        }
    
    # LEAN = Everything else above threshold
    elif market_result["score"] >= 5.5:
        return {
            "final_tier": "🟡 LEAN",
            "final_color": "#ffaa00",
            "is_tracked": False,
            "engines_agree": engines_agree,
            "agreement_icon": "🧠" if engines_agree else "⚠️"
        }
    
    # PASS = Low score or disagreement
    else:
        return {
            "final_tier": "⚪ PASS",
            "final_color": "#666666",
            "is_tracked": False,
            "engines_agree": engines_agree,
            "agreement_icon": "⚠️" if not engines_agree else ""
        }

# ============================================================
# FETCH ALL DATA ONCE
# ============================================================
games = fetch_espn_ncaa_scores()
yesterday_teams = fetch_yesterday_teams()
ap_rankings = fetch_ap_rankings()
news = fetch_cbb_news()
streaks = fetch_team_streaks()
splits = fetch_team_home_away_splits()
now = datetime.now(eastern)

# Filter yesterday teams to today's teams only
today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams.intersection(today_teams)

# ============================================================
# PRECOMPUTE ALL SCORES WITH DUAL ENGINE
# ============================================================
precomputed = {}
for gk, g in games.items():
    try:
        # Run both engines independently
        market = market_edge_engine(g, yesterday_teams, ap_rankings)
        analyzer = team_strength_analyzer(g, streaks, splits, yesterday_teams, ap_rankings)
        final = get_final_signal(market, analyzer)
        
        precomputed[gk] = {
            "game_key": gk,
            "away_abbrev": g["away_abbrev"],
            "home_abbrev": g["home_abbrev"],
            "status_type": g.get("status_type", "STATUS_SCHEDULED"),
            # Market Engine results
            "market_pick": market["pick"],
            "market_pick_name": market["pick_name"],
            "market_pick_ap": market["pick_ap"],
            "market_opp": market["opp"],
            "market_opp_ap": market["opp_ap"],
            "market_score": market["score"],
            "market_reasons": market["reasons"],
            "market_is_home": market["is_home"],
            # Analyzer results
            "analyzer_pick": analyzer["pick"],
            "analyzer_conf": analyzer["confidence"],
            "analyzer_edge": analyzer["edge"],
            # Final combined signal
            "final_tier": final["final_tier"],
            "final_color": final["final_color"],
            "is_tracked": final["is_tracked"],
            "engines_agree": final["engines_agree"],
            "agreement_icon": final["agreement_icon"]
        }
    except: continue

# Sort by market score and assign pick_order
sorted_picks = sorted(precomputed.values(), key=lambda x: x["market_score"], reverse=True)
for idx, p in enumerate(sorted_picks, start=1):
    p["pick_order"] = idx
    precomputed[p["game_key"]]["pick_order"] = idx

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔒 **STRONG+** → Dual Confirmed
<span style="color:#888;font-size:0.85em">Market + Analyzer agree</span>

🔒 **STRONG** → 9.8+
<span style="color:#888;font-size:0.85em">Market signal only</span>

🔵 **BUY** → 8.0+ + Confident
<span style="color:#888;font-size:0.85em">Dual confirmation</span>

🟡 **LEAN** → 5.5+
<span style="color:#888;font-size:0.85em">Single engine</span>

⚪ **PASS** → No edge
""", unsafe_allow_html=True)
    st.divider()
    st.header("🧠 DUAL ENGINE")
    st.markdown("""
<span style="color:#888;font-size:0.85em">
**Engine 1: Market**<br>
• Home court • AP rank<br>
• Conference • Record • B2B<br><br>
**Engine 2: Analyzer**<br>
• Recent form • Splits<br>
• Strength • Fatigue
</span>
""", unsafe_allow_html=True)
    st.divider()
    st.caption("v2.0 DUAL ENGINE")

# ============================================================
# TITLE
# ============================================================
st.title("🎓 NCAA EDGE FINDER")
st.caption("Dual Confirmation Model | v2.0")
st.markdown("<p style='color:#888;font-size:0.85em;margin-top:-10px'>🧠 = Engines agree | ⚠️ = Engines disagree</p>", unsafe_allow_html=True)

# ============================================================
# 💰 TOP PICK OF THE DAY (ONLY IF STRONG+)
# ============================================================
def get_top_pick():
    scheduled = [p for p in sorted_picks if p.get('status_type') == "STATUS_SCHEDULED"]
    for p in scheduled:
        if "STRONG+" in p["final_tier"]:
            return p
    return None

top_pick = get_top_pick()
if top_pick:
    kalshi_url = build_kalshi_ncaa_url(top_pick["away_abbrev"], top_pick["home_abbrev"])
    buy_btn = get_buy_button_html(kalshi_url, "🎯 BUY NOW")
    ap_display = f"#{top_pick['market_pick_ap']} " if top_pick['market_pick_ap'] > 0 else ""
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a2a0a,#1a3a1a);padding:20px;border-radius:12px;border:3px solid #00ff00;margin:15px 0;text-align:center">
        <div style="color:#888;font-size:0.9em;margin-bottom:8px">💰 TOP PICK OF THE DAY — DUAL CONFIRMED</div>
        <div style="font-size:2.2em;font-weight:bold;color:#fff;margin-bottom:5px">{escape_html(ap_display)}{escape_html(top_pick['market_pick'])} 🧠</div>
        <div style="color:#00ff00;font-size:1.4em;font-weight:bold;margin-bottom:10px">{top_pick['final_tier']} {top_pick['market_score']}/10</div>
        <div style="color:#aaa;font-size:0.9em;margin-bottom:8px">vs {escape_html(top_pick['market_opp'])} • {' · '.join(top_pick['market_reasons'][:3])}</div>
        <div style="color:#38bdf8;font-size:0.85em;margin-bottom:12px">Analyzer: {top_pick['analyzer_conf']} ({top_pick['analyzer_edge']} edge)</div>
        <div>{buy_btn if kalshi_url else '<span style="color:#666">Market loading...</span>'}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background:#1a1a2e;padding:15px;border-radius:8px;text-align:center;margin:15px 0;border:1px solid #333">
        <span style="color:#888">No STRONG+ picks today — engines not aligned on any game</span>
    </div>
    """, unsafe_allow_html=True)

# STATS SUMMARY
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Games", len(games))
with col2:
    strong_plus = sum(1 for p in sorted_picks if "STRONG+" in p["final_tier"])
    st.metric("🔒 STRONG+", strong_plus)
with col3:
    agreed = sum(1 for p in sorted_picks if p["engines_agree"])
    st.metric("🧠 Aligned", f"{agreed}/{len(sorted_picks)}")
with col4:
    strong_wins = sum(1 for pos in st.session_state.ncaa_positions 
                      if pos.get('tracked') and games.get(pos.get('game'), {}).get('status_type') == "STATUS_FINAL"
                      and ((pos.get('pick') == pos.get('game', '').split('@')[1] and games.get(pos.get('game'), {}).get('home_score', 0) > games.get(pos.get('game'), {}).get('away_score', 0))
                           or (pos.get('pick') == pos.get('game', '').split('@')[0] and games.get(pos.get('game'), {}).get('away_score', 0) > games.get(pos.get('game'), {}).get('home_score', 0))))
    strong_total = sum(1 for pos in st.session_state.ncaa_positions 
                       if pos.get('tracked') and games.get(pos.get('game'), {}).get('status_type') == "STATUS_FINAL")
    st.metric("📊 Today", f"{strong_wins}-{strong_total - strong_wins}" if strong_total > 0 else "0-0")

# LEGEND
st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);padding:12px 16px;border-radius:8px;margin:10px 0;border:1px solid #333">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div style="display:flex;align-items:center;gap:15px;flex-wrap:wrap">
            <span style="color:#00ff00;font-weight:bold">🔒 STRONG+ (dual)</span>
            <span style="color:#00ff00">🔒 STRONG</span>
            <span style="color:#00aaff">🔵 BUY</span>
            <span style="color:#ffaa00">🟡 LEAN</span>
            <span style="color:#666">⚪ PASS</span>
        </div>
        <span style="color:#888;font-size:0.8em">🧠 agree | ⚠️ disagree</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Status indicator
scheduled_games = [g for g in games.values() if g.get('status_type') == "STATUS_SCHEDULED"]
if scheduled_games and not live_games:
    st.markdown(f"""<div style="background:#1a1a2e;padding:10px 15px;border-radius:6px;text-align:center;margin-bottom:10px;border-left:3px solid #38bdf8">
        <span style="color:#38bdf8;font-weight:bold">⏰ {len(scheduled_games)} games scheduled</span>
    </div>""", unsafe_allow_html=True)
elif live_games:
    st.markdown(f"""<div style="background:#1a2a1a;padding:10px 15px;border-radius:6px;text-align:center;margin-bottom:10px;border-left:3px solid #00ff00">
        <span style="color:#00ff00;font-weight:bold">🔴 {len(live_games)} LIVE NOW</span>
    </div>""", unsafe_allow_html=True)

st.divider()

# 📰 NEWS
if news:
    st.subheader("📰 BREAKING NEWS")
    for article in news[:3]:
        if article.get("headline"):
            link = article.get("link", "#")
            st.markdown(f"""<div style="background:#0f172a;padding:10px 12px;border-radius:6px;margin-bottom:6px;border-left:3px solid #38bdf8">
                <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;font-weight:bold;font-size:0.95em">{escape_html(article['headline'])}</a>
            </div>""", unsafe_allow_html=True)
    st.divider()

# LIVE GAMES
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
        
        if half >= 3: state, clr = "OT", "#ff0000"
        elif half == 2 and diff <= 8: state, clr = "CLOSE", "#ffaa00"
        else: state, clr = "LIVE", "#44ff44"
        
        away_ap = ap_rankings.get(g['away_abbrev'], 0)
        home_ap = ap_rankings.get(g['home_abbrev'], 0)
        away_display = f"#{away_ap} " if away_ap > 0 else ""
        home_display = f"#{home_ap} " if home_ap > 0 else ""
        half_label = "H1" if half == 1 else "H2" if half == 2 else f"OT{half-2}"
        
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:12px;border-radius:10px;border:2px solid {clr};margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <b style="color:#fff;font-size:1.1em">{escape_html(away_display)}{escape_html(g['away_abbrev'])} {g['away_score']} @ {escape_html(home_display)}{escape_html(g['home_abbrev'])} {g['home_score']}</b>
                <div><span style="color:{clr};font-weight:bold">{half_label} {escape_html(clock)}</span> | <span style="color:#888">Pace: {pace}/min → {proj}</span></div>
            </div></div>""", unsafe_allow_html=True)
    st.divider()

# ============================================================
# ML PICKS - DUAL ENGINE VIEW
# ============================================================
st.subheader("🎯 ML PICKS")

if sorted_picks:
    for p in sorted_picks:
        if p["market_score"] < 5.5:
            continue
        
        gk = p["game_key"]
        kalshi_url = build_kalshi_ncaa_url(p["away_abbrev"], p["home_abbrev"])
        reasons_str = " · ".join([escape_html(r) for r in p["market_reasons"][:3]])
        
        g = games.get(gk, {})
        if g.get('status_type') == "STATUS_FINAL":
            status_badge, status_color = "FINAL", "#888"
        elif g.get('period', 0) > 0:
            half_label = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}"
            status_badge = f"{half_label} {escape_html(g.get('clock', ''))}"
            status_color = "#ff4444"
        else:
            status_badge, status_color = "PRE", "#00ff00"
        
        tracked_badge = ' <span style="background:#00ff00;color:#000;padding:1px 4px;border-radius:3px;font-size:0.65em">📊</span>' if p["is_tracked"] else ""
        border_width = "3px" if p["is_tracked"] else "2px"
        
        order_display = f"#{p['pick_order']}"
        ap_badge = f" <span style='color:#ffaa00;font-size:0.75em'>AP{p['market_pick_ap']}</span>" if p['market_pick_ap'] > 0 else ""
        
        # Analyzer confidence badge
        conf_colors = {"CONFIDENT": "#00ff00", "SLIGHT": "#ffaa00", "NO EDGE": "#666"}
        conf_color = conf_colors.get(p["analyzer_conf"], "#666")
        
        buy_btn = get_buy_button_html(kalshi_url)
        
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;border-radius:6px;border-left:{border_width} solid {p['final_color']};margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
<span style="color:{p['final_color']};font-weight:bold;font-size:0.85em">{escape_html(p['final_tier'])}</span>
<span style="color:#666;font-size:0.8em">{order_display}</span>
<b style="color:#fff">{escape_html(p['market_pick'])}</b>{ap_badge}
<span style="color:#555">v {escape_html(p['market_opp'])}</span>
<span style="color:#38bdf8;font-weight:bold">{p['market_score']}</span>
<span style="font-size:0.9em">{p['agreement_icon']}</span>{tracked_badge}
<span style="color:{status_color};font-size:0.75em">{status_badge}</span>
</div>
{buy_btn}
</div>
<div style="color:#666;font-size:0.75em;margin:-2px 0 6px 14px">{reasons_str} | <span style="color:{conf_color}">Analyzer: {p['analyzer_conf']}</span></div>""", unsafe_allow_html=True)
    
    # Add tracked picks
    scheduled_tracked = [p for p in sorted_picks if p["is_tracked"] and p.get('status_type') == "STATUS_SCHEDULED"]
    if scheduled_tracked:
        if st.button(f"➕ Add {len(scheduled_tracked)} Tracked Picks", use_container_width=True, key="add_ncaa_picks"):
            added = 0
            for p in scheduled_tracked:
                if not any(pos.get('game') == p['game_key'] and pos.get('pick') == p['market_pick'] for pos in st.session_state.ncaa_positions):
                    st.session_state.ncaa_positions.append({
                        "game": p['game_key'], "type": "ml",
                        "pick": p['market_pick'], "pick_name": p['market_pick_name'],
                        "price": 50, "contracts": 1, "tracked": True
                    })
                    added += 1
            if added:
                save_positions(st.session_state.ncaa_positions)
                st.rerun()
else:
    st.info("No games today — check back later!")

st.divider()

# ============================================================
# 🔍 ON-DEMAND ANALYZER (User Control)
# ============================================================
st.subheader("🔍 GAME ANALYZER")
st.caption("Select a matchup to see both engines' analysis")

if games:
    game_options = ["-- Select a game --"] + sorted(games.keys())
    selected_game = st.selectbox("Choose matchup:", game_options, key="analyzer_select")
    
    if selected_game != "-- Select a game --" and selected_game in precomputed:
        p = precomputed[selected_game]
        g = games[selected_game]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""<div style="background:#0f172a;padding:15px;border-radius:8px;border:2px solid #38bdf8">
                <div style="color:#38bdf8;font-weight:bold;margin-bottom:10px">📊 MARKET ENGINE</div>
                <div style="color:#fff;font-size:1.2em;margin-bottom:8px"><b>{escape_html(p['market_pick'])}</b> → {p['market_score']}/10</div>
                <div style="color:#888;font-size:0.9em">{' · '.join(p['market_reasons'])}</div>
                <div style="margin-top:10px;color:{p['final_color']};font-weight:bold">{p['final_tier']}</div>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            conf_colors = {"CONFIDENT": "#00ff00", "SLIGHT": "#ffaa00", "NO EDGE": "#666"}
            st.markdown(f"""<div style="background:#0f172a;padding:15px;border-radius:8px;border:2px solid {conf_colors.get(p['analyzer_conf'], '#666')}">
                <div style="color:{conf_colors.get(p['analyzer_conf'], '#666')};font-weight:bold;margin-bottom:10px">🧠 TEAM ANALYZER</div>
                <div style="color:#fff;font-size:1.2em;margin-bottom:8px"><b>{escape_html(p['analyzer_pick'])}</b> → {p['analyzer_conf']}</div>
                <div style="color:#888;font-size:0.9em">Edge magnitude: {p['analyzer_edge']}</div>
                <div style="margin-top:10px;color:{'#00ff00' if p['engines_agree'] else '#ff6666'};font-weight:bold">{'✅ ALIGNED' if p['engines_agree'] else '⚠️ DISAGREE'}</div>
            </div>""", unsafe_allow_html=True)
        
        # Why explanation
        if p['engines_agree']:
            st.success(f"Both engines pick **{p['market_pick']}** — this is a stronger signal.")
        else:
            st.warning(f"Market picks **{p['market_pick']}** but Analyzer picks **{p['analyzer_pick']}** — proceed with caution.")

st.divider()

# HOT/COLD STREAKS
hot_teams = []
cold_teams = []
for gk in games.keys():
    parts = gk.split("@")
    for team in parts:
        streak = streaks.get(team, 0)
        if streak >= 5: hot_teams.append({"team": team, "streak": streak})
        elif streak <= -4: cold_teams.append({"team": team, "streak": streak})

if hot_teams:
    st.subheader("🔥 HOT STREAKS")
    hot_cols = st.columns(min(len(hot_teams), 4))
    for i, t in enumerate(sorted(hot_teams, key=lambda x: x['streak'], reverse=True)[:4]):
        with hot_cols[i]:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a2a1a,#0a1a0a);padding:12px;border-radius:8px;text-align:center;border:2px solid #00ff00">
                <div style="color:#fff;font-weight:bold;font-size:1.2em">{escape_html(t['team'])}</div>
                <div style="color:#00ff00;font-size:1.1em;font-weight:bold">🔥 W{t['streak']}</div>
            </div>""", unsafe_allow_html=True)
    st.divider()

if cold_teams:
    st.subheader("❄️ FADE ALERT")
    cold_cols = st.columns(min(len(cold_teams), 4))
    for i, t in enumerate(sorted(cold_teams, key=lambda x: x['streak'])[:4]):
        with cold_cols[i]:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#2a1a1a,#1a0a0a);padding:12px;border-radius:8px;text-align:center;border:2px solid #ff4444">
                <div style="color:#fff;font-weight:bold;font-size:1.2em">{escape_html(t['team'])}</div>
                <div style="color:#ff4444;font-size:1.1em;font-weight:bold">❄️ L{abs(t['streak'])}</div>
            </div>""", unsafe_allow_html=True)
    st.divider()

# AP TOP 25
st.subheader("📊 AP TOP 25")
if ap_rankings:
    sorted_rankings = sorted(ap_rankings.items(), key=lambda x: x[1])
    rc1, rc2 = st.columns(2)
    for i, (abbrev, rank) in enumerate(sorted_rankings[:25]):
        with rc1 if i < 13 else rc2:
            clr = "#00ff00" if rank <= 5 else "#88ff00" if rank <= 10 else "#ffff00" if rank <= 15 else "#ffaa00"
            st.markdown(f"""<div style="display:flex;align-items:center;background:#0f172a;padding:5px 8px;margin-bottom:2px;border-radius:4px;border-left:2px solid {clr}">
                <span style="color:{clr};font-weight:bold;width:24px">#{rank}</span>
                <span style="color:#fff;font-weight:bold">{escape_html(abbrev)}</span>
            </div>""", unsafe_allow_html=True)
else:
    st.info("Rankings unavailable")

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
                label, clr = ("🟢 CRUISING", "#00ff00") if lead >= 10 else ("🟡 CLOSE", "#ffff00") if lead >= 0 else ("🔴 BEHIND", "#ff0000")
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
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️", key=f"del_ncaa_{idx}"):
                    st.session_state.ncaa_positions.pop(idx)
                    save_positions(st.session_state.ncaa_positions)
                    st.rerun()
else:
    st.info("No active positions")

st.divider()

# ALL GAMES
st.subheader("📺 ALL GAMES")
st.caption(f"{len(games)} games today")

if games:
    for gk, g in sorted(games.items()):
        away_ap = ap_rankings.get(g['away_abbrev'], 0)
        home_ap = ap_rankings.get(g['home_abbrev'], 0)
        away_display = f"#{away_ap} " if away_ap > 0 else ""
        home_display = f"#{home_ap} " if home_ap > 0 else ""
        
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

st.divider()

# HOW TO USE
with st.expander("📖 HOW THE DUAL ENGINE WORKS", expanded=False):
    st.markdown("""
### 🧠 **Dual Confirmation Model**

This app uses **two independent scoring engines** that must agree for top-tier signals.

---

### **Engine 1: Market Edge**
Evaluates market-based factors:
- 🏠 Home court advantage
- 📊 AP Top 25 rankings
- 🏆 Conference tier
- 📈 Win/loss record
- 🛏️ Back-to-back fatigue

**Output:** Score (0-10) + Tier

---

### **Engine 2: Team Strength Analyzer**
Evaluates performance factors:
- 🔥 Recent form (streaks)
- 🏠 Home/away splits
- 💪 Strength ratings
- 😴 Fatigue density

**Output:** Pick + Confidence

---

### **Final Signal Tiers**

| Tier | Requirement |
|------|-------------|
| 🔒 **STRONG+** | STRONG + CONFIDENT + Both agree |
| 🔒 **STRONG** | STRONG market signal only |
| 🔵 **BUY** | BUY + CONFIDENT + Both agree |
| 🟡 **LEAN** | Everything else |
| ⚪ **PASS** | Disagreement or low confidence |

---

### **Icons**
- 🧠 = Engines agree
- ⚠️ = Engines disagree

---

*When someone asks "Why didn't you pick this game?"*
**Answer: "Market and reality didn't agree."**
""")

st.divider()
st.caption("⚠️ Educational only. Not financial advice. v2.0 DUAL ENGINE")
