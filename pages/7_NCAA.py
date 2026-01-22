import streamlit as st
from auth import require_auth

require_auth()

import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import hashlib
from styles import apply_styles, buy_button

st.set_page_config(page_title="NCAA Edge Finder", page_icon="🎓", layout="wide")

apply_styles()

# ========== GOOGLE ANALYTICS ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== MOBILE CSS ==========
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
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

# ============================================================
# MULTI-USER SAFE POSITIONS STORAGE
# Uses session-specific file to prevent conflicts
# ============================================================
def get_session_id():
    """Generate session-specific ID for position storage"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = hashlib.md5(
            f"{time.time()}_{os.getpid()}".encode()
        ).hexdigest()[:12]
    return st.session_state.session_id

def get_positions_file():
    """Get session-specific positions file path"""
    session_id = get_session_id()
    return f"ncaa_positions_{session_id}.json"

def load_positions():
    try:
        filepath = get_positions_file()
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Validate data structure
                if isinstance(data, list):
                    return data
    except: pass
    return []

def save_positions(positions):
    try:
        filepath = get_positions_file()
        with open(filepath, 'w') as f:
            json.dump(positions, f, indent=2)
    except: pass

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "ncaa_positions" not in st.session_state:
    st.session_state.ncaa_positions = load_positions()

# Auto-refresh status display
if st.session_state.auto_refresh:
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}

# Travel-neutral venues (tournament sites, neutral courts)
NEUTRAL_VENUES = {"Las Vegas", "Atlanta", "Indianapolis", "Phoenix", "Houston", "New Orleans"}

def normalize_abbrev(abbrev):
    if not abbrev: return ""
    return abbrev.upper().strip()

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ============================================================
# HARDENED KALSHI TICKER CONSTRUCTION
# ============================================================
def build_kalshi_ncaa_url(team1_code, team2_code):
    """
    Build Kalshi NCAA basketball URL with validation and fallback.
    Format: kxncaambgame-{YY}{MMM}{DD}{team1}{team2}
    """
    try:
        if not team1_code or not team2_code:
            return None
        
        # Clean codes - letters only, uppercase
        t1 = ''.join(c for c in str(team1_code).upper() if c.isalpha())
        t2 = ''.join(c for c in str(team2_code).upper() if c.isalpha())
        
        # Validate minimum length
        if len(t1) < 2 or len(t2) < 2:
            return None
        
        # Truncate to 4 chars max
        t1 = t1[:4]
        t2 = t2[:4]
        
        # Build date string
        date_str = now.strftime("%y%b%d").upper()
        
        # Construct ticker
        ticker = f"KXNCAAMBGAME-{date_str}{t1}{t2}"
        
        # Validate ticker format before returning
        if len(ticker) < 20 or len(ticker) > 30:
            return None
            
        return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"
    except Exception:
        return None

def get_kalshi_link_html(kalshi_url, label="view →"):
    """Generate neutral link to Kalshi market"""
    if kalshi_url:
        return f'<a href="{kalshi_url}" target="_blank" style="color:#555;font-size:0.7em;text-decoration:none">{label}</a>'
    return ''

def get_buy_button_html(kalshi_url, team_abbrev):
    """Generate green BUY button for conviction picks"""
    if kalshi_url:
        return f'<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:6px 14px;border-radius:4px;font-size:0.85em;font-weight:bold;text-decoration:none">BUY {team_abbrev}</a>'
    return ''

# ============================================================
# CACHED HISTORICAL SCOREBOARD FETCH
# Single cached call derives streaks, splits, and B2B
# ============================================================
@st.cache_data(ttl=3600)
def fetch_historical_scoreboards(days_back=14):
    """
    Fetch and cache historical scoreboards once.
    All derived stats (streaks, splits, fatigue) computed from this cache.
    """
    historical = {}
    dates = [(now - timedelta(days=i)).strftime('%Y%m%d') for i in range(1, days_back + 1)]
    
    for date in dates:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date}&limit=100"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                historical[date] = data.get("events", [])
        except:
            continue
    
    return historical

def derive_team_stats_from_cache(historical):
    """
    Derive all team stats from cached historical data.
    Returns: streaks, splits, fatigue_data
    """
    team_results = {}  # For streaks
    splits = {}  # Home/away splits
    fatigue_data = {}  # Minutes, OT, recent games
    
    yesterday = (now - timedelta(days=1)).strftime('%Y%m%d')
    two_days_ago = (now - timedelta(days=2)).strftime('%Y%m%d')
    
    for date, events in sorted(historical.items(), reverse=True):
        for event in events:
            status = event.get("status", {}).get("type", {}).get("name", "")
            if status != "STATUS_FINAL":
                continue
            
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            
            # Check for OT
            period = event.get("status", {}).get("period", 2)
            was_ot = period > 2
            
            for c in competitors:
                abbrev = normalize_abbrev(c.get("team", {}).get("abbreviation", ""))
                if not abbrev:
                    continue
                
                won = c.get("winner", False)
                is_home = c.get("homeAway") == "home"
                
                # Initialize if needed
                if abbrev not in team_results:
                    team_results[abbrev] = []
                if abbrev not in splits:
                    splits[abbrev] = {"home_w": 0, "home_l": 0, "away_w": 0, "away_l": 0}
                if abbrev not in fatigue_data:
                    fatigue_data[abbrev] = {"played_yesterday": False, "played_2d_ago": False, "ot_recent": False, "games_last_5d": 0}
                
                # Streaks
                team_results[abbrev].append({"date": date, "won": won})
                
                # Splits
                if is_home:
                    if won: splits[abbrev]["home_w"] += 1
                    else: splits[abbrev]["home_l"] += 1
                else:
                    if won: splits[abbrev]["away_w"] += 1
                    else: splits[abbrev]["away_l"] += 1
                
                # Fatigue data
                if date == yesterday:
                    fatigue_data[abbrev]["played_yesterday"] = True
                    if was_ot:
                        fatigue_data[abbrev]["ot_recent"] = True
                if date == two_days_ago:
                    fatigue_data[abbrev]["played_2d_ago"] = True
                
                # Games in last 5 days
                date_obj = datetime.strptime(date, '%Y%m%d')
                if (now.date() - date_obj.date()).days <= 5:
                    fatigue_data[abbrev]["games_last_5d"] += 1
    
    # Calculate streaks
    streaks = {}
    for team, results in team_results.items():
        results.sort(key=lambda x: x['date'], reverse=True)
        if not results:
            continue
        streak = 0
        streak_type = results[0]['won']
        for r in results:
            if r['won'] == streak_type:
                streak += 1
            else:
                break
        streaks[team] = streak if streak_type else -streak
    
    return streaks, splits, fatigue_data

def fetch_espn_ncaa_scores():
    """Fetch today's NCAA basketball scores"""
    today_date = now.strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today_date}&limit=100"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            home_abbrev, away_abbrev = "", ""
            home_record, away_record = "", ""
            home_conf, away_conf = "", ""
            
            # Check if neutral site
            venue = comp.get("venue", {}).get("city", "")
            is_neutral = any(nv in venue for nv in NEUTRAL_VENUES) if venue else False
            
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
                "period": period, "clock": clock, "status_type": status_type,
                "is_neutral": is_neutral
            }
        return games
    except Exception as e:
        st.error(f"Error fetching ESPN data: {e}")
        return {}

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
    except:
        return {}

@st.cache_data(ttl=1800)
def fetch_cbb_news():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/news?limit=5"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return [{"headline": a.get("headline", ""), "link": a.get("links", {}).get("web", {}).get("href", "")} 
                for a in data.get("articles", [])[:5]]
    except:
        return []

def get_conference_tier(conf_name):
    if not conf_name:
        return 3
    if any(p in conf_name for p in POWER_CONFERENCES):
        return 1
    if any(h in conf_name for h in HIGH_MAJOR):
        return 2
    return 3

def get_minutes_played(period, clock, status_type):
    """Calculate minutes played with guard against low-minute distortion"""
    if status_type == "STATUS_FINAL":
        return 40
    if status_type == "STATUS_HALFTIME":
        return 20
    if period == 0:
        return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs / 60
        if period == 1:
            return max(0, 20 - time_left)
        elif period == 2:
            return max(20, 20 + (20 - time_left))
        else:
            return max(40, 40 + (period - 2) * 5 + (5 - time_left))
    except:
        return (period - 1) * 20 if period <= 2 else 40 + (period - 2) * 5

# ============================================================
# WEIGHTED FATIGUE SCORE (replaces boolean B2B)
# ============================================================
def calculate_fatigue_score(abbrev, fatigue_data):
    """
    Calculate weighted fatigue score (0-10).
    Higher = more fatigued = worse for team.
    """
    data = fatigue_data.get(abbrev, {})
    score = 0.0
    
    # Back-to-back (played yesterday)
    if data.get("played_yesterday", False):
        score += 4.0
    
    # Played 2 days ago (cumulative fatigue)
    if data.get("played_2d_ago", False):
        score += 1.5
    
    # Recent OT game (extra minutes)
    if data.get("ot_recent", False):
        score += 2.0
    
    # High game density (3+ games in 5 days)
    games_5d = data.get("games_last_5d", 0)
    if games_5d >= 4:
        score += 2.5
    elif games_5d >= 3:
        score += 1.5
    
    return min(score, 10.0)

# ============================================================
# CONDITIONAL HOME COURT ADVANTAGE
# ============================================================
def calculate_home_court_bonus(g, home_abbrev, splits):
    """
    Conditionalize home-court advantage instead of unconditional +1.5.
    Factors: neutral site, home record, conference matchup.
    """
    # Neutral site = no home advantage
    if g.get("is_neutral", False):
        return 0.0, None
    
    # Base home advantage
    base = 1.0
    
    # Check home team's actual home record
    home_split = splits.get(home_abbrev, {})
    home_w = home_split.get("home_w", 0)
    home_l = home_split.get("home_l", 0)
    home_games = home_w + home_l
    
    if home_games >= 3:
        home_pct = home_w / home_games
        if home_pct >= 0.80:
            base = 1.8  # Elite home team
        elif home_pct >= 0.65:
            base = 1.4  # Good home team
        elif home_pct <= 0.40:
            base = 0.5  # Poor home team
    
    # Power conference home game bonus
    home_conf = g.get("home_conf", "")
    if get_conference_tier(home_conf) == 1:
        base += 0.3
    
    return base, "🏠 Home" if base >= 1.0 else "🏠 Weak Home"

# ============================================================
# ENGINE 1: MARKET EDGE ENGINE
# ============================================================
def market_edge_engine(g, fatigue_data, ap_rankings, splits):
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
    
    # Calculate fatigue scores
    home_fatigue = calculate_fatigue_score(home_abbrev, fatigue_data)
    away_fatigue = calculate_fatigue_score(away_abbrev, fatigue_data)
    
    # 1. CONDITIONAL HOME COURT
    hc_bonus, hc_reason = calculate_home_court_bonus(g, home_abbrev, splits)
    if hc_bonus > 0:
        sh += hc_bonus
        if hc_reason:
            rh.append(hc_reason)
    
    # 2. AP RANKING
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
    
    # 3. CONFERENCE TIER
    h_tier = get_conference_tier(home_conf)
    a_tier = get_conference_tier(away_conf)
    if h_tier < a_tier:
        sh += 0.8
        rh.append("🏆 Power")
    elif a_tier < h_tier:
        sa += 0.8
        ra.append("🏆 Power")
    
    # 4. WEIGHTED FATIGUE (replaces boolean B2B)
    fatigue_diff = away_fatigue - home_fatigue
    if fatigue_diff >= 3.0:
        sh += min(fatigue_diff / 2, 2.0)
        rh.append("😴 OppFatigue")
    elif fatigue_diff <= -3.0:
        sa += min(abs(fatigue_diff) / 2, 2.0)
        ra.append("😴 OppFatigue")
    
    # 5. RECORD
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
    
    # 6. TOP 10 BONUS
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
            "score": hf, "reasons": rh[:4], "is_home": True,
            "pick_fatigue": home_fatigue, "opp_fatigue": away_fatigue
        }
    else:
        return {
            "pick": away_abbrev, "pick_name": away_team,
            "pick_ap": away_ap, "opp": home_abbrev, "opp_ap": home_ap,
            "score": af, "reasons": ra[:4], "is_home": False,
            "pick_fatigue": away_fatigue, "opp_fatigue": home_fatigue
        }

# ============================================================
# ENGINE 2: TEAM STRENGTH ANALYZER
# Preserves signed edge internally; abs() only for display
# ============================================================
def team_strength_analyzer(g, streaks, splits, fatigue_data, ap_rankings):
    home_abbrev = g["home_abbrev"]
    away_abbrev = g["away_abbrev"]
    
    sh, sa = 0, 0
    
    # 1. RECENT FORM
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
    
    home_hw = home_split.get("home_w", 0)
    home_hl = home_split.get("home_l", 0)
    home_home_pct = home_hw / (home_hw + home_hl) if (home_hw + home_hl) >= 3 else 0.5
    
    away_aw = away_split.get("away_w", 0)
    away_al = away_split.get("away_l", 0)
    away_away_pct = away_aw / (away_aw + away_al) if (away_aw + away_al) >= 3 else 0.5
    
    if home_home_pct >= 0.75: sh += 1.5
    elif home_home_pct >= 0.60: sh += 0.75
    
    if away_away_pct >= 0.75: sa += 1.5
    elif away_away_pct >= 0.60: sa += 0.75
    elif away_away_pct <= 0.33: sh += 1.0
    
    # 3. STRENGTH RATING
    home_ap = ap_rankings.get(home_abbrev, 0)
    away_ap = ap_rankings.get(away_abbrev, 0)
    
    if home_ap > 0 and home_ap <= 5: sh += 2.0
    elif home_ap > 0 and home_ap <= 15: sh += 1.0
    elif home_ap > 0: sh += 0.5
    
    if away_ap > 0 and away_ap <= 5: sa += 2.0
    elif away_ap > 0 and away_ap <= 15: sa += 1.0
    elif away_ap > 0: sa += 0.5
    
    # 4. WEIGHTED FATIGUE
    home_fatigue = calculate_fatigue_score(home_abbrev, fatigue_data)
    away_fatigue = calculate_fatigue_score(away_abbrev, fatigue_data)
    
    if home_fatigue >= 4.0: sa += home_fatigue / 3
    if away_fatigue >= 4.0: sh += away_fatigue / 3
    
    # SIGNED EDGE (preserved internally)
    signed_edge = sh - sa
    
    if signed_edge >= 3.0:
        return {"pick": home_abbrev, "confidence": "CONFIDENT", "edge": signed_edge, "is_home": True}
    elif signed_edge >= 1.5:
        return {"pick": home_abbrev, "confidence": "SLIGHT", "edge": signed_edge, "is_home": True}
    elif signed_edge <= -3.0:
        return {"pick": away_abbrev, "confidence": "CONFIDENT", "edge": signed_edge, "is_home": False}
    elif signed_edge <= -1.5:
        return {"pick": away_abbrev, "confidence": "SLIGHT", "edge": signed_edge, "is_home": False}
    else:
        if sh >= sa:
            return {"pick": home_abbrev, "confidence": "NO EDGE", "edge": signed_edge, "is_home": True}
        else:
            return {"pick": away_abbrev, "confidence": "NO EDGE", "edge": signed_edge, "is_home": False}

# ============================================================
# STRENGTHENED ENGINE AGREEMENT LOGIC
# ============================================================
def check_engine_agreement(market, analyzer):
    """
    Strengthened agreement check to prevent false alignment.
    Requires: same pick AND directionally consistent reasoning.
    """
    # Basic pick agreement
    if market["pick"] != analyzer["pick"]:
        return False, "DISAGREE"
    
    # Check directional consistency
    # Market picked home = analyzer edge should be positive (favors home)
    # Market picked away = analyzer edge should be negative (favors away)
    if market["is_home"] and analyzer["edge"] < 0:
        return False, "WEAK"  # Market likes home but analyzer math favors away
    if not market["is_home"] and analyzer["edge"] > 0:
        return False, "WEAK"  # Market likes away but analyzer math favors home
    
    # Check confidence alignment
    if analyzer["confidence"] == "NO EDGE":
        return True, "SOFT"  # Agree on pick but no conviction
    
    return True, "STRONG"

# ============================================================
# VISIBILITY GATE + DISPLAY TIERS (v2.4)
# ============================================================
def passes_visibility_gate(market, analyzer):
    """
    Tightened gate - need actual signal strength, not just agreement.
    """
    score = market["score"]
    edge = abs(analyzer["edge"])
    
    # Need meaningful signal from at least one engine
    return score >= 8.8 or edge >= 2.5

def get_final_signal(market, analyzer):
    score = market["score"]
    signed_edge = analyzer["edge"]
    pick_fatigue = market.get("pick_fatigue", 0)
    
    agrees, agreement_strength = check_engine_agreement(market, analyzer)
    
    # Check visibility gate first
    visible = passes_visibility_gate(market, analyzer)
    
    # CONVICTION: Two paths
    # Path 1: Elite score (≥9.7) + agreement → market carries it
    # Path 2: High score (≥9.3) + agreement + analyzer confirms (edge ≥1.5)
    conf = analyzer["confidence"]
    
    elite_path = (score >= 9.7 and agrees and pick_fatigue < 4.0)
    confirmed_path = (score >= 9.3 and agrees and pick_fatigue < 4.0 and abs(signed_edge) >= 1.5)
    
    if elite_path or confirmed_path:
        return {
            "final_tier": "CONVICTION",
            "display_tier": "✓ CONVICTION",
            "final_color": "#00cc66",
            "is_conviction": True,
            "is_near": False,
            "is_mixed": False,
            "engines_agree": True,
            "agreement_icon": "🧠",
            "agreement_strength": agreement_strength,
            "visible": True
        }
    
    # NEAR: High score + agreement (analyzer may be weak)
    if score >= 9.3 and agrees:
        return {
            "final_tier": "NEAR",
            "display_tier": "◐ NEAR",
            "final_color": "#888888",
            "is_conviction": False,
            "is_near": True,
            "is_mixed": False,
            "engines_agree": True,
            "agreement_icon": "",
            "agreement_strength": agreement_strength,
            "visible": True
        }
    
    # MIXED SIGNAL: Good score but engines disagree
    if score >= 8.8 and not agrees:
        return {
            "final_tier": "MIXED",
            "display_tier": "⚠ MIXED",
            "final_color": "#aa6600",
            "is_conviction": False,
            "is_near": False,
            "is_mixed": True,
            "engines_agree": False,
            "agreement_icon": "⚠️",
            "agreement_strength": agreement_strength,
            "visible": True
        }
    
    # Below visibility but still passes gate (edge >= 1.5 or agrees)
    if visible:
        return {
            "final_tier": "WEAK",
            "display_tier": "○ WEAK",
            "final_color": "#444444",
            "is_conviction": False,
            "is_near": False,
            "is_mixed": False,
            "engines_agree": agrees,
            "agreement_icon": "",
            "agreement_strength": agreement_strength,
            "visible": True
        }
    
    # Does not pass visibility gate
    return {
        "final_tier": "HIDDEN",
        "display_tier": "",
        "final_color": "#222",
        "is_conviction": False,
        "is_near": False,
        "is_mixed": False,
        "engines_agree": agrees,
        "agreement_icon": "",
        "agreement_strength": agreement_strength,
        "visible": False
    }

# ============================================================
# FETCH ALL DATA (OPTIMIZED API CALLS)
# ============================================================
games = fetch_espn_ncaa_scores()
ap_rankings = fetch_ap_rankings()
news = fetch_cbb_news()

# Single cached historical fetch - derive all stats from it
historical = fetch_historical_scoreboards(14)
streaks, splits, fatigue_data = derive_team_stats_from_cache(historical)

# ============================================================
# PRECOMPUTE ALL SCORES
# ============================================================
precomputed = {}
for gk, g in games.items():
    try:
        market = market_edge_engine(g, fatigue_data, ap_rankings, splits)
        analyzer = team_strength_analyzer(g, streaks, splits, fatigue_data, ap_rankings)
        final = get_final_signal(market, analyzer)
        
        precomputed[gk] = {
            "game_key": gk,
            "away_abbrev": g["away_abbrev"],
            "home_abbrev": g["home_abbrev"],
            "status_type": g.get("status_type", "STATUS_SCHEDULED"),
            "market_pick": market["pick"],
            "market_pick_name": market["pick_name"],
            "market_pick_ap": market["pick_ap"],
            "market_opp": market["opp"],
            "market_opp_ap": market["opp_ap"],
            "market_score": market["score"],
            "market_reasons": market["reasons"],
            "market_is_home": market["is_home"],
            "pick_fatigue": market.get("pick_fatigue", 0),
            "analyzer_pick": analyzer["pick"],
            "analyzer_conf": analyzer["confidence"],
            "analyzer_edge_signed": analyzer["edge"],
            "analyzer_edge_display": round(abs(analyzer["edge"]), 1),
            "final_tier": final["final_tier"],
            "display_tier": final["display_tier"],
            "final_color": final["final_color"],
            "is_conviction": final["is_conviction"],
            "is_near": final.get("is_near", False),
            "is_mixed": final.get("is_mixed", False),
            "visible": final.get("visible", False),
            "engines_agree": final["engines_agree"],
            "agreement_icon": final["agreement_icon"],
            "agreement_strength": final["agreement_strength"]
        }
    except:
        continue

# Filter by visibility gate, then sort
visible_picks = [p for p in precomputed.values() if p.get("visible", False)]
sorted_picks = sorted(visible_picks, key=lambda x: x["market_score"], reverse=True)

# RANK-BASED TIERS — PURE RANKING BY SCORE (no agreement check)
# Top 3 = CONVICTION, Next 5 = NEAR
conviction_picks = []
near_picks = []

for i, p in enumerate(sorted_picks):
    if i < 3 and p["market_score"] >= 9.0:
        p["final_tier"] = "CONVICTION"
        p["display_tier"] = "✓ CONVICTION"
        p["final_color"] = "#00ff00"
        p["is_conviction"] = True
        p["is_near"] = False
        conviction_picks.append(p)
    elif i < 8 and p["market_score"] >= 8.5:
        p["final_tier"] = "NEAR"
        p["display_tier"] = "◐ NEAR"
        p["final_color"] = "#888888"
        p["is_conviction"] = False
        p["is_near"] = True
        near_picks.append(p)

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 PICK TIERS")
    st.markdown("""
<div style="background:#0f172a;padding:10px;border-radius:6px;border-left:4px solid #00ff00;margin-bottom:10px">
<span style="color:#00ff00;font-weight:bold">🔒 STRONG</span><br>
<span style="color:#888;font-size:0.85em">Top 3 by score</span>
</div>

<div style="background:#0f172a;padding:10px;border-radius:6px;border-left:4px solid #ffaa00">
<span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span><br>
<span style="color:#888;font-size:0.85em">Next 5 picks</span>
</div>
""", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
<div style="background:#0f172a;padding:10px;border-radius:6px">
<span style="color:#888;font-size:0.85em">
🎯 Max 3 strong picks<br>
🟡 Max 5 lean picks<br>
🔗 All link to Kalshi
</span>
</div>
""", unsafe_allow_html=True)
    st.divider()
    st.caption("v3.7 FIXED-LIVE")

# ============================================================
# TITLE
# ============================================================
st.title("🎓 NCAA EDGE FINDER")
st.caption("Signal Analysis | v3.7")

st.markdown("""
<div style="background:#0f172a;padding:12px 16px;border-radius:8px;margin:10px 0;border-left:4px solid #00ff00">
    <span style="color:#00ff00;font-weight:bold">🔒 STRONG</span> = Top 3 picks &nbsp;|&nbsp; 
    <span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span> = Next 5 picks
</div>
""", unsafe_allow_html=True)

# ============================================================
# TOP CONVICTION (if any)
# ============================================================
scheduled_conviction = [p for p in conviction_picks if p.get('status_type') == "STATUS_SCHEDULED"]

# No hero card - all picks in unified list below

# ============================================================
# STATS
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Games", len(games))
with col2:
    live_count = len([g for g in games.values() if g['period'] > 0 and g['status_type'] != "STATUS_FINAL"])
    st.metric("Live", live_count)
with col3:
    st.metric("🔒 Strong", len(conviction_picks))
with col4:
    st.metric("🟡 Lean", len(near_picks))

st.divider()

# ============================================================
# ML PICKS (NBA-STYLE LAYOUT)
# ============================================================
st.subheader("🎯 ML PICKS")

scheduled_conviction_list = [p for p in conviction_picks if p.get('status_type') == "STATUS_SCHEDULED"]
scheduled_near_list = [p for p in near_picks if p.get('status_type') == "STATUS_SCHEDULED"]
finished_conviction_list = [p for p in conviction_picks if p.get('status_type') == "STATUS_FINAL"]
live_conviction_list = [p for p in conviction_picks if p.get('status_type') not in ["STATUS_SCHEDULED", "STATUS_FINAL"]]

# Show all STRONG picks (scheduled + live + finished) + scheduled LEAN picks
all_picks = scheduled_conviction_list + live_conviction_list + scheduled_near_list

# Show finished STRONG picks with results
if finished_conviction_list:
    wins = 0
    losses = 0
    for p in finished_conviction_list:
        g = games.get(p['game_key'])
        if g:
            pick = p['market_pick']
            home_won = g['home_score'] > g['away_score']
            pick_won = (pick == g['home_abbrev'] and home_won) or (pick == g['away_abbrev'] and not home_won)
            if pick_won:
                wins += 1
            else:
                losses += 1
    
    if wins > 0 or losses > 0:
        record_color = "#00ff00" if wins > losses else "#ff4444" if losses > wins else "#888"
        st.markdown(f"""<div style="background:#0f172a;padding:12px 16px;border-radius:8px;border:1px solid {record_color};margin-bottom:14px">
<div style="color:{record_color};font-weight:bold;font-size:1.1em;margin-bottom:8px">📊 TODAY'S STRONG PICKS: {wins}-{losses}</div>
</div>""", unsafe_allow_html=True)
    
    for p in finished_conviction_list:
        g = games.get(p['game_key'])
        if g:
            pick = p['market_pick']
            home_won = g['home_score'] > g['away_score']
            pick_won = (pick == g['home_abbrev'] and home_won) or (pick == g['away_abbrev'] and not home_won)
            
            if pick_won:
                result_badge = '<span style="background:#00aa00;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold">✅ WON</span>'
                border_color = "#00aa00"
            else:
                result_badge = '<span style="background:#aa0000;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold">❌ LOST</span>'
                border_color = "#aa0000"
            
            pick_score = g['home_score'] if pick == g['home_abbrev'] else g['away_score']
            opp_score = g['away_score'] if pick == g['home_abbrev'] else g['home_score']
            
            st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid {border_color};margin-bottom:10px;opacity:0.85">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
<span style="color:#00ff00;font-weight:bold">🔒 STRONG</span>
<b style="color:#fff;font-size:1.2em">{escape_html(p['market_pick'])}</b>
<span style="color:#666">v {escape_html(p['market_opp'])}</span>
<span style="color:#38bdf8;font-weight:bold">{p['market_score']}</span>
<span style="color:#888">{pick_score}-{opp_score}</span>
</div>
{result_badge}
</div>
</div>""", unsafe_allow_html=True)
    
    st.markdown("---")

# Note if strong picks are live
if len(live_conviction_list) > 0:
    st.markdown(f"""<div style="background:#1a2a1a;padding:12px 16px;border-radius:8px;border:1px solid #00ff00;margin-bottom:14px">
<div style="color:#00ff00;font-weight:bold;font-size:1em;margin-bottom:4px">🔒 {len(live_conviction_list)} STRONG pick{'s are' if len(live_conviction_list) > 1 else ' is'} now LIVE</div>
<div style="color:#aaa;font-size:0.85em">Scroll down to LIVE section to track.</div>
</div>""", unsafe_allow_html=True)

if all_picks:
    for p in all_picks:
        kalshi_url = build_kalshi_ncaa_url(p["away_abbrev"], p["home_abbrev"])
        reasons = p.get('market_reasons', [])[:3]
        reasons_str = " · ".join([escape_html(r) for r in reasons]) if reasons else "🏠 Home"
        
        # Check if live
        is_live = p.get('status_type') not in ["STATUS_SCHEDULED", "STATUS_FINAL"]
        
        if p["is_conviction"]:
            border_color = "#00ff00"
            tier_badge = '<span style="color:#00ff00;font-weight:bold">🔒 STRONG</span>'
        else:
            border_color = "#ffaa00"
            tier_badge = '<span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span>'
        
        if is_live:
            g = games.get(p['game_key'])
            if g:
                status_badge = f'<span style="background:#aa0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em">🔴 LIVE</span>'
                score_display = f'<span style="color:#fff;margin-left:8px">{g["away_score"]}-{g["home_score"]}</span>'
            else:
                status_badge = '<span style="background:#aa0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em">🔴 LIVE</span>'
                score_display = ''
        else:
            status_badge = '<span style="background:#1e3a5f;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:0.75em">PRE</span>'
            score_display = ''
        
        st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid {border_color};margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
{tier_badge}
<b style="color:#fff;font-size:1.2em">{escape_html(p['market_pick'])}</b>
<span style="color:#666">v {escape_html(p['market_opp'])}</span>
<span style="color:#38bdf8;font-weight:bold">{p['market_score']}</span>
{status_badge}{score_display}
</div>
<a href="{kalshi_url}" target="_blank" style="background:#22c55e;color:#000;padding:8px 20px;border-radius:6px;font-weight:bold;text-decoration:none">BUY {escape_html(p['market_pick'])}</a>
</div>
<div style="color:#666;font-size:0.8em;margin-top:8px">{reasons_str}</div>
</div>""", unsafe_allow_html=True)
    
    st.caption(f"{len(scheduled_conviction_list)} strong + {len(scheduled_near_list)} lean scheduled")
    
    if scheduled_conviction_list:
        if st.button(f"📋 Watch All {len(scheduled_conviction_list)} Strong Picks", use_container_width=True, key="add_watch"):
            added = 0
            for p in scheduled_conviction_list:
                if not any(pos.get('game') == p['game_key'] and pos.get('pick') == p['market_pick'] for pos in st.session_state.ncaa_positions):
                    st.session_state.ncaa_positions.append({
                        "game": p['game_key'], "type": "signal",
                        "pick": p['market_pick'], "pick_name": p['market_pick_name']
                    })
                    added += 1
            if added:
                save_positions(st.session_state.ncaa_positions)
                st.rerun()

else:
    st.markdown("""
    <div style="background:#0f172a;padding:30px;border-radius:12px;text-align:center">
        <div style="color:#666;font-size:1em">No picks today</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ============================================================
# LIVE GAMES (GUARDED PACE PROJECTION)
# ============================================================
if live_games:
    st.subheader("⚡ LIVE")
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
        
        # GUARDED PACE PROJECTION - require minimum 5 minutes to avoid distortion
        if mins >= 5:
            pace = round(g['total'] / mins, 2)
            proj = round(pace * 40)
            pace_display = f"→ {proj}"
        else:
            pace_display = ""
        
        if half >= 3: clr = "#ff0000"
        elif half == 2 and diff <= 8: clr = "#ffaa00"
        else: clr = "#00ff00"
        
        half_label = "H1" if half == 1 else "H2" if half == 2 else f"OT{half-2}"
        
        # Build Kalshi URL for live game
        kalshi_url = build_kalshi_ncaa_url(g['away_abbrev'], g['home_abbrev'])
        
        # Get pick data and tier from precomputed
        pick_data = precomputed.get(gk, {})
        buy_team = pick_data.get('market_pick', g['home_abbrev'])
        
        # Check if this was a STRONG or LEAN pick
        is_strong = pick_data.get('is_conviction', False)
        if is_strong:
            tier_badge = '<span style="color:#00ff00;font-weight:bold">🔒 STRONG</span>'
            border_clr = "#00ff00"
        else:
            tier_badge = '<span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span>'
            border_clr = "#ffaa00"
        
        st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid {border_clr};margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px">
{tier_badge}
<b style="color:#fff;font-size:1.1em">{escape_html(g['away_abbrev'])} {g['away_score']} @ {escape_html(g['home_abbrev'])} {g['home_score']}</b>
</div>
<div style="display:flex;align-items:center;gap:12px">
<span style="color:{clr};font-weight:bold">{half_label} {escape_html(clock)}</span>
<span style="color:#666">{pace_display}</span>
<a href="{kalshi_url}" target="_blank" style="background:#22c55e;color:#000;padding:8px 20px;border-radius:6px;font-weight:bold;text-decoration:none">BUY {escape_html(buy_team)}</a>
</div>
</div>
</div>""", unsafe_allow_html=True)
    st.divider()

# ============================================================
# WATCHLIST
# ============================================================
st.subheader("📋 WATCHLIST")

if st.session_state.ncaa_positions:
    for idx, pos in enumerate(st.session_state.ncaa_positions):
        gk = pos['game']
        g = games.get(gk)
        
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            pick_score = g['home_score'] if pick == parts[1] else g['away_score']
            opp_score = g['away_score'] if pick == parts[1] else g['home_score']
            lead = pick_score - opp_score
            is_final = g['status_type'] == "STATUS_FINAL"
            
            if is_final:
                won = pick_score > opp_score
                label, clr = ("✅ WON", "#00aa00") if won else ("❌ LOST", "#aa0000")
            elif g['period'] > 0:
                label, clr = ("🟢", "#00aa00") if lead >= 10 else ("🟡", "#aaaa00") if lead >= 0 else ("🔴", "#aa0000")
            else:
                label, clr = "⏳", "#444"
            
            half_label = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}" if g['period'] > 2 else ""
            status = "FINAL" if is_final else f"{half_label} {escape_html(g['clock'])}" if g['period'] > 0 else ""
            
            st.markdown(f"""<div style='background:#0a0a14;padding:10px;border-radius:6px;border-left:2px solid {clr};margin-bottom:6px'>
                <div style='display:flex;justify-content:space-between;font-size:0.85em'><b style='color:#888'>{escape_html(gk.replace('@', ' @ '))}</b> <span style='color:#444'>{status}</span> <b style='color:{clr}'>{label}</b></div>
                <div style='color:#555;margin-top:4px;font-size:0.75em'>Signal: {escape_html(pick)} | {lead:+d}</div></div>""", unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️", key=f"del_ncaa_{idx}"):
                    st.session_state.ncaa_positions.pop(idx)
                    save_positions(st.session_state.ncaa_positions)
                    st.rerun()
else:
    st.caption("No watched games")

st.divider()

# ============================================================
# ALL GAMES (Collapsed)
# ============================================================
with st.expander(f"📺 ALL GAMES ({len(games)})", expanded=False):
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
            status, clr = f"🔴 {half_label}", "#ff4444"
        else:
            status, clr = "—", "#333"
        
        st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#050508;padding:5px 10px;margin-bottom:2px;border-radius:4px;font-size:0.85em">
            <div><span style="color:#666">{escape_html(away_display)}{escape_html(g['away_abbrev'])}</span> {g['away_score']} @ <span style="color:#666">{escape_html(home_display)}{escape_html(g['home_abbrev'])}</span> {g['home_score']}</div>
            <span style="color:{clr};font-size:0.8em">{status}</span>
        </div>""", unsafe_allow_html=True)

st.divider()
st.caption("v3.7 FIXED-LIVE • Auto-refresh safe")
