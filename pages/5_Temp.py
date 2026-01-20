import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

# --- GOOGLE ANALYTICS G4 ---
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# --- CITY CONFIG ---
# Each city: NWS grid point + Kalshi series tickers
CITIES = {
    "Atlanta": {
        "nws_office": "FFC",
        "nws_grid": "52,88",
        "high_series": "KXHIGHATL",
        "low_series": "KXLOWTATL"
    },
    "Austin": {
        "nws_office": "EWX",
        "nws_grid": "156,91",
        "high_series": "KXHIGHAUS",
        "low_series": "KXLOWTAUS"
    },
    "Boston": {
        "nws_office": "BOX",
        "nws_grid": "71,90",
        "high_series": "KXHIGHBOS",
        "low_series": "KXLOWTBOS"
    },
    "Chicago": {
        "nws_office": "LOT",
        "nws_grid": "65,76",
        "high_series": "KXHIGHCHI",
        "low_series": "KXLOWTCHI"
    },
    "Dallas": {
        "nws_office": "FWD",
        "nws_grid": "79,108",
        "high_series": "KXHIGHDAL",
        "low_series": "KXLOWTDAL"
    },
    "Denver": {
        "nws_office": "BOU",
        "nws_grid": "62,60",
        "high_series": "KXHIGHDEN",
        "low_series": "KXLOWTDEN"
    },
    "Houston": {
        "nws_office": "HGX",
        "nws_grid": "65,97",
        "high_series": "KXHIGHHOU",
        "low_series": "KXLOWTHOU"
    },
    "Los Angeles": {
        "nws_office": "LOX",
        "nws_grid": "154,44",
        "high_series": "KXHIGHLA",
        "low_series": "KXLOWTLA"
    },
    "Miami": {
        "nws_office": "MFL",
        "nws_grid": "109,50",
        "high_series": "KXHIGHMIA",
        "low_series": "KXLOWTMIA"
    },
    "New York City": {
        "nws_office": "OKX",
        "nws_grid": "33,37",
        "high_series": "KXHIGHNY",
        "low_series": "KXLOWTNYC"
    },
    "Philadelphia": {
        "nws_office": "PHI",
        "nws_grid": "49,75",
        "high_series": "KXHIGHPHL",
        "low_series": "KXLOWTPHL"
    },
    "Phoenix": {
        "nws_office": "PSR",
        "nws_grid": "161,58",
        "high_series": "KXHIGHPHX",
        "low_series": "KXLOWTPHX"
    },
    "San Francisco": {
        "nws_office": "MTR",
        "nws_grid": "85,105",
        "high_series": "KXHIGHSF",
        "low_series": "KXLOWTSF"
    },
    "Seattle": {
        "nws_office": "SEW",
        "nws_grid": "124,67",
        "high_series": "KXHIGHSEA",
        "low_series": "KXLOWTSEA"
    },
    "Washington DC": {
        "nws_office": "LWX",
        "nws_grid": "97,71",
        "high_series": "KXHIGHDC",
        "low_series": "KXLOWTDC"
    }
}

def get_date_suffix(target_date):
    return target_date.strftime("%y%b%d").upper()

def get_nws_forecast(office, grid):
    """Fetch forecast from NWS API"""
    try:
        url = f"https://api.weather.gov/gridpoints/{office}/{grid}/forecast"
        response = requests.get(url, headers={"User-Agent": "BigSnapshot Weather App"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            periods = data.get("properties", {}).get("periods", [])
            update_time = data.get("properties", {}).get("updateTime", "")
            return periods, update_time, None
        return [], None, f"NWS API {response.status_code}"
    except Exception as e:
        return [], None, str(e)

def fetch_series_markets(series_ticker):
    """Fetch all markets in a Kalshi series"""
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets"
        response = requests.get(url, params={"series_ticker": series_ticker, "limit": 100}, timeout=10)
        if response.status_code == 200:
            return response.json().get("markets", []), None
        return [], f"API {response.status_code}"
    except Exception as e:
        return [], str(e)

def find_todays_markets(markets, series_ticker, date_suffix):
    """Find all bracket markets for a specific day"""
    prefix = f"{series_ticker}-{date_suffix}".upper()
    found = []
    for m in markets:
        ticker = m.get("ticker", "").upper()
        if ticker.startswith(prefix):
            found.append(m)
    return found

def parse_forecast_for_date(periods, target_date):
    """Extract high and low for a specific date from NWS periods"""
    high, low = None, None
    
    for p in periods:
        temp = p.get("temperature")
        is_day = p.get("isDaytime", True)
        start_time = p.get("startTime", "")
        
        # Parse the period's date
        if start_time:
            try:
                period_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
            except:
                continue
            
            # Match target date
            if period_date == target_date:
                if is_day and high is None:
                    high = temp
                elif not is_day and low is None:
                    low = temp
    
    # Fallback for today if we didn't find by date
    if high is None or low is None:
        for p in periods[:4]:
            name = p.get("name", "").lower()
            temp = p.get("temperature")
            
            if high is None and ("today" in name or "this afternoon" in name):
                high = temp
            if low is None and ("tonight" in name or "night" in name):
                low = temp
    
    return high, low

def calculate_market_implied(markets):
    """Calculate probability-weighted temperature from bracket markets"""
    if not markets:
        return None
    # This would need bracket parsing - simplified for now
    return None

# --- HEADER ---
st.title("🌡️ Temperature Edge Finder")
st.caption("NWS Forecast vs Kalshi Markets | BigSnapshot.com")

# --- OWNER CHECK ---
is_owner = st.session_state.get("user_type") == "Owner"

# Backup: URL param unlock for owner features
if st.query_params.get("mode") == "owner":
    is_owner = True
    st.session_state["user_type"] = "Owner"

# --- TIME ---
et = pytz.timezone("America/New_York")
now_et = datetime.now(et)

st.caption(f"Current time: {now_et.strftime('%I:%M %p ET')} | Today: {now_et.strftime('%A, %B %d, %Y')}")

# --- CITY SELECTOR ---
st.subheader("Select City")

# Get default from URL params, fallback to NYC
city_list = list(CITIES.keys())
default_city = st.query_params.get("city", "New York City")
if default_city not in city_list:
    default_city = "New York City"
default_index = city_list.index(default_city)

col_city, col_default = st.columns([3, 1])
with col_city:
    city = st.selectbox("City", city_list, index=default_index, label_visibility="collapsed")
with col_default:
    if st.button("⭐ Set as Default"):
        st.query_params["city"] = city
        st.success(f"✓ Saved!")
        st.caption("Bookmark this page")

config = CITIES[city]

# --- DATE SELECTION ---
today = now_et.date()
tomorrow = today + timedelta(days=1)

# Owner sees 7-day view, public sees today only
is_owner = st.session_state.get("user_type") == "Owner"

if is_owner:
    date_options = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
    date_option = st.radio("Select Date", date_options, horizontal=True)
    
    day_index = date_options.index(date_option)
    target_date = today + timedelta(days=day_index)
    
    # Show market availability
    if day_index == 0:
        st.success("🟢 **MARKET OPEN** — Trade now")
    elif day_index == 1:
        st.success("🟢 **MARKET OPENS 2AM** — You see the answer first")
    else:
        days_until = day_index - 1
        st.warning(f"🟡 **MARKET OPENS IN {days_until} DAYS** — Plan your position now")
else:
    target_date = today

date_suffix = get_date_suffix(target_date)

st.caption(f"Looking for: {target_date.strftime('%A, %B %d')} | Suffix: `{date_suffix}`")

# --- NWS FORECAST ---
st.subheader(f"📡 NWS Forecast — {city}")

periods, update_time, nws_err = get_nws_forecast(config["nws_office"], config["nws_grid"])

if nws_err:
    st.error(f"NWS Error: {nws_err}")
    nws_high, nws_low = None, None
else:
    nws_high, nws_low = parse_forecast_for_date(periods, target_date)
    
    # Show last update time
    if update_time:
        try:
            update_dt = datetime.fromisoformat(update_time.replace("Z", "+00:00"))
            update_et = update_dt.astimezone(et)
            st.caption(f"Last NWS update: {update_et.strftime('%I:%M %p ET')}")
        except:
            pass
    
    col1, col2 = st.columns(2)
    with col1:
        if nws_high:
            st.metric("🔥 NWS High", f"{nws_high}°F")
        else:
            st.metric("🔥 NWS High", "—")
    with col2:
        if nws_low:
            st.metric("❄️ NWS Low", f"{nws_low}°F")
        else:
            st.metric("❄️ NWS Low", "—")

# --- KALSHI MARKETS ---
st.subheader("📊 Kalshi Markets")

col_high, col_low = st.columns(2)

with col_high:
    st.write("**HIGH Temp Market**")
    
    high_markets, err = fetch_series_markets(config["high_series"])
    if err:
        st.error(err)
    else:
        day_markets = find_todays_markets(high_markets, config["high_series"], date_suffix)
        if day_markets:
            # Header
            st.markdown("""
            <div style="display:flex; padding:8px 0; border-bottom:1px solid #444;">
                <div style="flex:2; font-weight:bold;">Bracket</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Chance</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Yes</div>
            </div>
            """, unsafe_allow_html=True)
            
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                # Extract bracket range
                bracket = title
                low_temp, high_temp = None, None
                if "be " in title and "°" in title:
                    try:
                        part = title.split("be ")[1].split(" on")[0]
                        if "-" in part:
                            nums = part.replace("°", "").split("-")
                            low_temp, high_temp = int(nums[0]), int(nums[1])
                            bracket = f"{nums[0]}° to {nums[1]}°"
                        elif "<" in part:
                            num = int(part.replace("<", "").replace("°", ""))
                            high_temp = num - 1
                            bracket = f"{num}° or below"
                        elif ">" in part:
                            num = int(part.replace(">", "").replace("°", ""))
                            low_temp = num + 1
                            bracket = f"{num}° or above"
                    except:
                        bracket = title[:30]
                
                # Check if NWS forecast falls in this bracket
                is_pick = False
                if nws_high and low_temp is not None and high_temp is not None:
                    if low_temp <= nws_high <= high_temp:
                        is_pick = True
                elif nws_high and high_temp is not None and low_temp is None:
                    if nws_high <= high_temp:
                        is_pick = True
                elif nws_high and low_temp is not None and high_temp is None:
                    if nws_high >= low_temp:
                        is_pick = True
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    chance = f"{mid:.0f}%" if mid > 1 else "<1%"
                    yes_price = f"{yes_ask}¢"
                else:
                    chance = "<1%"
                    yes_price = "—"
                
                bg_color = "#e67e22" if is_pick else "transparent"
                text_color = "#000" if is_pick else "#fff"
                
                st.markdown(f"""
                <div style="display:flex; padding:10px 8px; background:{bg_color}; border-radius:4px; margin:2px 0;">
                    <div style="flex:2; color:{text_color};">{bracket}</div>
                    <div style="flex:1; text-align:center; color:{text_color};">{chance}</div>
                    <div style="flex:1; text-align:center; color:{text_color};">{yes_price}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No markets for this date")

with col_low:
    st.write("**LOW Temp Market**")
    
    low_markets, err = fetch_series_markets(config["low_series"])
    if err:
        st.error(err)
    else:
        day_markets = find_todays_markets(low_markets, config["low_series"], date_suffix)
        if day_markets:
            # Header
            st.markdown("""
            <div style="display:flex; padding:8px 0; border-bottom:1px solid #444;">
                <div style="flex:2; font-weight:bold;">Bracket</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Chance</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Yes</div>
            </div>
            """, unsafe_allow_html=True)
            
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                # Extract bracket range
                bracket = title
                low_temp, high_temp = None, None
                if "be " in title and "°" in title:
                    try:
                        part = title.split("be ")[1].split(" on")[0]
                        if "-" in part:
                            nums = part.replace("°", "").split("-")
                            low_temp, high_temp = int(nums[0]), int(nums[1])
                            bracket = f"{nums[0]}° to {nums[1]}°"
                        elif "<" in part:
                            num = int(part.replace("<", "").replace("°", ""))
                            high_temp = num - 1
                            bracket = f"{num}° or below"
                        elif ">" in part:
                            num = int(part.replace(">", "").replace("°", ""))
                            low_temp = num + 1
                            bracket = f"{num}° or above"
                    except:
                        bracket = title[:30]
                
                # Check if NWS forecast falls in this bracket
                is_pick = False
                if nws_low and low_temp is not None and high_temp is not None:
                    if low_temp <= nws_low <= high_temp:
                        is_pick = True
                elif nws_low and high_temp is not None and low_temp is None:
                    if nws_low <= high_temp:
                        is_pick = True
                elif nws_low and low_temp is not None and high_temp is None:
                    if nws_low >= low_temp:
                        is_pick = True
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    chance = f"{mid:.0f}%" if mid > 1 else "<1%"
                    yes_price = f"{yes_ask}¢"
                else:
                    chance = "<1%"
                    yes_price = "—"
                
                bg_color = "#e67e22" if is_pick else "transparent"
                text_color = "#000" if is_pick else "#fff"
                
                st.markdown(f"""
                <div style="display:flex; padding:10px 8px; background:{bg_color}; border-radius:4px; margin:2px 0;">
                    <div style="flex:2; color:{text_color};">{bracket}</div>
                    <div style="flex:1; text-align:center; color:{text_color};">{chance}</div>
                    <div style="flex:1; text-align:center; color:{text_color};">{yes_price}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No markets for this date")

# --- 7-DAY OVERVIEW (Owner Only) ---
if is_owner:
    st.subheader("📅 7-DAY EDGE OVERVIEW")
    st.markdown("**Your weekly edge — see every bracket before markets open**")
    
    # Build 7-day forecast table
    week_data = []
    for i in range(7):
        day_date = today + timedelta(days=i)
        day_high, day_low = parse_forecast_for_date(periods, day_date)
        
        # Market status
        if i == 0:
            status = "🟢 OPEN"
        elif i == 1:
            status = "🟢 2AM"
        else:
            status = f"🟡 {i-1}d"
        
        week_data.append({
            "day": day_date.strftime("%a"),
            "date": day_date.strftime("%b %d"),
            "high": day_high,
            "low": day_low,
            "status": status
        })
    
    # Display as table
    st.markdown("""
    <style>
    .week-table { width: 100%; border-collapse: collapse; }
    .week-table th, .week-table td { padding: 12px 8px; text-align: center; border-bottom: 1px solid #333; }
    .week-table th { background: #1a1a1a; color: #888; font-size: 12px; }
    .week-table td { font-size: 14px; }
    .bracket-cell { background: #e67e22; color: #000; border-radius: 4px; padding: 4px 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    table_html = """
    <table class="week-table">
        <tr>
            <th>DAY</th>
            <th>DATE</th>
            <th>HIGH</th>
            <th>HIGH BRACKET</th>
            <th>LOW</th>
            <th>LOW BRACKET</th>
            <th>MARKET</th>
        </tr>
    """
    
    for d in week_data:
        high_str = f"{d['high']}°F" if d['high'] else "—"
        low_str = f"{d['low']}°F" if d['low'] else "—"
        
        # Calculate brackets (2-degree ranges)
        if d['high']:
            h = d['high']
            high_bracket = f"<span class='bracket-cell'>{h-1}° to {h}°</span>"
        else:
            high_bracket = "—"
        
        if d['low']:
            l = d['low']
            low_bracket = f"<span class='bracket-cell'>{l}° to {l+1}°</span>"
        else:
            low_bracket = "—"
        
        table_html += f"""
        <tr>
            <td><strong>{d['day']}</strong></td>
            <td>{d['date']}</td>
            <td>{high_str}</td>
            <td>{high_bracket}</td>
            <td>{low_str}</td>
            <td>{low_bracket}</td>
            <td>{d['status']}</td>
        </tr>
        """
    
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.caption("🔥 Orange = Your target bracket | 🟢 = Market open | 🟡 = Days until market opens")
    st.divider()

# --- EDGE ANALYSIS ---
st.subheader("🎯 Edge Analysis")
st.caption("Kalshi settlements reference NWS Daily Climate Report. Other sources are informational only.")

# --- DEBUG ---
with st.expander("🔧 Debug"):
    st.write(f"**City Config:**")
    st.json(config)
    st.write(f"**Date Suffix:** `{date_suffix}`")
    
    if st.button("Show HIGH Series Tickers"):
        markets, _ = fetch_series_markets(config["high_series"])
        for m in markets[:10]:
            st.code(f"{m.get('ticker')} — {m.get('title', '')[:50]}")
    
    if st.button("Show LOW Series Tickers"):
        markets, _ = fetch_series_markets(config["low_series"])
        for m in markets[:10]:
            st.code(f"{m.get('ticker')} — {m.get('title', '')[:50]}")

st.divider()
st.caption("BigSnapshot.com | Temp Edge Finder v3.0")
