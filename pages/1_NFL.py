def get_smart_ball_position(poss_text, possession_team, yards_to_endzone, is_home_possession, 
                            last_play, period, clock, home_team, away_team, game_key,
                            home_abbrev, away_abbrev):
    """
    Calculate ball position with smart fallbacks for scoring/between plays.
    Returns: (ball_yard, display_mode, poss_team, status_text)
    """
    last_known = st.session_state.last_ball_positions.get(game_key, {})
    
    # CASE 1: We have valid possession text (e.g., "LAR 24")
    if poss_text and possession_team:
        try:
            parts = poss_text.strip().split()
            if len(parts) >= 2:
                side_team = parts[0].upper()
                yard_line = int(parts[1])
                
                # CRITICAL FIX: Use ESPN's actual abbreviations, not KALSHI_CODES
                # ESPN uses "LAR" for Rams, while KALSHI_CODES has "LA"
                # This caused ball position mismatches
                
                # Determine ball position (0-100 scale)
                # Away endzone = 0, Home endzone = 100
                if side_team == home_abbrev.upper():
                    ball_yard = 100 - yard_line
                elif side_team == away_abbrev.upper():
                    ball_yard = yard_line
                else:
                    # Fallback if abbreviation doesn't match
                    if is_home_possession is not None and yards_to_endzone is not None:
                        ball_yard = 100 - yards_to_endzone if is_home_possession else yards_to_endzone
                    else:
                        ball_yard = last_known.get('ball_yard', 50)
