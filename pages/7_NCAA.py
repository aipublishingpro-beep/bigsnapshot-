@st.cache_data(ttl=30)
def fetch_plays(game_id):
    if not game_id: return [], "", {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        all_plays = data.get("plays", [])
        plays = []
        for p in all_plays[-15:]:
            team_data = p.get("team", {})
            team_abbrev = ""
            if isinstance(team_data, dict):
                team_abbrev = team_data.get("abbreviation", "") or team_data.get("displayName", "")
            plays.append({"text": p.get("text", ""), "period": p.get("period", {}).get("number", 0), "clock": p.get("clock", {}).get("displayValue", ""), "score_value": p.get("scoreValue", 0), "play_type": p.get("type", {}).get("text", ""), "team": team_abbrev.upper() if team_abbrev else ""})
        poss_team = ""
        situation = data.get("situation", {})
        if situation:
            poss_text = situation.get("possessionText", "") or ""
            poss_team = poss_text.split()[0] if poss_text else ""
        half_scores = {"away": [], "home": [], "away_record": "", "home_record": "", "away_abbrev": "", "home_abbrev": ""}
        header = data.get("header", {})
        competitions = header.get("competitions", [{}])
        away_abbrev, home_abbrev = "", ""
        if competitions:
            for comp in competitions[0].get("competitors", []):
                linescores = comp.get("linescores", [])
                record = comp.get("record", [{}])
                record_str = record[0].get("summary", "") if record else ""
                team_info = comp.get("team", {})
                abbrev = team_info.get("abbreviation", "").upper()
                scores = [int(ls.get("value", 0)) for ls in linescores] if linescores else []
                if comp.get("homeAway") == "home":
                    home_abbrev = abbrev
                    half_scores["home_abbrev"] = abbrev
                    half_scores["home_record"] = record_str
                    if scores and any(s > 0 for s in scores):
                        half_scores["home"] = scores
                else:
                    away_abbrev = abbrev
                    half_scores["away_abbrev"] = abbrev
                    half_scores["away_record"] = record_str
                    if scores and any(s > 0 for s in scores):
                        half_scores["away"] = scores
        # FALLBACK: Calculate from play-by-play if ESPN didn't give linescores
        if (not half_scores["away"] or not half_scores["home"]) and all_plays:
            away_h1, away_h2, home_h1, home_h2 = 0, 0, 0, 0
            for p in all_plays:
                score_val = p.get("scoreValue", 0)
                if score_val > 0:
                    period_num = p.get("period", {}).get("number", 1)
                    team_data = p.get("team", {})
                    scoring_team = ""
                    if isinstance(team_data, dict):
                        scoring_team = team_data.get("abbreviation", "").upper()
                    if scoring_team:
                        is_home = (scoring_team == home_abbrev or home_abbrev in scoring_team or scoring_team in home_abbrev)
                        is_away = (scoring_team == away_abbrev or away_abbrev in scoring_team or scoring_team in away_abbrev)
                        if is_home:
                            if period_num == 1: home_h1 += score_val
                            else: home_h2 += score_val
                        elif is_away:
                            if period_num == 1: away_h1 += score_val
                            else: away_h2 += score_val
            if away_h1 > 0 or away_h2 > 0:
                half_scores["away"] = [away_h1, away_h2] if away_h2 > 0 else [away_h1]
            if home_h1 > 0 or home_h2 > 0:
                half_scores["home"] = [home_h1, home_h2] if home_h2 > 0 else [home_h1]
        return plays[-10:], poss_team, half_scores
    except: return [], "", {}
