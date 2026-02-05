import streamlit as st

st.set_page_config(page_title="NCAA Edge Finder", page_icon="🎓", layout="wide")

import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import hashlib
from styles import apply_styles

apply_styles()

# ========== GA4 SERVER-SIDE ==========
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NCAA Edge Finder", "/NCAA")

# ========== MOBILE-RESPONSIVE CSS ==========
st.markdown("""
<style>
.game-card {
    background: #1a1a2e;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.signal-badge {
    text-align: center;
    padding: 10px 14px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    color: white;
    min-width: 90px;
    flex-shrink: 0;
}
.signal-badge .score {
    font-size: 20px;
    display: block;
    margin-top: 2px;
}
.matchup-info {
    flex: 1;
    min-width: 180px;
}
.matchup-info .teams {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
    margin: 0;
}
.matchup-info .names {
    font-size: 12px;
    color: #999;
    margin: 2px 0 0 0;
}
.pick-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #333;
    flex-wrap: wrap;
}
.pick-info {
    flex: 1;
    min-width: 200px;
}
.pick-info .pick-team {
    font-size: 16px;
    font-weight: bold;
    color: #00ff88;
    margin: 0;
}
.pick-info .pick-vs {
    font-size: 12px;
    color: #888;
    margin: 2px 0;
}
.pick-info .edge-factors {
    font-size: 12px;
    color: #aaa;
    margin: 4px 0 0 0;
}
.model-box {
    text-align: right;
    min-width: 120px;
    flex-shrink: 0;
}
.model-box .model-pct {
    font-size: 18px;
    font-weight: bold;
    color: #00aaff;
}
.model-box .model-sub {
    font-size: 12px;
    color: #888;
}
.b2b-badge {
    display: inline-block;
    background: #cc3300;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    margin-left: 6px;
}
.stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
}
.stats-grid .stat-col {
    background: #111;
    border-radius: 8px;
    padding: 12px;
}
.stats-grid .stat-col h4 {
    color: #fff;
    margin: 0 0 8px 0;
    font-size: 14px;
}
.stats-grid .stat-line {
    font-size: 12px;
    color: #bbb;
    margin: 3px 0;
}
.stats-grid .stat-line.warn {
    color: #ff6644;
    font-weight: bold;
}
.live-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #0f172a, #020617);
    padding: 10px 14px;
    margin-bottom: 6px;
    border-radius: 8px;
    flex-wrap: wrap;
    gap: 8px;
}
.live-bar .items {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
@media (max-width: 768px) {
    .card-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .signal-badge {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 8px 14px;
    }
    .signal-badge .score {
        display: inline;
        margin-top: 0;
    }
    .pick-row {
        flex-direction: column;
    }
    .model-box {
        text-align: left;
    }
    .stats-grid {
        grid-template-columns: 1fr;
    }
    .live-bar {
        flex-direction: column;
        align-items: flex-start;
    }
    .live-bar .items {
        width: 100%;
    }
    div[data-testid="column"] {
        width: 100% !important;
        flex: 100% !important;
        min-width: 100% !important;
    }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    .stButton button { padding: 8px 12px !important; font-size: 14px !important; }
}
</style>
""", unsafe_allow_html=True)

VERSION = "19.0 LIVE"
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

# ============================================================
# MULTI-USER SAFE POSITIONS STORAGE
# ============================================================
def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = hashlib.md5(
            f"{time.time()}_{os.getpid()}".encode()
        ).hexdigest()[:12]
    return st.session_state.session_id

def get_positions_file():
    return f"ncaa_positions_{get_session_id()}.json"

def load_positions():
    try:
        filepath = get_positions_file()
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except: pass
    return []

def save_positions(positions):
    try:
        with open(get_positions_file(), 'w') as f:
            json.dump(positions, f, indent=2)
    except: pass

# ============================================================
# STRONG PICKS SYSTEM
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
        "ml_number": ml_num, "game": game_key, "pick": pick_team,
        "price": price, "timestamp": datetime.now(eastern).isoformat(), "sport": sport
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
# 3-GATE SYSTEM FOR STRONG PICKS
# ============================================================
def get_match_stability(g, fatigue_data):
    home_abbrev = g.get("home_abbrev", "")
    away_abbrev = g.get("away_abbrev", "")
    home_fatigue = fatigue_data.get(home_abbrev, {})
    away_fatigue = fatigue_data.get(away_abbrev, {})
    if home_fatigue.get("played_yesterday") and away_fatigue.get("played_yesterday"):
        return False, "Both teams B2B"
    return True, None

def get_cushion_tier(g, market_data, is_live=False):
    if is_live:
        home_score = g.get("home_score", 0)
        away_score = g.get("away_score", 0)
        pick = market_data.get("pick", "")
        lead = (home_score - away_score) if pick == g.get("home_abbrev") else (away_score - home_score)
        if lead < 10:
            return False, f"Lead only {lead:+d} (need 10+)"
        return True, None
    else:
        score = market_data.get("score", 0)
        edge = abs(market_data.get("edge", 0)) if "edge" in market_data else 0
        if score < 9.5 and edge < 3.0:
            return False, f"Edge too thin ({score}/10)"
        return True, None

def get_pace_direction(g, market_data):
    period = g.get("period", 0)
    status = g.get("status_type", "STATUS_SCHEDULED")
    if status == "STATUS_SCHEDULED" or period == 0:
        return True, None
    is_late = period >= 2
    if is_late:
        diff = abs(g.get("home_score", 0) - g.get("away_score", 0))
        if diff <= 7:
            half_label = "H2" if period == 2 else f"OT{period-2}"
            return False, f"{half_label} + only {diff}pt diff"
    return True, None

def check_strong_pick_eligible(g, market_data, fatigue_data):
    block_reasons = []
    is_live = g.get("period", 0) > 0 and g.get("status_type") != "STATUS_FINAL"
    stable, r1 = get_match_stability(g, fatigue_data)
    if not stable: block_reasons.append(r1)
    cushion, r2 = get_cushion_tier(g, market_data, is_live)
    if not cushion: block_reasons.append(r2)
    pace, r3 = get_pace_direction(g, market_data)
    if not pace: block_reasons.append(r3)
    return len(block_reasons) == 0, block_reasons

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "ncaa_positions" not in st.session_state:
    st.session_state.ncaa_positions = load_positions()

auto_status = "🔄 Auto-refresh ON (30s)" if st.session_state.auto_refresh else "⏸️ Auto-refresh OFF"

POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}
NEUTRAL_VENUES = {"Las Vegas", "Atlanta", "Indianapolis", "Phoenix", "Houston", "New Orleans"}

def normalize_abbrev(abbrev):
    return abbrev.upper().strip() if abbrev else ""

def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if text else ""

# ============================================================
# KALSHI TICKER CONSTRUCTION
# ============================================================
def build_kalshi_ncaa_url(team1_code, team2_code):
    try:
        if not team1_code or not team2_code: return None
        t1 = ''.join(c for c in str(team1_code).upper() if c.isalpha())[:4]
        t2 = ''.join(c for c in str(team2_code).upper() if c.isalpha())[:4]
        if len(t1) < 2 or len(t2) < 2: return None
        date_str = now.strftime("%y%b%d").upper()
        ticker = f"KXNCAAMBGAME-{date_str}{t1}{t2}"
        if len(ticker) < 20 or len(ticker) > 30: return None
        return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"
    except: return None

# ============================================================
# ESPN DATA FETCHERS
# ============================================================
@st.cache_data(ttl=3600)
def fetch_historical_scoreboards(days_back=14):
    historical = {}
    for i in range(1, days_back + 1):
        date = (now - timedelta(days=i)).strftime('%Y%m%d')
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date}&limit=100"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                historical[date] = resp.json().get("events", [])
        except: continue
    return historical

def derive_team_stats_from_cache(historical):
    team_results, splits, fatigue_data = {}, {}, {}
    yesterday = (now - timedelta(days=1)).strftime('%Y%m%d')
    two_days_ago = (now - timedelta(days=2)).strftime('%Y%m%d')

    for date, events in sorted(historical.items(), reverse=True):
        for event in events:
            if event.get("status", {}).get("type", {}).get("name", "") != "STATUS_FINAL":
                continue
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            was_ot = event.get("status", {}).get("period", 2) > 2

            for c in competitors:
                abbrev = normalize_abbrev(c.get("team", {}).get("abbreviation", ""))
                if not abbrev: continue
                won = c.get("winner", False)
                is_home = c.get("homeAway") == "home"

                if abbrev not in team_results: team_results[abbrev] = []
                if abbrev not in splits: splits[abbrev] = {"home_w": 0, "home_l": 0, "away_w": 0, "away_l": 0}
                if abbrev not in fatigue_data: fatigue_data[abbrev] = {"played_yesterday": False, "played_2d_ago": False, "ot_recent": False, "games_last_5d": 0}

                team_results[abbrev].append({"date": date, "won": won})
                if is_home:
                    splits[abbrev]["home_w" if won else "home_l"] += 1
                else:
                    splits[abbrev]["away_w" if won else "away_l"] += 1

                if date == yesterday:
                    fatigue_data[abbrev]["played_yesterday"] = True
                    if was_ot: fatigue_data[abbrev]["ot_recent"] = True
                if date == two_days_ago:
                    fatigue_data[abbrev]["played_2d_ago"] = True
                if (now.date() - datetime.strptime(date, '%Y%m%d').date()).days <= 5:
                    fatigue_data[abbrev]["games_last_5d"] += 1

    streaks = {}
    for team, results in team_results.items():
        results.sort(key=lambda x: x['date'], reverse=True)
        if not results: continue
        streak, streak_type = 0, results[0]['won']
        for r in results:
            if r['won'] == streak_type: streak += 1
            else: break
        streaks[team] = streak if streak_type else -streak

    return streaks, splits, fatigue_data

def fetch_espn_ncaa_scores():
    today_date = now.strftime('%Y%m%d')
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
            venue = comp.get("venue", {}).get("city", "")
            is_neutral = any(nv in venue for nv in NEUTRAL_VENUES) if venue else False

            for c in competitors:
                td = c.get("team", {})
                name = td.get("displayName", td.get("name", ""))
                abbrev = normalize_abbrev(td.get("abbreviation", name[:4]))
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
    try:
        resp = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings", timeout=10)
        data = resp.json()
        rankings = {}
        for rg in data.get("rankings", []):
            if rg.get("name") == "AP Top 25":
                for team in rg.get("ranks", []):
                    abbrev = normalize_abbrev(team.get("team", {}).get("abbreviation", ""))
                    rank = team.get("current", 0)
                    if abbrev and 1 <= rank <= 25:
                        rankings[abbrev] = rank
                break
        return rankings
    except: return {}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
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
        time_left = mins + secs / 60
        if period == 1: return max(0, 20 - time_left)
        elif period == 2: return max(20, 20 + (20 - time_left))
        else: return max(40, 40 + (period - 2) * 5 + (5 - time_left))
    except: return (period - 1) * 20 if period <= 2 else 40 + (period - 2) * 5

def calculate_fatigue_score(abbrev, fatigue_data):
    d = fatigue_data.get(abbrev, {})
    score = 0.0
    if d.get("played_yesterday"): score += 4.0
    if d.get("played_2d_ago"): score += 1.5
    if d.get("ot_recent"): score += 2.0
    g5 = d.get("games_last_5d", 0)
    if g5 >= 4: score += 2.5
    elif g5 >= 3: score += 1.5
    return min(score, 10.0)

def calculate_home_court_bonus(g, home_abbrev, splits):
    if g.get("is_neutral"): return 0.0, None
    base = 1.0
    hs = splits.get(home_abbrev, {})
    hw, hl = hs.get("home_w", 0), hs.get("home_l", 0)
    if hw + hl >= 3:
        pct = hw / (hw + hl)
        if pct >= 0.80: base = 1.8
        elif pct >= 0.65: base = 1.4
        elif pct <= 0.40: base = 0.5
    if get_conference_tier(g.get("home_conf", "")) == 1: base += 0.3
    return base, "🏠 Home" if base >= 1.0 else "🏠 Weak Home"

# ============================================================
# ENGINE 1: MARKET EDGE ENGINE
# ============================================================
def market_edge_engine(g, fatigue_data, ap_rankings, splits):
    ha, aa = g["home_abbrev"], g["away_abbrev"]
    sh, sa, rh, ra = 0, 0, [], []
    home_ap = ap_rankings.get(ha, 0)
    away_ap = ap_rankings.get(aa, 0)
    home_fatigue = calculate_fatigue_score(ha, fatigue_data)
    away_fatigue = calculate_fatigue_score(aa, fatigue_data)

    hc_bonus, hc_reason = calculate_home_court_bonus(g, ha, splits)
    if hc_bonus > 0:
        sh += hc_bonus
        if hc_reason: rh.append(hc_reason)

    if home_ap > 0 and away_ap == 0:
        sh += 1.5; rh.append(f"📊 #{home_ap}")
    elif away_ap > 0 and home_ap == 0:
        sa += 1.5; ra.append(f"📊 #{away_ap}")
    elif home_ap > 0 and away_ap > 0:
        if away_ap - home_ap >= 10: sh += 1.0; rh.append(f"📊 #{home_ap}v#{away_ap}")
        elif home_ap - away_ap >= 10: sa += 1.0; ra.append(f"📊 #{away_ap}v#{home_ap}")

    h_tier = get_conference_tier(g.get("home_conf", ""))
    a_tier = get_conference_tier(g.get("away_conf", ""))
    if h_tier < a_tier: sh += 0.8; rh.append("🏆 Power")
    elif a_tier < h_tier: sa += 0.8; ra.append("🏆 Power")

    fat_diff = away_fatigue - home_fatigue
    if fat_diff >= 3.0: sh += min(fat_diff / 2, 2.0); rh.append("😴 OppFatigue")
    elif fat_diff <= -3.0: sa += min(abs(fat_diff) / 2, 2.0); ra.append("😴 OppFatigue")

    try:
        hw, hl = map(int, g.get("home_record", "0-0").split("-")[:2])
        aw, al = map(int, g.get("away_record", "0-0").split("-")[:2])
        hp = hw / (hw + hl) if (hw + hl) > 0 else 0.5
        ap = aw / (aw + al) if (aw + al) > 0 else 0.5
        if hp - ap > 0.20: sh += 1.0; rh.append(f"📈 {g['home_record']}")
        elif ap - hp > 0.20: sa += 1.0; ra.append(f"📈 {g['away_record']}")
    except: pass

    if home_ap > 0 and home_ap <= 10 and away_ap == 0: sh += 1.0; rh.append("🔝 Top10")
    elif away_ap > 0 and away_ap <= 10 and home_ap == 0: sa += 1.0; ra.append("🔝 Top10")

    total = sh + sa
    hf = round((sh / total) * 10, 1) if total > 0 else 5.0
    af = round((sa / total) * 10, 1) if total > 0 else 5.0

    if hf >= af:
        return {"pick": ha, "pick_name": g["home_team"], "pick_ap": home_ap, "opp": aa, "opp_ap": away_ap,
                "score": hf, "reasons": rh[:4], "is_home": True, "pick_fatigue": home_fatigue, "opp_fatigue": away_fatigue}
    else:
        return {"pick": aa, "pick_name": g["away_team"], "pick_ap": away_ap, "opp": ha, "opp_ap": home_ap,
                "score": af, "reasons": ra[:4], "is_home": False, "pick_fatigue": away_fatigue, "opp_fatigue": home_fatigue}

# ============================================================
# ENGINE 2: TEAM STRENGTH ANALYZER
# ============================================================
def team_strength_analyzer(g, streaks, splits, fatigue_data, ap_rankings):
    ha, aa = g["home_abbrev"], g["away_abbrev"]
    sh, sa = 0, 0
    hs, as_ = streaks.get(ha, 0), streaks.get(aa, 0)

    if hs >= 5: sh += 2.0
    elif hs >= 3: sh += 1.0
    elif hs <= -4: sa += 1.5
    elif hs <= -2: sa += 0.5
    if as_ >= 5: sa += 2.0
    elif as_ >= 3: sa += 1.0
    elif as_ <= -4: sh += 1.5
    elif as_ <= -2: sh += 0.5

    hsp = splits.get(ha, {})
    asp = splits.get(aa, {})
    hhw, hhl = hsp.get("home_w", 0), hsp.get("home_l", 0)
    aaw, aal = asp.get("away_w", 0), asp.get("away_l", 0)
    hhp = hhw / (hhw + hhl) if (hhw + hhl) >= 3 else 0.5
    aap = aaw / (aaw + aal) if (aaw + aal) >= 3 else 0.5

    if hhp >= 0.75: sh += 1.5
    elif hhp >= 0.60: sh += 0.75
    if aap >= 0.75: sa += 1.5
    elif aap >= 0.60: sa += 0.75
    elif aap <= 0.33: sh += 1.0

    hap = ap_rankings.get(ha, 0)
    aap_r = ap_rankings.get(aa, 0)
    if hap > 0 and hap <= 5: sh += 2.0
    elif hap > 0 and hap <= 15: sh += 1.0
    elif hap > 0: sh += 0.5
    if aap_r > 0 and aap_r <= 5: sa += 2.0
    elif aap_r > 0 and aap_r <= 15: sa += 1.0
    elif aap_r > 0: sa += 0.5

    hf = calculate_fatigue_score(ha, fatigue_data)
    af = calculate_fatigue_score(aa, fatigue_data)
    if hf >= 4.0: sa += hf / 3
    if af >= 4.0: sh += af / 3

    edge = sh - sa
    if edge >= 3.0: return {"pick": ha, "confidence": "CONFIDENT", "edge": edge, "is_home": True}
    elif edge >= 1.5: return {"pick": ha, "confidence": "SLIGHT", "edge": edge, "is_home": True}
    elif edge <= -3.0: return {"pick": aa, "confidence": "CONFIDENT", "edge": edge, "is_home": False}
    elif edge <= -1.5: return {"pick": aa, "confidence": "SLIGHT", "edge": edge, "is_home": False}
    else:
        pick = ha if sh >= sa else aa
        return {"pick": pick, "confidence": "NO EDGE", "edge": edge, "is_home": sh >= sa}

def passes_visibility_gate(market, analyzer):
    return market["score"] >= 8.8 or abs(analyzer["edge"]) >= 2.5

def get_final_signal(market, analyzer):
    score = market["score"]
    edge = analyzer["edge"]
    pick_fatigue = market.get("pick_fatigue", 0)
    agrees = market["pick"] == analyzer["pick"]

    elite = score >= 9.7 and agrees and pick_fatigue < 4.0
    confirmed = score >= 9.3 and agrees and pick_fatigue < 4.0 and abs(edge) >= 1.5
    visible = passes_visibility_gate(market, analyzer)

    if elite or confirmed:
        return {"final_tier": "CONVICTION", "display_tier": "✓ CONVICTION", "final_color": "#00cc66",
                "is_conviction": True, "is_near": False, "visible": True, "engines_agree": True}
    if score >= 9.3 and agrees:
        return {"final_tier": "NEAR", "display_tier": "◐ NEAR", "final_color": "#888888",
                "is_conviction": False, "is_near": True, "visible": True, "engines_agree": True}
    if score >= 8.8 and not agrees:
        return {"final_tier": "MIXED", "display_tier": "⚠ MIXED", "final_color": "#aa6600",
                "is_conviction": False, "is_near": False, "visible": True, "engines_agree": False}
    if visible:
        return {"final_tier": "WEAK", "display_tier": "○ WEAK", "final_color": "#444444",
                "is_conviction": False, "is_near": False, "visible": True, "engines_agree": agrees}
    return {"final_tier": "HIDDEN", "display_tier": "", "final_color": "#222",
            "is_conviction": False, "is_near": False, "visible": False, "engines_agree": agrees}

# ============================================================
# FETCH ALL DATA
# ============================================================
games = fetch_espn_ncaa_scores()
ap_rankings = fetch_ap_rankings()
historical = fetch_historical_scoreboards(14)
streaks, splits, fatigue_data = derive_team_stats_from_cache(historical)

# ============================================================
# PRECOMPUTE SCORES
# ============================================================
precomputed = {}
for gk, g in games.items():
    try:
        market = market_edge_engine(g, fatigue_data, ap_rankings, splits)
        analyzer = team_strength_analyzer(g, streaks, splits, fatigue_data, ap_rankings)
        final = get_final_signal(market, analyzer)
        strong_eligible, block_reasons = check_strong_pick_eligible(g, {"pick": market["pick"], "score": market["score"], "edge": analyzer["edge"]}, fatigue_data)
        precomputed[gk] = {
            "game_key": gk, "away_abbrev": g["away_abbrev"], "home_abbrev": g["home_abbrev"],
            "status_type": g.get("status_type", "STATUS_SCHEDULED"),
            "market_pick": market["pick"], "market_pick_name": market["pick_name"],
            "market_pick_ap": market["pick_ap"], "market_opp": market["opp"],
            "market_opp_ap": market["opp_ap"], "market_score": market["score"],
            "market_reasons": market["reasons"], "market_is_home": market["is_home"],
            "pick_fatigue": market.get("pick_fatigue", 0),
            "analyzer_pick": analyzer["pick"], "analyzer_conf": analyzer["confidence"],
            "analyzer_edge_signed": analyzer["edge"],
            "final_tier": final["final_tier"], "display_tier": final["display_tier"],
            "final_color": final["final_color"],
            "is_conviction": final["is_conviction"], "is_near": final.get("is_near", False),
            "visible": final.get("visible", False), "engines_agree": final["engines_agree"],
            "strong_eligible": strong_eligible, "block_reasons": block_reasons
        }
    except: continue

visible_picks = sorted([p for p in precomputed.values() if p.get("visible")], key=lambda x: x["market_score"], reverse=True)
conviction_picks, near_picks = [], []
for i, p in enumerate(visible_picks):
    if i < 3 and p["market_score"] >= 9.0:
        p["final_tier"], p["display_tier"], p["final_color"] = "CONVICTION", "✓ CONVICTION", "#00ff00"
        p["is_conviction"], p["is_near"] = True, False
        conviction_picks.append(p)
    elif i < 8 and p["market_score"] >= 8.5:
        p["final_tier"], p["display_tier"], p["final_color"] = "NEAR", "◐ NEAR", "#888888"
        p["is_conviction"], p["is_near"] = False, True
        near_picks.append(p)

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    st.header("🏷️ STRONG PICKS")
    today_tags = len([p for p in st.session_state.strong_picks.get('picks', [])
                      if p.get('sport') == 'NCAA' and today_str in p.get('timestamp', '')])
    st.markdown(f"""<div style="background:#0f172a;padding:12px;border-radius:8px;border-left:4px solid #00ff00;margin-bottom:12px">
<div style="color:#00ff00;font-weight:bold">Next ML#: ML-{get_next_ml_number():03d}</div>
<div style="color:#888;font-size:0.85em;margin-top:4px">Today's Tags: {today_tags}</div>
</div>""", unsafe_allow_html=True)
    st.divider()
    st.header("📖 PICK TIERS")
    st.markdown("""
<div style="background:#0f172a;padding:10px;border-radius:6px;border-left:4px solid #00ff00;margin-bottom:10px">
<span style="color:#00ff00;font-weight:bold">🔒 STRONG</span> — Top 3 by score
</div>
<div style="background:#0f172a;padding:10px;border-radius:6px;border-left:4px solid #ffaa00">
<span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span> — Next 5 picks
</div>
""", unsafe_allow_html=True)
    st.divider()
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
**3-Gate Strong Pick System:**
- **Gate 1:** Match Stability (no dual B2B)
- **Gate 2:** Cushion Tier (score 9.5+ or edge 3+)
- **Gate 3:** Pace Direction (blocks late close games)

When all gates pass, the ➕ button appears.
""")
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN CONTENT
# ============================================================
st.title("🎓 NCAA EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Live ESPN Data")

st.markdown("""<div style="background:#0f172a;padding:12px 16px;border-radius:8px;margin:10px 0;border-left:4px solid #00ff00">
    <span style="color:#00ff00;font-weight:bold">🔒 STRONG</span> = Top 3 picks &nbsp;|&nbsp;
    <span style="color:#ffaa00;font-weight:bold">🟡 LEAN</span> = Next 5 picks
</div>""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Games", len(games))
with col2: st.metric("Live", len(live_games))
with col3: st.metric("🔒 Strong", len(conviction_picks))
with col4: st.metric("🟡 Lean", len(near_picks))

st.divider()

# ============================================================
# TODAY'S STRONG PICKS TRACKER
# ============================================================
today_strong = [p for p in st.session_state.strong_picks.get('picks', [])
                if p.get('sport') == 'NCAA' and today_str in p.get('timestamp', '')]

if today_strong:
    st.subheader("🏷️ TODAY'S STRONG PICKS")
    wins, losses, pending = 0, 0, 0
    for sp in today_strong:
        g = games.get(sp.get('game'))
        if g:
            pick = sp.get('pick')
            if g['status_type'] == "STATUS_FINAL":
                home_won = g['home_score'] > g['away_score']
                if (pick == g['home_abbrev'] and home_won) or (pick == g['away_abbrev'] and not home_won): wins += 1
                else: losses += 1
            else: pending += 1
        else: pending += 1

    if wins + losses > 0:
        rc = "#00ff00" if wins > losses else "#ff4444" if losses > wins else "#888"
        st.markdown(f"""<div style="background:#0f172a;padding:12px 16px;border-radius:8px;border:1px solid {rc};margin-bottom:14px">
<div style="color:{rc};font-weight:bold;font-size:1.1em">📊 STRONG PICKS: {wins}W-{losses}L ({pending} pending)</div>
</div>""", unsafe_allow_html=True)

    for sp in today_strong:
        g = games.get(sp.get('game'))
        pick, ml_num = sp.get('pick', ''), sp.get('ml_number', 0)
        if g:
            if g['status_type'] == "STATUS_FINAL":
                home_won = g['home_score'] > g['away_score']
                pick_won = (pick == g['home_abbrev'] and home_won) or (pick == g['away_abbrev'] and not home_won)
                ps = g['home_score'] if pick == g['home_abbrev'] else g['away_score']
                os_ = g['away_score'] if pick == g['home_abbrev'] else g['home_score']
                badge = f'<span style="background:{"#00aa00" if pick_won else "#aa0000"};color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold">{"✅ WON" if pick_won else "❌ LOST"}</span>'
                bc = "#00aa00" if pick_won else "#aa0000"
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid {bc};margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px"><span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b><span style="color:#888">{ps}-{os_}</span></div>{badge}</div></div>""", unsafe_allow_html=True)
            elif g['period'] > 0:
                ps = g['home_score'] if pick == g['home_abbrev'] else g['away_score']
                os_ = g['away_score'] if pick == g['home_abbrev'] else g['home_score']
                lead = ps - os_
                lc = "#00ff00" if lead > 0 else "#ff4444" if lead < 0 else "#888"
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid #ffaa00;margin-bottom:10px">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px"><span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b><span style="color:{lc};font-weight:bold">{lead:+d}</span></div>
<span style="background:#aa0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em">🔴 LIVE {g['period']}H</span></div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background:#0f172a;padding:14px 18px;border-radius:8px;border-left:4px solid #444;margin-bottom:10px">
<div style="display:flex;align-items:center;gap:12px"><span style="color:#00ff00;font-weight:bold">ML-{ml_num:03d}</span>
<b style="color:#fff">{escape_html(pick)}</b><span style="background:#1e3a5f;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:0.75em">PRE</span></div></div>""", unsafe_allow_html=True)
    st.divider()

# ============================================================
# ML PICKS
# ============================================================
st.subheader("🎯 ML PICKS")

scheduled_conviction = [p for p in conviction_picks if p.get('status_type') == "STATUS_SCHEDULED"]
scheduled_near = [p for p in near_picks if p.get('status_type') == "STATUS_SCHEDULED"]
live_conviction = [p for p in conviction_picks if p.get('status_type') not in ["STATUS_SCHEDULED", "STATUS_FINAL"]]
all_picks = scheduled_conviction + live_conviction + scheduled_near

if all_picks:
    for p in all_picks:
        kalshi_url = build_kalshi_ncaa_url(p["away_abbrev"], p["home_abbrev"])
        reasons = " · ".join([escape_html(r) for r in p.get('market_reasons', [])[:3]]) or "🏠 Home"
        existing_tag = is_game_already_tagged(p['game_key'])
        is_live = p.get('status_type') not in ["STATUS_SCHEDULED", "STATUS_FINAL"]
        is_strong = p["is_conviction"]

        border_color = "#00ff00" if is_strong else "#ffaa00"
        tier_badge = f'<span style="color:{border_color};font-weight:bold">{"🔒 STRONG" if is_strong else "🟡 LEAN"}</span>'

        if is_live:
            g = games.get(p['game_key'])
            status_badge = '<span style="background:#aa0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em">🔴 LIVE</span>'
            score_display = f'<span style="color:#fff;margin-left:8px">{g["away_score"]}-{g["home_score"]}</span>' if g else ''
        else:
            status_badge = '<span style="background:#1e3a5f;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:0.75em">PRE</span>'
            score_display = ''

        tag_badge = ''
        if existing_tag:
            ti = get_strong_pick_for_game(p['game_key'])
            tag_badge = f'<span style="background:#00aa00;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:8px">ML-{ti["ml_number"]:03d}</span>'

        buy_html = f'<a href="{kalshi_url}" target="_blank" style="background:#22c55e;color:#000;padding:8px 20px;border-radius:6px;font-weight:bold;text-decoration:none">BUY {escape_html(p["market_pick"])}</a>' if kalshi_url else ''

        st.markdown(f"""<div class="game-card" style="border-left:4px solid {border_color}">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
{tier_badge}
<b style="color:#fff;font-size:1.2em">{escape_html(p['market_pick'])}</b>
<span style="color:#666">v {escape_html(p['market_opp'])}</span>
<span style="color:#38bdf8;font-weight:bold">{p['market_score']}</span>
{status_badge}{score_display}{tag_badge}
</div>
{buy_html}
</div>
<div style="color:#666;font-size:0.8em;margin-top:8px">{reasons}</div>
</div>""", unsafe_allow_html=True)

        if is_strong and p.get("strong_eligible") and not existing_tag and p.get("status_type") != "STATUS_FINAL":
            if st.button(f"➕ Add Strong Pick", key=f"strong_{p['game_key']}", use_container_width=True):
                ml_num = add_strong_pick(p['game_key'], p['market_pick'], "NCAA")
                st.success(f"✅ Tagged ML-{ml_num:03d}: {p['market_pick']}")
                st.rerun()
        elif is_strong and not p.get("strong_eligible") and not existing_tag and p.get("status_type") != "STATUS_FINAL":
            br = p.get("block_reasons", [])
            if br:
                st.markdown(f"<div style='color:#ff6666;font-size:0.75em;margin-bottom:8px;margin-left:14px'>⚠️ Blocked: {', '.join(br)}</div>", unsafe_allow_html=True)

    st.caption(f"{len(scheduled_conviction)} strong + {len(scheduled_near)} lean scheduled")
else:
    st.markdown("""<div style="background:#0f172a;padding:30px;border-radius:12px;text-align:center">
<div style="color:#666;font-size:1em">No picks today</div></div>""", unsafe_allow_html=True)

st.divider()

# ============================================================
# LIVE GAMES
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
        pace_display = f"→ {round((g['total'] / mins) * 40)}" if mins >= 5 else ""
        clr = "#ff0000" if half >= 3 else "#ffaa00" if (half == 2 and diff <= 8) else "#00ff00"
        half_label = "H1" if half == 1 else "H2" if half == 2 else f"OT{half-2}"
        kalshi_url = build_kalshi_ncaa_url(g['away_abbrev'], g['home_abbrev'])
        pd_ = precomputed.get(gk, {})
        buy_team = pd_.get('market_pick', g['home_abbrev'])
        is_strong = pd_.get('is_conviction', False)
        bc = "#00ff00" if is_strong else "#ffaa00"
        tb = f'<span style="color:{bc};font-weight:bold">{"🔒 STRONG" if is_strong else "🟡 LEAN"}</span>'
        buy_html = f'<a href="{kalshi_url}" target="_blank" style="background:#22c55e;color:#000;padding:8px 20px;border-radius:6px;font-weight:bold;text-decoration:none">BUY {escape_html(buy_team)}</a>' if kalshi_url else ''

        st.markdown(f"""<div class="game-card" style="border-left:4px solid {bc}">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
<div style="display:flex;align-items:center;gap:12px">{tb}
<b style="color:#fff;font-size:1.1em">{escape_html(g['away_abbrev'])} {g['away_score']} @ {escape_html(g['home_abbrev'])} {g['home_score']}</b></div>
<div style="display:flex;align-items:center;gap:12px">
<span style="color:{clr};font-weight:bold">{half_label} {escape_html(clock)}</span>
<span style="color:#666">{pace_display}</span>{buy_html}</div></div></div>""", unsafe_allow_html=True)
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
            ps = g['home_score'] if pick == parts[1] else g['away_score']
            os_ = g['away_score'] if pick == parts[1] else g['home_score']
            lead = ps - os_
            is_final = g['status_type'] == "STATUS_FINAL"
            if is_final:
                won = ps > os_
                label, clr = ("✅ WON", "#00aa00") if won else ("❌ LOST", "#aa0000")
            elif g['period'] > 0:
                label, clr = ("🟢", "#00aa00") if lead >= 10 else ("🟡", "#aaaa00") if lead >= 0 else ("🔴", "#aa0000")
            else:
                label, clr = "⏳", "#444"
            hl = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}" if g['period'] > 2 else ""
            status = "FINAL" if is_final else f"{hl} {escape_html(g['clock'])}" if g['period'] > 0 else ""
            st.markdown(f"""<div style='background:#0a0a14;padding:10px;border-radius:6px;border-left:2px solid {clr};margin-bottom:6px'>
<div style='display:flex;justify-content:space-between;font-size:0.85em;flex-wrap:wrap'><b style='color:#888'>{escape_html(gk.replace("@"," @ "))}</b> <span style='color:#444'>{status}</span> <b style='color:{clr}'>{label}</b></div>
<div style='color:#555;margin-top:4px;font-size:0.75em'>Signal: {escape_html(pick)} | {lead:+d}</div></div>""", unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c2:
                if st.button("🗑️", key=f"del_ncaa_{idx}"):
                    st.session_state.ncaa_positions.pop(idx)
                    save_positions(st.session_state.ncaa_positions)
                    st.rerun()
else:
    st.caption("No watched games")

st.divider()

# ============================================================
# CUSHION SCANNER
# ============================================================
NCAA_THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5, 165.5, 170.5]

st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals in live games")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [5, 8, 10, 12, 15], index=0, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

cush_results = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    total = g['total']
    if g['status_type'] == "STATUS_FINAL" or mins < cush_min or mins <= 0: continue
    pace = total / mins
    remaining = max(40 - mins, 1)
    projected = round(total + pace * remaining)

    if cush_side == "NO":
        bi = next((i for i, t in enumerate(NCAA_THRESHOLDS) if t > projected), len(NCAA_THRESHOLDS)-1)
        si = min(bi + 2, len(NCAA_THRESHOLDS) - 1)
        safe_line = NCAA_THRESHOLDS[si]
        cushion = safe_line - projected
    else:
        bi = next((i for i in range(len(NCAA_THRESHOLDS)-1, -1, -1) if NCAA_THRESHOLDS[i] < projected), 0)
        si = max(bi - 2, 0)
        safe_line = NCAA_THRESHOLDS[si]
        cushion = projected - safe_line

    if cushion < 6: continue

    if cush_side == "NO":
        ps, pc = ("✅ SLOW", "#00ff00") if pace < 3.2 else ("⚠️ AVG", "#ffff00") if pace < 3.5 else ("❌ FAST", "#ff0000")
    else:
        ps, pc = ("✅ FAST", "#00ff00") if pace > 3.8 else ("⚠️ AVG", "#ffff00") if pace > 3.5 else ("❌ SLOW", "#ff0000")

    cush_results.append({'game': gk, 'total': total, 'mins': mins, 'pace': pace,
                         'ps': ps, 'pc': pc, 'projected': projected, 'cushion': cushion,
                         'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']})

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        hl = "H1" if r['period'] == 1 else "H2" if r['period'] == 2 else f"OT{r['period']-2}"
        sc = "#00aa00" if cush_side == "NO" else "#cc6600"
        st.markdown(f"""<div class="live-bar" style="border-left:3px solid {r['pc']}">
<div class="items">
<b style="color:#fff">{escape_html(r['game'].replace('@',' @ '))}</b>
<span style="color:#888">{hl} {escape_html(r['clock'])}</span>
<span style="color:#888">{r['total']}pts/{r['mins']:.0f}min</span>
<span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
<span style="background:{sc};color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {cush_side} {r['safe_line']}</span>
<span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
<span style="color:{r['pc']}">{r['ps']}</span>
</div></div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet.")

st.divider()

# ============================================================
# PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for all live games")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 5:
        pace = round(g['total'] / mins, 2)
        pace_data.append({"game": gk, "pace": pace, "proj": round(pace * 40),
                          "total": g['total'], "mins": mins,
                          "period": g['period'], "clock": g['clock'],
                          "final": g['status_type'] == "STATUS_FINAL"})

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        hl = "H1" if p['period'] == 1 else "H2" if p['period'] == 2 else f"OT{p['period']-2}" if p['period'] > 2 else ""
        if p['pace'] < 3.2:
            lbl, clr = "🟢 SLOW", "#00ff00"
            bi = next((i for i, t in enumerate(NCAA_THRESHOLDS) if t > p['proj']), len(NCAA_THRESHOLDS)-1)
            si = min(bi + 2, len(NCAA_THRESHOLDS) - 1)
            rec_html = f'<span style="background:#00aa00;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">NO {NCAA_THRESHOLDS[si]}</span>' if not p['final'] else ""
        elif p['pace'] < 3.5:
            lbl, clr, rec_html = "🟡 AVG", "#ffff00", ""
        elif p['pace'] < 3.8:
            lbl, clr = "🟠 FAST", "#ff8800"
            bi = next((i for i in range(len(NCAA_THRESHOLDS)-1, -1, -1) if NCAA_THRESHOLDS[i] < p['proj']), 0)
            si = max(bi - 2, 0)
            rec_html = f'<span style="background:#cc6600;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">YES {NCAA_THRESHOLDS[si]}</span>' if not p['final'] else ""
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
            bi = next((i for i in range(len(NCAA_THRESHOLDS)-1, -1, -1) if NCAA_THRESHOLDS[i] < p['proj']), 0)
            si = max(bi - 2, 0)
            rec_html = f'<span style="background:#cc0000;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">YES {NCAA_THRESHOLDS[si]}</span>' if not p['final'] else ""

        status = "FINAL" if p['final'] else f"{hl} {p['clock']}"
        st.markdown(f"""<div class="live-bar" style="border-left:3px solid {clr}">
<div class="items">
<b style="color:#fff">{escape_html(p['game'].replace('@',' @ '))}</b>
<span style="color:#666">{status}</span>
<span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span>
<span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span>
<span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span>
{rec_html}
</div></div>""", unsafe_allow_html=True)
else:
    st.info("No games with 5+ minutes played yet")

st.divider()

# ============================================================
# ALL GAMES
# ============================================================
with st.expander(f"📺 ALL GAMES ({len(games)})", expanded=False):
    for gk, g in sorted(games.items()):
        aap = ap_rankings.get(g['away_abbrev'], 0)
        hap = ap_rankings.get(g['home_abbrev'], 0)
        ad = f"#{aap} " if aap > 0 else ""
        hd = f"#{hap} " if hap > 0 else ""
        if g['status_type'] == "STATUS_FINAL":
            winner = g['home_abbrev'] if g['home_score'] > g['away_score'] else g['away_abbrev']
            status, clr = f"✅ {escape_html(winner)}", "#44ff44"
        elif g['period'] > 0:
            hl = "H1" if g['period'] == 1 else "H2" if g['period'] == 2 else f"OT{g['period']-2}"
            status, clr = f"🔴 {hl}", "#ff4444"
        else:
            status, clr = "—", "#333"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#050508;padding:5px 10px;margin-bottom:2px;border-radius:4px;font-size:0.85em;flex-wrap:wrap">
<div><span style="color:#666">{escape_html(ad)}{escape_html(g['away_abbrev'])}</span> {g['away_score']} @ <span style="color:#666">{escape_html(hd)}{escape_html(g['home_abbrev'])}</span> {g['home_score']}</div>
<span style="color:{clr};font-size:0.8em">{status}</span></div>""", unsafe_allow_html=True)

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
