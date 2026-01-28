"""
🦈 SHARK DESKTOP ALERT v1.0
Monitors Kalshi temp markets and shows Windows notifications when opportunities hit.

SETUP (one time):
1. Open Command Prompt
2. Run: pip install win10toast requests pytz
3. Save this file as shark_alert.py
4. Run: python shark_alert.py

Keep it running overnight. It will pop up notifications when:
- Early lock probability >= 70%
- Ask price < 30¢
- Temperature upticks detected
"""

import requests
import time
from datetime import datetime, timedelta
import pytz
import winsound

# Try to import win10toast, give helpful error if not installed
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
except ImportError:
    print("❌ Missing win10toast! Run: pip install win10toast")
    print("Then run this script again.")
    input("Press Enter to exit...")
    exit()

# ============================================================
# CONFIG - Cities to monitor
# ============================================================
CITIES = {
    "Chicago": {"metar": "KMDW", "kalshi": "KXLOWTCHI", "tz": "US/Central"},
    "New York City": {"metar": "KNYC", "kalshi": "KXLOWTNYC", "tz": "US/Eastern"},
    "Philadelphia": {"metar": "KPHL", "kalshi": "KXLOWTPHIL", "tz": "US/Eastern"},
    "Miami": {"metar": "KMIA", "kalshi": "KXLOWTMIA", "tz": "US/Eastern"},
    "Denver": {"metar": "KDEN", "kalshi": "KXLOWTDEN", "tz": "US/Mountain"},
}

# Alert thresholds
MIN_PROBABILITY = 70  # Alert when early lock prob >= this
MAX_ASK_PRICE = 30    # Alert when ask <= this (cents)
CHECK_INTERVAL = 60   # Seconds between checks

# Track state
temp_history = {}  # For uptick detection
alerted_today = {}  # Prevent spam - one alert per city per condition

# ============================================================
# METAR FETCH
# ============================================================
def fetch_metar(station):
    """Fetch raw METAR data from airport"""
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "SharkAlert/1.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None
        metar = data[0]
        temp_c = metar.get("temp")
        return {
            "temp_f": round(temp_c * 9/5 + 32, 1) if temp_c is not None else None,
            "wind_speed": metar.get("wspd", 0) or 0,
            "clouds": metar.get("clouds", []),
            "raw": metar.get("rawOb", "")
        }
    except Exception as e:
        return None

# ============================================================
# KALSHI FETCH
# ============================================================
def fetch_kalshi_brackets(series_ticker):
    """Fetch today's Kalshi brackets"""
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        
        eastern = pytz.timezone("US/Eastern")
        today_str = datetime.now(eastern).strftime('%y%b%d').upper()
        today_markets = [m for m in markets if today_str in m.get("event_ticker", "").upper()]
        
        if not today_markets:
            first_event = markets[0].get("event_ticker", "")
            today_markets = [m for m in markets if m.get("event_ticker") == first_event]
        
        brackets = []
        for m in today_markets:
            title = m.get("title", "")
            yes_ask = m.get("yes_ask", 0) or 0
            
            # Parse bracket range
            import re
            range_match = re.search(r'(-?\d+)\s*[-–to]+\s*(-?\d+)°', title)
            if range_match:
                low = int(range_match.group(1))
                high = int(range_match.group(2))
                brackets.append({"name": f"{low}-{high}°", "low": low, "high": high, "ask": yes_ask})
            
            above_match = re.search(r'(-?\d+)°?\s*(or above|or more|\+)', title, re.IGNORECASE)
            if above_match and not range_match:
                low = int(above_match.group(1))
                brackets.append({"name": f"{low}°+", "low": low, "high": 999, "ask": yes_ask})
        
        return brackets
    except:
        return []

def find_winning_bracket(temp, brackets):
    """Find which bracket the temp falls into"""
    if temp is None or not brackets:
        return None
    rounded = round(temp)
    for b in brackets:
        if b["high"] == 999 and rounded >= b["low"]:
            return b
        if b["low"] <= rounded <= b["high"]:
            return b
    return None

# ============================================================
# PROBABILITY CALCULATION
# ============================================================
def calculate_early_lock_prob(metar):
    """Calculate probability of early lock based on conditions"""
    if not metar:
        return 0
    
    prob = 40  # Base
    
    # Sky conditions
    clouds = metar.get("clouds", [])
    if clouds:
        cover = clouds[0].get("cover", "")
        if cover in ["OVC", "BKN"]:
            prob += 30  # Cloudy = early lock likely
        elif cover == "SCT":
            prob += 10
    
    # Wind
    wind = metar.get("wind_speed", 0)
    if wind >= 15:
        prob += 25  # Windy = mixing = early stabilization
    elif wind >= 8:
        prob += 10
    
    return min(95, max(5, prob))

# ============================================================
# UPTICK DETECTION
# ============================================================
def check_upticks(city, current_temp):
    """Check for consecutive temperature upticks"""
    if city not in temp_history:
        temp_history[city] = []
    
    history = temp_history[city]
    history.append({"temp": current_temp, "time": datetime.now()})
    
    # Keep last 30 min
    cutoff = datetime.now() - timedelta(minutes=30)
    temp_history[city] = [h for h in history if h["time"] > cutoff]
    history = temp_history[city]
    
    if len(history) < 3:
        return 0
    
    # Check last 3 readings for upticks
    recent = history[-3:]
    upticks = 0
    for i in range(1, len(recent)):
        if recent[i]["temp"] > recent[i-1]["temp"] + 0.2:
            upticks += 1
    
    return upticks

# ============================================================
# NOTIFICATION
# ============================================================
def send_alert(city, message, urgent=False):
    """Send Windows desktop notification"""
    print(f"\n🚨 ALERT: {city}")
    print(f"   {message}")
    
    # Play sound
    if urgent:
        # Urgent beeps
        for _ in range(3):
            winsound.Beep(1000, 200)
            time.sleep(0.1)
            winsound.Beep(1200, 200)
            time.sleep(0.1)
    else:
        winsound.Beep(800, 300)
        winsound.Beep(1000, 400)
    
    # Windows toast notification
    try:
        toaster.show_toast(
            f"🦈 SHARK ALERT: {city}",
            message,
            duration=10,
            threaded=True
        )
    except:
        pass  # Toast might fail if previous still showing

# ============================================================
# MAIN LOOP
# ============================================================
def check_all_cities():
    """Check all cities for opportunities"""
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    today_key = now.strftime("%Y-%m-%d")
    
    print(f"\n[{now.strftime('%I:%M:%S %p')}] Scanning all cities...")
    
    for city, cfg in CITIES.items():
        metar = fetch_metar(cfg["metar"])
        if not metar or metar.get("temp_f") is None:
            print(f"  {city}: No METAR data")
            continue
        
        temp = metar["temp_f"]
        prob = calculate_early_lock_prob(metar)
        upticks = check_upticks(city, temp)
        
        brackets = fetch_kalshi_brackets(cfg["kalshi"])
        winning = find_winning_bracket(temp, brackets)
        ask = winning["ask"] if winning else 100
        
        # Status line
        status = f"  {city}: {temp}°F | Prob: {prob}% | Ask: {ask}¢"
        if upticks >= 2:
            status += " | 🔥 UPTICKS!"
        print(status)
        
        # Check alert conditions
        alert_key = f"{today_key}_{city}"
        
        # SHARK ALERT: All conditions met
        if prob >= MIN_PROBABILITY and ask <= MAX_ASK_PRICE and upticks >= 1:
            if alert_key + "_shark" not in alerted_today:
                alerted_today[alert_key + "_shark"] = True
                send_alert(
                    city,
                    f"🦈 POUNCE! {temp}°F locked\nProb: {prob}% | Ask: {ask}¢ | Upticks: ✓\nBUY {winning['name']} NOW!",
                    urgent=True
                )
        
        # High probability alert
        elif prob >= MIN_PROBABILITY and ask <= 50:
            if alert_key + "_prob" not in alerted_today:
                alerted_today[alert_key + "_prob"] = True
                send_alert(
                    city,
                    f"⚠️ High probability: {prob}%\nTemp: {temp}°F | Ask: {ask}¢\nWatching for upticks...",
                    urgent=False
                )
        
        # Cheap ask alert
        elif ask <= MAX_ASK_PRICE and prob >= 50:
            if alert_key + "_cheap" not in alerted_today:
                alerted_today[alert_key + "_cheap"] = True
                send_alert(
                    city,
                    f"💰 Cheap entry: {ask}¢\nTemp: {temp}°F | Prob: {prob}%\nMonitoring...",
                    urgent=False
                )

def main():
    print("=" * 50)
    print("🦈 SHARK DESKTOP ALERT v1.0")
    print("=" * 50)
    print(f"Monitoring: {', '.join(CITIES.keys())}")
    print(f"Alert when: Prob >= {MIN_PROBABILITY}% AND Ask <= {MAX_ASK_PRICE}¢")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("=" * 50)
    print("\nKeep this window open. Notifications will pop up when opportunities hit.")
    print("Press Ctrl+C to stop.\n")
    
    # Test notification
    print("Testing notification system...")
    winsound.Beep(600, 200)
    winsound.Beep(800, 300)
    print("✅ Sound works! Starting monitor...\n")
    
    while True:
        try:
            check_all_cities()
            
            # Reset alerts at midnight
            eastern = pytz.timezone("US/Eastern")
            if datetime.now(eastern).hour == 0 and datetime.now(eastern).minute < 2:
                alerted_today.clear()
                print("\n🌙 Midnight - alerts reset for new day")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            print("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
