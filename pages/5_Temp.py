import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

apply_styles()

# --- GOOGLE ANALYTICS G4 ---
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# --- OWNER CHECK (ONE TIME ONLY) ---
is_owner = st.session_state.get("user_type") == "Owner"
if st.query_params.get("mode") == "owner":
    is_owner = True
    st.session_state["user_type"] = "Owner"

# --- CITY CONFIG ---
CITIES = {
    "Atlanta": {"nws_office": "FFC", "nws_grid": "52,88", "high_series": "KXHIGHATL", "low_series": "KXLOWTATL"},
    "Austin": {"nws_office": "EWX", "nws_grid": "156,91", "high_series": "KXHIGHAUS", "low_series": "KXLOWTAUS"},
    "Boston": {"nws_office": "BOX", "nws_grid": "71,90", "high_series": "KXHIGHBOS", "low_series": "KXLOWTBOS"},
    "Chicago": {"nws_office": "LOT", "nws_grid": "65,76", "high_series": "KXHIGHCHI", "low_series": "KXLOWTCHI"},
    "Dallas": {"nws_office": "FWD", "nws_grid": "79,108", "high_series": "KXHIGHDAL", "low_series": "KXLOWTDAL"},
    "Denver": {"nws_office": "BOU", "nws_grid": "62,60", "high_series": "KXHIGHDEN", "low_series": "KXLOWTDEN"},
    "Houston": {"nws_office": "HGX", "nws_grid": "65,97", "high_series": "KXHIGHHOU", "low_series": "KXLOWTHOU"},
    "Los Angeles": {"nws_office": "LOX", "nws_grid": "154,44", "high_series": "KXHIGHLA", "low_series": "KXLOWTLA"},
    "Miami": {"nws_office": "MFL", "nws_grid": "109,50", "high_series": "KXHIGHMIA", "low_series": "KXLOWTMIA"},
    "New York City": {"nws_office": "OKX", "nws_grid": "33,37", "high_series": "KXHIGHNY", "low_series": "KXLOWTNYC"},
    "Philadelphia": {"nws_office": "PHI", "nws_grid": "49,75", "high_series": "KXHIGHPHL", "low_series": "KXLOWTPHL"},
    "Phoenix": {"nws_office": "PSR", "nws_grid": "161,58", "high_series": "KXHIGHPHX", "low_series": "KXLOWTPHX"},
    "San Francisco": {"nws_office": "MTR", "nws_grid": "85,105", "high_series": "KXHIGHSF", "low_series": "KXLOWTSF"},
    "Seattle": {"nws_office": "SEW", "nws_grid": "124,67", "high_series": "KXHIGHSEA", "low_series": "KXLOWTSEA"},
    "Washington DC": {"nws_office": "LWX", "nws_grid": "97,71", "high_series": "KXHIGHDC", "low_series": "KXLOWTDC"}
}

def get_date_suffix(target_date):
    return target_date.strftime("%y%b%d").upper()

def get_nws_forecast(office, grid):
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
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets"
        response = requests.get(url, params={"series_ticker": series_ticker, "limit": 100}, timeout=10)
        if response.status_code == 200:
            return response.json().get("markets", []), None
        return [], f"API {response.status_code}"
    except Exception as e:
        return [], str(e)

def find_todays_markets(markets, series_ticker, date_suffix):
    prefix = f"{series_ticker}-{date_suffix}".upper()
    found = []
    for m in markets:
        ticker = m.get("ticker", "").upper()
        if ticker.startswith(prefix):
            found.append(m)
    return found

def parse_forecast_for_date(periods, target_date):
    high, low = None, None
    for p in periods:
        temp = p.get("temperature")
        is_day = p.get("isDaytime", True)
        start_time = p.get("startTime", "")
        if start_time:
            try:
                period_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
            except:
                continue
            if period_date == target_date:
                if is_day and high is None:
                    high = temp
                elif not is_day and low is None:
                    low = temp
    return high, low

# --- HEADER ---
st.title("🌡️ Temperature Edge Finder")
st.caption("NWS Forecast vs Kalshi Markets | BigSnapshot.com")

# --- TIME ---
et = pytz.timezone("America/New_York")
now_et = datetime.now(et)
today = now_et.date()

st.caption(f"Current time: {now_et.strftime('%I:%M %p ET')} | Today: {now_et.strftime('%A, %B %d, %Y')}")

# --- CITY SELECTOR ---
st.subheader("Select City")
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

config = CITIES[city]

# --- DATE SELECTION (Owner gets 7 days, public gets today only) ---
if is_owner:
    date_options = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
    date_option = st.radio("Select Date", date_options, horizontal=True)
    day_index = date_options.index(date_option)
    target_date = today + timedelta(days=day_index)
    
    if day_index == 0:
        st.success("🟢 **MARKET OPEN** — Trade now")
    elif day_index == 1:
        st.success("🟢 **MARKET OPENS 2AM** — You see the answer first")
    else:
        st.warning(f"🟡 **MARKET OPENS IN {day_index - 1} DAYS** — Plan your position now")
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
    if update_time:
        try:
            update_dt = datetime.fromisoformat(update_time.replace("Z", "+00:00"))
            update_et = update_dt.astimezone(et)
            st.caption(f"Last NWS update: {update_et.strftime('%I:%M %p ET')}")
        except:
            pass
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔥 NWS High", f"{nws_high}°F" if nws_high else "—")
    with col2:
        st.metric("❄️ NWS Low", f"{nws_low}°F" if nws_low else "—")

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
            st.markdown("""<div style="display:flex; padding:8px 0; border-bottom:1px solid #444;">
                <div style="flex:2; font-weight:bold;">Bracket</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Chance</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Yes</div>
            </div>""", unsafe_allow_html=True)
            
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                bracket, low_temp, high_temp = title, None, None
                
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
                
                is_pick = False
                if nws_high:
                    if low_temp is not None and high_temp is not None and low_temp <= nws_high <= high_temp:
                        is_pick = True
                    elif high_temp is not None and low_temp is None and nws_high <= high_temp:
                        is_pick = True
                    elif low_temp is not None and high_temp is None and nws_high >= low_temp:
                        is_pick = True
                
                mid = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else 0
                chance = f"{mid:.0f}%" if mid > 1 else "<1%"
                yes_price = f"{yes_ask}¢" if yes_ask else "—"
                bg = "#e67e22" if is_pick else "transparent"
                txt = "#000" if is_pick else "#fff"
                
                st.markdown(f"""<div style="display:flex; padding:10px 8px; background:{bg}; border-radius:4px; margin:2px 0;">
                    <div style="flex:2; color:{txt};">{bracket}</div>
                    <div style="flex:1; text-align:center; color:{txt};">{chance}</div>
                    <div style="flex:1; text-align:center; color:{txt};">{yes_price}</div>
                </div>""", unsafe_allow_html=True)
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
            st.markdown("""<div style="display:flex; padding:8px 0; border-bottom:1px solid #444;">
                <div style="flex:2; font-weight:bold;">Bracket</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Chance</div>
                <div style="flex:1; font-weight:bold; text-align:center;">Yes</div>
            </div>""", unsafe_allow_html=True)
            
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                bracket, low_temp, high_temp = title, None, None
                
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
                
                is_pick = False
                if nws_low:
                    if low_temp is not None and high_temp is not None and low_temp <= nws_low <= high_temp:
                        is_pick = True
                    elif high_temp is not None and low_temp is None and nws_low <= high_temp:
                        is_pick = True
                    elif low_temp is not None and high_temp is None and nws_low >= low_temp:
                        is_pick = True
                
                mid = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else 0
                chance = f"{mid:.0f}%" if mid > 1 else "<1%"
                yes_price = f"{yes_ask}¢" if yes_ask else "—"
                bg = "#e67e22" if is_pick else "transparent"
                txt = "#000" if is_pick else "#fff"
                
                st.markdown(f"""<div style="display:flex; padding:10px 8px; background:{bg}; border-radius:4px; margin:2px 0;">
                    <div style="flex:2; color:{txt};">{bracket}</div>
                    <div style="flex:1; text-align:center; color:{txt};">{chance}</div>
                    <div style="flex:1; text-align:center; color:{txt};">{yes_price}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.warning("No markets for this date")

# --- 7-DAY EDGE OVERVIEW (Owner Only) ---
if is_owner:
    st.subheader("📅 7-DAY EDGE OVERVIEW")
    st.markdown("**Your weekly edge — see every bracket before markets open**")
    
    st.markdown("""<style>
    .week-table { width: 100%; border-collapse: collapse; }
    .week-table th, .week-table td { padding: 12px 8px; text-align: center; border-bottom: 1px solid #333; }
    .week-table th { background: #1a1a1a; color: #888; font-size: 12px; }
    .week-table td { font-size: 14px; }
    .bracket-cell { background: #e67e22; color: #000; border-radius: 4px; padding: 4px 8px; font-weight: bold; }
    </style>""", unsafe_allow_html=True)
    
    table_html = """<table class="week-table"><tr>
        <th>DAY</th><th>DATE</th><th>HIGH</th><th>HIGH BRACKET</th><th>LOW</th><th>LOW BRACKET</th><th>MARKET</th>
    </tr>"""
    
    for i in range(7):
        day_date = today + timedelta(days=i)
        day_high, day_low = parse_forecast_for_date(periods, day_date)
        status = "🟢 OPEN" if i == 0 else ("🟢 2AM" if i == 1 else f"🟡 {i-1}d")
        
        high_str = f"{day_high}°F" if day_high else "—"
        low_str = f"{day_low}°F" if day_low else "—"
        high_bracket = f"<span class='bracket-cell'>{day_high-1}° to {day_high}°</span>" if day_high else "—"
        low_bracket = f"<span class='bracket-cell'>{day_low}° to {day_low+1}°</span>" if day_low else "—"
        
        table_html += f"""<tr>
            <td><strong>{day_date.strftime('%a')}</strong></td>
            <td>{day_date.strftime('%b %d')}</td>
            <td>{high_str}</td><td>{high_bracket}</td>
            <td>{low_str}</td><td>{low_bracket}</td>
            <td>{status}</td>
        </tr>"""
    
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.caption("🔥 Orange = Your target bracket | 🟢 = Market open | 🟡 = Days until market opens")

# --- HOW TO USE DOCUMENTATION ---
st.divider()
with st.expander("📖 How to Use Temp Edge Finder", expanded=False):
    st.markdown("""
**🌡️ Reading the Forecast:**
- **NWS High/Low** = Official National Weather Service forecast
- **Kalshi Markets** = Live prediction market prices
- **Orange Highlight** = Where NWS predicts temp will land (your target)

**📊 Understanding the Markets:**
- **Bracket** = Temperature range (e.g., 45 to 46)
- **Chance** = Market implied probability
- **Yes** = Cost to buy YES contract (pays $1 if correct)

**🏙️ 15 Cities Available:** Atlanta, Austin, Boston, Chicago, Dallas, Denver, Houston, Los Angeles, Miami, New York City, Philadelphia, Phoenix, San Francisco, Seattle, Washington DC

**💡 Pro Tips:**
- NWS updates forecasts ~4x daily. Trade right after update.
- Volatile weather (Denver, Chicago) = bigger edge
- Check all 15 cities for best opportunities
""")

# --- FOOTER ---
st.divider()
st.caption("⚠️ Entertainment only. Not financial advice. v3.1")
st.caption("BigSnapshot.com | Temp Edge Finder")
