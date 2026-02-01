"""
🌡️ TEMP.PY - Temperature Trading Dashboard (VIEW ONLY)
Combines SHARK (today's 6hr settlement) + TOM (tomorrow's forecast)
No trading - monitoring and analysis only
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

# ============================================================
# CITIES CONFIG
# ============================================================
CITIES = {
    "New York City": {"nws": "KNYC", "kalshi_low": "KXLOWTNYC", "kalshi_high": "KXHIGHNY", "tz": "US/Eastern", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"nws": "KPHL", "kalshi_low": "KXLOWTPHL", "kalshi_high": "KXHIGHPHIL", "tz": "US/Eastern", "lat": 39.87, "lon": -75.23},
    "Miami": {"nws": "KMIA", "kalshi_low": "KXLOWTMIA", "kalshi_high": "KXHIGHMIA", "tz": "US/Eastern", "lat": 25.80, "lon": -80.29},
    "Los Angeles": {"nws": "KLAX", "kalshi_low": "KXLOWTLAX", "kalshi_high": "KXHIGHLAX", "tz": "US/Pacific", "lat": 33.94, "lon": -118.41},
    "Houston": {"nws": "KIAH", "kalshi_low": None, "kalshi_high": "KXHIGHHOU", "tz": "US/Central", "lat": 29.98, "lon": -95.37},
    "Las Vegas": {"nws": "KLAS", "kalshi_low": None, "kalshi_high": "KXHIGHTLV", "tz": "US/Pacific", "lat": 36.08, "lon": -115.15},
    "Seattle": {"nws": "KSEA", "kalshi_low": None, "kalshi_high": "KXHIGHSEA", "tz": "US/Pacific", "lat": 47.45, "lon": -122.31},
}

WEATHER_DANGER = ["cold front", "warm front", "freeze", "frost", "winter storm", "heat wave", "extreme heat", "severe thunderstorm", "tornado", "hurricane"]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_data(ttl=900)
def fetch_6hr_settlement(station, city_tz_str):
    """Fetch 6-hour settlement from NWS obhistory"""
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        city_tz = pytz.timezone(city_tz_str)
        today = datetime.now(city_tz).day
        resp = requests.get(url, headers={"User-Agent": "TempDashboard/1.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, None, False, False
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return None, None, None, None, False, False
        
        rows = table.find_all('tr')
        all_6hr_mins, all_6hr_maxs = [], []
        
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue
            try:
                date_val = cells[0].text.strip()
                time_val = cells[1].text.strip()
                if date_val and int(date_val) != today:
                    continue
                
                max_6hr = cells[8].text.strip()
                min_6hr = cells[9].text.strip()
                
                if max_6hr:
                    max_val = int(float(max_6hr))
                    hour = int(time_val.replace(":", "")[:2])
                    if hour >= 12:
                        all_6hr_maxs.append((time_val, max_val))
                
                if min_6hr:
                    min_val = int(float(min_6hr))
                    all_6hr_mins.append((time_val, min_val))
            except:
                continue
        
        settlement_low = min(all_6hr_mins, key=lambda x: x[1])[1] if all_6hr_mins else None
        low_time = min(all_6hr_mins, key=lambda x: x[1])[0] if all_6hr_mins else None
        settlement_high = max(all_6hr_maxs, key=lambda x: x[1])[1] if all_6hr_maxs else None
        high_time = max(all_6hr_maxs, key=lambda x: x[1])[0] if all_6hr_maxs else None
        
        is_low_locked = any(int(t.replace(":", "")[:2]) >= 6 for t, _ in all_6hr_mins)
        is_high_locked = any(int(t.replace(":", "")[:2]) >= 18 for t, _ in all_6hr_maxs)
        
        return settlement_low, settlement_high, low_time, high_time, is_low_locked, is_high_locked
    except:
        return None, None, None, None, False, False

@st.cache_data(ttl=900)
def fetch_kalshi_brackets(series_ticker, city_tz_str, is_tomorrow=False):
    """Fetch Kalshi brackets for today or tomorrow"""
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        
        city_tz = pytz.timezone(city_tz_str)
        target_date = datetime.now(city_tz) + (timedelta(days=1) if is_tomorrow else timedelta(days=0))
        date_str = target_date.strftime('%y%b%d').upper()
        
        target_markets = [m for m in markets if date_str in m.get("event_ticker", "").upper()]
        if not target_markets:
            target_markets = [m for m in markets if m.get("event_ticker") == markets[0].get("event_ticker")]
        
        brackets = []
        for m in target_markets:
            title = m.get("title", "")
            ticker = m.get("ticker", "")
            yes_ask = m.get("yes_ask", 0) or 0
            
            low, high, name = None, None, ""
            
            # Parse bracket ranges
            if match := re.search(r'>\s*(-?\d+)', title):
                low, high, name = int(match.group(1)) + 1, 999, f">{match.group(1)}"
            elif match := re.search(r'<\s*(-?\d+)', title):
                low, high, name = -999, int(match.group(1)) - 1, f"<{match.group(1)}"
            elif match := re.search(r'(-?\d+)\s*to\s*(-?\d+)', title, re.I):
                low, high, name = int(match.group(1)), int(match.group(2)), f"{match.group(1)}-{match.group(2)}"
            
            if low is not None:
                brackets.append({"name": name, "low": low, "high": high, "ask": yes_ask, "ticker": ticker})
        
        return sorted(brackets, key=lambda x: x['low'])
    except:
        return []

def find_winning_bracket(temp, brackets):
    """Find bracket that contains temperature"""
    if temp is None or not brackets:
        return None
    for b in brackets:
        if (b["high"] == 999 and temp >= b["low"]) or \
           (b["low"] == -999 and temp <= b["high"]) or \
           (b["low"] <= temp <= b["high"]):
            return b
    return None

@st.cache_data(ttl=1800)
def fetch_tomorrow_forecast(lat, lon):
    """Fetch NWS forecast for tomorrow"""
    try:
        points_resp = requests.get(f"https://api.weather.gov/points/{lat},{lon}", 
                                   headers={"User-Agent": "TempDashboard/1.0"}, timeout=10)
        if points_resp.status_code != 200:
            return None, None
        
        forecast_url = points_resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None, None
        
        forecast_resp = requests.get(forecast_url, headers={"User-Agent": "TempDashboard/1.0"}, timeout=10)
        if forecast_resp.status_code != 200:
            return None, None
        
        periods = forecast_resp.json().get("properties", {}).get("periods", [])
        
        tomorrow_low, tomorrow_high = None, None
        for p in periods:
            if not any(day in p.get("name", "").lower() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                continue
            
            temp = p.get("temperature")
            if temp is None:
                continue
            
            if not p.get("isDaytime", True) and tomorrow_low is None:
                tomorrow_low = round(temp)
            elif p.get("isDaytime", True) and tomorrow_high is None:
                tomorrow_high = round(temp)
            
            if tomorrow_low and tomorrow_high:
                break
        
        return tomorrow_low, tomorrow_high
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_current_temp(station):
    """Get current temperature"""
    try:
        url = f"https://api.weather.gov/stations/{station}/observations/latest"
        resp = requests.get(url, headers={"User-Agent": "TempDashboard/1.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        temp_c = resp.json().get("properties", {}).get("temperature", {}).get("value")
        return round(temp_c * 9/5 + 32, 1) if temp_c else None
    except:
        return None

def check_weather_guards(lat, lon):
    """Check for dangerous weather conditions"""
    try:
        points_resp = requests.get(f"https://api.weather.gov/points/{lat},{lon}", 
                                   headers={"User-Agent": "TempDashboard/1.0"}, timeout=10)
        forecast_url = points_resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return []
        
        forecast_resp = requests.get(forecast_url, headers={"User-Agent": "TempDashboard/1.0"}, timeout=10)
        periods = forecast_resp.json().get("properties", {}).get("periods", [])[:4]
        
        warnings = []
        for p in periods:
            text = (p.get("detailedForecast", "") + " " + p.get("shortForecast", "")).lower()
            for word in WEATHER_DANGER:
                if word in text:
                    warnings.append(f"⛈️ {word.upper()} in {p.get('name')}")
        
        return warnings
    except:
        return []

# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🌡️ Temperature Trading Dashboard")
st.caption("Real-time monitoring for SHARK (today) + TOM (tomorrow) strategies")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    mode = st.radio("Mode", ["🦈 SHARK (Today)", "🦅 TOM (Tomorrow)", "📊 Both"])
    
    st.divider()
    
    selected_cities = st.multiselect(
        "Cities to Monitor",
        list(CITIES.keys()),
        default=["Miami", "New York City"]
    )
    
    st.divider()
    
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
    if auto_refresh:
        st.rerun()
    
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

# Main content
if not selected_cities:
    st.warning("Select at least one city from the sidebar")
    st.stop()

# SHARK Mode (Today)
if mode in ["🦈 SHARK (Today)", "📊 Both"]:
    st.header("🦈 SHARK - Today's Settlement Tracker")
    
    shark_data = []
    for city in selected_cities:
        cfg = CITIES[city]
        
        # Fetch settlement data
        low_6hr, high_6hr, low_time, high_time, low_locked, high_locked = fetch_6hr_settlement(cfg["nws"], cfg["tz"])
        current = fetch_current_temp(cfg["nws"])
        
        # Check LOW
        if cfg["kalshi_low"] and low_6hr:
            brackets_low = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"])
            match_low = find_winning_bracket(low_6hr, brackets_low)
            
            shark_data.append({
                "City": city,
                "Type": "LOW",
                "Settlement": f"{low_6hr}°F @ {low_time}" if low_6hr else "—",
                "Current": f"{current}°F" if current else "—",
                "Locked": "🔒" if low_locked else "⏳",
                "Bracket": match_low["name"] if match_low else "NO MATCH",
                "Ask": f"{match_low['ask']}¢" if match_low else "—",
                "Edge": f"{100 - match_low['ask']}¢" if match_low else "—"
            })
        
        # Check HIGH
        if high_6hr:
            brackets_high = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"])
            match_high = find_winning_bracket(high_6hr, brackets_high)
            
            shark_data.append({
                "City": city,
                "Type": "HIGH",
                "Settlement": f"{high_6hr}°F @ {high_time}" if high_6hr else "—",
                "Current": f"{current}°F" if current else "—",
                "Locked": "🔒" if high_locked else "⏳",
                "Bracket": match_high["name"] if match_high else "NO MATCH",
                "Ask": f"{match_high['ask']}¢" if match_high else "—",
                "Edge": f"{100 - match_high['ask']}¢" if match_high else "—"
            })
    
    if shark_data:
        df_shark = pd.DataFrame(shark_data)
        st.dataframe(df_shark, use_container_width=True, hide_index=True)
    else:
        st.info("No SHARK data available")

# TOM Mode (Tomorrow)
if mode in ["🦅 TOM (Tomorrow)", "📊 Both"]:
    st.header("🦅 TOM - Tomorrow's Forecast Scanner")
    
    tom_data = []
    alerts = []
    
    for city in selected_cities:
        cfg = CITIES[city]
        
        # Fetch tomorrow forecast
        forecast_low, forecast_high = fetch_tomorrow_forecast(cfg["lat"], cfg["lon"])
        weather_warnings = check_weather_guards(cfg["lat"], cfg["lon"])
        
        # Check LOW
        if cfg["kalshi_low"] and forecast_low:
            brackets_low = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"], is_tomorrow=True)
            match_low = find_winning_bracket(forecast_low, brackets_low)
            
            guards_status = "⚠️ BLOCKED" if weather_warnings or (match_low and match_low["ask"] <= 7) else "✅ SAFE"
            
            tom_data.append({
                "City": city,
                "Type": "LOW",
                "Forecast": f"{forecast_low}°F" if forecast_low else "—",
                "Bracket": match_low["name"] if match_low else "NO MATCH",
                "Ask": f"{match_low['ask']}¢" if match_low else "—",
                "Edge": f"{100 - match_low['ask']}¢" if match_low else "—",
                "Guards": guards_status
            })
            
            if match_low and match_low["ask"] <= 20 and not weather_warnings:
                alerts.append(f"🎯 {city} LOW: {forecast_low}°F → {match_low['name']} @ {match_low['ask']}¢")
        
        # Check HIGH
        if forecast_high:
            brackets_high = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"], is_tomorrow=True)
            match_high = find_winning_bracket(forecast_high, brackets_high)
            
            guards_status = "⚠️ BLOCKED" if weather_warnings or (match_high and match_high["ask"] <= 7) else "✅ SAFE"
            
            tom_data.append({
                "City": city,
                "Type": "HIGH",
                "Forecast": f"{forecast_high}°F" if forecast_high else "—",
                "Bracket": match_high["name"] if match_high else "NO MATCH",
                "Ask": f"{match_high['ask']}¢" if match_high else "—",
                "Edge": f"{100 - match_high['ask']}¢" if match_high else "—",
                "Guards": guards_status
            })
            
            if match_high and match_high["ask"] <= 20 and not weather_warnings:
                alerts.append(f"🎯 {city} HIGH: {forecast_high}°F → {match_high['name']} @ {match_high['ask']}¢")
    
    # Show alerts
    if alerts:
        st.success("🚨 **OPPORTUNITIES FOUND:**")
        for alert in alerts:
            st.write(alert)
    
    # Show data table
    if tom_data:
        df_tom = pd.DataFrame(tom_data)
        st.dataframe(df_tom, use_container_width=True, hide_index=True)
    else:
        st.info("No TOM data available (markets may not be live yet)")

# Footer
st.divider()
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
st.caption(f"Last updated: {now.strftime('%I:%M:%S %p ET')} | View-only dashboard - no trading functionality")
