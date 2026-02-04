import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NCAA Edge Finder", "/NCAA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "NCAA 1.0"
LEAGUE_AVG_TOTAL = 145  # NCAA avg total ~140-150
THRESHOLDS = [130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

TEAM_ABBREVS = {
    "Alabama Crimson Tide": "Alabama", "Arizona Wildcats": "Arizona", "Arkansas Razorbacks": "Arkansas",
    "Auburn Tigers": "Auburn", "Baylor Bears": "Baylor", "Cincinnati Bearcats": "Cincinnati",
    "Connecticut Huskies": "UConn", "Duke Blue Devils": "Duke", "Florida Gators": "Florida",
    "Gonzaga Bulldogs": "Gonzaga", "Houston Cougars": "Houston", "Illinois Fighting Illini": "Illinois",
    "Indiana Hoosiers": "Indiana", "Iowa Hawkeyes": "Iowa", "Kansas Jayhawks": "Kansas",
    "Kentucky Wildcats": "Kentucky", "Louisville Cardinals": "Louisville", "Marquette Golden Eagles": "Marquette",
    "Maryland Terrapins": "Maryland", "Michigan State Spartans": "Michigan State", "Michigan Wolverines": "Michigan",
    "North Carolina Tar Heels": "North Carolina", "Northwestern Wildcats": "Northwestern", "Ohio State Buckeyes": "Ohio State",
    "Oregon Ducks": "Oregon", "Purdue Boilermakers": "Purdue", "Saint Mary's Gaels": "Saint Mary's",
    "San Diego State Aztecs": "San Diego State", "Seton Hall Pirates": "Seton Hall", "Tennessee Volunteers": "Tennessee",
    "Texas Longhorns": "Texas", "UCLA Bruins": "UCLA", "USC Trojans": "USC", "Villanova Wildcats": "Villanova",
    "Virginia Cavaliers": "Virginia", "Wisconsin Badgers": "Wisconsin", "Xavier Musketeers": "Xavier",
    # Add more NCAA teams as needed — this is a starter set
}

KALSHI_CODES = {
    "Alabama": "ALA", "Arizona": "ARI", "Arkansas": "ARK", "Auburn": "AUB", "Baylor": "BAY",
    "Cincinnati": "CIN", "UConn": "UCONN", "Duke": "DUKE", "Florida": "FLA", "Gonzaga": "GONZ",
    "Houston": "HOU", "Illinois": "ILL", "Indiana": "IND", "Iowa": "IOWA", "Kansas": "KAN",
    "Kentucky": "UK", "Louisville": "LOU", "Marquette": "MARQ", "Maryland": "MD", "Michigan State": "MSU",
    "Michigan": "MICH", "North Carolina": "UNC", "Northwestern": "NW", "Ohio State": "OSU", "Oregon": "ORE",
    "Purdue": "PUR", "Saint Mary's": "SMC", "San Diego State": "SDSU", "Seton Hall": "SHU",
    "Tennessee": "TENN", "Texas": "TEX", "UCLA": "UCLA", "USC": "USC", "Villanova": "NOVA",
    "Virginia": "UVA", "Wisconsin": "WIS", "Xavier": "XAV"
    # Expand as needed
}

TEAM_COLORS = {
    "Alabama": "#9E1B32", "Arizona": "#AB0003", "Arkansas": "#9D2235", "Auburn": "#F26522",
    "Baylor": "#154734", "Cincinnati": "#E00122", "UConn": "#0C2340", "Duke": "#001A57",
    "Florida": "#0021A5", "Gonzaga": "#041E42", "Houston": "#C8102E", "Illinois": "#13294B",
    "Indiana": "#7D110C", "Iowa": "#552583", "Kansas": "#0022B4", "Kentucky": "#0033A0",
    "Louisville": "#AD0000", "Marquette": "#000000", "Maryland": "#E03A3E", "Michigan State": "#18453B",
    "Michigan": "#00274C", "North Carolina": "#7BAFD4", "Northwestern": "#4E2A84", "Ohio State": "#BB0000",
    "Oregon": "#007AC1", "Purdue": "#000000", "Saint Mary's": "#990000", "San Diego State": "#A6192E",
    "Seton Hall": "#0C2340", "Tennessee": "#FF8200", "Texas": "#BF5700", "UCLA": "#2774AE",
    "USC": "#990000", "Villanova": "#00205B", "Virginia": "#232D4B", "Wisconsin": "#C5050C",
    "Xavier": "#00205B"
}

# (Add NCAA-specific TEAM_STATS, STAR_PLAYERS, STAR_TIERS, PLAYER_TEAMS if you have them — or leave as empty dicts for now)

def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def speak_play(text):
    clean_text = text.replace("'", "").replace('"', '').replace('\n', ' ')[:100]
    js = f'''<script>if(!window.lastSpoken||window.lastSpoken!=="{clean_text}"){{window.lastSpoken="{clean_text}";var u=new SpeechSynthesisUtterance("{clean_text}");u.rate=1.1;window.speechSynthesis.speak(u);}}</script>'''
    components.html(js, height=0)

@st.cache_data(ttl=30)
def fetch_espn_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=" + today
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            home_record, away_record = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                if c.get("homeAway") == "home": home_team, home_score, home_record = team_name, score, record
                else: away_team, away_score, away_record = team_name, score, record
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_id = event.get("id", "")
            minutes_played = 0
            if period > 0:
                if period <= 2:
                    completed_halves = (period - 1) * 20
                    if clock:
                        try:
                            if ":" in clock: minutes_played = completed_halves + (20 - int(clock.split(":")[0]))
                            else: minutes_played = completed_halves + 20
                        except: minutes_played = completed_halves + 20
                    else: minutes_played = completed_halves
                else: minutes_played = 40 + (period - 2) * 5  # OT
            game_date = event.get("date", "")
            game_time_str, game_datetime_str = "", ""
            if game_date:
                try:
                    game_dt = datetime.fromisoformat(game_date.replace("Z", "+00:00")).astimezone(eastern)
                    game_time_str = game_dt.strftime("%I:%M %p ET")
                    game_datetime_str = game_dt.strftime("%b %d, %I:%M %p ET")
                except: pass
            odds_data = comp.get("odds", [])
            vegas_odds = {}
            if odds_data and len(odds_data) > 0:
                odds = odds_data[0]
                vegas_odds = {"spread": odds.get("spread"), "overUnder": odds.get("overUnder"), "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"), "awayML": odds.get("awayTeamOdds", {}).get("moneyLine")}
            games.append({"away": away_team, "home": home_team, "away_score": away_score, "home_score": home_score, "away_record": away_record, "home_record": home_record, "status": status, "period": period, "clock": clock, "minutes_played": minutes_played, "total_score": home_score + away_score, "game_id": game_id, "vegas_odds": vegas_odds, "game_time": game_time_str, "game_datetime": game_datetime_str})
        return games
    except Exception as e: st.error("ESPN NCAA fetch error: " + str(e)); return []

    @st.cache_data(ttl=60)
def fetch_kalshi_ml():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCBBGAME&status=open&limit=200"  # NCAA series ticker
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNCBBGAME-" not in ticker: continue
            parts = ticker.replace("KXNCBBGAME-", "")
            if "-" not in parts: continue
            main_part, yes_team_code = parts.rsplit("-", 1)
            if len(main_part) < 13: continue
            teams_part = main_part[7:]
            away_code, home_code = teams_part[:3], teams_part[3:6]
            game_key = away_code + "@" + home_code
            yes_bid, yes_ask = m.get("yes_bid", 0) or 0, m.get("yes_ask", 0) or 0
            yes_price = yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)
            yes_team_code = yes_team_code.upper()
            if yes_team_code == home_code.upper(): home_implied, away_implied = yes_price, 100 - yes_price
            else: away_implied, home_implied = yes_price, 100 - yes_price
            if game_key not in markets:
                markets[game_key] = {"away_code": away_code, "home_code": home_code, "yes_team_code": yes_team_code, "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price, "away_implied": away_implied, "home_implied": home_implied}
        return markets
    except Exception as e: st.error("Kalshi NCAA ML fetch error: " + str(e)); return {}

games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
# (add fetch_kalshi_spreads, fetch_injuries, fetch_yesterday_teams if you want them — NCAA may need different endpoints)

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

st.title("🏀 BIGSNAPSHOT NCAA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Vegas vs Kalshi Mispricing Detector (NCAA)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")
st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = edge")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    away, home = g['away'], g['home']
    vegas = g.get('vegas_odds', {})
    away_code, home_code = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
    kalshi_data = kalshi_ml.get(away_code + "@" + home_code, {})
    if not kalshi_data: continue
    home_ml, away_ml, spread = vegas.get('homeML'), vegas.get('awayML'), vegas.get('spread')
    if home_ml and away_ml:
        vegas_home_prob = american_to_implied_prob(home_ml) * 100
        vegas_away_prob = american_to_implied_prob(away_ml) * 100
        total = vegas_home_prob + vegas_away_prob
        vegas_home_prob, vegas_away_prob = vegas_home_prob / total * 100, vegas_away_prob / total * 100
    elif spread:
        try: vegas_home_prob = max(10, min(90, 50 - (float(spread) * 2.8))); vegas_away_prob = 100 - vegas_home_prob
        except: continue
    else: continue
    kalshi_home_prob, kalshi_away_prob = kalshi_data.get('home_implied', 50), kalshi_data.get('away_implied', 50)
    home_edge, away_edge = vegas_home_prob - kalshi_home_prob, vegas_away_prob - kalshi_away_prob
    if home_edge >= 5 or away_edge >= 5:
        if home_edge >= away_edge:
            team, vegas_prob, kalshi_prob, edge = home, vegas_home_prob, kalshi_home_prob, home_edge
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
        else:
            team, vegas_prob, kalshi_prob, edge = away, vegas_away_prob, kalshi_away_prob, away_edge
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
        mispricings.append({'game': g, 'team': team, 'vegas_prob': vegas_prob, 'kalshi_prob': kalshi_prob, 'edge': edge, 'action': action})

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    mp_col1, mp_col2 = st.columns([3, 1])
    with mp_col1: st.success(f"🔥 {len(mispricings)} mispricing opportunities found!")
    with mp_col2:
        if st.button(f"➕ ADD ALL ({len(mispricings)})", key="add_all_mispricing", use_container_width=True):
            added = 0
            for mp in mispricings:
                g = mp['game']
                game_key = f"{g['away']}@{g['home']}"
                if not any(pos['game'] == game_key for pos in st.session_state.positions):
                    st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]})
                    added += 1
            st.toast(f"✅ Added {added} positions!"); st.rerun()
    for mp in mispricings:
        g = mp['game']
        game_key = f"{g['away']}@{g['home']}"
        edge_color = "#ff6b6b" if mp['edge'] >= 10 else ("#22c55e" if mp['edge'] >= 7 else "#eab308")
        edge_label = "🔥 STRONG" if mp['edge'] >= 10 else ("🟢 GOOD" if mp['edge'] >= 7 else "🟡 EDGE")
        action_color = "#22c55e" if mp['action'] == "YES" else "#ef4444"
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else (g.get('game_datetime', 'Scheduled') or 'Scheduled')
        col1, col2 = st.columns([3, 1])
        with col1: st.markdown(f"**{g['away']} @ {g['home']}** • {status_text}")
        with col2: st.markdown(f"<span style='color:{edge_color};font-weight:bold'>{edge_label} +{round(mp['edge'])}%</span>", unsafe_allow_html=True)
        st.markdown(f"""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:12px"><div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">🎯 BUY <span style="color:{action_color};background:{action_color}22;padding:4px 12px;border-radius:6px">{mp['action']}</span> on Kalshi</div><div style="color:#aaa;margin-bottom:12px">{mp['action']} = {mp['team']} wins</div><table style="width:100%;text-align:center;color:#fff"><tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr><tr style="font-size:1.3em;font-weight:bold"><td>{round(mp['vegas_prob'])}%</td><td>{round(mp['kalshi_prob'])}¢</td><td style="color:{edge_color}">+{round(mp['edge'])}%</td></tr></table></div>""", unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1: st.link_button(f"🎯 BUY {mp['action']} ({mp['team']})", get_kalshi_game_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            already = any(pos['game'] == game_key for pos in st.session_state.positions)
            if already: st.success("✅ Tracked")
            elif st.button("➕ Track", key=f"mp_{game_key}"):
                st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]}); st.rerun()
else:
    st.info("🔍 No mispricings found (need 5%+ gap between Vegas & Kalshi)")

st.divider()

st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away, home, total, mins, game_id = g['away'], g['home'], g['total_score'], g['minutes_played'], g['game_id']
        plays = fetch_plays(game_id)
        st.markdown(f"### {away} @ {home}")
        st.markdown(render_scoreboard(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], g.get('away_record', ''), g.get('home_record', '')), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            last_play = plays[-1] if plays else None
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], last_play), unsafe_allow_html=True)
            poss_team, poss_text = infer_possession(plays, away, home)
            if poss_text:
                poss_color = TEAM_COLORS.get(poss_team, "#ffd700") if poss_team else "#888"
                st.markdown(f"<div style='text-align:center;padding:8px;background:#1a1a2e;border-radius:6px;margin-top:4px'><span style='color:{poss_color};font-size:1.3em;font-weight:bold'>{poss_text} BALL</span></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key=f"tts_{game_id}")
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    play_text = p['text'][:60] if p['text'] else "Play"
                    st.markdown(f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;border-radius:4px;border-left:3px solid {color}'><span style='color:{color}'>{icon}</span> {p['period']} {p['clock']} • {play_text}</div>", unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']:
                        speak_play(f"{p['period']} {p['clock']}. {p['text']}")
            else:
                st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home if g['home_score'] > g['away_score'] else away
            kalshi_link = get_kalshi_game_link(away, home)
            st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'><b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br><b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>", unsafe_allow_html=True)
            away_code, home_code = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
            kalshi_data = kalshi_ml.get(away_code + "@" + home_code, {})
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                ml_pick = leader
                ml_confidence = "🔥 STRONG" if abs(lead) >= 15 else "🟢 GOOD"
                if kalshi_data:
                    if leader == home: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
                    else: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
                    st.link_button(f"{ml_confidence} BUY {ml_action} ({ml_pick} ML) • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
                else: st.link_button(f"{ml_confidence} {ml_pick} ML • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
            else: st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over) — go LOW</span>", unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cushion) in enumerate(yes_lines[:3]):
                        if cushion >= 20: safety = "🔒 FORTRESS"
                        elif cushion >= 12: safety = "✅ SAFE"
                        else: safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} YES {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe YES lines (need 6+ cushion)")
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under) — go HIGH</span>", unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cushion) in enumerate(no_lines[:3]):
                        if cushion >= 20: safety = "🔒 FORTRESS"
                        elif cushion >= 12: safety = "✅ SAFE"
                        else: safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} NO {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe NO lines (need 6+ cushion)")
        else: st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else:
    st.info("No live NCAA games right now")

st.divider()

st.subheader("🔥 SECRET SAUCE EARLY EDGE")
st.caption("Early momentum at 12+ min • Only shows games with strong edge • Pace + Net Rating")

secret_sauce = []
for g in live_games:
    mins = g.get('minutes_played', 0)
    if mins < 12 or mins > 18:
        continue
    
    h_ortg, a_ortg, net_rating, poss = calculate_net_rating(g)
    if poss < 22:
        continue
    
    pace = g['total_score'] / mins if mins > 0 else 0
    pace_label, pace_color = get_pace_label(pace)
    pace_dev = pace - 4.7
    
    leader = g['home'] if g['home_score'] > g['away_score'] else g['away'] if g['away_score'] > g['home_score'] else None
    if not leader:
        continue
    
    signal_text = ""
    confidence = ""
    stars = ""
    conf_color = "#22c55e"
    
    if net_rating >= 16:
        if net_rating >= 20:
            confidence = "SECRET SAUCE"
            stars = "⭐⭐⭐"
        elif net_rating >= 18:
            confidence = "STRONG"
            stars = "⭐⭐"
        else:
            confidence = "GOOD"
            stars = "⭐"
        
        totals_side = ""
        if pace_dev >= 0.3:
            totals_side = " + OVER"
        elif pace_dev <= -0.3:
            totals_side = " + UNDER"
        
        signal_text = f"🔒 BUY **{leader}** YES{totals_side}"
    
    if signal_text:
        kalshi_link = get_kalshi_game_link(g['away'], g['home'])
        secret_sauce.append({
            "game": f"{g['away']} @ {g['home']}",
            "mins": mins,
            "net": net_rating,
            "pace": pace,
            "pace_label": pace_label,
            "poss": poss,
            "signal": signal_text,
            "stars": stars,
            "confidence": confidence,
            "conf_color": conf_color,
            "link": kalshi_link
        })

if secret_sauce:
    for s in sorted(secret_sauce, key=lambda x: -x['net']):
        st.markdown(f"""
        <div style="background:#0f172a;padding:16px;border-radius:12px;border:3px solid {s['conf_color']};margin-bottom:16px">
            <div style="font-size:22px;font-weight:bold;color:#ffd700">{s['game']}</div>
            <div style="font-size:28px;margin:8px 0">{s['signal']} {s['stars']}</div>
            <div style="color:#ccc">Net Rating: <b>{s['net']}</b> Pace: <span style="color:{s['pace_label'][1] if isinstance(s['pace_label'], tuple) else '#fff'}">{s['pace_label']}</span> ({s['pace']:.1f}/min) Poss: <b>{s['poss']}</b></div>
            <div style="margin-top:12px;color:{s['conf_color']};font-weight:bold">{s['confidence']}</div>
            <a href="{s['link']}" target="_blank" style="background:#22c55e;color:#000;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:12px">🎯 BUY ON KALSHI</a>
        </div>
        """, unsafe_allow_html=True)
