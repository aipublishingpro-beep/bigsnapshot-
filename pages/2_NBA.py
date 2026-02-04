st.divider()

# ───────────────────────────────────────────────
# SECRET SAUCE EARLY EDGE (only shows games with real edge)
# ───────────────────────────────────────────────
st.subheader("🔥 SECRET SAUCE EARLY EDGE")
st.caption("Shows only games with strong early momentum at 12+ min • Pace + Net Rating • Better entry prices")

secret_sauce = []
for g in live_games:
    mins = g.get('minutes_played', 0)
    if mins < 12 or mins > 18:  # Sweet spot: ~Q1 end / early Q2
        continue
    
    # Reuse your existing Net Rating function
    h_ortg, a_ortg, net_rating, poss = calculate_net_rating(g)
    if poss < 22:  # Minimum for early signal (avoids noise)
        continue
    
    pace = g['total_score'] / mins if mins > 0 else 0
    pace_label, pace_color = get_pace_label(pace)
    pace_dev = pace - 4.7  # League avg ~4.7 pts/min
    
    leader = g['home'] if g['home_score'] > g['away_score'] else g['away'] if g['away_score'] > g['home_score'] else None
    if not leader:
        continue  # Skip ties/no leader
    
    signal_text = ""
    confidence = ""
    stars = ""
    conf_color = "#22c55e"
    
    # Stricter early thresholds for high-conviction only
    if net_rating >= 16:
        if net_rating >= 20:
            confidence = "SECRET SAUCE"
            stars = "⭐⭐⭐"
        elif net_rating >= 18:
            confidence = "STRONG"
            stars = "⭐⭐"
        else:
            confidence = "GOOD"
            stars = "⭐"
        
        totals_side = ""
        if pace_dev >= 0.3:
            totals_side = " + OVER"
        elif pace_dev <= -0.3:
            totals_side = " + UNDER"
        
        signal_text = f"🔒 BUY **{leader}** YES{totals_side}"
    
    if signal_text:
        kalshi_link = get_kalshi_game_link(g['away'], g['home'])
        secret_sauce.append({
            "game": f"{g['away']} @ {g['home']}",
            "mins": mins,
            "net": net_rating,
            "pace": pace,
            "pace_label": pace_label,
            "poss": poss,
            "signal": signal_text,
            "stars": stars,
            "confidence": confidence,
            "conf_color": conf_color,
            "link": kalshi_link
        })

if secret_sauce:
    for s in sorted(secret_sauce, key=lambda x: -x['net']):  # Strongest first
        st.markdown(f"""
        <div style="background:#0f172a;padding:16px;border-radius:12px;border:3px solid {s['conf_color']};margin-bottom:16px">
            <div style="font-size:22px;font-weight:bold;color:#ffd700">{s['game']}</div>
            <div style="font-size:28px;margin:8px 0">{s['signal']} {s['stars']}</div>
            <div style="color:#ccc">
                Net Rating: <b>{s['net']}</b> 
                Pace: <span style="color:{s['pace_label'][1] if isinstance(s['pace_label'], tuple) else '#fff'}">{s['pace_label']}</span> ({s['pace']:.1f}/min) 
                Poss: <b>{s['poss']}</b>
            </div>
            <div style="margin-top:12px;color:{s['conf_color']};font-weight:bold">{s['confidence']}</div>
            <a href="{s['link']}" target="_blank" style="background:#22c55e;color:#000;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:12px">🎯 BUY ON KALSHI</a>
        </div>
        """, unsafe_allow_html=True)
