"""
🦈 SHARK AUTO-BUY v7.5 - FIXED SETTLEMENT LOCK + 5 GUARDS
- ✅ GUARD 1: Weather (blocks storms/fronts/freezes)
- ✅ GUARD 2: Price (blocks ≤20¢, warns ≤40¢)
- ✅ GUARD 3: Trend (blocks if current temp contradicts settlement)
- ✅ GUARD 4: Forecast (blocks if NWS disagrees by 3°+)
- ✅ GUARD 5: Settlement Lock (blocks if 6hr ≠ hourly ±0.5°F) ← FIXES $7K BUG
- 📊 AUTO-LOGS all scans to shark_log.csv
- Uses 6hr aggregate from obhistory + hourly API for verification
- LOW = LOWEST 6hr Min (verified against hourly low)
- HIGH = HIGHEST 6hr Max after NOON (verified against hourly high)
"""
import requests
import time
from datetime import datetime, timedelta
import pytz
import winsound
import base64
import re
import csv
import os
from bs4 import BeautifulSoup

# ============================================================
# 🔑 KALSHI API KEYS - PASTE YOUR CREDENTIALS HERE FIRST!
# ============================================================
# Get these from: https://kalshi.com → Settings → API
# API_KEY = The API Key ID (looks like: 3abd1b21-023d-4088-abae-35c36e9ba806)
# PRIVATE_KEY = The full private key (multi-line, starts with -----BEGIN PRIVATE KEY-----)

API_KEY = "paste-your-api-key-id-here"

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
paste-all-lines-of-your-private-key-here
keep-the-BEGIN-and-END-lines
-----END PRIVATE KEY-----"""

# ============================================================
# ⚙️ SETTINGS
# ============================================================
CONTRACTS_PER_TRADE = 20
MAX_DAILY_SPEND = 100
AUTO_BUY_ENABLED = False  # 🧪 TEST MODE - Alerts only, no buying
MAX_ASK_PRICE = 89
CHECK_INTERVAL = 60
LOG_FILE = "shark_log.csv"
LOG_INTERVAL = 1800  # Log summary every 30 min

# ============================================================
# 🛡️ GUARD SETTINGS
# ============================================================
GUARD_ENABLED = True
PRICE_FLOOR = 20         # Ask ≤ this = BLOCK
PRICE_WARN = 40          # Ask ≤ this = WARN + BLOCK
FORECAST_GAP_THRESHOLD = 3  # NWS forecast disagrees by this many degrees = BLOCK
SETTLEMENT_TOLERANCE = 0.5  # 6hr must match hourly within this tolerance

WEATHER_DANGER_WORDS = [
    "cold front", "warm front", "frontal passage", "front passage",
    "freeze", "hard freeze", "flash freeze",
    "frost", "killing frost",
    "winter storm", "ice storm", "blizzard",
    "arctic", "polar vortex", "polar outbreak",
    "heat wave", "excessive heat", "heat advisory", "extreme heat",
    "severe thunderstorm", "tornado", "tropical storm", "hurricane",
    "record high", "record low", "near record",
    "wind chill warning", "wind chill advisory",
    "freeze warning", "frost advisory",
    "rapidly falling", "rapidly rising",
    "sharply colder", "sharply warmer",
    "much colder", "much warmer",
    "plunging", "plummeting", "soaring",
    "temperature crash", "temperature plunge",
]

# ============================================================
# 🎯 CITY TOGGLES
# ============================================================
TRADE_LOW = {
    "New York City": True,
    "Philadelphia": False,
    "Miami": True,
    "Los Angeles": False,
    "Austin": False,
}

TRADE_HIGH = {
    "New York City": True,
    "Philadelphia": True,
    "Miami": True,
    "Los Angeles": True,
    "Austin": True,
    "Houston": True,
    "Las Vegas": True,
    "Seattle": True,
    "San Francisco": True,
    "Washington DC": True,
    "New Orleans": True,
}

# ============================================================
# CITIES CONFIG
# ============================================================
CITIES = {
    "New York City": {
        "nws": "KNYC", "kalshi_low": "KXLOWTNYC", "kalshi_high": "KXHIGHNY",
        "tz": "US/Eastern", "lat": 40.78, "lon": -73.97,
    },
    "Philadelphia": {
        "nws": "KPHL", "kalshi_low": "KXLOWTPHL", "kalshi_high": "KXHIGHPHIL",
        "tz": "US/Eastern", "lat": 39.87, "lon": -75.23,
    },
    "Miami": {
        "nws": "KMIA", "kalshi_low": "KXLOWTMIA", "kalshi_high": "KXHIGHMIA",
        "tz": "US/Eastern", "lat": 25.80, "lon": -80.29,
    },
    "Los Angeles": {
        "nws": "KLAX", "kalshi_low": "KXLOWTLAX", "kalshi_high": "KXHIGHLAX",
        "tz": "US/Pacific", "lat": 33.94, "lon": -118.41,
    },
    "Austin": {
        "nws": "KAUS", "kalshi_low": "KXLOWTAUS", "kalshi_high": "KXHIGHAUS",
        "tz": "US/Central", "lat": 30.19, "lon": -97.67,
    },
    "Houston": {
        "nws": "KIAH", "kalshi_low": None, "kalshi_high": "KXHIGHHOU",
        "tz": "US/Central", "lat": 29.98, "lon": -95.37,
    },
    "Las Vegas": {
        "nws": "KLAS", "kalshi_low": None, "kalshi_high": "KXHIGHTLV",
        "tz": "US/Pacific", "lat": 36.08, "lon": -115.15,
    },
    "Seattle": {
        "nws": "KSEA", "kalshi_low": None, "kalshi_high": "KXHIGHSEA",
        "tz": "US/Pacific", "lat": 47.45, "lon": -122.31,
    },
    "San Francisco": {
        "nws": "KSFO", "kalshi_low": None, "kalshi_high": "KXHIGHSFO",
        "tz": "US/Pacific", "lat": 37.62, "lon": -122.38,
    },
    "Washington DC": {
        "nws": "KDCA", "kalshi_low": None, "kalshi_high": "KXHIGHDC",
        "tz": "US/Eastern", "lat": 38.85, "lon": -77.04,
    },
    "New Orleans": {
        "nws": "KMSY", "kalshi_low": None, "kalshi_high": "KXHIGHNOLA",
        "tz": "US/Central", "lat": 29.99, "lon": -90.25,
    },
}

daily_spent = 0
_forecast_cache = {}
FORECAST_CACHE_TTL = 900
_last_log_time = 0

# ============================================================
# 🔑 KALSHI API KEYS - PASTE YOUR CREDENTIALS HERE
# ============================================================
# Get these from: https://kalshi.com → Settings → API
# API_KEY = The API Key ID (looks like: 3abd1b21-023d-4088-abae-35c36e9ba806)
# PRIVATE_KEY = The full private key (multi-line, starts with -----BEGIN PRIVATE KEY-----)

API_KEY = "paste-your-api-key-id-here"

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
paste-all-lines-of-your-private-key-here
keep-the-BEGIN-and-END-lines
-----END PRIVATE KEY-----"""

# ============================================================
# 📊 CSV LOGGING
# ============================================================
def init_csv_log():
    """Create CSV file with headers if it doesn't exist"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'Date', 'Time', 'Hour',
                'City', 'Type', 
                'Settlement_Temp', 'Settlement_Time', 'Is_Locked',
                'Hourly_Extreme', 'Settlement_Match',
                'Bracket', 'Ask', 'Ticker',
                'Guards_Passed', 'Guard_Warnings',
                'Action', 'Edge', 'Contracts', 'Cost', 'Potential_Profit'
            ])

def log_to_csv(scan_time, city, market_type, settlement_temp, settlement_time, is_locked, hourly_extreme=None, settlement_match=None, bracket=None, guards_passed=None, guard_warnings=None, order_placed=False):
    """Log scan result to CSV"""
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        
        date_str = scan_time.strftime('%Y-%m-%d')
        time_str = scan_time.strftime('%H:%M:%S')
        hour = scan_time.hour
        
        if bracket:
            cost = (bracket['ask'] / 100) * CONTRACTS_PER_TRADE
            profit = ((100 - bracket['ask']) / 100) * CONTRACTS_PER_TRADE
            edge = 100 - bracket['ask']
            
            writer.writerow([
                scan_time.isoformat(),
                date_str,
                time_str,
                hour,
                city,
                market_type,
                settlement_temp or '',
                settlement_time or '',
                'YES' if is_locked else 'NO',
                hourly_extreme or '',
                'YES' if settlement_match else 'NO',
                bracket['name'],
                bracket['ask'],
                bracket['ticker'],
                'YES' if guards_passed else 'NO',
                '|'.join(guard_warnings) if guard_warnings else '',
                'BOUGHT' if order_placed else ('ALERT' if guards_passed else 'BLOCKED'),
                edge,
                CONTRACTS_PER_TRADE if (guards_passed and order_placed) else 0,
                f"${cost:.2f}" if guards_passed else '',
                f"${profit:.2f}" if guards_passed else ''
            ])
        else:
            action = 'LOCKED_NO_MATCH' if is_locked else 'WAITING_FOR_LOCK'
            writer.writerow([
                scan_time.isoformat(),
                date_str,
                time_str,
                hour,
                city,
                market_type,
                settlement_temp or '',
                settlement_time or '',
                'YES' if is_locked else 'NO',
                hourly_extreme or '',
                'YES' if settlement_match else 'NO',
                'NO_MATCH' if is_locked else 'WAITING',
                '',
                '',
                '',
                '',
                action,
                '',
                0,
                '',
                ''
            ])

# ============================================================
# 🔑 KALSHI API AUTHENTICATION (PASTE YOUR KEYS HERE)
# ============================================================
API_KEY = "your-api-key-id-here"

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
paste-your-full-private-key-here
multiple-lines-from-kalshi
-----END PRIVATE KEY-----"""

def create_kalshi_signature(timestamp, method, path):
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        private_key = serialization.load_pem_private_key(
            PRIVATE_KEY.encode() if isinstance(PRIVATE_KEY, str) else PRIVATE_KEY,
            password=None, backend=default_backend()
        )
        message = f"{timestamp}{method}{path}".encode('utf-8')
        signature = private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    except Exception as e:
        print(f"  ❌ Signature error: {e}")
        return None

def place_kalshi_order(ticker, price_cents, contracts):
    global daily_spent
    cost = (price_cents / 100) * contracts
    if daily_spent + cost > MAX_DAILY_SPEND:
        print(f"  ⚠️ Daily limit reached (${daily_spent:.2f}/${MAX_DAILY_SPEND})")
        return False, "Daily limit reached"
    try:
        path = '/trade-api/v2/portfolio/orders'
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = create_kalshi_signature(timestamp, "POST", path)
        if not signature:
            return False, "Failed to create signature"
        headers = {
            'KALSHI-ACCESS-KEY': API_KEY,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        import uuid
        order_data = {
            "ticker": ticker, "action": "buy", "side": "yes",
            "count": contracts, "type": "limit", "yes_price": price_cents,
            "client_order_id": str(uuid.uuid4())
        }
        response = requests.post(
            f"https://api.elections.kalshi.com{path}",
            headers=headers, json=order_data, timeout=10
        )
        if response.status_code == 201:
            daily_spent += cost
            return True, f"✅ ORDER PLACED {contracts}x @ {price_cents}¢ (${cost:.2f})"
        else:
            error = response.json().get('error', {}).get('message', response.text)
            return False, f"❌ Order failed: {error}"
    except Exception as e:
        return False, f"❌ Error: {e}"

# ============================================================
# 📡 HOURLY OBSERVATIONS FETCH (for verification)
# ============================================================
def fetch_hourly_observations(station, city_tz_str):
    """Fetch today's hourly temps from NWS API for verification"""
    url = f"https://api.weather.gov/stations/{station}/observations?limit=500"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "SHARK/7.5"}, timeout=15)
        if resp.status_code != 200:
            return None, None
        
        observations = resp.json().get("features", [])
        if not observations:
            return None, None
        
        now_local = datetime.now(city_tz)
        today_midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_noon = now_local.replace(hour=12, minute=0, second=0, microsecond=0)
        temps = []
        temps_after_noon = []
        
        for obs in observations:
            props = obs.get("properties", {})
            timestamp_str = props.get("timestamp", "")
            temp_c = props.get("temperature", {}).get("value")
            if not timestamp_str or temp_c is None:
                continue
            
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                ts_local = ts.astimezone(city_tz)
                if ts_local >= today_midnight and ts_local <= now_local:
                    temp_f = round(temp_c * 9/5 + 32, 1)
                    temps.append(temp_f)
                    if ts_local >= today_noon:
                        temps_after_noon.append(temp_f)
            except:
                continue
        
        if not temps:
            return None, None
        
        hourly_low = min(temps)
        hourly_high = max(temps_after_noon) if temps_after_noon else None
        
        return hourly_low, hourly_high
    except:
        return None, None

# ============================================================
# 🛡️ WEATHER GUARD SYSTEM
# ============================================================
def fetch_forecast_cached(city_name, lat, lon):
    now = time.time()
    if city_name in _forecast_cache:
        cached_time, cached_data = _forecast_cache[city_name]
        if now - cached_time < FORECAST_CACHE_TTL:
            return cached_data
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "SHARK/7.5"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp2 = requests.get(forecast_url, headers={"User-Agent": "SHARK/7.5"}, timeout=10)
        if resp2.status_code != 200:
            return None
        periods = resp2.json().get("properties", {}).get("periods", [])
        _forecast_cache[city_name] = (now, periods)
        return periods
    except:
        return None

def fetch_current_temp(station):
    try:
        url = f"https://api.weather.gov/stations/{station}/observations/latest"
        resp = requests.get(url, headers={"User-Agent": "SHARK/7.5"}, timeout=10)
        if resp.status_code != 200:
            return None
        temp_c = resp.json().get("properties", {}).get("temperature", {}).get("value")
        if temp_c is not None:
            return round(temp_c * 9/5 + 32, 1)
        return None
    except:
        return None

def run_all_guards(city_name, cfg, settlement_value, market_type, ask_price, hourly_extreme):
    """Run all 5 guards - returns (safe, warnings)"""
    if not GUARD_ENABLED:
        return True, []
    
    warnings = []
    blocked = False
    lat = cfg.get("lat")
    lon = cfg.get("lon")
    station = cfg["nws"]

    # ===== GUARD 1: WEATHER - danger words in forecast =====
    if lat and lon:
        periods = fetch_forecast_cached(city_name, lat, lon)
        if periods:
            matched_words = set()
            for p in periods[:4]:
                detailed = (p.get("detailedForecast", "") or "").lower()
                short_fc = (p.get("shortForecast", "") or "").lower()
                period_name = p.get("name", "")
                combined = detailed + " " + short_fc
                for danger_word in WEATHER_DANGER_WORDS:
                    if danger_word in combined and danger_word not in matched_words:
                        matched_words.add(danger_word)
                        warnings.append(f"   ⛈️ WEATHER: '{danger_word}' in {period_name} forecast")
                        blocked = True
        else:
            warnings.append("   ⚠️ WEATHER: Could not fetch NWS forecast — proceed with caution")

    # ===== GUARD 2: PRICE - suspiciously cheap =====
    if ask_price <= PRICE_FLOOR:
        warnings.append(f"   💰 PRICE BLOCK: Ask is only {ask_price}¢ — market knows something you don't!")
        blocked = True
    elif ask_price <= PRICE_WARN:
        warnings.append(f"   💰 PRICE WARN: Ask is {ask_price}¢ — unusually cheap for a locked bracket")
        blocked = True

    # ===== GUARD 3: TREND - current temp vs settlement =====
    current_temp = fetch_current_temp(station)
    if current_temp is not None:
        if market_type == "LOW" and current_temp < settlement_value:
            diff = settlement_value - current_temp
            warnings.append(f"   📉 TREND: Current {current_temp}°F is BELOW settlement {settlement_value}°F — low may drop {diff:.0f}° more!")
            blocked = True
        elif market_type == "HIGH" and current_temp > settlement_value:
            diff = current_temp - settlement_value
            warnings.append(f"   📈 TREND: Current {current_temp}°F is ABOVE settlement {settlement_value}°F — high may rise {diff:.0f}° more!")
            blocked = True
        if current_temp is not None and not blocked:
            warnings.append(f"   ✅ TREND: Current {current_temp}°F — no conflict with settlement {settlement_value}°F")
    else:
        warnings.append(f"   ⚠️ TREND: Could not fetch current temp — proceed with caution")

    # ===== GUARD 4: FORECAST - NWS forecast temp vs settlement =====
    if lat and lon:
        periods = fetch_forecast_cached(city_name, lat, lon)
        if periods:
            for p in periods[:4]:
                is_daytime = p.get("isDaytime", True)
                forecast_temp = p.get("temperature")
                period_name = p.get("name", "")
                if forecast_temp is None:
                    continue
                if market_type == "LOW" and not is_daytime:
                    gap = abs(settlement_value - forecast_temp)
                    if gap > FORECAST_GAP_THRESHOLD:
                        warnings.append(f"   🌡️ FORECAST: NWS {period_name} low = {forecast_temp}°F vs settlement {settlement_value}°F — {gap:.0f}° gap!")
                        blocked = True
                    else:
                        warnings.append(f"   ✅ FORECAST: NWS {period_name} low = {forecast_temp}°F — within {FORECAST_GAP_THRESHOLD}° of settlement")
                    break
                if market_type == "HIGH" and is_daytime:
                    gap = abs(forecast_temp - settlement_value)
                    if gap > FORECAST_GAP_THRESHOLD:
                        warnings.append(f"   🌡️ FORECAST: NWS {period_name} high = {forecast_temp}°F vs settlement {settlement_value}°F — {gap:.0f}° gap!")
                        blocked = True
                    else:
                        warnings.append(f"   ✅ FORECAST: NWS {period_name} high = {forecast_temp}°F — within {FORECAST_GAP_THRESHOLD}° of settlement")
                    break

    # ===== GUARD 5: SETTLEMENT LOCK VERIFICATION (THE $7K FIX) =====
    if hourly_extreme is not None:
        gap = abs(settlement_value - hourly_extreme)
        if gap > SETTLEMENT_TOLERANCE:
            warnings.append(f"   🚨 SETTLEMENT MISMATCH: 6hr={settlement_value}°F vs Hourly={hourly_extreme}°F ({gap:.1f}° gap) — DATA CONFLICT!")
            blocked = True
        else:
            warnings.append(f"   ✅ SETTLEMENT VERIFIED: 6hr={settlement_value}°F matches Hourly={hourly_extreme}°F (±{SETTLEMENT_TOLERANCE}°)")
    else:
        warnings.append(f"   ⚠️ SETTLEMENT: Could not verify hourly data — proceed with caution")
        blocked = True

    return not blocked, warnings

# ============================================================
# 6HR SETTLEMENT FETCH
# ============================================================
def fetch_6hr_settlement(station, city_tz_str):
    """Fetch 6hr settlement from obhistory table"""
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        city_tz = pytz.timezone(city_tz_str)
        today = datetime.now(city_tz).day
        resp = requests.get(url, headers={"User-Agent": "SHARK/7.5"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, None, False, False
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return None, None, None, None, False, False
        rows = table.find_all('tr')
        all_6hr_mins = []
        all_6hr_maxs = []
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue
            try:
                date_val = cells[0].text.strip()
                time_val = cells[1].text.strip()
                if date_val:
                    try:
                        if int(date_val) != today:
                            continue
                    except:
                        continue
                max_6hr_text = cells[8].text.strip() if len(cells) > 8 else ""
                min_6hr_text = cells[9].text.strip() if len(cells) > 9 else ""
                if max_6hr_text:
                    try:
                        max_val = int(float(max_6hr_text))
                        hour = int(time_val.replace(":", "")[:2])
                        if hour >= 12:
                            all_6hr_maxs.append((time_val, max_val))
                    except:
                        pass
                if min_6hr_text:
                    try:
                        min_val = int(float(min_6hr_text))
                        all_6hr_mins.append((time_val, min_val))
                    except:
                        pass
            except:
                continue
        
        settlement_low, low_time = None, None
        if all_6hr_mins:
            all_6hr_mins.sort(key=lambda x: x[1])
            low_time, settlement_low = all_6hr_mins[0]
        
        settlement_high, high_time = None, None
        if all_6hr_maxs:
            all_6hr_maxs.sort(key=lambda x: x[1], reverse=True)
            high_time, settlement_high = all_6hr_maxs[0]
        
        # Lock detection: Does 6hr data exist?
        is_low_locked = len(all_6hr_mins) > 0 and settlement_low is not None
        is_high_locked = len(all_6hr_maxs) > 0 and settlement_high is not None
        
        return settlement_low, settlement_high, low_time, high_time, is_low_locked, is_high_locked
    except Exception as e:
        print(f"    6hr fetch error: {e}")
        return None, None, None, None, False, False

# ============================================================
# KALSHI BRACKET FETCH
# ============================================================
def fetch_kalshi_brackets(series_ticker, city_tz_str):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        city_tz = pytz.timezone(city_tz_str)
        today_str = datetime.now(city_tz).strftime('%y%b%d').upper()
        today_markets = [m for m in markets if today_str in m.get("event_ticker", "").upper()]
        if not today_markets:
            first_event = markets[0].get("event_ticker", "")
            today_markets = [m for m in markets if m.get("event_ticker") == first_event]
        brackets = []
        for m in today_markets:
            title = m.get("title", "")
            ticker = m.get("ticker", "")
            yes_ask = m.get("yes_ask", 0) or 0
            low_bound, high_bound, bracket_name = None, None, ""
            gt_match = re.search(r'>\s*(-?\d+)', title)
            if gt_match:
                threshold = int(gt_match.group(1))
                low_bound = threshold + 1
                high_bound = 999
                bracket_name = f">{threshold} ({low_bound}+)"
            if low_bound is None:
                lt_match = re.search(r'<\s*(-?\d+)', title)
                if lt_match:
                    threshold = int(lt_match.group(1))
                    high_bound = threshold - 1
                    low_bound = -999
                    bracket_name = f"<{threshold} (<={high_bound})"
            if low_bound is None:
                range_match = re.search(r'(-?\d+)\s*to\s*(-?\d+)', title, re.IGNORECASE)
                if range_match:
                    low_bound = int(range_match.group(1))
                    high_bound = int(range_match.group(2))
                    bracket_name = f"{low_bound} to {high_bound}"
                else:
                    dash_match = re.search(r'be\s+(-?\d+)-(-?\d+)', title)
                    if dash_match:
                        low_bound = int(dash_match.group(1))
                        high_bound = int(dash_match.group(2))
                        bracket_name = f"{low_bound} to {high_bound}"
            if low_bound is None:
                above_match = re.search(r'(-?\d+)\s*(or above|or more|at least|\+)', title, re.IGNORECASE)
                if above_match:
                    low_bound = int(above_match.group(1))
                    high_bound = 999
                    bracket_name = f"{low_bound}+"
            if low_bound is None:
                below_match = re.search(r'(-?\d+)\s*(or below|or less|or under)', title, re.IGNORECASE)
                if below_match:
                    high_bound = int(below_match.group(1))
                    low_bound = -999
                    bracket_name = f"<={high_bound}"
            if low_bound is not None and high_bound is not None:
                brackets.append({
                    "name": bracket_name, "low": low_bound, "high": high_bound,
                    "ask": yes_ask, "ticker": ticker, "title": title
                })
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except Exception as e:
        print(f"  Bracket fetch error: {e}")
        return []

def find_winning_bracket(temp, brackets):
    if temp is None or not brackets:
        return None
    for b in brackets:
        if b["high"] == 999 and temp >= b["low"]:
            return b
        if b["low"] == -999 and temp <= b["high"]:
            return b
        if b["low"] <= temp <= b["high"]:
            return b
    return None

# ============================================================
# ALERT & BUY
# ============================================================
def send_alert_and_buy(city, cfg, bracket, temp_value, market_type, settlement_time, hourly_extreme, settlement_match):
    global daily_spent
    ask = bracket["ask"]
    ticker = bracket["ticker"]
    potential_cost = (ask / 100) * CONTRACTS_PER_TRADE
    potential_profit = ((100 - ask) / 100) * CONTRACTS_PER_TRADE

    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    print(f"\n{'='*60}")
    print(f"🦈🚨 SHARK ALERT: {city} ({market_type})")
    print(f"   6HR SETTLEMENT: {temp_value}°F @ {settlement_time}")
    print(f"   HOURLY EXTREME: {hourly_extreme}°F (Match: {'YES' if settlement_match else 'NO'})")
    print(f"   BRACKET: {bracket['name']} (ticker: {ticker})")
    print(f"   Ask: {ask}¢ | Potential profit: {100-ask}¢")
    print(f"")
    print(f"   💰 WOULD BUY: {CONTRACTS_PER_TRADE} contracts @ {ask}¢")
    print(f"   💵 Cost: ${potential_cost:.2f} | Profit if wins: ${potential_profit:.2f}")

    # ===== RUN ALL 5 GUARDS =====
    print(f"\n   🛡️ RUNNING 5 SAFETY GUARDS...")
    safe, guard_warnings = run_all_guards(city, cfg, temp_value, market_type, ask, hourly_extreme)

    for w in guard_warnings:
        print(w)

    if not safe:
        print(f"\n   ⛔⛔⛔ GUARDS BLOCKED — DO NOT BUY ⛔⛔⛔")
        print(f"   🔍 CHECK MANUALLY before overriding!")
        
        log_to_csv(now, city, market_type, temp_value, settlement_time, True, hourly_extreme, settlement_match, bracket, False, guard_warnings, False)
        
        for _ in range(5):
            winsound.Beep(400, 300)
            time.sleep(0.15)
        print(f"{'='*60}\n")
        return

    # All guards passed
    print(f"\n   ✅ ALL 5 GUARDS PASSED")
    for _ in range(3):
        winsound.Beep(1000, 200)
        time.sleep(0.1)
        winsound.Beep(1200, 200)
        time.sleep(0.1)

    if AUTO_BUY_ENABLED and API_KEY and len(API_KEY) > 10:
        print(f"\n   🛒 PLACING ORDER...")
        success, msg = place_kalshi_order(ticker, ask, CONTRACTS_PER_TRADE)
        print(f"   {msg}")
        if success:
            winsound.Beep(800, 500)
            print(f"   📊 Daily spent: ${daily_spent:.2f} / ${MAX_DAILY_SPEND}")
            log_to_csv(now, city, market_type, temp_value, settlement_time, True, hourly_extreme, settlement_match, bracket, True, guard_warnings, True)
        else:
            log_to_csv(now, city, market_type, temp_value, settlement_time, True, hourly_extreme, settlement_match, bracket, True, guard_warnings, False)
    else:
        print(f"\n   🧪 TEST MODE - Not buying. Verify this is correct!")
        log_to_csv(now, city, market_type, temp_value, settlement_time, True, hourly_extreme, settlement_match, bracket, True, guard_warnings, False)

    print(f"{'='*60}\n")

# ============================================================
# MAIN LOOP
# ============================================================
def check_all_cities():
    global daily_spent, _last_log_time
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    et_date = now.date()
    
    init_csv_log()
    
    current_time = time.time()
    should_log_summary = (current_time - _last_log_time) >= LOG_INTERVAL

    print(f"\n[{now.strftime('%I:%M:%S %p')}] Scanning cities...")
    print("=" * 70)

    for city, cfg in CITIES.items():
        try:
            city_tz = pytz.timezone(cfg["tz"])
            city_date = datetime.now(city_tz).date()
            if city_date < et_date:
                city_date_str = datetime.now(city_tz).strftime("%b %d")
                print(f"  ⏸️ {city} — Still on {city_date_str}, skipping")
                continue

            settlement_low, settlement_high, low_time, high_time, is_low_locked, is_high_locked = fetch_6hr_settlement(cfg["nws"], cfg["tz"])
            hourly_low, hourly_high = fetch_hourly_observations(cfg["nws"], cfg["tz"])

            # ===== CHECK LOW =====
            if cfg["kalshi_low"] and TRADE_LOW.get(city, False):
                if settlement_low is not None:
                    settlement_match = (hourly_low is not None and abs(settlement_low - hourly_low) <= SETTLEMENT_TOLERANCE)
                    brackets_low = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"])
                    winning_low = find_winning_bracket(settlement_low, brackets_low)
                    if winning_low:
                        ask_low = winning_low["ask"]
                        bracket_name_low = winning_low["name"]
                    else:
                        ask_low = 100
                        bracket_name_low = "NO MATCH"
                    lock_icon = "🔒" if is_low_locked else "⏳"
                    match_icon = "✅" if settlement_match else "⚠️"
                    print(f"  {lock_icon}{match_icon} {city} LOW: 6hr↓{settlement_low} @ {low_time} (hourly:{hourly_low}) -> {bracket_name_low} @ {ask_low}¢")
                    
                    if is_low_locked and settlement_match and ask_low <= MAX_ASK_PRICE and winning_low:
                        send_alert_and_buy(city, cfg, winning_low, settlement_low, "LOW", low_time, hourly_low, settlement_match)
                    elif should_log_summary:
                        log_to_csv(now, city, "LOW", settlement_low, low_time, is_low_locked, hourly_low, settlement_match, winning_low if winning_low and ask_low <= MAX_ASK_PRICE else None, None, None, False)
                elif should_log_summary:
                    log_to_csv(now, city, "LOW", None, None, False, hourly_low, None, None, None, None, False)

            # ===== CHECK HIGH =====
            if TRADE_HIGH.get(city, False):
                if settlement_high is not None:
                    settlement_match = (hourly_high is not None and abs(settlement_high - hourly_high) <= SETTLEMENT_TOLERANCE)
                    brackets_high = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"])
                    winning_high = find_winning_bracket(settlement_high, brackets_high)
                    if winning_high:
                        ask_high = winning_high["ask"]
                        bracket_name_high = winning_high["name"]
                    else:
                        ask_high = 100
                        bracket_name_high = "NO MATCH"
                    lock_icon = "🔒" if is_high_locked else "⏳"
                    match_icon = "✅" if settlement_match else "⚠️"
                    print(f"  {lock_icon}{match_icon} {city} HIGH: 6hr↑{settlement_high} @ {high_time} (hourly:{hourly_high}) -> {bracket_name_high} @ {ask_high}¢")
                    
                    if is_high_locked and settlement_match and ask_high <= MAX_ASK_PRICE and winning_high:
                        send_alert_and_buy(city, cfg, winning_high, settlement_high, "HIGH", high_time, hourly_high, settlement_match)
                    elif should_log_summary:
                        log_to_csv(now, city, "HIGH", settlement_high, high_time, is_high_locked, hourly_high, settlement_match, winning_high if winning_high and ask_high <= MAX_ASK_PRICE else None, None, None, False)
                elif should_log_summary:
                    log_to_csv(now, city, "HIGH", None, None, False, hourly_high, None, None, None, None, False)

        except Exception as e:
            print(f"  ❌ {city}: Error - {e}")
    
    if should_log_summary:
        _last_log_time = current_time

    print("=" * 70)

def main():
    global daily_spent
    low_enabled = [c for c, v in TRADE_LOW.items() if v]
    high_enabled = [c for c, v in TRADE_HIGH.items() if v]

    print("=" * 70)
    print("🦈 SHARK AUTO-BUY v7.5 - FIXED SETTLEMENT LOCK + 5 GUARDS")
    print("=" * 70)
    print("")
    if AUTO_BUY_ENABLED:
        print("🔴 LIVE MODE - REAL BUYING ENABLED")
    else:
        print("🧪 TEST MODE - ALERTS ONLY, NO BUYING")
    print("")
    print(f"🛡️ 5 GUARDS: {'ON' if GUARD_ENABLED else 'OFF'}")
    if GUARD_ENABLED:
        print(f"   1️⃣ Weather Guard     — blocks on storms/fronts/freezes/heat")
        print(f"   2️⃣ Price Guard       — blocks ≤{PRICE_FLOOR}¢, warns ≤{PRICE_WARN}¢")
        print(f"   3️⃣ Trend Guard       — blocks if current temp contradicts settlement")
        print(f"   4️⃣ Forecast Guard    — blocks if NWS forecast disagrees by {FORECAST_GAP_THRESHOLD}°+")
        print(f"   5️⃣ Settlement Guard  — blocks if 6hr ≠ hourly ±{SETTLEMENT_TOLERANCE}° (FIXES $7K BUG)")
    print("")
    print(f"📊 AUTO-LOGGING: All scans → {LOG_FILE}")
    print(f"   ⚡ ALWAYS logs: Alerts, Blocks, Buys")
    print(f"   📋 Summary logs: Every 30 min (lock status, prices)")
    print("")
    print(f"📍 ENABLED: {len(low_enabled)} LOWs, {len(high_enabled)} HIGHs")
    print(f"   LOWs:  {', '.join(low_enabled) if low_enabled else 'NONE'}")
    print(f"   HIGHs: {', '.join(high_enabled) if high_enabled else 'NONE'}")
    print("")
    print("✅ Uses 6hr aggregate from obhistory + hourly API for verification")
    print("✅ LOW = LOWEST 6hr Min (verified against hourly low)")
    print("✅ HIGH = HIGHEST 6hr Max after NOON (verified against hourly high)")
    print("=" * 70)
    print("")
    print("📋 Settings:")
    print(f"   Contracts per trade: {CONTRACTS_PER_TRADE}")
    print(f"   Max ask price: {MAX_ASK_PRICE}¢")
    print(f"   Max daily spend: ${MAX_DAILY_SPEND}")
    print(f"   Check interval: {CHECK_INTERVAL}s")
    print("=" * 70)
    print("\nPress Ctrl+C to stop.\n")

    winsound.Beep(600, 200)
    winsound.Beep(800, 300)

    while True:
        try:
            check_all_cities()
            eastern = pytz.timezone("US/Eastern")
            if datetime.now(eastern).hour == 0 and datetime.now(eastern).minute < 2:
                daily_spent = 0
                _forecast_cache.clear()
                global _last_log_time
                _last_log_time = 0
                print("\n[MIDNIGHT] Daily spend + cache + log timer reset")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n\n[STOPPED] Daily spent: ${daily_spent:.2f}")
            break
        except Exception as e:
            print(f"\n[WARNING] Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
