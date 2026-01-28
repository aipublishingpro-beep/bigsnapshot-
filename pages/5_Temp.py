# ============================================================
# CITY CONFIG - 6 VERIFIED KALSHI LOW TEMP MARKETS ONLY
# ============================================================
CITY_CONFIG = {
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "pattern": "midnight", "sunrise_hour": 7},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "pattern": "midnight", "sunrise_hour": 7},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "pattern": "sunrise", "sunrise_hour": 7},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "Philadelphia": {"low": "KXLOWTPHIL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
}
CITY_LIST = sorted(CITY_CONFIG.keys())
