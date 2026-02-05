import streamlit as st

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

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

send_ga4_event("NHL Edge Finder", "/NHL")

# ============================================================
# IMPORTS
# ============================================================
import requests
import json
import os
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

apply_styles()

VERSION = "21.1 LIVE"

# ============================================================
# MOBILE-RESPONSIVE CSS
# ============================================================
st.markdown("""
<style>
/* Game card container */
.game-card {
    background: #1a1a2e;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}

/* Card header: signal badge + matchup + time */
.card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

/* Signal badge */
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

/* Matchup info */
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

/* Game time */
.game-time {
    text-align: right;
    flex-shrink: 0;
    min-width: 100px;
}
.game-time .date {
    font-weight: bold;
    color: #ddd;
    font-size: 14px;
}
.game-time .time {
    font-size: 12px;
    color: #999;
}

/* Pick row */
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

/* Model probability */
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

/* B2B warning badge */
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

/* Detail stats grid */
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

/* Edge breakdown */
.edge-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
}
.edge-col {
    background: #111;
    border-radius: 8px;
    padding: 10px;
}
.edge-col .edge-title {
    font-size: 13px;
    font-weight: bold;
    color: #ddd;
    margin-bottom: 6px;
}
.edge-col .edge-line {
    font-size: 11px;
    color: #aaa;
    margin: 2px 0;
}
.edge-col .edge-line.pos { color: #00cc66; }
.edge-col .edge-line.neg { color: #ff5555; }

/* MOBILE: stack everything vertically */
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
    .game-time {
        text-align: left;
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
    .edge-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

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
    return {"picks": [], "next_ml": 1}

def save_strong_picks(data):
    try:
        with open(STRONG_PICKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

def get_next_ml_number():
    picks_data = st.session_state.strong_picks
    return picks_data.get("next_ml", 1)

def add_strong_pick(sport, team, opponent, edge_score, reasons):
    picks_data = st.session_state.strong_picks
    ml_num = get_next_ml_number()
    pick = {
        "ml_number": ml_num, "sport": sport, "team": team,
        "opponent": opponent, "edge_score": edge_score, "reasons": reasons,
        "timestamp": datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        "result": "PENDING"
    }
    picks_data["picks"].append(pick)
    picks_data["next_ml"] = ml_num + 1
    save_strong_picks(picks_data)
    st.session_state.strong_picks = picks_data
    return ml_num

if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

# ============================================================
# TEAM DATA
# ============================================================
NHL_TEAMS = {
    "ANA": {"name": "Anaheim Ducks"}, "BOS": {"name": "Boston Bruins"},
    "BUF": {"name": "Buffalo Sabres"}, "CGY": {"name": "Calgary Flames"},
    "CAR": {"name": "Carolina Hurricanes"}, "CHI": {"name": "Chicago Blackhawks"},
    "COL": {"name": "Colorado Avalanche"}, "CBJ": {"name": "Columbus Blue Jackets"},
    "DAL": {"name": "Dallas Stars"}, "DET": {"name": "Detroit Red Wings"},
    "EDM": {"name": "Edmonton Oilers"}, "FLA": {"name": "Florida Panthers"},
    "LAK": {"name": "Los Angeles Kings"}, "MIN": {"name": "Minnesota Wild"},
    "MTL": {"name": "Montreal Canadiens"}, "NSH": {"name": "Nashville Predators"},
    "NJD": {"name": "New Jersey Devils"}, "NYI": {"name": "New York Islanders"},
    "NYR": {"name": "New York Rangers"}, "OTT": {"name": "Ottawa Senators"},
    "PHI": {"name": "Philadelphia Flyers"}, "PIT": {"name": "Pittsburgh Penguins"},
    "SJS": {"name": "San Jose Sharks"}, "SEA": {"name": "Seattle Kraken"},
    "STL": {"name": "St. Louis Blues"}, "TBL": {"name": "Tampa Bay Lightning"},
    "TOR": {"name": "Toronto Maple Leafs"}, "UTA": {"name": "Utah Hockey Club"},
    "VAN": {"name": "Vancouver Canucks"}, "VGK": {"name": "Vegas Golden Knights"},
    "WSH": {"name": "Washington Capitals"}, "WPG": {"name": "Winnipeg Jets"},
}

eastern = pytz.timezone('US/Eastern')

TEAM_ABBREVS = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "Montréal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
    "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

ESPN_TEAM_IDS = {}

# ============================================================
# ESPN API FUNCTIONS
# ============================================================
@st.cache_data(ttl=3600)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={yesterday}"
    teams_played = set()
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            status_name = event.get("status", {}).get("type", {}).get("name", "")
            if status_name in ("STATUS_FINAL", "STATUS_IN_PROGRESS", "STATUS_END_PERIOD"):
                for c in comp.get("competitors", []):
                    full_name = c.get("team", {}).get("displayName", "")
                    abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                    if abbr:
                        teams_played.add(abbr)
    except: pass
    return teams_played

@st.cache_data(ttl=3600)
def fetch_team_stats():
    stats = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/standings"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for group in data.get("children", []):
            for div in group.get("standings", {}).get("entries", []):
                team_obj = div.get("team", {})
                full_name = team_obj.get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, team_obj.get("abbreviation", ""))
                espn_id = team_obj.get("id", "")
                if abbr:
                    ESPN_TEAM_IDS[abbr] = espn_id
                    ts = {}
                    for s in div.get("stats", []):
                        ts[s.get("name", "")] = s.get("value", 0)
                    gp = max(int(ts.get("gamesPlayed", 1)), 1)
                    stats[abbr] = {
                        "wins": int(ts.get("wins", 0)),
                        "losses": int(ts.get("losses", 0)),
                        "otl": int(ts.get("OTLosses", ts.get("otLosses", 0))),
                        "points": int(ts.get("points", 0)),
                        "gp": gp,
                        "gf_per_game": round(ts.get("pointsFor", 0) / gp, 2),
                        "ga_per_game": round(ts.get("pointsAgainst", 0) / gp, 2),
                        "point_pct": round(ts.get("points", 0) / (gp * 2), 3),
                    }
    except Exception as e:
        st.warning(f"Could not fetch team stats: {e}")
    return stats

@st.cache_data(ttl=3600)
def fetch_team_special_teams():
    special = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams?limit=40"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_entry in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            t = team_entry.get("team", {})
            full_name = t.get("displayName", "")
            abbr = TEAM_ABBREVS.get(full_name, t.get("abbreviation", ""))
            espn_id = t.get("id", "")
            if abbr and espn_id:
                try:
                    stats_url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{espn_id}/statistics"
                    sr = requests.get(stats_url, timeout=5)
                    sd = sr.json()
                    ts = {}
                    for cat in sd.get("results", {}).get("stats", {}).get("categories", []):
                        for stat in cat.get("stats", []):
                            ts[stat.get("name", "")] = stat.get("value", 0)
                    pp = ts.get("powerPlayPct", ts.get("PPPctg", 0))
                    pk = ts.get("penaltyKillPct", ts.get("PKPctg", 0))
                    special[abbr] = {
                        "pp_pct": round(float(pp), 1) if pp else 20.0,
                        "pk_pct": round(float(pk), 1) if pk else 80.0,
                    }
                except:
                    special[abbr] = {"pp_pct": 20.0, "pk_pct": 80.0}
    except: pass
    return special

@st.cache_data(ttl=1800)
def fetch_last10_record(team_abbr):
    espn_id = ESPN_TEAM_IDS.get(team_abbr, "")
    if not espn_id:
        return "?-?-?"
    try:
        now_et = datetime.now(eastern)
        season_year = now_et.year if now_et.month >= 9 else now_et.year
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{espn_id}/schedule?season={season_year}&seasontype=2"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        completed = []
        for event in data.get("events", []):
            if event.get("status", {}).get("type", {}).get("name", "") == "STATUS_FINAL":
                comp = event.get("competitions", [{}])[0]
                for c in comp.get("competitors", []):
                    t_abbr = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), c.get("team", {}).get("abbreviation", ""))
                    if t_abbr == team_abbr:
                        winner = c.get("winner", False)
                        period = event.get("status", {}).get("period", 3)
                        completed.append("W" if winner else ("OT" if period > 3 else "L"))
                        break
        last10 = completed[-10:] if len(completed) >= 10 else completed
        return f"{last10.count('W')}-{last10.count('L')}-{last10.count('OT')}"
    except:
        return "?-?-?"

@st.cache_data(ttl=900)
def fetch_probable_goalies(event_id):
    home_goalie, away_goalie = "TBD", "TBD"
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={event_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for item in data.get("rosters", []):
            ha = item.get("homeAway", "")
            for entry in item.get("roster", []):
                if entry.get("probable", False) or entry.get("starter", False):
                    if entry.get("position", {}).get("abbreviation", "") == "G":
                        name = entry.get("athlete", {}).get("shortName", "TBD")
                        if ha == "home": home_goalie = name
                        else: away_goalie = name
        if home_goalie == "TBD" or away_goalie == "TBD":
            for comp in data.get("header", {}).get("competitions", []):
                for c in comp.get("competitors", []):
                    for lc in c.get("leaders", []):
                        if lc.get("abbreviation", "") == "SV%":
                            athletes = lc.get("leaders", [])
                            if athletes:
                                gn = athletes[0].get("athlete", {}).get("shortName", "TBD")
                                if c.get("homeAway") == "home" and home_goalie == "TBD": home_goalie = gn
                                elif c.get("homeAway") == "away" and away_goalie == "TBD": away_goalie = gn
    except: pass
    return home_goalie, away_goalie

@st.cache_data(ttl=120)
def fetch_nhl_games_real():
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={today_date}"
    yesterday_teams = fetch_yesterday_teams()
    team_stats = fetch_team_stats()
    special_teams = fetch_team_special_teams()
    games = []
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_abbr, away_abbr = None, None, "", ""
            home_record, away_record = "0-0-0", "0-0-0"
            for c in competitors:
                fn = c.get("team", {}).get("displayName", "")
                ab = TEAM_ABBREVS.get(fn, c.get("team", {}).get("abbreviation", ""))
                rec = c.get("records", [{}])[0].get("summary", "0-0-0") if c.get("records") else "0-0-0"
                if c.get("homeAway") == "home":
                    home_team, home_abbr, home_record = fn, ab, rec
                else:
                    away_team, away_abbr, away_record = fn, ab, rec
            gd = event.get("date", "")
            status_type = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            game_date_str, game_time = "TBD", "TBD"
            if gd:
                for fmt in ["%Y-%m-%dT%H:%M%SZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"]:
                    try:
                        dt = datetime.strptime(gd[:20].rstrip("Z"), fmt.replace("Z","").replace("%z",""))
                        dt_e = dt.replace(tzinfo=pytz.UTC).astimezone(eastern)
                        game_date_str = dt_e.strftime("%a %b %d")
                        game_time = dt_e.strftime("%I:%M %p ET")
                        break
                    except: continue
            home_st = special_teams.get(home_abbr, {"pp_pct": 20.0, "pk_pct": 80.0})
            away_st = special_teams.get(away_abbr, {"pp_pct": 20.0, "pk_pct": 80.0})
            home_ts = team_stats.get(home_abbr, {"gf_per_game": 3.0, "ga_per_game": 3.0, "point_pct": 0.500})
            away_ts = team_stats.get(away_abbr, {"gf_per_game": 3.0, "ga_per_game": 3.0, "point_pct": 0.500})
            eid = event.get("id", "")
            hg, ag = fetch_probable_goalies(eid)
            games.append({
                "id": eid, "home": home_abbr, "away": away_abbr,
                "home_name": home_team, "away_name": away_team,
                "home_record": home_record, "away_record": away_record,
                "game_date": game_date_str, "game_time": game_time, "status": status_type,
                "home_b2b": home_abbr in yesterday_teams, "away_b2b": away_abbr in yesterday_teams,
                "home_rest": 0 if home_abbr in yesterday_teams else 1,
                "away_rest": 0 if away_abbr in yesterday_teams else 1,
                "home_pp": home_st["pp_pct"], "away_pp": away_st["pp_pct"],
                "home_pk": home_st["pk_pct"], "away_pk": away_st["pk_pct"],
                "home_gf_pg": home_ts["gf_per_game"], "home_ga_pg": home_ts["ga_per_game"],
                "away_gf_pg": away_ts["gf_per_game"], "away_ga_pg": away_ts["ga_per_game"],
                "home_point_pct": home_ts["point_pct"], "away_point_pct": away_ts["point_pct"],
                "home_goalie_name": hg, "away_goalie_name": ag,
            })
        return games
    except Exception as e:
        st.error(f"ESPN API error: {e}")
        return []

# ============================================================
# EDGE CALCULATIONS
# ============================================================
def calc_goalie_edge(game, team):
    g = game[f"{team}_goalie_name"]
    o = game[f"{'home' if team == 'away' else 'away'}_goalie_name"]
    edge = 0
    if g != "TBD" and o == "TBD": edge += 0.3
    elif g == "TBD" and o != "TBD": edge -= 0.3
    return max(-2, min(2, edge))

def calc_fatigue_edge(game, team):
    opp = "home" if team == "away" else "away"
    b2b, ob2b = game[f"{team}_b2b"], game[f"{opp}_b2b"]
    r, or_ = game[f"{team}_rest"], game[f"{opp}_rest"]
    edge = 0
    if b2b and not ob2b: edge -= 1.0
    elif not b2b and ob2b: edge += 1.0
    edge += (r - or_) * 0.25
    return max(-1.5, min(1.5, edge))

def calc_home_ice(game, team):
    return 0.5 if team == "home" else -0.3

def calc_form_edge(game, team):
    opp = "home" if team == "away" else "away"
    diff = game[f"{team}_point_pct"] - game[f"{opp}_point_pct"]
    return max(-1.5, min(1.5, diff * 6))

def calc_st_edge(game, team):
    opp = "home" if team == "away" else "away"
    pp_e = (game[f"{team}_pp"] - game[f"{opp}_pk"]) / 100
    pk_e = (game[f"{team}_pk"] - game[f"{opp}_pp"]) / 100
    return max(-1, min(1, (pp_e + pk_e) * 5))

def calc_gfga_edge(game, team):
    opp = "home" if team == "away" else "away"
    td = game[f"{team}_gf_pg"] - game[f"{team}_ga_pg"]
    od = game[f"{opp}_gf_pg"] - game[f"{opp}_ga_pg"]
    return max(-1.5, min(1.5, (td - od) / 2))

def calc_record_edge(game, team):
    opp = "home" if team == "away" else "away"
    def prs(rec):
        try:
            p = rec.split("-")
            w, l = int(p[0]), int(p[1])
            ot = int(p[2]) if len(p) > 2 else 0
            t = w + l + ot
            return (w * 2 + ot) / (t * 2) if t > 0 else 0.5
        except: return 0.5
    return max(-0.5, min(0.5, (prs(game[f"{team}_record"]) - prs(game[f"{opp}_record"])) * 2))

def calc_total_edge(game, team):
    g = calc_goalie_edge(game, team)
    f = calc_fatigue_edge(game, team)
    h = calc_home_ice(game, team)
    fo = calc_form_edge(game, team)
    st = calc_st_edge(game, team)
    gf = calc_gfga_edge(game, team)
    r = calc_record_edge(game, team)
    total = g*1.5 + f*1.2 + h*1.0 + fo*1.0 + st*0.8 + gf*1.0 + r*0.5
    return {"total": round(total,2), "goalie": round(g,2), "fatigue": round(f,2),
            "home_ice": round(h,2), "form": round(fo,2), "special_teams": round(st,2),
            "gf_ga": round(gf,2), "record": round(r,2)}

def get_score(edge_total):
    return round(max(0, min(10, 5.0 + edge_total)), 1)

def get_model_prob(ae, he):
    d = he - ae
    hp = max(10, min(90, 50 + d * 5))
    return round(100 - hp), round(hp)

def analyze_game(game):
    ae = calc_total_edge(game, "away")
    he = calc_total_edge(game, "home")
    a_sc = get_score(ae["total"])
    h_sc = get_score(he["total"])
    reasons_h, reasons_a = [], []
    if he["fatigue"] >= 0.7: reasons_h.append(f"Rest adv (+{he['fatigue']:.1f})")
    elif ae["fatigue"] >= 0.7: reasons_a.append(f"Rest adv (+{ae['fatigue']:.1f})")
    if he["form"] >= 0.5: reasons_h.append(f"Better form (+{he['form']:.1f})")
    elif ae["form"] >= 0.5: reasons_a.append(f"Better form (+{ae['form']:.1f})")
    if he["special_teams"] >= 0.3: reasons_h.append(f"Special teams (+{he['special_teams']:.1f})")
    elif ae["special_teams"] >= 0.3: reasons_a.append(f"Special teams (+{ae['special_teams']:.1f})")
    if he["gf_ga"] >= 0.3: reasons_h.append(f"GF/GA edge (+{he['gf_ga']:.1f})")
    elif ae["gf_ga"] >= 0.3: reasons_a.append(f"GF/GA edge (+{ae['gf_ga']:.1f})")
    reasons_h.append("Home ice (+0.5)")
    if h_sc >= a_sc:
        return game["home"], h_sc, reasons_h[:4]
    else:
        return game["away"], a_sc, reasons_a[:4]

def get_tier(score):
    if score >= 10.0: return "🔥 ELITE", "#cc0000"
    elif score >= 9.0: return "🔒 STRONG", "#00cc00"
    elif score >= 7.0: return "🔵 BUY", "#0088cc"
    elif score >= 5.5: return "🟡 LEAN", "#ccaa00"
    else: return "⚪ PASS", "#666666"

# ============================================================
# SIDEBAR
# ============================================================
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    st.header("🏷️ STRONG PICKS")
    today_tags = len([p for p in st.session_state.strong_picks.get('picks', [])
                      if p.get('sport') == 'NHL' and today_str in p.get('timestamp', '')])
    st.markdown(f"**Next ML#:** ML-{get_next_ml_number():03d}  \n**Today's Tags:** {today_tags}")
    st.divider()
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔥 **ELITE** → 10.0  
🔒 **STRONG** → 9.0-9.9  
🔵 **BUY** → 7.0-8.9  
🟡 **LEAN** → 5.5-6.9  
⚪ **PASS** → Below 5.5
""")
    st.divider()
    st.header("🔗 KALSHI")
    st.markdown('<a href="https://kalshi.com/?search=nhl" target="_blank" style="color:#00aaff;">NHL Markets ↗</a>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"v{VERSION} | ESPN Live Data")

# ============================================================
# MAIN
# ============================================================
st.title("🏒 NHL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Live ESPN Data")

games = fetch_nhl_games_real()
if not games:
    st.warning("No NHL games scheduled today.")
    st.stop()

st.header("🎯 MONEYLINE PICKS")

# Analyze and sort
analyses = []
for game in games:
    pt, ps, reasons = analyze_game(game)
    tier, tc = get_tier(ps)
    ae = calc_total_edge(game, "away")
    he = calc_total_edge(game, "home")
    ap, hp = get_model_prob(ae["total"], he["total"])
    analyses.append({"game": game, "pick_team": pt, "pick_score": ps, "reasons": reasons,
                      "tier": tier, "tc": tc, "ae": ae, "he": he, "ap": ap, "hp": hp})
analyses.sort(key=lambda x: x["pick_score"], reverse=True)

for a in analyses:
    g = a["game"]
    pt, ps = a["pick_team"], a["pick_score"]
    tier, tc = a["tier"], a["tc"]
    is_away = pt == g["away"]
    pick_name = NHL_TEAMS.get(pt, {}).get("name", pt)
    opp = g["home"] if is_away else g["away"]
    opp_name = NHL_TEAMS.get(opp, {}).get("name", opp)
    pick_prob = a["ap"] if is_away else a["hp"]
    opp_prob = a["hp"] if is_away else a["ap"]

    # B2B badges
    away_b2b_html = ' <span class="b2b-badge">B2B</span>' if g["away_b2b"] else ""
    home_b2b_html = ' <span class="b2b-badge">B2B</span>' if g["home_b2b"] else ""

    reasons_html = ", ".join(a["reasons"]) if a["reasons"] else "Base model edge"

    # Render card as pure HTML for mobile responsiveness
    card_html = f"""
    <div class="game-card">
        <div class="card-header">
            <div class="signal-badge" style="background:{tc};">
                {tier} <span class="score">{ps}/10</span>
            </div>
            <div class="matchup-info">
                <p class="teams">{g['away']}{away_b2b_html} @ {g['home']}{home_b2b_html}</p>
                <p class="names">{g.get('away_name','')} at {g.get('home_name','')}</p>
            </div>
            <div class="game-time">
                <div class="date">{g['game_date']}</div>
                <div class="time">{g['game_time']}</div>
            </div>
        </div>
        <div class="pick-row">
            <div class="pick-info">
                <p class="pick-team">PICK: {pt} {pick_name}</p>
                <p class="pick-vs">vs {opp} {opp_name}</p>
                <p class="edge-factors">Edge: {reasons_html}</p>
            </div>
            <div class="model-box">
                <div class="model-pct">{pt} {pick_prob}%</div>
                <div class="model-sub">{opp} {opp_prob}%</div>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Expandable details (Streamlit native - works on mobile)
    with st.expander(f"📊 {g['away']} @ {g['home']} — Full Details"):
        ae, he = a["ae"], a["he"]

        # Stats as HTML grid (responsive)
        away_b2b_warn = '<p class="stat-line warn">⚠️ BACK-TO-BACK</p>' if g["away_b2b"] else ""
        home_b2b_warn = '<p class="stat-line warn">⚠️ BACK-TO-BACK</p>' if g["home_b2b"] else ""

        stats_html = f"""
        <div class="stats-grid">
            <div class="stat-col">
                <h4>{g['away']} {g.get('away_name','')}</h4>
                <p class="stat-line">Record: {g['away_record']}</p>
                <p class="stat-line">Pt%: {g['away_point_pct']:.3f}</p>
                <p class="stat-line">GF/G: {g['away_gf_pg']:.2f} | GA/G: {g['away_ga_pg']:.2f}</p>
                <p class="stat-line">PP: {g['away_pp']:.1f}% | PK: {g['away_pk']:.1f}%</p>
                <p class="stat-line">🥅 {g['away_goalie_name']}</p>
                {away_b2b_warn}
            </div>
            <div class="stat-col">
                <h4>{g['home']} {g.get('home_name','')}</h4>
                <p class="stat-line">Record: {g['home_record']}</p>
                <p class="stat-line">Pt%: {g['home_point_pct']:.3f}</p>
                <p class="stat-line">GF/G: {g['home_gf_pg']:.2f} | GA/G: {g['home_ga_pg']:.2f}</p>
                <p class="stat-line">PP: {g['home_pp']:.1f}% | PK: {g['home_pk']:.1f}%</p>
                <p class="stat-line">🥅 {g['home_goalie_name']}</p>
                {home_b2b_warn}
            </div>
        </div>
        """
        st.markdown(stats_html, unsafe_allow_html=True)

        # Last 10 (fetched on demand)
        l10_away = fetch_last10_record(g['away'])
        l10_home = fetch_last10_record(g['home'])
        st.caption(f"Last 10: {g['away']} {l10_away} | {g['home']} {l10_home}")

        # Edge breakdown as HTML
        def edge_class(v):
            return "pos" if v > 0.05 else ("neg" if v < -0.05 else "")

        edge_html = f"""
        <div class="edge-grid">
            <div class="edge-col">
                <div class="edge-title">{g['away']} Edge: {ae['total']:+.2f}</div>
                <p class="edge-line {edge_class(ae['goalie'])}">Goalie: {ae['goalie']:+.2f}</p>
                <p class="edge-line {edge_class(ae['fatigue'])}">Fatigue: {ae['fatigue']:+.2f}</p>
                <p class="edge-line {edge_class(ae['home_ice'])}">Home Ice: {ae['home_ice']:+.2f}</p>
                <p class="edge-line {edge_class(ae['form'])}">Form: {ae['form']:+.2f}</p>
                <p class="edge-line {edge_class(ae['special_teams'])}">ST: {ae['special_teams']:+.2f}</p>
                <p class="edge-line {edge_class(ae['gf_ga'])}">GF/GA: {ae['gf_ga']:+.2f}</p>
                <p class="edge-line {edge_class(ae['record'])}">Record: {ae['record']:+.2f}</p>
            </div>
            <div class="edge-col">
                <div class="edge-title">{g['home']} Edge: {he['total']:+.2f}</div>
                <p class="edge-line {edge_class(he['goalie'])}">Goalie: {he['goalie']:+.2f}</p>
                <p class="edge-line {edge_class(he['fatigue'])}">Fatigue: {he['fatigue']:+.2f}</p>
                <p class="edge-line {edge_class(he['home_ice'])}">Home Ice: {he['home_ice']:+.2f}</p>
                <p class="edge-line {edge_class(he['form'])}">Form: {he['form']:+.2f}</p>
                <p class="edge-line {edge_class(he['special_teams'])}">ST: {he['special_teams']:+.2f}</p>
                <p class="edge-line {edge_class(he['gf_ga'])}">GF/GA: {he['gf_ga']:+.2f}</p>
                <p class="edge-line {edge_class(he['record'])}">Record: {he['record']:+.2f}</p>
            </div>
        </div>
        """
        st.markdown(edge_html, unsafe_allow_html=True)

    # Tag button
    if ps >= 9.0:
        if st.button("🏷️ TAG AS STRONG PICK", key=f"tag_{g['id']}", use_container_width=True):
            ml_num = add_strong_pick("NHL", pt, opp, ps, a["reasons"])
            st.success(f"Tagged as ML-{ml_num:03d}")
            st.rerun()

# ============================================================
# LEGEND
# ============================================================
st.markdown("---")
with st.expander("📖 LEGEND & GUIDE"):
    st.markdown("""
### Signal Tiers
🔥 **ELITE (10.0)** — Perfect edge | 🔒 **STRONG (9.0-9.9)** — High confidence | 🔵 **BUY (7.0-8.9)** — Good edge | 🟡 **LEAN (5.5-6.9)** — Slight edge | ⚪ **PASS (<5.5)** — No edge

### Edge Factors (All Real ESPN Data)
**Goalie** (1.5x) — Confirmed starter vs TBD | **Fatigue** (1.2x) — B2B from schedule | **Home Ice** (1.0x) — Home advantage | **Form** (1.0x) — Point % from standings | **GF/GA** (1.0x) — Goals per game differential | **Special Teams** (0.8x) — PP% and PK% | **Record** (0.5x) — W-L-OTL strength

### How to Use
1. Focus on 🔵 BUY (7.0+) or better
2. Expand details to verify stats and goalies
3. Confirm on Kalshi before trading
4. TAG strong picks (9.0+) for tracking
5. Verify goalies on DailyFaceoff.com ~90 min before game
""")

st.markdown("---")
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
