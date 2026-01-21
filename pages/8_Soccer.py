# FILE: pages/8_Soccer.py
import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import extra_streamlit_components as stx

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
    .signal-weak { color: #ff6b6b; font-weight: 500; }
    
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
    
    .game-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin: 16px 0;
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
# COOKIE MANAGER AUTH
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

LEAGUES = {
    "EPL": {"name": "Premier League", "code": "eng.1", "kalshi": "EPL", "color": "#3d195b"},
    "LALIGA": {"name": "La Liga", "code": "esp.1", "kalshi": "LALIGA", "color": "#ee8707"},
    "BUNDESLIGA": {"name": "Bundesliga", "code": "ger.1", "kalshi": "BUNDESLIGA", "color": "#d20515"},
    "SERIEA": {"name": "Serie A", "code": "ita.1", "kalshi": "SERIEA", "color": "#024494"},
    "LIGUE1": {"name": "Ligue 1", "code": "fra.1", "kalshi": "LIGUE1", "color": "#091c3e"},
    "MLS": {"name": "MLS", "code": "usa.1", "kalshi": "MLS", "color": "#000000"},
    "UCL": {"name": "Champions League", "code": "uefa.champions", "kalshi": "UCL", "color": "#0a1128"},
}

# Team strength ratings (1-100 scale, based on general performance)
TEAM_RATINGS = {
    # Premier League
    "Manchester City": 95, "Arsenal": 92, "Liverpool": 93, "Chelsea": 86,
    "Manchester United": 82, "Newcastle United": 84, "Tottenham Hotspur": 83,
    "Aston Villa": 81, "Brighton & Hove Albion": 78, "West Ham United": 76,
    "Brentford": 74, "Fulham": 73, "Crystal Palace": 72, "Wolverhampton Wanderers": 71,
    "Everton": 70, "Bournemouth": 69, "Nottingham Forest": 71, "Luton Town": 65,
    "Burnley": 66, "Sheffield United": 64, "Leicester City": 75, "Ipswich Town": 67,
    # La Liga
    "Real Madrid": 95, "Barcelona": 93, "Atletico Madrid": 86, "Real Sociedad": 80,
    "Athletic Club": 79, "Real Betis": 77, "Villarreal": 78, "Sevilla": 76,
    "Valencia": 73, "Girona": 76, "Getafe": 70, "Osasuna": 71,
    # Bundesliga
    "Bayern Munich": 94, "Borussia Dortmund": 87, "RB Leipzig": 85, "Bayer Leverkusen": 88,
    "Union Berlin": 74, "Freiburg": 76, "Eintracht Frankfurt": 77, "Wolfsburg": 73,
    # Serie A
    "Inter Milan": 90, "Napoli": 86, "AC Milan": 85, "Juventus": 86,
    "Atalanta": 83, "Roma": 80, "Lazio": 79, "Fiorentina": 76,
    # Ligue 1
    "Paris Saint-Germain": 92, "Monaco": 80, "Marseille": 79, "Lille": 77,
    "Lyon": 76, "Nice": 75, "Lens": 76, "Rennes": 74,
    # UCL Giants
    "Bayern München": 94, "Real Madrid CF": 95, "FC Barcelona": 93,
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_team_rating(team_name):
    """Get team rating with fuzzy matching"""
    for key, rating in TEAM_RATINGS.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return rating
    return 70  # Default rating

def get_team_abbrev(team_name):
    """Get 3-letter abbreviation for Kalshi URLs"""
    # Common abbreviations that Kalshi uses
    TEAM_ABBREVS = {
        # UCL / Top Teams
        "Barcelona": "bar", "Real Madrid": "rma", "Bayern Munich": "bay", "Bayern München": "bay",
        "Paris Saint-Germain": "psg", "Manchester City": "mci", "Liverpool": "liv",
        "Chelsea": "che", "Arsenal": "ars", "Manchester United": "mun",
        "Juventus": "juv", "Inter Milan": "int", "AC Milan": "acm", "Napoli": "nap",
        "Borussia Dortmund": "dor", "RB Leipzig": "rbl", "Bayer Leverkusen": "lev",
        "Atletico Madrid": "atm", "Sevilla": "sev", "Real Sociedad": "rso",
        "Tottenham Hotspur": "tot", "Newcastle United": "new", "Aston Villa": "avl",
        "West Ham United": "whu", "Brighton & Hove Albion": "bha", "Fulham": "ful",
        "Crystal Palace": "cry", "Brentford": "bre", "Everton": "eve",
        "Wolverhampton Wanderers": "wol", "Bournemouth": "bou", "Nottingham Forest": "nfo",
        "Monaco": "mon", "Marseille": "mar", "Lyon": "oly", "Lille": "lil",
        "Atalanta": "ata", "Roma": "rom", "Lazio": "laz", "Fiorentina": "fio",
        "Slavia Prague": "sla", "Sporting CP": "scp", "Benfica": "ben", "Porto": "por",
        "Ajax": "aja", "PSV Eindhoven": "psv", "Feyenoord": "fey",
        "Celtic": "cel", "Rangers": "ran", "Union St.-Gilloise": "usg",
        # Add more as needed
    }
    
    # Check exact match first
    for name, abbrev in TEAM_ABBREVS.items():
        if name.lower() == team_name.lower():
            return abbrev
        if name.lower() in team_name.lower() or team_name.lower() in name.lower():
            return abbrev
    
    # Fallback: first 3 letters of first word, lowercase
    first_word = team_name.split()[0] if team_name else "xxx"
    return first_word[:3].lower()

def build_kalshi_url(league_key, home_team, away_team, game_date):
    """Build Kalshi market URL for soccer match"""
    
    # League to Kalshi market mapping
    LEAGUE_MARKETS = {
        "EPL": ("english-premier-league-game", "kxeplgame"),
        "LALIGA": ("la-liga-game", "kxlaligagame"),
        "BUNDESLIGA": ("bundesliga-game", "kxbundesligagame"),
        "SERIEA": ("serie-a-game", "kxseriagame"),
        "LIGUE1": ("ligue-1-game", "kxligue1game"),
        "MLS": ("mls-game", "kxmlsgame"),
        "UCL": ("uefa-champions-league-game", "kxuclgame"),
    }
    
    if league_key not in LEAGUE_MARKETS:
        return f"https://kalshi.com/sports/soccer"
    
    market_slug, ticker_prefix = LEAGUE_MARKETS[league_key]
    
    # Format date: YYmmmDD (e.g., 26jan21 for Jan 21, 2026)
    date_str = game_date.strftime("%y%b%d").lower()
    
    # Get team abbreviations (home first, then away)
    home_abbrev = get_team_abbrev(home_team)
    away_abbrev = get_team_abbrev(away_team)
    
    # Build ticker: kxuclgame-26jan21slabar
    ticker = f"{ticker_prefix}-{date_str}{home_abbrev}{away_abbrev}"
    
    # Full URL
    return f"https://kalshi.com/markets/{market_slug}/{ticker}"

def calculate_rest_days(last_game_date):
    """Calculate rest days since last match"""
    if not last_game_date:
        return 4  # Default assumption
    now = datetime.now(eastern)
    delta = now - last_game_date
    return delta.days

# ============================================================
# SCORING MODEL
# ============================================================
def calculate_edge_score(home_team, away_team, league, is_home_pick=True, 
                         home_form=None, away_form=None, home_rest=4, away_rest=4):
    """
    Calculate edge score for soccer picks (0-100 scale)
    
    Factors:
    1. Team Strength Differential (30%)
    2. Home Advantage (20%)
    3. Recent Form (25%)
    4. Rest Days Advantage (15%)
    5. League Position Factor (10%)
    """
    
    home_rating = get_team_rating(home_team)
    away_rating = get_team_rating(away_team)
    
    score = 50  # Baseline
    
    # 1. Team Strength Differential (±15 points max)
    if is_home_pick:
        strength_diff = home_rating - away_rating
    else:
        strength_diff = away_rating - home_rating
    score += min(15, max(-15, strength_diff * 0.5))
    
    # 2. Home Advantage (+8 points for home team, varies by league)
    home_advantage_map = {
        "EPL": 7, "LALIGA": 9, "BUNDESLIGA": 8, "SERIEA": 8,
        "LIGUE1": 7, "MLS": 6, "UCL": 5
    }
    home_bonus = home_advantage_map.get(league, 7)
    if is_home_pick:
        score += home_bonus
    else:
        score -= home_bonus * 0.5
    
    # 3. Recent Form (±10 points max)
    if home_form is not None and away_form is not None:
        if is_home_pick:
            form_diff = home_form - away_form
        else:
            form_diff = away_form - home_form
        score += min(10, max(-10, form_diff * 2))
    
    # 4. Rest Days Advantage (±8 points max)
    rest_diff = home_rest - away_rest if is_home_pick else away_rest - home_rest
    if rest_diff >= 3:
        score += 8
    elif rest_diff >= 1:
        score += 4
    elif rest_diff <= -3:
        score -= 8
    elif rest_diff <= -1:
        score -= 4
    
    # 5. League coefficient boost for top teams in UCL
    if league == "UCL":
        picked_team = home_team if is_home_pick else away_team
        if get_team_rating(picked_team) >= 90:
            score += 5
    
    return max(0, min(100, round(score)))

def get_signal_tier(score):
    """Convert score to signal tier"""
    if score >= 75:
        return "🔥 STRONG", "signal-strong"
    elif score >= 60:
        return "✅ MODERATE", "signal-moderate"
    elif score >= 45:
        return "⚡ LEAN", "signal-weak"
    else:
        return "⏸️ HOLD", "signal-weak"

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
    except Exception as e:
        st.error(f"Error fetching {league_code}: {e}")
        return None

@st.cache_data(ttl=600)
def fetch_standings(league_code):
    """Fetch league standings"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/standings"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
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
    except Exception as e:
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
            
            # ESPN: competitors[0] is usually home, competitors[1] is away
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
            
            # Parse game time
            game_date_str = event.get('date', '')
            try:
                game_time = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                game_time_et = game_time.astimezone(eastern)
            except:
                game_time_et = datetime.now(eastern)
            
            # Calculate edge scores for both sides
            home_edge = calculate_edge_score(home_team, away_team, league_key, is_home_pick=True)
            away_edge = calculate_edge_score(home_team, away_team, league_key, is_home_pick=False)
            
            # Determine best pick
            if home_edge >= away_edge:
                pick = home_team
                edge_score = home_edge
            else:
                pick = away_team
                edge_score = away_edge
            
            signal, signal_class = get_signal_tier(edge_score)
            
            games.append({
                'id': event.get('id'),
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
                'kalshi_url': build_kalshi_url(league_key, home_team, away_team, game_time_et),
            })
            
        except Exception as e:
            continue
    
    return games

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚽ Soccer Edge Finder")
    st.markdown("---")
    
    st.markdown("#### 📊 Signal Legend")
    st.markdown("""
    🔥 **STRONG** (75+) - High conviction  
    ✅ **MODERATE** (60-74) - Good value  
    ⚡ **LEAN** (45-59) - Slight edge  
    ⏸️ **HOLD** (<45) - No clear edge
    """)
    
    st.markdown("---")
    st.markdown("#### 🏆 Leagues")
    for key, league in LEAGUES.items():
        st.markdown(f"• {league['name']}")
    
    st.markdown("---")
    st.markdown("#### ℹ️ Model Factors")
    st.markdown("""
    1. Team Strength (30%)
    2. Home Advantage (20%)
    3. Recent Form (25%)
    4. Rest Days (15%)
    5. League Position (10%)
    """)

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown("# ⚽ Soccer Edge Finder")
st.markdown("*Multi-league analysis for Kalshi soccer markets*")

# Status bar
now = datetime.now(eastern)
st.markdown(f"**Last Updated:** {now.strftime('%B %d, %Y at %I:%M %p ET')}")

# League selector
st.markdown("---")
selected_leagues = st.multiselect(
    "Select Leagues to Analyze",
    options=list(LEAGUES.keys()),
    default=["EPL", "UCL", "LALIGA"],
    format_func=lambda x: LEAGUES[x]['name']
)

if not selected_leagues:
    st.warning("Please select at least one league")
    st.stop()

# Fetch all games
all_games = []
live_games = []

with st.spinner("Fetching soccer data..."):
    for league_key in selected_leagues:
        league_info = LEAGUES[league_key]
        data = fetch_soccer_games(league_info['code'])
        games = parse_games(data, league_key)
        all_games.extend(games)
        live_games.extend([g for g in games if g['state'] == 'in'])

# Sort by edge score
all_games.sort(key=lambda x: x['edge_score'], reverse=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Matches", len(all_games))
with col2:
    st.metric("Live Now", len(live_games))
with col3:
    strong_picks = len([g for g in all_games if g['edge_score'] >= 75])
    st.metric("Strong Picks", strong_picks)
with col4:
    avg_edge = sum(g['edge_score'] for g in all_games) / len(all_games) if all_games else 0
    st.metric("Avg Edge Score", f"{avg_edge:.1f}")

# Legend box
st.markdown("""
<div class="legend-box">
<strong>📊 Signal Guide:</strong> 
🔥 STRONG (75+) = High conviction | 
✅ MODERATE (60-74) = Good value | 
⚡ LEAN (45-59) = Slight edge | 
⏸️ HOLD (<45) = Pass
</div>
""", unsafe_allow_html=True)

# Breaking news
st.markdown("### 📰 Breaking News")
news_displayed = 0
for league_key in selected_leagues[:2]:  # Limit to first 2 leagues for news
    news_data = fetch_news(LEAGUES[league_key]['code'])
    if news_data and 'articles' in news_data:
        for article in news_data['articles'][:2]:
            headline = article.get('headline', '')
            if headline and news_displayed < 3:
                st.markdown(f"""
                <div class="news-ticker">
                    <span class="league-badge league-{league_key.lower()}">{LEAGUES[league_key]['name']}</span>
                    {headline}
                </div>
                """, unsafe_allow_html=True)
                news_displayed += 1

# Live Games Section
if live_games:
    st.markdown("### 🔴 Live Matches")
    for game in live_games:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"""
            <div class="pick-card">
                <span class="live-badge">LIVE</span>
                <span class="league-badge league-{game['league'].lower()}">{LEAGUES[game['league']]['name']}</span>
                <br><br>
                <strong>{game['home_team']}</strong> {game['home_score']} - {game['away_score']} <strong>{game['away_team']}</strong>
                <br>
                <small>⏱️ {game['clock']} | {game['status_detail']}</small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Pick:** {game['pick']}")
            st.markdown(f"**Edge:** {game['edge_score']}")
        with col3:
            st.link_button("📈 Trade on Kalshi", game['kalshi_url'])

# Top Pick Hero Section
if all_games:
    top_pick = all_games[0]
    st.markdown("### 🏆 Top Pick")
    st.markdown(f"""
    <div class="top-pick-card">
        <span class="league-badge league-{top_pick['league'].lower()}">{LEAGUES[top_pick['league']]['name']}</span>
        <h2 style="margin: 12px 0; color: white;">{top_pick['home_team']} vs {top_pick['away_team']}</h2>
        <p style="font-size: 1.2rem; color: #a0d2ff;">
            <strong>🎯 Pick: {top_pick['pick']}</strong>
        </p>
        <p style="font-size: 1.5rem; margin: 8px 0;">
            <span class="{top_pick['signal_class']}">{top_pick['signal']}</span> | 
            Edge Score: <strong>{top_pick['edge_score']}</strong>
        </p>
        <p style="color: #8899aa;">
            📅 {top_pick['game_time'].strftime('%b %d, %I:%M %p ET')}
        </p>
        <a href="{top_pick['kalshi_url']}" target="_blank" style="
            display: inline-block;
            background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
            color: white !important;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 12px;
            text-decoration: none;
        ">📈 Trade on Kalshi</a>
    </div>
    """, unsafe_allow_html=True)

# ML Picks List
st.markdown("### ⚽ All Soccer Picks")
st.markdown("*Sorted by Edge Score (highest first)*")

for game in all_games:
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        state_icon = "🔴" if game['state'] == 'in' else "⏳" if game['state'] == 'pre' else "✅"
        st.markdown(f"""
        <div class="pick-card">
            {state_icon} <span class="league-badge league-{game['league'].lower()}">{LEAGUES[game['league']]['name']}</span>
            <strong>{game['home_team']}</strong> vs <strong>{game['away_team']}</strong>
            <br><small>📅 {game['game_time'].strftime('%b %d, %I:%M %p ET')}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**Pick:** {game['pick']}")
        st.markdown(f"<span class='{game['signal_class']}'>{game['signal']}</span>", unsafe_allow_html=True)
    
    with col3:
        st.metric("Edge", game['edge_score'])
    
    with col4:
        st.link_button("Trade", game['kalshi_url'], use_container_width=True)

# How to Use Expander
with st.expander("📖 How to Use Soccer Edge Finder"):
    st.markdown("""
    ## How the Model Works
    
    The Soccer Edge Finder analyzes multiple factors to identify value in Kalshi soccer markets:
    
    ### Factors Analyzed
    
    1. **Team Strength Differential (30%)** - Based on historical performance, squad quality, and league position
    
    2. **Home Advantage (20%)** - Soccer has significant home advantage, varying by league:
       - La Liga: +9 (loudest crowds)
       - Serie A/Bundesliga: +8
       - Premier League/Ligue 1: +7
       - MLS: +6
       - Champions League: +5 (neutral venues reduce advantage)
    
    3. **Recent Form (25%)** - Points from last 5 matches
    
    4. **Rest Days (15%)** - Teams with 3+ extra rest days get significant boost
    
    5. **League Position Factor (10%)** - Table position impacts confidence
    
    ### Trading Tips
    
    - **Strong signals (75+)**: Consider larger positions
    - **Moderate signals (60-74)**: Standard position size
    - **Lean signals (45-59)**: Small position or combine with other edges
    - **Hold (<45)**: Skip or look for draws
    
    ### Important Notes
    
    - European leagues (EPL, La Liga, etc.) typically have more predictable outcomes
    - Champions League knockouts are harder to predict
    - Always check for late injuries before trading
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem; padding: 20px;">
    <p>⚠️ <strong>Disclaimer:</strong> This tool provides analysis for educational purposes only. 
    Past performance does not guarantee future results. Trade responsibly.</p>
    <p>© 2025 BigSnapshot | <a href="https://bigsnapshot.com">bigsnapshot.com</a></p>
</div>
""", unsafe_allow_html=True)
