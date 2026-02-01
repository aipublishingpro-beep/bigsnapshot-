@st.cache_data(ttl=25)
def fetch_plays_and_linescores(game_id, known_away="", known_home=""):
    """Fetch plays AND period-by-period scoring - NCAA ENHANCED v12.0"""
    if not game_id: 
        return [], "", {}, []
    
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        # ============================================================
        # PART A: GET PLAYS (existing - works fine)
        # ============================================================
        all_plays = data.get("plays", [])
        plays = []
        for p in all_plays[-15:]:
            team_data = p.get("team", {})
            team_abbrev = ""
            if isinstance(team_data, dict):
                team_abbrev = team_data.get("abbreviation", "") or team_data.get("displayName", "")
            plays.append({
                "text": p.get("text", ""),
                "period": p.get("period", {}).get("number", 0),
                "clock": p.get("clock", {}).get("displayValue", ""),
                "score_value": p.get("scoreValue", 0),
                "play_type": p.get("type", {}).get("text", ""),
                "team": team_abbrev.upper() if team_abbrev else ""
            })
        
        # ============================================================
        # PART B: GET POSSESSION (existing - works fine)
        # ============================================================
        poss_team = ""
        situation = data.get("situation", {})
        if situation:
            poss_text = situation.get("possessionText", "") or ""
            poss_team = poss_text.split()[0] if poss_text else ""
        
        # ============================================================
        # PART C: GET RECORDS (existing - works fine)
        # ============================================================
        half_scores = {"away_record": "", "home_record": ""}
        header = data.get("header", {})
        competitions = header.get("competitions", [{}])
        if competitions:
            for comp in competitions[0].get("competitors", []):
                record = comp.get("record", [{}])
                record_str = record[0].get("summary", "") if record else ""
                if comp.get("homeAway") == "home":
                    half_scores["home_record"] = record_str
                else:
                    half_scores["away_record"] = record_str
        
        # ============================================================
        # PART D: GET PERIOD SCORES - **THIS IS THE FIX**
        # ============================================================
        linescores = []
        away_line = []
        home_line = []
        
        # PATH 1: boxscore.teams[].statistics[] 
        # This is the MOST RELIABLE source for NCAA period scores
        box_score = data.get("boxscore", {})
        teams = box_score.get("teams", [])
        
        for team in teams:
            team_ha = team.get("homeAway", "")
            team_stats = team.get("statistics", [])
            
            # Look for linescores in statistics array
            for stat_group in team_stats:
                if stat_group.get("name") == "linescores":
                    line = []
                    for period_stat in stat_group.get("stats", []):
                        try:
                            val = period_stat.get("value", 0)
                            line.append(int(float(val)) if val else 0)
                        except:
                            line.append(0)
                    
                    if team_ha == "home":
                        home_line = line
                    else:
                        away_line = line
                    break
        
        # PATH 2: header.competitions[].competitors[].linescores[]
        # Backup path if PATH 1 fails
        if not away_line and not home_line and competitions:
            for comp in competitions[0].get("competitors", []):
                comp_linescores = comp.get("linescores", [])
                if comp_linescores:
                    line = []
                    for ls in comp_linescores:
                        try:
                            val = ls.get("value", 0)
                            line.append(int(float(val)) if val else 0)
                        except:
                            line.append(0)
                    
                    if comp.get("homeAway") == "home":
                        home_line = line
                    else:
                        away_line = line
        
        # Build final linescores array
        # Format: [{"period": "H1", "away": 40, "home": 35}, {"period": "H2", "away": 50, "home": 28}]
        max_periods = max(len(away_line), len(home_line))
        if max_periods > 0:
            for i in range(max_periods):
                period_name = f"H{i+1}" if i < 2 else f"OT{i-1}"
                away_pts = away_line[i] if i < len(away_line) else 0
                home_pts = home_line[i] if i < len(home_line) else 0
                linescores.append({
                    "period": period_name,
                    "away": away_pts,
                    "home": home_pts
                })
        
        return plays[-10:], poss_team, half_scores, linescores
        
    except Exception as e:
        # Return empty data on error - won't crash the app
        return [], "", {}, []
        def render_scoreboard_ncaa(away_abbrev, home_abbrev, away_score, home_score, period, clock, half_scores, linescores):
    """Render scoreboard with half-by-half breakdown - NCAA v12.0 ENHANCED"""
    away_color = TEAM_COLORS.get(away_abbrev, "#666")
    home_color = TEAM_COLORS.get(home_abbrev, "#666")
    away_record = half_scores.get("away_record", "")
    home_record = half_scores.get("home_record", "")
    period_text = f"H{period}" if period <= 2 else f"OT{period-2}"
    
    # ============================================================
    # FALLBACK: No period scores available yet
    # ============================================================
    if not linescores or len(linescores) == 0:
        return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
        <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
        <table style="width:100%;border-collapse:collapse;color:#fff">
        <tr style="border-bottom:2px solid #333">
            <td style="padding:16px;text-align:left;width:70%">
                <span style="color:{away_color};font-weight:bold;font-size:28px">{away_abbrev}</span>
                <span style="color:#666;font-size:14px;margin-left:12px">{away_record}</span>
            </td>
            <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{away_score}</td>
        </tr>
        <tr>
            <td style="padding:16px;text-align:left;width:70%">
                <span style="color:{home_color};font-weight:bold;font-size:28px">{home_abbrev}</span>
                <span style="color:#666;font-size:14px;margin-left:12px">{home_record}</span>
            </td>
            <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{home_score}</td>
        </tr>
        </table>
        <div style="text-align:center;color:#888;font-size:12px;margin-top:12px">⏳ Period scores loading...</div>
        </div>'''
    
    # ============================================================
    # FULL SCOREBOARD: With H1, H2, OT breakdown
    # ============================================================
    
    # Build dynamic period headers (H1, H2, OT1, OT2, etc.)
    period_headers = ""
    away_period_scores = ""
    home_period_scores = ""
    
    for ls in linescores:
        period_headers += f'<th style="padding:8px;text-align:center;color:#888;font-size:14px">{ls["period"]}</th>'
        away_period_scores += f'<td style="padding:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold">{ls["away"]}</td>'
        home_period_scores += f'<td style="padding:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold">{ls["home"]}</td>'
    
    # Render full table with period breakdown
    return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
    <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
    <table style="width:100%;border-collapse:collapse;color:#fff">
    <thead>
        <tr style="border-bottom:1px solid #333">
            <th style="padding:8px;text-align:left;width:35%;color:#888;font-size:14px">TEAM</th>
            {period_headers}
            <th style="padding:8px;text-align:center;color:#ffd700;font-size:16px;font-weight:bold">TOTAL</th>
        </tr>
    </thead>
    <tbody>
    <tr style="border-bottom:2px solid #333">
        <td style="padding:16px;text-align:left">
            <span style="color:{away_color};font-weight:bold;font-size:24px">{away_abbrev}</span>
            <span style="color:#666;font-size:12px;margin-left:8px">{away_record}</span>
        </td>
        {away_period_scores}
        <td style="padding:16px;text-align:center;font-weight:bold;font-size:42px;color:#fff">{away_score}</td>
    </tr>
    <tr>
        <td style="padding:16px;text-align:left">
            <span style="color:{home_color};font-weight:bold;font-size:24px">{home_abbrev}</span>
            <span style="color:#666;font-size:12px;margin-left:8px">{home_record}</span>
        </td>
        {home_period_scores}
        <td style="padding:16px;text-align:center;font-weight:bold;font-size:42px;color:#fff">{home_score}</td>
    </tr>
    </tbody>
    </table></div>'''
