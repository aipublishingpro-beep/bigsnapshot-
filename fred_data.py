# FILE: fred_data.py
# FRED API Integration for BigSnapshot Economics Page
# v3.0 - Optimized signal generation logic

import requests
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "fed_rate_upper": "DFEDTARU",
    "fed_rate_lower": "DFEDTARL",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "unemployment": "UNRATE",
    "gdp_growth": "A191RL1Q225SBEA",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "jobless_claims": "ICSA",
}

FALLBACKS = {
    "fed_rate": "4.25%-4.50%",
    "unemployment": "4.2%",
    "gdp_growth": "2.5%",
    "cpi_yoy": "2.7%",
}

# ============================================================
# THRESHOLDS (Based on historical norms)
# ============================================================
THRESHOLDS = {
    # Jobless claims
    "claims_low": 200000,
    "claims_normal": 225000,
    "claims_elevated": 260000,
    "claims_high": 300000,
    "claims_weekly_change_significant": 10000,
    
    # CPI
    "cpi_mom_hot": 0.3,
    "cpi_mom_target": 0.17,
    "cpi_mom_cool": 0.1,
    
    # Unemployment
    "unemp_low": 4.0,
    "unemp_normal": 4.5,
    "unemp_elevated": 5.0,
    
    # GDP
    "gdp_strong": 3.0,
    "gdp_trend": 2.0,
    "gdp_weak": 1.0,
    "gdp_recession": 0,
    
    # Yield curve
    "spread_inverted_deep": -0.5,
    "spread_inverted": 0,
    "spread_flat": 0.25,
    "spread_normal": 1.0,
}

# ============================================================
# API FUNCTIONS
# ============================================================
def get_api_key():
    try:
        return st.secrets["FRED_API_KEY"]
    except:
        return "YOUR_KEY_HERE"

@st.cache_data(ttl=3600)
def fetch_fred_series(series_id, limit=1):
    try:
        params = {
            "series_id": series_id,
            "api_key": get_api_key(),
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                value = obs.get('value', 'N/A')
                if value == '.':
                    return None
                return {"value": value, "date": obs.get('date', 'N/A')}
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def fetch_fred_series_multiple(series_id, limit=13):
    try:
        params = {
            "series_id": series_id,
            "api_key": get_api_key(),
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                return data['observations']
        return None
    except Exception:
        return None

# ============================================================
# BASIC DATA GETTERS
# ============================================================
def get_fed_rate():
    upper = fetch_fred_series(SERIES["fed_rate_upper"])
    lower = fetch_fred_series(SERIES["fed_rate_lower"])
    
    if upper and lower:
        try:
            u = float(upper['value'])
            l = float(lower['value'])
            return {"value": f"{l:.2f}%-{u:.2f}%", "upper": u, "lower": l, "date": upper['date']}
        except:
            pass
    return {"value": FALLBACKS["fed_rate"], "upper": 4.50, "lower": 4.25, "date": "N/A"}

def get_unemployment():
    data = fetch_fred_series(SERIES["unemployment"])
    if data:
        try:
            return {"value": f"{float(data['value']):.1f}%", "raw": float(data['value']), "date": data['date']}
        except:
            pass
    return {"value": FALLBACKS["unemployment"], "raw": 4.2, "date": "N/A"}

def get_gdp_growth():
    data = fetch_fred_series(SERIES["gdp_growth"])
    if data:
        try:
            return {"value": f"{float(data['value']):.1f}%", "raw": float(data['value']), "date": data['date']}
        except:
            pass
    return {"value": FALLBACKS["gdp_growth"], "raw": 2.5, "date": "N/A"}

def get_cpi_yoy():
    observations = fetch_fred_series_multiple(SERIES["cpi"], limit=13)
    if observations and len(observations) >= 13:
        try:
            current = float(observations[0]['value'])
            year_ago = float(observations[12]['value'])
            yoy_change = ((current - year_ago) / year_ago) * 100
            return {
                "value": f"{yoy_change:.1f}%",
                "raw": yoy_change,
                "date": observations[0]['date'],
                "current_cpi": current,
                "year_ago_cpi": year_ago
            }
        except:
            pass
    return {"value": FALLBACKS["cpi_yoy"], "raw": 2.7, "date": "N/A"}

def get_treasury_spread():
    t10 = fetch_fred_series(SERIES["treasury_10y"])
    t2 = fetch_fred_series(SERIES["treasury_2y"])
    
    if t10 and t2:
        try:
            t10_val = float(t10['value'])
            t2_val = float(t2['value'])
            spread = t10_val - t2_val
            return {
                "spread": f"{spread:.2f}%",
                "raw": spread,
                "inverted": spread < 0,
                "t10": t10_val,
                "t2": t2_val,
                "date": t10['date']
            }
        except:
            pass
    return None

def get_jobless_claims():
    data = fetch_fred_series(SERIES["jobless_claims"])
    if data:
        try:
            claims = int(float(data['value']))
            return {"value": f"{claims:,}", "raw": claims, "date": data['date']}
        except:
            pass
    return None

# ============================================================
# TREND ANALYSIS FUNCTIONS
# ============================================================
def get_jobless_claims_trend():
    observations = fetch_fred_series_multiple(SERIES["jobless_claims"], limit=7)
    if not observations or len(observations) < 6:
        return None
    
    try:
        weeks = []
        for i in range(min(6, len(observations))):
            val = observations[i]['value']
            if val != '.':
                weeks.append({"value": int(float(val)), "date": observations[i]['date']})
        
        if len(weeks) < 5:
            return None
        
        changes = []
        for i in range(len(weeks) - 1):
            change = weeks[i]['value'] - weeks[i+1]['value']
            changes.append(change)
        
        consecutive_up = 0
        consecutive_down = 0
        
        for change in changes:
            if change > 0:
                if consecutive_down == 0:
                    consecutive_up += 1
                else:
                    break
            elif change < 0:
                if consecutive_up == 0:
                    consecutive_down += 1
                else:
                    break
            else:
                break
        
        current_4wk_avg = sum(w['value'] for w in weeks[:4]) / 4
        newest = weeks[0]['value']
        oldest = weeks[-1]['value']
        total_change = newest - oldest
        
        if consecutive_up >= 3 or (consecutive_up >= 2 and total_change > THRESHOLDS['claims_weekly_change_significant'] * 2):
            trend = "RISING"
            strength = "strong" if consecutive_up >= 4 or total_change > THRESHOLDS['claims_weekly_change_significant'] * 3 else "moderate"
        elif consecutive_down >= 3 or (consecutive_down >= 2 and total_change < -THRESHOLDS['claims_weekly_change_significant'] * 2):
            trend = "FALLING"
            strength = "strong" if consecutive_down >= 4 or total_change < -THRESHOLDS['claims_weekly_change_significant'] * 3 else "moderate"
        else:
            trend = "MIXED"
            strength = "weak"
        
        if newest < THRESHOLDS['claims_low']:
            level = "VERY_LOW"
            level_desc = "Claims very low - tight labor market"
        elif newest < THRESHOLDS['claims_normal']:
            level = "LOW"
            level_desc = "Claims below normal - healthy labor market"
        elif newest < THRESHOLDS['claims_elevated']:
            level = "NORMAL"
            level_desc = "Claims in normal range"
        elif newest < THRESHOLDS['claims_high']:
            level = "ELEVATED"
            level_desc = "Claims elevated - some labor softening"
        else:
            level = "HIGH"
            level_desc = "Claims high - significant labor weakness"
        
        return {
            "trend": trend,
            "strength": strength,
            "level": level,
            "level_desc": level_desc,
            "weeks": weeks,
            "changes": changes,
            "total_change": total_change,
            "consecutive_up": consecutive_up,
            "consecutive_down": consecutive_down,
            "four_week_avg": round(current_4wk_avg),
            "latest": newest,
            "latest_date": weeks[0]['date']
        }
    except Exception:
        return None

def get_cpi_momentum():
    observations = fetch_fred_series_multiple(SERIES["cpi"], limit=5)
    if not observations or len(observations) < 5:
        return None
    
    try:
        mom_changes = []
        for i in range(4):
            current = float(observations[i]['value'])
            previous = float(observations[i+1]['value'])
            mom_pct = ((current - previous) / previous) * 100
            mom_changes.append({"value": round(mom_pct, 3), "date": observations[i]['date']})
        
        latest_mom = mom_changes[0]['value']
        prev_mom = mom_changes[1]['value']
        avg_3mo = sum(m['value'] for m in mom_changes[:3]) / 3
        avg_4mo = sum(m['value'] for m in mom_changes) / 4
        
        recent_avg = (mom_changes[0]['value'] + mom_changes[1]['value']) / 2
        older_avg = (mom_changes[2]['value'] + mom_changes[3]['value']) / 2
        
        if recent_avg > older_avg + 0.05:
            direction = "ACCELERATING"
        elif recent_avg < older_avg - 0.05:
            direction = "DECELERATING"
        else:
            direction = "STABLE"
        
        target_mom = THRESHOLDS['cpi_mom_target']
        
        if avg_3mo > THRESHOLDS['cpi_mom_hot']:
            level = "HOT"
            level_desc = f"Running hot ({avg_3mo:.2f}% avg MoM = {avg_3mo*12:.1f}% annualized)"
        elif avg_3mo > target_mom + 0.05:
            level = "ABOVE_TARGET"
            level_desc = f"Above 2% target ({avg_3mo:.2f}% avg MoM = {avg_3mo*12:.1f}% annualized)"
        elif avg_3mo > THRESHOLDS['cpi_mom_cool']:
            level = "AT_TARGET"
            level_desc = f"Near 2% target ({avg_3mo:.2f}% avg MoM = {avg_3mo*12:.1f}% annualized)"
        else:
            level = "COOL"
            level_desc = f"Running cool ({avg_3mo:.2f}% avg MoM = {avg_3mo*12:.1f}% annualized)"
        
        months_above_target = sum(1 for m in mom_changes if m['value'] > target_mom)
        consistency = "consistent" if months_above_target >= 3 or months_above_target <= 1 else "mixed"
        
        return {
            "direction": direction,
            "level": level,
            "level_desc": level_desc,
            "consistency": consistency,
            "latest_mom": latest_mom,
            "prev_mom": prev_mom,
            "avg_3mo": round(avg_3mo, 3),
            "avg_4mo": round(avg_4mo, 3),
            "annualized_3mo": round(avg_3mo * 12, 1),
            "months_above_target": months_above_target,
            "mom_history": mom_changes,
            "date": mom_changes[0]['date']
        }
    except Exception:
        return None

def get_unemployment_trend():
    observations = fetch_fred_series_multiple(SERIES["unemployment"], limit=5)
    if not observations or len(observations) < 4:
        return None
    
    try:
        months = []
        for i in range(min(4, len(observations))):
            val = observations[i]['value']
            if val != '.':
                months.append({"value": float(val), "date": observations[i]['date']})
        
        if len(months) < 3:
            return None
        
        latest = months[0]['value']
        three_months_ago = months[-1]['value']
        change = latest - three_months_ago
        
        mom_changes = [months[i]['value'] - months[i+1]['value'] for i in range(len(months)-1)]
        consecutive_up = sum(1 for c in mom_changes if c > 0)
        
        if change > 0.4 or (change > 0.2 and consecutive_up >= 2):
            trend = "RISING_FAST"
            direction = "deteriorating rapidly"
        elif change > 0.2:
            trend = "RISING"
            direction = "softening"
        elif change < -0.3:
            trend = "FALLING_FAST"
            direction = "improving rapidly"
        elif change < -0.1:
            trend = "FALLING"
            direction = "improving"
        else:
            trend = "STABLE"
            direction = "steady"
        
        if latest < THRESHOLDS['unemp_low']:
            level = "LOW"
        elif latest < THRESHOLDS['unemp_normal']:
            level = "NORMAL"
        elif latest < THRESHOLDS['unemp_elevated']:
            level = "ELEVATED"
        else:
            level = "HIGH"
        
        return {
            "trend": trend,
            "direction": direction,
            "level": level,
            "latest": latest,
            "three_months_ago": three_months_ago,
            "change": round(change, 2),
            "months": months,
            "consecutive_up": consecutive_up,
            "date": months[0]['date']
        }
    except Exception:
        return None

def get_yield_curve_signal():
    spread_data = get_treasury_spread()
    if not spread_data:
        return None
    
    spread = spread_data['raw']
    
    if spread < THRESHOLDS['spread_inverted_deep']:
        signal = "DEEPLY_INVERTED"
        severity = "high"
        implication = "Deep inversion historically precedes recessions by 12-18 months"
    elif spread < THRESHOLDS['spread_inverted']:
        signal = "INVERTED"
        severity = "elevated"
        implication = "Yield curve inverted - markets pricing slower growth"
    elif spread < THRESHOLDS['spread_flat']:
        signal = "FLAT"
        severity = "caution"
        implication = "Yield curve flat - transition period, watch closely"
    elif spread < THRESHOLDS['spread_normal']:
        signal = "NORMAL"
        severity = "neutral"
        implication = "Normal yield curve - no recession signal"
    else:
        signal = "STEEP"
        severity = "growth"
        implication = "Steep curve - markets expect strong growth"
    
    return {
        "signal": signal,
        "severity": severity,
        "implication": implication,
        "spread": spread,
        "spread_display": spread_data['spread'],
        "t10": spread_data['t10'],
        "t2": spread_data['t2'],
        "inverted": spread_data['inverted'],
        "date": spread_data['date']
    }

def get_gdp_signal():
    gdp = get_gdp_growth()
    if not gdp or gdp.get('date') == 'N/A':
        return None
    
    growth = gdp['raw']
    
    if growth < THRESHOLDS['gdp_recession']:
        level = "CONTRACTION"
        implication = "Economy contracting - recession risk elevated"
    elif growth < THRESHOLDS['gdp_weak']:
        level = "WEAK"
        implication = "Growth weak - below trend, watch for further slowing"
    elif growth < THRESHOLDS['gdp_trend']:
        level = "BELOW_TREND"
        implication = "Growth below trend but positive"
    elif growth < THRESHOLDS['gdp_strong']:
        level = "TREND"
        implication = "Growth near trend - healthy economy"
    else:
        level = "STRONG"
        implication = "Growth strong - may support hawkish Fed"
    
    return {
        "level": level,
        "implication": implication,
        "growth": growth,
        "growth_display": gdp['value'],
        "date": gdp['date']
    }

# ============================================================
# EDGE SIGNAL GENERATOR
# ============================================================
def generate_edge_signals():
    signals = []
    
    # 1. JOBLESS CLAIMS SIGNAL
    claims = get_jobless_claims_trend()
    if claims:
        if claims['trend'] == "RISING":
            if claims['consecutive_up'] >= 4 or (claims['consecutive_up'] >= 3 and claims['level'] in ['ELEVATED', 'HIGH']):
                strength = "STRONG"
            elif claims['consecutive_up'] >= 3 or claims['level'] in ['ELEVATED', 'HIGH']:
                strength = "MODERATE"
            else:
                strength = "WATCH"
            
            week_display = " → ".join([f"{w['value']:,}" for w in reversed(claims['weeks'][:4])])
            
            signals.append({
                "id": "claims_rising",
                "title": "Labor Market Softening",
                "subtitle": "Unemployment ABOVE contracts may have value",
                "strength": strength,
                "color": "#ff6b35" if strength == "STRONG" else "#ffcc00" if strength == "MODERATE" else "#4a9eff",
                "market": "Unemployment Rate",
                "direction": "ABOVE",
                "data_points": [
                    f"Claims rising {claims['consecutive_up']} consecutive weeks",
                    f"Trend: {week_display}",
                    f"Current level: {claims['latest']:,} ({claims['level_desc']})",
                    f"4-week avg: {claims['four_week_avg']:,}"
                ],
                "implication": "Rising claims typically lead unemployment rate increases by 1-2 months. If claims continue rising, ABOVE contracts may be underpriced.",
                "kalshi_market": "economics",
                "latest_data": f"{claims['latest']:,}",
                "data_date": claims['latest_date']
            })
        
        elif claims['trend'] == "FALLING":
            if claims['consecutive_down'] >= 4 or (claims['consecutive_down'] >= 3 and claims['level'] in ['LOW', 'VERY_LOW']):
                strength = "MODERATE"
            elif claims['consecutive_down'] >= 3:
                strength = "WATCH"
            else:
                strength = None
            
            if strength:
                week_display = " → ".join([f"{w['value']:,}" for w in reversed(claims['weeks'][:4])])
                
                signals.append({
                    "id": "claims_falling",
                    "title": "Labor Market Tightening",
                    "subtitle": "Unemployment BELOW contracts may have value",
                    "strength": strength,
                    "color": "#4ade80" if strength == "MODERATE" else "#4a9eff",
                    "market": "Unemployment Rate",
                    "direction": "BELOW",
                    "data_points": [
                        f"Claims falling {claims['consecutive_down']} consecutive weeks",
                        f"Trend: {week_display}",
                        f"Current level: {claims['latest']:,} ({claims['level_desc']})"
                    ],
                    "implication": "Falling claims suggest labor market resilience. BELOW contracts may be underpriced if trend continues.",
                    "kalshi_market": "economics",
                    "latest_data": f"{claims['latest']:,}",
                    "data_date": claims['latest_date']
                })
    
    # 2. CPI MOMENTUM SIGNAL
    cpi = get_cpi_momentum()
    if cpi:
        if cpi['direction'] == "ACCELERATING" and cpi['level'] in ['HOT', 'ABOVE_TARGET']:
            strength = "STRONG" if cpi['consistency'] == 'consistent' else "MODERATE"
            
            mom_display = " → ".join([f"{m['value']:.2f}%" for m in reversed(cpi['mom_history'])])
            
            signals.append({
                "id": "cpi_hot",
                "title": "Inflation Running Hot",
                "subtitle": "CPI ABOVE contracts may have value",
                "strength": strength,
                "color": "#ff6b35" if strength == "STRONG" else "#ffcc00",
                "market": "CPI Inflation",
                "direction": "ABOVE",
                "data_points": [
                    f"CPI MoM {cpi['direction'].lower()}: {mom_display}",
                    f"3-month avg: {cpi['avg_3mo']:.2f}% MoM ({cpi['annualized_3mo']}% annualized)",
                    f"{cpi['months_above_target']}/4 months above Fed's 2% target pace",
                    f"{cpi['level_desc']}"
                ],
                "implication": "Inflation momentum building. If trend persists, next CPI print may surprise to upside. ABOVE contracts may be underpriced.",
                "kalshi_market": "cpi",
                "latest_data": f"{cpi['latest_mom']:.2f}% MoM",
                "data_date": cpi['date']
            })
        
        elif cpi['direction'] == "DECELERATING" and cpi['level'] in ['COOL', 'AT_TARGET']:
            strength = "MODERATE" if cpi['consistency'] == 'consistent' else "WATCH"
            
            mom_display = " → ".join([f"{m['value']:.2f}%" for m in reversed(cpi['mom_history'])])
            
            signals.append({
                "id": "cpi_cooling",
                "title": "Inflation Cooling",
                "subtitle": "CPI BELOW contracts may have value",
                "strength": strength,
                "color": "#4ade80" if strength == "MODERATE" else "#4a9eff",
                "market": "CPI Inflation",
                "direction": "BELOW",
                "data_points": [
                    f"CPI MoM {cpi['direction'].lower()}: {mom_display}",
                    f"3-month avg: {cpi['avg_3mo']:.2f}% MoM ({cpi['annualized_3mo']}% annualized)",
                    f"Only {cpi['months_above_target']}/4 months above Fed's 2% target pace",
                    f"{cpi['level_desc']}"
                ],
                "implication": "Inflation momentum fading. Next CPI print may come in soft. BELOW contracts may be underpriced.",
                "kalshi_market": "cpi",
                "latest_data": f"{cpi['latest_mom']:.2f}% MoM",
                "data_date": cpi['date']
            })
    
    # 3. YIELD CURVE SIGNAL
    yc = get_yield_curve_signal()
    if yc:
        if yc['signal'] in ["INVERTED", "DEEPLY_INVERTED"]:
            strength = "STRONG" if yc['signal'] == "DEEPLY_INVERTED" else "MODERATE"
            
            signals.append({
                "id": "yield_curve",
                "title": "Yield Curve Warning",
                "subtitle": "Recession YES / More Fed Cuts may have value",
                "strength": strength,
                "color": "#ff6b6b",
                "market": "Fed Rate / Recession",
                "direction": "MORE CUTS / RECESSION YES",
                "data_points": [
                    f"10Y-2Y Spread: {yc['spread_display']}",
                    f"10Y Treasury: {yc['t10']:.2f}%",
                    f"2Y Treasury: {yc['t2']:.2f}%",
                    f"Signal: {yc['signal'].replace('_', ' ')}"
                ],
                "implication": yc['implication'] + " Markets pricing more cuts or recession probability may be underpriced.",
                "kalshi_market": "fed_rate",
                "latest_data": yc['spread_display'],
                "data_date": yc['date']
            })
    
    # 4. UNEMPLOYMENT TREND SIGNAL
    unemp = get_unemployment_trend()
    if unemp:
        if unemp['trend'] in ["RISING", "RISING_FAST"]:
            strength = "STRONG" if unemp['trend'] == "RISING_FAST" else "MODERATE"
            
            signals.append({
                "id": "unemployment_rising",
                "title": "Unemployment Rising",
                "subtitle": "Fed Cuts / Unemployment ABOVE may have value",
                "strength": strength,
                "color": "#ff6b35" if strength == "STRONG" else "#ffcc00",
                "market": "Fed Decision / Unemployment",
                "direction": "CUTS / ABOVE",
                "data_points": [
                    f"Unemployment: {unemp['three_months_ago']:.1f}% → {unemp['latest']:.1f}%",
                    f"3-month change: +{unemp['change']:.1f}%",
                    f"Trend: {unemp['direction']}"
                ],
                "implication": "Rising unemployment supports Fed cut narrative. Watch for dovish pivot in FOMC language.",
                "kalshi_market": "fed_decision",
                "latest_data": f"{unemp['latest']:.1f}%",
                "data_date": unemp['date']
            })
    
    # 5. GDP SIGNAL
    gdp_sig = get_gdp_signal()
    if gdp_sig:
        if gdp_sig['level'] in ["CONTRACTION", "WEAK"]:
            strength = "STRONG" if gdp_sig['level'] == "CONTRACTION" else "MODERATE"
            
            signals.append({
                "id": "gdp_weak",
                "title": "Growth Weakening",
                "subtitle": "Recession YES / Fed Cuts may have value",
                "strength": strength,
                "color": "#ff6b6b" if strength == "STRONG" else "#ffcc00",
                "market": "Recession / Fed",
                "direction": "RECESSION YES / CUTS",
                "data_points": [
                    f"GDP Growth: {gdp_sig['growth_display']}",
                    f"Level: {gdp_sig['level']}",
                ],
                "implication": gdp_sig['implication'],
                "kalshi_market": "economics",
                "latest_data": gdp_sig['growth_display'],
                "data_date": gdp_sig['date']
            })
        elif gdp_sig['level'] == "STRONG":
            signals.append({
                "id": "gdp_strong",
                "title": "Growth Running Strong",
                "subtitle": "Fed HOLD / Recession NO may have value",
                "strength": "WATCH",
                "color": "#4ade80",
                "market": "Fed / Recession",
                "direction": "HOLD / RECESSION NO",
                "data_points": [
                    f"GDP Growth: {gdp_sig['growth_display']}",
                    f"Level: {gdp_sig['level']}",
                ],
                "implication": gdp_sig['implication'],
                "kalshi_market": "fed_decision",
                "latest_data": gdp_sig['growth_display'],
                "data_date": gdp_sig['date']
            })
    
    # Sort by strength
    strength_order = {"STRONG": 0, "MODERATE": 1, "WATCH": 2}
    signals.sort(key=lambda x: strength_order.get(x['strength'], 3))
    
    return signals

# ============================================================
# DISPLAY HELPERS
# ============================================================
def get_indicator_color(indicator, value):
    if indicator == "unemployment":
        if value < THRESHOLDS['unemp_low']:
            return "#4ade80"
        elif value < THRESHOLDS['unemp_normal']:
            return "#4ade80"
        elif value < THRESHOLDS['unemp_elevated']:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    elif indicator == "cpi_yoy":
        if value < 2.0:
            return "#4a9eff"
        elif value < 2.5:
            return "#4ade80"
        elif value < 3.5:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    elif indicator == "gdp_growth":
        if value > THRESHOLDS['gdp_trend']:
            return "#4ade80"
        elif value > THRESHOLDS['gdp_weak']:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    return "#4a9eff"

def get_all_indicators():
    return {
        "fed_rate": get_fed_rate(),
        "unemployment": get_unemployment(),
        "gdp_growth": get_gdp_growth(),
        "cpi_yoy": get_cpi_yoy(),
        "treasury_spread": get_treasury_spread(),
        "jobless_claims": get_jobless_claims(),
    }
