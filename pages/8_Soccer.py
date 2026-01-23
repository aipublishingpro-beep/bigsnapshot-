# FILE: pages/8_Soccer.py
import streamlit as st
from auth import require_auth

require_auth()

import requests
from datetime import datetime, timedelta
import pytz
import json
import os

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Soccer Edge Finder | BigSnapshot",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# STYLES
# ============================================================
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1a 100%);
    }
    
    .top-pick-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 2px solid #4a9eff;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.3);
    }
    
    .pick-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #252545 100%);
        border: 1px solid #3a3a5a;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        transition: all 0.3s ease;
    }
    
    .pick-card:hover {
        border-color: #4a9eff;
        box-shadow: 0 4px 20px rgba(74, 158, 255, 0.2);
    }
    
    .live-badge {
        background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .signal-strong { color: #00ff88; font-weight: 700; }
    .signal-moderate { color: #ffcc00; font-weight: 600; }
    .signal-weak { color: #ff9500; font-weight: 500; }
    .signal-hold { color: #ff6b6b; font-weight: 500; }
    
    .league-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .league-epl { background: #3d195b; color: white; }
    .league-laliga { background: #ee8707; color: white; }
    .league-bundesliga { background: #d20515; color: white; }
    .league-seriea { background: #024494; color: white; }
    .league-ligue1 { background: #091c3e; color: white; }
    .league-mls { background: #000000; color: white; }
    .league-ucl { background: #0a1128; color: #ffd700; }
    
    .legend-box {
        background: rgba(26, 26, 46, 0.8);
        border: 1px solid #3a3a5a;
        border-radius: 10px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .news-ticker {
        background: linear-gradient(90deg, #1a1a2e 0%, #2d2d4a 50%, #1a1a2e 100%);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        border-left: 4px solid #4a9eff;
    }
    
    a { color: #4a9eff !important; text-decoration: none !important; }
    a:hover { color: #6bb3ff !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6bb3ff 0%, #4a9eff 100%);
        box-shadow: 0 4px 15px rgba(74, 158, 255, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div { flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button { padding: 8px 12px !important; font-size: 0.85em !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTS
# ============================================================
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

LEAGUES = {
    "EPL": {"name": "Premier League", "code": "eng.1", "color": "#3d195b", "kalshi_page": "https://kalshi.com/sports/soccer/EPL"},
    "LALIGA": {"name": "La Liga", "code": "esp.1", "color": "#ee8707", "kalshi_page": "https://kalshi.com/sports/soccer/LALIGA"},
    "BUNDESLIGA": {"name": "Bundesliga", "code": "ger.1", "color": "#d20515", "kalshi_page": "https://kalshi.com/sports/soccer/BUNDESLIGA"},
    "SERIEA": {"name": "Serie A", "code": "ita.1", "color": "#024494", "kalshi_page": "https://kalshi.com/sports/soccer/SERIEA"},
    "LIGUE1": {"name": "Ligue 1", "code": "fra.1", "color": "#091c3e", "kalshi_page": "https://kalshi.com/sports/soccer/LIGUE1"},
    "MLS": {"name": "MLS", "code": "usa.1", "color": "#000000", "kalshi_page": "https://kalshi.com/sports/soccer/MLS"},
    "UCL": {"name": "Champions League", "code": "uefa.champions", "color": "#0a1128", "kalshi_page": "https://kalshi.com/sports/soccer/UCL"},
}

# Team strength ratings (1-100 scale)
TEAM_RATINGS = {
    "Manchester City": 95, "Arsenal": 92, "Liverpool": 93, "Chelsea": 86,
    "Manchester United": 82, "Newcastle United": 84, "Tottenham Hotspur": 83,
    "Aston Villa": 81, "Brighton & Hove Albion": 78, "West Ham United": 76,
    "Brentford": 74, "Fulham": 73, "Crystal Palace": 72, "Wolverhampton Wanderers": 71,
    "Everton": 70, "Bournemouth": 69, "Nottingham Forest": 71, "Luton Town": 65,
    "Burnley": 66, "Sheffield United": 64, "Leicester City": 75, "Ipswich Town": 67,
    "Real Madrid": 95, "Barcelona": 93, "Atletico Madrid": 86, "Real Sociedad": 80,
    "Athletic Club": 79, "Real Betis": 77, "Villarreal": 78, "Sevilla": 76,
    "Valencia": 73, "Girona": 76, "Getafe": 70, "Osasuna": 71,
    "Bayern Munich": 94, "Borussia Dortmund": 87, "RB Leipzig": 85, "Bayer Leverkusen": 88,
    "Union Berlin": 74, "Freiburg": 76, "Eintracht Frankfurt": 77, "Wolfsburg": 73,
    "Inter Milan": 90, "Napoli": 86, "AC Milan": 85, "Juventus": 86,
    "Atalanta": 83, "Roma": 80, "Lazio": 79, "Fiorentina": 76,
    "Paris Saint-Germain": 92, "Monaco": 80, "Marseille": 79, "Lille": 77,
    "Lyon": 76, "Nice": 75, "Lens": 76, "Rennes": 74,
    "Bayern München": 94, "Real Madrid CF": 95, "FC Barcelona": 93,
    "Slavia Prague": 68, "Sporting CP": 78, "Benfica": 80, "Porto": 79,
}

# ============================================================
# TEAM ABBREVIATIONS FOR KALSHI URLs
# ============================================================
TEAM_ABBREVS = {
    "Barcelona": "bar", "FC Barcelona": "bar", "Real Madrid": "rma", "Real Madrid CF": "rma",
    "Bayern Munich": "bay", "Bayern München": "bay", "Paris Saint-Germain": "psg",
    "Manchester City": "mci", "Liverpool": "liv", "Chelsea": "che", "Arsenal": "ars",
    "Manchester United": "mun", "Juventus": "juv", "Inter Milan": "int", "Inter": "int",
    "AC Milan": "acm", "Milan": "acm", "Napoli": "nap", "Borussia Dortmund": "dor",
    "RB Leipzig": "rbl", "Bayer Leverkusen": "lev", "Atletico Madrid": "atm",
    "Sevilla": "sev", "Real Sociedad": "rso", "Tottenham Hotspur": "tot", "Tottenham": "tot",
    "Newcastle United": "new", "Aston Villa": "avl", "West Ham United": "whu", "West Ham": "whu",
    "Brighton & Hove Albion": "bha", "Brighton": "bha", "Fulham": "ful",
    "Crystal Palace": "cry", "Brentford": "bre", "Everton": "eve",
    "Wolverhampton Wanderers": "wol", "Wolves": "wol", "Bournemouth": "bou",
    "Nottingham Forest": "nfo", "Monaco": "mon", "Marseille": "mar", "Olympique Marseille": "mar",
    "Lyon": "oly", "Olympique Lyonnais": "oly", "Lille": "lil",
    "Atalanta": "ata", "Roma": "rom", "AS Roma": "rom", "Lazio": "laz", "Fiorentina": "fio",
    "Slavia Prague": "sla", "Sporting CP": "scp", "Sporting": "scp",
    "Benfica": "ben", "Porto": "por", "FC Porto": "por",
    "Ajax": "aja", "PSV Eindhoven": "psv", "PSV": "psv", "Feyenoord": "fey",
    "Celtic": "cel", "Rangers": "ran", "Union St.-Gilloise": "usg", "Union SG": "usg",
    "Athletic Club": "ath", "Athletic Bilbao": "bil", "Bilbao": "bil",
    "Villarreal": "vil", "Real Betis": "bet", "Valencia": "val", "Girona": "gir",
    "Lens": "len", "Rennes": "ren", "Nice": "nic",
}

# ============================================================
# STRONG PICKS SYSTEM (SHARED ACROSS ALL SPORTS)
# ============================================================
STRONG_PICKS_FILE = "strong_picks.json"

def load_strong_picks():
    try:
        if os.path.exists(STRONG_PICKS_FILE):
            with open(STRONG_PICKS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"next_ml": 1, "picks": []}

def save_strong_picks(data):
    try:
        with open(STRONG_PICKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

def get_next_ml_number():
    return st.session_state.strong_picks.get("next_ml", 1)

def add_strong_pick(game_key, pick_team, sport, price=50):
    ml_num = st.session_state.strong_picks.get("next_ml", 1)
    pick_data = {
        "ml_number": ml_num,
        "game": game_key,
        "pick": pick_team,
        "price": price,
        "timestamp": datetime.now(eastern).isoformat(),
        "sport": sport
    }
    st.session_state.strong_picks["picks"].append(pick_data)
    st.session_state.strong_picks["next_ml"] = ml_num + 1
    save_strong_picks(st.session_state.strong_picks)
    return ml_num

def get_strong_pick_for_game(game_key):
    for pick in st.session_state.strong_picks.get("picks", []):
        if pick.get("game") == game_key:
            return pick
    return None

def is_game_already_tagged(game_key):
    return get_strong_pick_for_game(game_key) is not None

# ============================================================
# 3-GATE SYSTEM FOR STRONG PICKS (SOCCER THRESHOLDS)
# ============================================================
def get_match_stability_soccer(home_team, away_team):
    """
    GATE 1: Match Stability
    Checks: Rating difference (coin-flip detection)
    Returns: (passes, reason)
    """
    home_rating = get_team_rating(home_team)
    away_rating = get_team_rating(away_team)
    
    # Coin-flip matchup = volatile
    if abs(home_rating - away_rating) < 5:
        return False, "Coin-flip matchup"
    
    return True, None

def get_cushion_tier_soccer(game, pick_team, is_live=False):
    """
    GATE 2: Cushion Tier
    Soccer thresholds: Pre=rating diff 10+, Live=2+ goal lead
    Returns: (passes, reason)
    """
    if is_live:
        home_score = int(game.get('home_score', 0) or 0)
        away_score = int(game.get('away_score', 0) or 0)
        
        if pick_team == game.get('home_team'):
            lead = home_score - away_score
        else:
            lead = away_score - home_score
        
        # Soccer live: need 2+ goal lead for Strong Pick
        if lead < 2:
            return False, f"Lead only {lead:+d} goals (need 2+)"
        return True, None
    else:
        # Pre-game: check edge score (already factors in rating diff)
        edge_score = game.get('edge_score', 0)
        
        # Soccer pre-game: need strong edge (80+)
        if edge_score < 80:
            return False, f"Edge only {edge_score} (need 80+)"
        return True, None

def get_pace_direction_soccer(game):
    """
    GATE 3: Pace Direction
    Blocks if: Late game (75+ min) + close game (within 1 goal)
    Returns: (passes, reason)
    """
    state = game.get('state', 'pre')
    
    # Only applies to live games
    if state != 'in':
        return True, None
    
    # Parse clock/minute
    clock = game.get('clock', '')
    try:
        # Clock format varies: "75'" or "75:00" or "75"
        minute = int(''.join(filter(str.isdigit, str(clock).split(':')[0])))
    except:
        minute = 0
    
    # Late game = 75+ minutes
    is_late = minute >= 75
    
    if is_late:
        home_score = int(game.get('home_score', 0) or 0)
        away_score = int(game.get('away_score', 0) or 0)
        diff = abs(home_score - away_score)
        
        # Close game in late stage = too volatile
        if diff <= 1:
            return False, f"{minute}' + only {diff} goal diff"
    
    return True, None

def check_strong_pick_eligible_soccer(game, pick_team):
    """
    Combine all 3 gates for soccer.
    Returns: (eligible, block_reasons[])
    """
    block_reasons = []
    is_live = game.get('state') == 'in'
    
    home_team = game.get('home_team', '')
    away_team = game.get('away_team', '')
    
    # Gate 1: Match Stability
    stable, reason1 = get_match_stability_soccer(home_team, away_team)
    if not stable:
        block_reasons.append(reason1)
    
    # Gate 2: Cushion Tier
    cushion, reason2 = get_cushion_tier_soccer(game, pick_team, is_live)
    if not cushion:
        block_reasons.append(reason2)
    
    # Gate 3: Pace Direction
    pace, reason3 = get_pace_direction_soccer(game)
    if not pace:
        block_reasons.append(reason3)
    
    return len(block_reasons) == 0, block_reasons

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_team_rating(team_name):
    """Get team rating with fuzzy matching"""
    for key, rating in TEAM_RATINGS.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return rating
    return 70

def get_team_abbrev(team_name):
    """Get team abbreviation for Kalshi URLs"""
    for name, abbrev in TEAM_ABBREVS.items():
        if name.lower() == team_name.lower():
            return abbrev
        if name.lower() in team_name.lower() or team_name.lower() in name.lower():
            return abbrev
    first_word = team_name.split()[0] if team_name else "xxx"
    return first_word[:3].lower()

def build_kalshi_url(league_key, home_team, away_team, game_date):
    """Build Kalshi market URL for soccer match"""
    LEAGUE_MARKETS = {
        "EPL": ("english-premier-league-game", "kxeplgame", "EPL"),
        "LALIGA": ("la-liga-game", "kxlaligagame", "LALIGA"),
        "BUNDESLIGA": ("bundesliga-game", "kxbundesligagame", "BUNDESLIGA"),
        "SERIEA": ("serie-a-game", "kxseriagame", "SERIEA"),
        "LIGUE1": ("ligue-1-game", "kxligue1game", "LIGUE1"),
        "MLS": ("mls-game", "kxmlsgame", "MLS"),
        "UCL": ("uefa-champions-league-game", "kxuclgame", "UCL"),
    }
    
    fallback_url = "https://kalshi.com/sports/soccer"
    
    if league_key not in LEAGUE_MARKETS:
        return fallback_url
    
    market_slug, ticker_prefix, kalshi_league = LEAGUE_MARKETS[league_key]
    fallback_url = f"https://kalshi.com/sports/soccer/{kalshi_league}"
    date_str = game_date.strftime("%y%b%d").lower()
    home_abbrev = get_team_abbrev(home_team)
    away_abbrev = get_team_abbrev(away_team)
    ticker = f"{ticker_prefix}-{date_str}{home_abbrev}{away_abbrev}"
    primary_url = f"https://kalshi.com/markets/{market_slug}/{ticker}"
    
    return primary_url

# ============================================================
# SCORING MODEL
# ============================================================
def calculate_edge_score(home_team, away_team, league, is_home_pick=True):
    """Calculate edge score for soccer picks (0-100 scale)"""
    home_rating = get_team_rating(home_team)
    away_rating = get_team_rating(away_team)
    
    score = 50
    
    # Team Strength Differential (±15 points max)
    if is_home_pick:
        strength_diff = home_rating - away_rating
    else:
        strength_diff = away_rating - home_rating
    score += min(15, max(-15, strength_diff * 0.5))
    
    # Home Advantage
    home_advantage_map = {
        "EPL": 7, "LALIGA": 9, "BUNDESLIGA": 8, "SERIEA": 8,
        "LIGUE1": 7, "MLS": 6, "UCL": 5
    }
    home_bonus = home_advantage_map.get(league, 7)
    if is_home_pick:
        score += home_bonus
    else:
        score -= home_bonus * 0.5
    
    # UCL boost for top teams
    if league == "UCL":
        picked_team = home_team if is_home_pick else away_team
        if get_team_rating(picked_team) >= 90:
            score += 5
    
    # Confidence Dampener - Close matchups are less predictable
    rating_diff = abs(home_rating - away_rating)
    if rating_diff < 3:
        score -= 8
    elif rating_diff < 6:
        score -= 5
    
    # UCL knockout stage dampener
    if league == "UCL":
        if home_rating >= 85 and away_rating >= 85:
            score -= 4
    
    return max(0, min(100, round(score)))

def get_signal_tier(score):
    """Convert score to signal tier"""
    if score >= 80:
        return "🔥 STRONG", "signal-strong", True
    elif score >= 65:
        return "✅ MODERATE", "signal-moderate", False
    elif score >= 50:
        return "⚡ LEAN", "signal-weak", False
    else:
        return "⏸️ HOLD", "signal-hold", False

# ============================================================
# API FUNCTIONS
# ============================================================
@st.cache_data(ttl=300)
def fetch_soccer_games(league_code):
    """Fetch games from ESPN API"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=600)
def fetch_news(league_code):
    """Fetch soccer news"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/news"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def parse_games(data, league_key):
    """Parse ESPN data into game objects"""
    games = []
    if not data or 'events' not in data:
        return games
    
    for event in data.get('events', []):
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            home = None
            away = None
            for comp in competitors:
                if comp.get('homeAway') == 'home':
                    home = comp
                else:
                    away = comp
            
            if not home or not away:
                home, away = competitors[0], competitors[1]
            
            home_team = home.get('team', {}).get('displayName', 'Unknown')
            away_team = away.get('team', {}).get('displayName', 'Unknown')
            home_score = home.get('score', '0')
            away_score = away.get('score', '0')
            
            status = event.get('status', {})
            status_type = status.get('type', {})
            state = status_type.get('state', 'pre')
            status_detail = status_type.get('detail', '')
            clock = status.get('displayClock', '')
            
            game_date_str = event.get('date', '')
            try:
                game_time = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                game_time_et = game_time.astimezone(eastern)
            except:
                game_time_et = datetime.now(eastern)
            
            home_edge = calculate_edge_score(home_team, away_team, league_key, is_home_pick=True)
            away_edge = calculate_edge_score(home_team, away_team, league_key, is_home_pick=False)
            
            if home_edge >= away_edge:
                pick = home_team
                edge_score = home_edge
            else:
                pick = away_team
                edge_score = away_edge
            
            signal, signal_class, is_strong = get_signal_tier(edge_score)
            
            kalshi_url = build_kalshi_url(league_key, home_team, away_team, game_time_et)
            fallback_url = LEAGUES[league_key].get('kalshi_page', 'https://kalshi.com/sports/soccer')
            
            game_key = f"{away_team}@{home_team}"
            
            # Check Strong Pick eligibility
            game_data = {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'state': state,
                'clock': clock,
                'edge_score': edge_score
            }
            strong_eligible, block_reasons = check_strong_pick_eligible_soccer(game_data, pick)
            
            games.append({
                'id': event.get('id'),
                'game_key': game_key,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'state': state,
                'status_detail': status_detail,
                'clock': clock,
                'game_time': game_time_et,
                'league': league_key,
                'pick': pick,
                'edge_score': edge_score,
                'home_edge': home_edge,
                'away_edge': away_edge,
                'signal': signal,
                'signal_class': signal_class,
                'is_strong': is_strong,
                'kalshi_url': kalshi_url,
                'fallback_url': fallback_url,
                'strong_eligible': strong_eligible,
                'block_reasons': block_reasons,
            })
            
        except:
            continue
    
    return games

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚽ Soccer Edge Finder")
    st.markdown("---")
    
    st.markdown("#### 🏷️ STRONG PICKS")
    today_tags = len([p for p in st.session_state.strong_picks.get('picks', []) 
                      if p.get('sport') == 'Soccer' and today_str in p.get('timestamp', '')])
    st.markdown(f"""
<div style="background:#0f172a;padding:12px;border-radius:8px;border-left:4px solid #00ff00;margin-bottom:12px">
<div style="color:#00ff00;font-weight:bold">Next ML#: ML-{get_next_ml_number():03d}</div>
<div style="color:#888;font-size:0.85em;margin-top:4px">Today's Tags: {today_tags}</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 📊 Signal Legend")
    st.markdown("""
    🔥 **STRONG** (80+) - High conviction  
    ✅ **MODERATE** (65-79) - Good value  
    ⚡ **LEAN** (50-64) - Slight edge  
    ⏸️ **HOLD** (<50) - No clear edge
    """)
    
    st.markdown("---")
    st.markdown("#### 🏆 Leagues")
    for key, league in LEAGUES.items():
        st.markdown(f"• {league['name']}")
    
    st.markdown("---")
    st.caption("v18.2")

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown("# ⚽ Soccer Edge Finder")
st.markdown("*Multi-league analysis for Kalshi soccer markets | v18.2*")

st.markdown(f"**Last Updated:** {now.strftime('%B %d, %Y at %I:%M %p ET')}")

st.markdown("---")
selected_leagues = st.multiselect(
    "Select Leagues to Analyze",
    options=list(LEAGUES.keys()),
    default=["UCL", "EPL"],
    format_func=lambda x: LEAGUES[x]['name']
)

if not selected_leagues:
    st.warning("Please select at least one league")
    st.stop()

all_games = []
live_games = []

with st.spinner("Fetching soccer data..."):
    for league_key in selected_leagues:
        league_info = LEAGUES[league_key]
        data = fetch_soccer_games(league_info['code'])
        games = parse_games(data, league_key)
        all_games.extend(games)

# ============================================================
# FILTER OUT COMPLETED AND PAST GAMES
# ============================================================
all_games = [g for g in all_games if g['state'] != 'post']
cutoff_time = now - timedelta(hours=3)
all_games = [g for g in all_games if g['game_time'] > cutoff_time]

live_games = [g for g in all_games if g['state'] == 'in']
all_games.sort(key=lambda x: x['edge_score'], reverse=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Matches", len(all_games))
with col2:
    st.metric("Live Now", len(live_games))
with col3:
    strong_picks = len([g for g in all_games if g['edge_score'] >= 80])
    st.metric("🔥 Strong", strong_picks)
with col4:
    st.metric("🏷️ Tags Today", today_tags)

# Legend
st.markdown("""
<div class="legend-box">
<strong>📊 Signal Guide:</strong> 
🔥 STRONG (80+) = High conviction | 
✅ MODERATE (65-79) = Good value | 
⚡ LEAN (50-64) = Slight edge | 
⏸️ HOLD (<50) = Pass
<br><br>
<em style="color: #888;">Note: Edge Score = relative value indicator, NOT win probability. Close matchups are dampened.</em>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TODAY'S STRONG PICKS TRACKER
# ============================================================
today_strong = [p for p in st.session_state.strong_picks.get('picks', []) 
                if p.get('sport') == 'Soccer' and today_str in p.get('timestamp', '')]

if today_strong:
    st.markdown("### 🏷️ TODAY'S STRONG PICKS")
    
    for sp in today_strong:
        gk = sp.get('game', '')
        pick = sp.get('pick', '')
        ml_num = sp.get('ml_number', 0)
        
        # Find matching game
        matching_game = None
        for g in all_games:
            if g.get('game_key') == gk:
                matching_game = g
                break
        
        if matching_game:
            state = matching_game.get('state', 'pre')
            if state == 'post':
                home_score = int(matching_game.get('home_score', 0) or 0)
                away_score = int(matching_game.get('away_score', 0) or 0)
                
                # Determine if pick won (soccer: win or draw matters)
                if pick == matching_game.get('home_team'):
                    pick_won = home_score > away_score
                else:
                    pick_won = away_score > home_score
                
                if pick_won:
                    result_badge = '<span style="background:#00aa00;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold">✅ WON</span>'
                    border_color = "#00aa00"
                else:
                    result_badge = '<span style="background:#aa0000;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold">❌ LOST</span>'
                    border_color = "#aa0000"
                
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid {border_color};margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px">
<span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b>
<span style="color:#888">{home_score}-{away_score}</span>
</div>
{result_badge}
</div>
</div>""", unsafe_allow_html=True)
            elif state == 'in':
                home_score = int(matching_game.get('home_score', 0) or 0)
                away_score = int(matching_game.get('away_score', 0) or 0)
                clock = matching_game.get('clock', '')
                
                if pick == matching_game.get('home_team'):
                    lead = home_score - away_score
                else:
                    lead = away_score - home_score
                
                lead_color = "#00ff00" if lead > 0 else "#ff4444" if lead < 0 else "#888"
                
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid #ffaa00;margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px">
<span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b>
<span style="color:{lead_color};font-weight:bold">{lead:+d}</span>
</div>
<span style="background:#aa0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em">🔴 LIVE {escape_html(clock)}</span>
</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid #444;margin-bottom:10px">
<div style="display:flex;align-items:center;gap:12px">
<span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b>
<span style="background:#1e3a5f;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:0.75em">PRE</span>
</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid #444;margin-bottom:10px">
<div style="display:flex;align-items:center;gap:12px">
<span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b>
<span style="color:#666">(game not in current feed)</span>
</div>
</div>""", unsafe_allow_html=True)
    
    st.markdown("---")

# Live Games
if live_games:
    st.markdown("### 🔴 Live Matches")
    st.caption("⚠️ Live games have higher variance - signals less reliable once in-play")
    for game in live_games:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"""
            <div class="pick-card">
                <span class="live-badge">LIVE</span>
                <span class="league-badge league-{game['league'].lower()}">{LEAGUES[game['league']]['name']}</span>
                <br><br>
                <strong>{escape_html(game['home_team'])}</strong> {game['home_score']} - {game['away_score']} <strong>{escape_html(game['away_team'])}</strong>
                <br>
                <small>⏱️ {escape_html(game['clock'])} | {escape_html(game['status_detail'])}</small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Pick:** {escape_html(game['pick'])}")
            st.markdown(f"**Edge:** {game['edge_score']}")
        with col3:
            st.link_button("📈 Trade on Kalshi", game['fallback_url'])
            st.caption(f"[Try direct link]({game['kalshi_url']})")

# Top Pick
if all_games:
    upcoming_games = [g for g in all_games if g['state'] in ['pre', 'in']]
    
    if upcoming_games:
        top_pick = upcoming_games[0]
        existing_tag = get_strong_pick_for_game(top_pick['game_key'])
        
        tag_badge = ""
        if existing_tag:
            tag_badge = f'<span style="background:#ffd700;color:#000;padding:2px 8px;border-radius:4px;font-size:0.8em;margin-left:8px">ML-{existing_tag["ml_number"]:03d}</span>'
        
        st.markdown("### 🏆 Top Pick")
        st.markdown(f"""
        <div class="top-pick-card">
            <span class="league-badge league-{top_pick['league'].lower()}">{LEAGUES[top_pick['league']]['name']}</span>
            <h2 style="margin: 12px 0; color: white;">{escape_html(top_pick['home_team'])} vs {escape_html(top_pick['away_team'])}</h2>
            <p style="font-size: 1.2rem; color: #a0d2ff;">
                <strong>🎯 Pick: {escape_html(top_pick['pick'])}</strong>{tag_badge}
            </p>
            <p style="font-size: 1.5rem; margin: 8px 0;">
                <span class="{top_pick['signal_class']}">{top_pick['signal']}</span> | 
                Edge Score: <strong>{top_pick['edge_score']}</strong>
            </p>
            <p style="color: #8899aa;">
                📅 {top_pick['game_time'].strftime('%b %d, %I:%M %p ET')}
            </p>
            <a href="{top_pick['fallback_url']}" target="_blank" style="
                display: inline-block;
                background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
                color: white !important;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                margin-top: 12px;
                text-decoration: none;
            ">📈 Trade on Kalshi</a>
            <br><a href="{top_pick['kalshi_url']}" target="_blank" style="color: #888; font-size: 0.8rem;">Try direct game link (may 404)</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Strong Pick Button for top pick
        if top_pick['is_strong'] and top_pick['strong_eligible'] and not existing_tag and top_pick['state'] != 'post':
            if st.button(f"➕ Add Strong Pick: {top_pick['pick']}", key=f"strong_top_{top_pick['game_key']}", use_container_width=True):
                ml_num = add_strong_pick(top_pick['game_key'], top_pick['pick'], "Soccer")
                st.success(f"✅ Tagged ML-{ml_num:03d}: {top_pick['pick']}")
                st.rerun()
        elif top_pick['is_strong'] and not top_pick['strong_eligible'] and not existing_tag:
            st.markdown(f"<div style='color:#ff6666;font-size:0.85em;margin-top:8px'>⚠️ Strong Pick blocked: {', '.join(top_pick['block_reasons'])}</div>", unsafe_allow_html=True)
    else:
        st.info("📅 No upcoming games scheduled. Check back later!")

# All Picks
if all_games:
    st.markdown("### ⚽ All Soccer Picks")
    st.markdown("*Sorted by Edge Score (highest first) — Completed games excluded*")

    for game in all_games:
        existing_tag = get_strong_pick_for_game(game['game_key'])
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            state_icon = "🔴" if game['state'] == 'in' else "⏳"
            tag_indicator = f' <span style="background:#ffd700;color:#000;padding:1px 6px;border-radius:3px;font-size:0.7em">ML-{existing_tag["ml_number"]:03d}</span>' if existing_tag else ""
            st.markdown(f"""
            <div class="pick-card">
                {state_icon} <span class="league-badge league-{game['league'].lower()}">{LEAGUES[game['league']]['name']}</span>
                <strong>{escape_html(game['home_team'])}</strong> vs <strong>{escape_html(game['away_team'])}</strong>{tag_indicator}
                <br><small>📅 {game['game_time'].strftime('%b %d, %I:%M %p ET')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Pick:** {escape_html(game['pick'])}")
            st.markdown(f"<span class='{game['signal_class']}'>{game['signal']}</span>", unsafe_allow_html=True)
        
        with col3:
            st.metric("Edge", game['edge_score'])
        
        with col4:
            st.link_button("Trade", game['fallback_url'], use_container_width=True)
            st.caption(f"[Direct link]({game['kalshi_url']})")
        
        # Strong Pick Button
        if game['is_strong'] and game['strong_eligible'] and not existing_tag and game['state'] != 'post':
            if st.button(f"➕ Add Strong Pick", key=f"strong_{game['game_key']}", use_container_width=True):
                ml_num = add_strong_pick(game['game_key'], game['pick'], "Soccer")
                st.success(f"✅ Tagged ML-{ml_num:03d}: {game['pick']}")
                st.rerun()
        elif game['is_strong'] and not game['strong_eligible'] and not existing_tag and game['state'] != 'post':
            st.markdown(f"<div style='color:#ff6666;font-size:0.75em;margin-bottom:8px'>⚠️ Strong Pick blocked: {', '.join(game['block_reasons'])}</div>", unsafe_allow_html=True)
else:
    st.info("📅 No upcoming games found for the selected leagues. Check back later!")

# How to Use
with st.expander("📖 How to Use Soccer Edge Finder"):
    st.markdown("""
    ## What This Tool Is (and Isn't)
    
    **Edge Score = Relative Value Indicator**
    
    This is NOT a win probability. It's NOT a guarantee.
    
    The Edge Score tells you how many factors align in favor of a pick. Higher score = more alignment, not certainty.
    
    ### How Scoring Works
    
    **Factors that INCREASE score:**
    - Team strength differential (stronger team favored)
    - Home advantage (varies by league - La Liga strongest, UCL weakest)
    - Top team in UCL gets small boost
    
    **Factors that DECREASE score (Confidence Dampeners):**
    - Close matchups (rating diff < 6) → subtract 5-8 points
    - Two strong UCL teams facing off → subtract 4 points
    - This makes STRONG signals rare and meaningful
    
    ### Signal Thresholds
    
    | Signal | Score | Meaning |
    |--------|-------|---------|
    | 🔥 STRONG | 80+ | Multiple factors strongly align - rare |
    | ✅ MODERATE | 65-79 | Good alignment - standard edge |
    | ⚡ LEAN | 50-64 | Slight alignment - small edge |
    | ⏸️ HOLD | <50 | No clear edge - pass or look at draw |
    
    ### 3-Gate Strong Pick System
    
    A pick must pass ALL 3 gates to qualify for tagging:
    
    **Gate 1: Match Stability**
    - Rating difference must be 5+ (no coin-flips)
    
    **Gate 2: Cushion Tier**
    - Pre-game: Edge score 80+
    - Live: Need 2+ goal lead
    
    **Gate 3: Pace Direction**
    - Blocks late-game (75+ min) close games (≤1 goal)
    
    When all gates pass, the ➕ button appears.
    
    ### Trading Tips
    
    - **If Trade button 404s**: Use "Browse League" link as fallback
    - **Close matchups**: Consider the draw market
    - **UCL games**: Higher variance - size positions accordingly
    
    ### Important Reminder
    
    This tool helps you make fewer bad decisions. It doesn't predict outcomes.
    
    Structure beats precision. Process over picks.
    """)

# Footer
st.markdown("---")
st.caption("⚠️ Educational only. Not financial advice. v18.2")
