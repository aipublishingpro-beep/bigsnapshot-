import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide")

st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-NQKY5VQ376');</script>
<style>
body{background:#0d1117;color:#e6edf3}
.stApp{background:#0d1117}
@media(max-width:768px){.row-widget.stHorizontal{flex-direction:column}}
</style>
""", unsafe_allow_html=True)

CITIES = {
    "Austin": {"station": "KAUS", "high": "KXHIGHAUS", "low": "KXLOWTAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central"},
    "Los Angeles": {"station": "KLAX", "high": "KXHIGHLAX", "low": "KXLOWTLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific"},
    "Miami": {"station": "KMIA", "high": "KXHIGHMIA", "low": "KXLOWTMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern"},
    "New York City": {"station": "KNYC", "high": "KXHIGHNY", "low": "KXLOWTNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern"},
    "Philadelphia": {"station": "KPHL", "high": "KXHIGHPHL", "low": "KXLOWTPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern"}
}

DANGER_WORDS = ["cold front", "warm front", "frontal passage", "freeze", "hard freeze", "frost", "killing frost", 
                "winter storm", "ice storm", "blizzard", "arctic", "polar vortex", "heat wave", "excessive heat",
                "heat advisory", "extreme heat", "severe thunderstorm", "tornado", "tropical storm", "hurricane",
                "record high", "record low", "near record", "wind chill warning", "freeze warning", "frost advisory",
                "rapidly falling", "rapidly rising", "sharply colder", "sharply warmer", "much colder", "much warmer",
                "plunging", "plummeting", "soaring"]

@st.cache_data(ttl=60)
def fetch_nws_6hr_extremes(station, tz):
    url = f"https://w1.weather.gov/data/obhistory/{station}.html"
    try:
        r = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('table tbody tr')
        today = datetime.now(pytz.timezone(tz)).date()
        extremes = {}
        for row in rows:
            cells = row.select('td')
            if len(cells) < 10: continue
            dt_str = cells[0].get_text(strip=True) + " " + cells[1].get_text(strip=True)
            try:
                dt = pytz.timezone(tz).localize(datetime.strptime(dt_str, "%m/%d/%y %H:%M"))
                if dt.date() != today: continue
                max_val = cells[8].get_text(strip=True)
                min_val = cells[9].get_text(strip=True)
                extremes[dt] = {"max": float(max_val) if max_val else None, "min": float(min_val) if min_val else None}
            except: continue
        return extremes
    except: return {}

@st.cache_data(ttl=60)
def fetch_nws_observations(station, tz):
    url = f"https://api.weather.gov/stations/{station}/observations?limit=500"
    try:
        r = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        data = r.json()
        features = data.get("features", [])
        timezone = pytz.timezone(tz)
        today = datetime.now(timezone).date()
        readings = []
        for f in features:
            ts = f["properties"]["timestamp"]
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone)
            if dt.date() != today: continue
            temp_c = f["properties"]["temperature"]["value"]
            if temp_c is None: continue
            temp_f = temp_c * 9/5 + 32
            readings.append({"time": dt, "temp": round(temp_f, 1)})
        if not readings: return None, None, None, [], None, None, None, None
        readings.sort(key=lambda x: x["time"])
        current = readings[-1]["temp"]
        low = min(r["temp"] for r in readings)
        high = max(r["temp"] for r in readings)
        confirm_time = readings[-1]["time"]
        oldest = readings[0]["time"]
        newest = readings[-1]["time"]
        mins_since = int((datetime.now(timezone) - confirm_time).total_seconds() / 60)
        return current, low, high, readings, confirm_time, oldest, newest, mins_since
    except: return None, None, None, [], None, None, None, None

@st.cache_data(ttl=300)
def fetch_nws_forecast(lat, lon):
    try:
        r1 = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        forecast_url = r1.json()["properties"]["forecast"]
        r2 = requests.get(forecast_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        periods = r2.json()["properties"]["periods"]
        return periods[:4]
    except: return []

@st.cache_data(ttl=300)
def fetch_nws_tomorrow_low(lat, lon):
    periods = fetch_nws_forecast(lat, lon)
    for p in periods:
        if "Tonight" in p["name"] or "Night" in p["name"]:
            return p["temperature"], p["shortForecast"]
    return None, None

@st.cache_data(ttl=60)
def fetch_kalshi_brackets(series, tz):
    today = datetime.now(pytz.timezone(tz)).strftime("%Y-%m-%d")
    url = f"https://trading-api.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open&with_nested_markets=true"
    try:
        r = requests.get(url, timeout=10)
        markets = r.json().get("markets", [])
        brackets = []
        for m in markets:
            if today not in m["title"]: continue
            ticker = m["ticker"]
            bid = m.get("yes_bid", 0) / 100
            ask = m.get("yes_ask", 0) / 100
            title = m["title"]
            low, high = get_bracket_bounds(title)
            brackets.append({"name": title, "low": low, "high": high, "bid": bid, "ask": ask, "ticker": ticker, "url": f"https://kalshi.com/markets/{series.lower()}"})
        return sorted(brackets, key=lambda x: x["low"] if x["low"] is not None else -999)
    except: return []

@st.cache_data(ttl=60)
def fetch_kalshi_tomorrow_brackets(series, tz):
    tomorrow = (datetime.now(pytz.timezone(tz)) + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://trading-api.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open&with_nested_markets=true"
    try:
        r = requests.get(url, timeout=10)
        markets = r.json().get("markets", [])
        brackets = []
        for m in markets:
            if tomorrow not in m["title"]: continue
            ticker = m["ticker"]
            bid = m.get("yes_bid", 0) / 100
            ask = m.get("yes_ask", 0) / 100
            title = m["title"]
            low, high = get_bracket_bounds(title)
            brackets.append({"name": title, "low": low, "high": high, "bid": bid, "ask": ask, "ticker": ticker, "url": f"https://kalshi.com/markets/{series.lower()}"})
        return sorted(brackets, key=lambda x: x["low"] if x["low"] is not None else -999)
    except: return []

def get_bracket_bounds(title):
    import re
    if "above" in title.lower() or ">" in title:
        match = re.search(r'(\d+)', title)
        return (float(match.group(1)) if match else None, 999)
    elif "or below" in title.lower() or "<" in title:
        match = re.search(r'(\d+)', title)
        return (-999, float(match.group(1)) if match else None)
    else:
        nums = re.findall(r'\d+', title)
        if len(nums) >= 2: return (float(nums[0]), float(nums[1]))
    return (None, None)

def get_settlement_from_6hr(extremes, type):
    if not extremes: return None, None
    if type == "LOW":
        vals = [(t, e["min"]) for t, e in extremes.items() if e["min"] is not None]
        if not vals: return None, None
        vals.sort(key=lambda x: x[1])
        return vals[0][1], vals[0][0]
    else:
        vals = [(t, e["max"]) for t, e in extremes.items() if e["max"] is not None]
        if not vals: return None, None
        vals.sort(key=lambda x: x[1], reverse=True)
        return vals[0][1], vals[0][0]

def check_low_locked_6hr(extremes, tz):
    if not extremes: return False
    for t in extremes.keys():
        if t.hour >= 6: return True
    return False

def find_winning_bracket(temp, brackets):
    if temp is None: return None
    for b in brackets:
        if b["low"] is not None and b["high"] is not None:
            if b["low"] <= temp <= b["high"]: return b
        elif b["low"] is not None and temp >= b["low"]: return b
        elif b["high"] is not None and temp <= b["high"]: return b
    return None

@st.cache_data(ttl=300)
def check_forecast_anomalies(lat, lon, city_name):
    periods = fetch_nws_forecast(lat, lon)
    matched = []
    wind_info = ""
    for p in periods[:4]:
        text = (p.get("detailedForecast", "") + " " + p.get("shortForecast", "")).lower()
        for word in DANGER_WORDS:
            if word in text: matched.append(word)
        wind = p.get("windSpeed", "")
        try:
            wind_num = int(''.join(filter(str.isdigit, wind.split()[0])))
            if wind_num >= 12: wind_info = f"Wind: {wind}"
        except: pass
    
    if city_name == "Miami":
        clear_sunny = any(w in " ".join([p.get("shortForecast", "").lower() for p in periods]) for w in ["clear", "sunny"])
        if not clear_sunny or matched:
            return ("ACTIVE", matched, wind_info)
        else:
            return ("NONE", [], wind_info)
    
    if matched or wind_info:
        return ("ACTIVE", matched, wind_info)
    return ("NONE", [], "")

def render_hero_box(city, cfg, extremes, brackets):
    settlement, lock_time = get_settlement_from_6hr(extremes, "LOW")
    locked = check_low_locked_6hr(extremes, cfg["tz"])
    anomaly_flag, anomaly_words, wind_info = check_forecast_anomalies(cfg["lat"], cfg["lon"], city)
    
    if settlement and locked:
        winner = find_winning_bracket(settlement, brackets)
        if winner:
            edge = 1 - winner["ask"]
            profit = edge * 100
            if profit >= 15: verdict = "🟢 STRONG"
            elif profit >= 10: verdict = "🟡 GOOD"
            else: verdict = "🔴 WEAK"
            
            if anomaly_flag == "ACTIVE":
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#4a0000,#2d0000);border:2px solid #ff4444;border-radius:12px;padding:20px;margin-bottom:20px'>
                <div style='background:#ff4444;color:#000;padding:8px;border-radius:6px;margin-bottom:15px;font-weight:bold'>⛈️ ANOMALY DETECTED: {', '.join(anomaly_words[:3])} — CHECK MANUALLY!</div>
                <div style='font-size:48px;font-weight:bold;margin-bottom:10px'>{settlement}°F</div>
                <div style='opacity:0.8;margin-bottom:15px'>Locked at {lock_time.strftime('%I:%M %p')}</div>
                <div style='font-size:20px;margin-bottom:10px'>{winner['name']}</div>
                <div style='font-size:24px;font-weight:bold;margin-bottom:15px'>Ask: {winner['ask']:.0%} | Edge: {edge:.0%} | Profit: ${profit:.0f}</div>
                <div style='margin-bottom:15px'>{verdict}</div>
                <a href='{winner['url']}' style='display:inline-block;padding:12px 24px;background:#555;color:#fff;text-decoration:none;border-radius:8px;pointer-events:none;opacity:0.5'>⚠️ MANUAL REVIEW REQUIRED</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#0a4a0a,#052505);border:2px solid #00ff88;border-radius:12px;padding:20px;margin-bottom:20px'>
                <div style='font-size:48px;font-weight:bold;margin-bottom:10px'>{settlement}°F</div>
                <div style='opacity:0.8;margin-bottom:15px'>Locked at {lock_time.strftime('%I:%M %p')}</div>
                <div style='font-size:20px;margin-bottom:10px'>{winner['name']}</div>
                <div style='font-size:24px;font-weight:bold;margin-bottom:15px'>Ask: {winner['ask']:.0%} | Edge: {edge:.0%} | Profit: ${profit:.0f}</div>
                <div style='margin-bottom:15px'>{verdict}</div>
                <a href='{winner['url']}' style='display:inline-block;padding:12px 24px;background:#00ff88;color:#000;text-decoration:none;border-radius:8px;font-weight:bold'>BUY NOW</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Settlement: {settlement}°F (locked) — No matching bracket found")
    elif settlement:
        winner = find_winning_bracket(settlement, brackets)
        msg = f"Current Winner: {winner['name']}" if winner else "No bracket match yet"
        if anomaly_flag == "ACTIVE":
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#4a3300,#2d1f00);border:2px solid #ffaa00;border-radius:12px;padding:20px;margin-bottom:20px'>
            <div style='background:#ffaa00;color:#000;padding:8px;border-radius:6px;margin-bottom:15px;font-weight:bold'>⚠️ ANOMALY: {', '.join(anomaly_words[:3])}</div>
            <div style='font-size:36px;font-weight:bold;margin-bottom:10px'>{settlement}°F</div>
            <div>{msg}</div>
            <div style='margin-top:10px;opacity:0.7'>Waiting for 6hr lock (after 6:53 AM)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"6hr Settlement: {settlement}°F — {msg} — Waiting for lock")
    else:
        current, low, high, readings, _, _, _, _ = fetch_nws_observations(cfg["station"], cfg["tz"])
        if anomaly_flag == "ACTIVE":
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#4a0000,#2d0000);border:2px solid #ff4444;border-radius:12px;padding:20px;margin-bottom:20px'>
            <div style='background:#ff4444;color:#000;padding:8px;border-radius:6px;margin-bottom:15px;font-weight:bold'>⛈️ ANOMALY: {', '.join(anomaly_words[:3])}</div>
            <div style='font-size:36px;font-weight:bold;margin-bottom:10px'>Hourly Low: {low}°F</div>
            <div style='opacity:0.7'>Waiting for 6hr data (appears ~6:53 AM & 6:53 PM)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"Hourly Low: {low}°F — Waiting for 6hr data")

def render_forecast(lat, lon, city_name):
    periods = fetch_nws_forecast(lat, lon)
    anomaly_flag, anomaly_words, wind_info = check_forecast_anomalies(lat, lon, city_name)
    
    if anomaly_flag == "ACTIVE":
        st.markdown(f"""
        <div style='background:#4a0000;border-left:4px solid #ff4444;padding:12px;margin-bottom:15px;border-radius:6px'>
        <strong>⛈️ ANOMALY DETECTED:</strong> {', '.join(anomaly_words[:5])} {wind_info}
        </div>
        """, unsafe_allow_html=True)
    
    cols = st.columns(len(periods))
    for i, p in enumerate(periods):
        with cols[i]:
            st.markdown(f"**{p['name']}**")
            st.metric("Temp", f"{p['temperature']}°F")
            st.caption(p['shortForecast'])

params = st.query_params
is_owner = params.get("mode") == "owner"
default_city = params.get("city", "New York City")

if is_owner:
    with st.sidebar:
        st.success("🔐 OWNER MODE")
        st.info("**Settlement Rules**\n\nLOW: Lowest 6hr min\n\nLocked: Any 6hr after 6:53 AM")
        st.warning("**Trading Schedule**\n\nOpen: 12:01 AM ET\nClose: 11:59 PM ET\n\nLock: 6:53 AM & 6:53 PM")
        st.info("**Row Colors**\n\n🟢 Locked = green\n🔵 6hr exists = blue\n⚪ Hourly only = white")
        st.error("**Entry Thresholds**\n\nStrong: 15%+\nGood: 10-15%\nWeak: <10%")
else:
    with st.sidebar:
        st.info("**Lock Times**\n\n6:53 AM & 6:53 PM local time")

if is_owner:
    tab_buttons = st.columns(4)
    with tab_buttons[0]: tab_city = st.button("🌡️ City", use_container_width=True)
    with tab_buttons[1]: tab_today = st.button("📊 Today", use_container_width=True)
    with tab_buttons[2]: tab_lottery = st.button("🎰 Lottery", use_container_width=True)
    with tab_buttons[3]: tab_shark = st.button("🦈 SHARK", use_container_width=True)
    
    active_tab = "city"
    if tab_today: active_tab = "today"
    elif tab_lottery: active_tab = "lottery"
    elif tab_shark: active_tab = "shark"
    
    if active_tab == "city":
        city = st.selectbox("Select City", list(CITIES.keys()), index=list(CITIES.keys()).index(default_city))
        cfg = CITIES[city]
        extremes = fetch_nws_6hr_extremes(cfg["station"], cfg["tz"])
        brackets = fetch_kalshi_brackets(cfg["low"], cfg["tz"])
        
        st.markdown(f"<h1 style='margin-bottom:20px'>{city}</h1>", unsafe_allow_html=True)
        st.link_button("📡 NWS Station", f"https://w1.weather.gov/data/obhistory/{cfg['station']}.html")
        
        render_hero_box(city, cfg, extremes, brackets)
        
        current, low, high, readings, confirm_time, oldest, newest, mins = fetch_nws_observations(cfg["station"], cfg["tz"])
        c1, c2 = st.columns(2)
        with c1: st.metric("Current", f"{current}°F" if current else "—", help=f"As of {confirm_time.strftime('%I:%M %p')}" if confirm_time else "")
        with c2: st.metric("High", f"{high}°F" if high else "—")
        
        with st.expander("📋 Observations", expanded=True):
            if readings:
                for r in readings:
                    t = r["time"].strftime("%I:%M %p")
                    temp = r["temp"]
                    is_low = (temp == low)
                    six_hr = extremes.get(r["time"])
                    if six_hr:
                        st.markdown(f"{'🟡' if is_low else '⚪'} **{t}**: {temp}°F — 6hr Max: {six_hr['max']}°F, Min: {six_hr['min']}°F")
                    else:
                        st.markdown(f"{'🟡' if is_low else '⚪'} **{t}**: {temp}°F")
        
        st.markdown("### NWS Forecast")
        render_forecast(cfg["lat"], cfg["lon"], city)
    
    elif active_tab == "today":
        st.markdown("<h1>Today's Scan</h1>", unsafe_allow_html=True)
        cfg = CITIES[default_city]
        extremes = fetch_nws_6hr_extremes(cfg["station"], cfg["tz"])
        brackets = fetch_kalshi_brackets(cfg["low"], cfg["tz"])
        render_hero_box(default_city, cfg, extremes, brackets)
        
        st.markdown("### All Cities")
        opportunities = []
        for city, cfg in CITIES.items():
            extremes = fetch_nws_6hr_extremes(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"], cfg["tz"])
            settlement, lock_time = get_settlement_from_6hr(extremes, "LOW")
            locked = check_low_locked_6hr(extremes, cfg["tz"])
            winner = find_winning_bracket(settlement, brackets) if settlement else None
            
            if winner:
                edge = 1 - winner["ask"]
                st.markdown(f"**{city}**: {settlement}°F {'🟢' if locked else '🔵'} → {winner['name']} @ {winner['ask']:.0%} = {edge:.0%} edge")
                if edge >= 0.10: opportunities.append((city, settlement, winner, edge))
            else:
                st.markdown(f"**{city}**: {settlement if settlement else 'No 6hr'}")
        
        if opportunities:
            st.markdown("### 🎯 Opportunities (10%+ Edge)")
            for city, settlement, winner, edge in opportunities:
                profit = edge * 100
                st.markdown(f"""
                <div style='background:#0a4a0a;border-left:4px solid #00ff88;padding:15px;margin-bottom:10px;border-radius:6px'>
                <strong>{city}</strong>: {settlement}°F → {winner['name']}<br>
                Ask: {winner['ask']:.0%} | Edge: {edge:.0%} | Profit: ${profit:.0f}<br>
                <a href='{winner['url']}' style='color:#00ff88'>BUY</a>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### Tomorrow Preview")
        for city, cfg in CITIES.items():
            tmr_low, forecast = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
            tmr_brackets = fetch_kalshi_tomorrow_brackets(cfg["low"], cfg["tz"])
            if tmr_low and tmr_brackets:
                winner = find_winning_bracket(tmr_low, tmr_brackets)
                if winner:
                    st.markdown(f"**{city}**: {tmr_low}°F ({forecast}) → {winner['name']} @ {winner['ask']:.0%}")
    
    elif active_tab == "lottery":
        tomorrow = (datetime.now(pytz.timezone("US/Eastern")) + timedelta(days=1)).strftime("%Y-%m-%d")
        st.markdown(f"<h1>🎰 Lottery Scan: {tomorrow}</h1>", unsafe_allow_html=True)
        st.info("Scanning for cheap brackets (≤10¢) with anomaly checks")
        
        cheap_opps = []
        for city, cfg in CITIES.items():
            tmr_brackets = fetch_kalshi_tomorrow_brackets(cfg["low"], cfg["tz"])
            anomaly_flag, anomaly_words, wind_info = check_forecast_anomalies(cfg["lat"], cfg["lon"], city)
            
            for b in tmr_brackets:
                if b["ask"] <= 0.10:
                    cheap_opps.append((city, b, anomaly_flag, anomaly_words))
        
        if cheap_opps:
            st.markdown("### Opportunities")
            for city, b, flag, words in cheap_opps:
                badge = "🟢 ✅ SAFE" if flag == "NONE" else "🔴 ⚠️ ANOMALY"
                st.markdown(f"""
                <div style='background:#1a1a2e;border-left:4px solid {'#ff4444' if flag == 'ACTIVE' else '#00ff88'};padding:12px;margin-bottom:8px;border-radius:6px'>
                <strong>{city}</strong> {badge}<br>
                {b['name']} @ {b['ask']:.0%}<br>
                {', '.join(words[:3]) if words else 'No anomalies detected'}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### All Cities")
        for city, cfg in CITIES.items():
            tmr_low, forecast = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
            tmr_brackets = fetch_kalshi_tomorrow_brackets(cfg["low"], cfg["tz"])
            anomaly_flag, _, _ = check_forecast_anomalies(cfg["lat"], cfg["lon"], city)
            badge = "✅" if anomaly_flag == "NONE" else "⚠️"
            
            if tmr_low and tmr_brackets:
                winner = find_winning_bracket(tmr_low, tmr_brackets)
                if winner:
                    st.markdown(f"**{city}** {badge}: {tmr_low}°F ({forecast}) → {winner['name']} @ {winner['ask']:.0%}")
    
    else:
        st.markdown("<h1>🦈 SHARK Scan</h1>", unsafe_allow_html=True)
        cfg = CITIES[default_city]
        extremes = fetch_nws_6hr_extremes(cfg["station"], cfg["tz"])
        brackets = fetch_kalshi_brackets(cfg["low"], cfg["tz"])
        render_hero_box(default_city, cfg, extremes, brackets)
        
        st.markdown("### All Cities")
        for city, cfg in CITIES.items():
            extremes = fetch_nws_6hr_extremes(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"], cfg["tz"])
            settlement, lock_time = get_settlement_from_6hr(extremes, "LOW")
            locked = check_low_locked_6hr(extremes, cfg["tz"])
            current, low, high, _, _, _, _, _ = fetch_nws_observations(cfg["station"], cfg["tz"])
            winner = find_winning_bracket(settlement, brackets) if settlement else None
            
            lock_status = "🟢 LOCKED" if locked else "🔵 OPEN"
            winner_str = f"{winner['name']} @ {winner['ask']:.0%}" if winner else "No match"
            st.markdown(f"**{city}**: {settlement if settlement else 'No 6hr'}°F {lock_status} | Current: {current}°F | Hourly Low: {low}°F → {winner_str}")

else:
    city = st.selectbox("Select City", list(CITIES.keys()), index=list(CITIES.keys()).index(default_city))
    cfg = CITIES[city]
    
    st.markdown(f"<h1>{city}</h1>", unsafe_allow_html=True)
    st.link_button("📡 NWS Station", f"https://w1.weather.gov/data/obhistory/{cfg['station']}.html")
    
    current, low, high, readings, confirm_time, oldest, newest, mins = fetch_nws_observations(cfg["station"], cfg["tz"])
    
    st.markdown("<h2 style='text-align:center;font-size:48px;margin:20px 0'>{}°F</h2>".format(low if low else "—"), unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;opacity:0.7;margin-bottom:30px'>Today's Observed Low</p>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.metric("Current", f"{current}°F" if current else "—", help=f"As of {confirm_time.strftime('%I:%M %p')}" if confirm_time else "")
    with c2: st.metric("High", f"{high}°F" if high else "—")
    
    with st.expander("📋 All Observations", expanded=True):
        if readings:
            for r in readings:
                t = r["time"].strftime("%I:%M %p")
                temp = r["temp"]
                is_low = (temp == low)
                st.markdown(f"{'🟡' if is_low else '⚪'} **{t}**: {temp}°F")
    
    st.markdown("### NWS Forecast")
    render_forecast(cfg["lat"], cfg["lon"], city)

st.markdown("<div style='text-align:center;margin-top:40px;padding:20px;border-top:1px solid #333'><strong>v10.0 (5 Cities)</strong><br><small>For entertainment only. Not financial advice.</small></div>", unsafe_allow_html=True)
