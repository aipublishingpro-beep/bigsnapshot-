import streamlit as st

st.set_page_config(
    page_title="MLB Edge Finder - Coming Soon",
    page_icon="⚾",
    layout="centered"
)

st.markdown("""
<style>
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #c41e3a 0%, #003087 50%, #bf0d3e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        padding-top: 1rem;
    }
    .hero-subtitle {
        font-size: 1.3rem;
        color: #a0aec0;
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    .tagline {
        font-size: 1.05rem;
        color: #718096;
        text-align: center;
        margin: 2rem auto;
        max-width: 600px;
        line-height: 1.8;
    }
    .feature-box {
        background: rgba(196, 30, 58, 0.1);
        border: 1px solid rgba(196, 30, 58, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }
    .feature-title {
        color: #c41e3a;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #a0aec0;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .coming-soon-badge {
        background: linear-gradient(90deg, #c41e3a 0%, #003087 100%);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        display: inline-block;
        margin: 1.5rem auto;
        text-align: center;
    }
    .launch-date {
        font-size: 1.2rem;
        color: #c41e3a;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    .footer {
        color: #4a5568;
        text-align: center;
        font-size: 0.8rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown('<p class="hero-title">⚾ MLB Edge Finder</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Kalshi MLB Contract Analysis</p>', unsafe_allow_html=True)

st.markdown("""
<p class="tagline">
Find mispriced MLB contracts on Kalshi using starting pitcher stats, 
bullpen strength, team OPS, ballpark factors, and injury reports.
</p>
""", unsafe_allow_html=True)

# Coming Soon Badge
st.markdown('<center><span class="coming-soon-badge">🚀 COMING MARCH 2026</span></center>', unsafe_allow_html=True)
st.markdown('<p class="launch-date">⚾ Ready for Opening Day</p>', unsafe_allow_html=True)

st.markdown("---")

# Features Preview
st.markdown("### What's Coming")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">⚾ Starting Pitcher Analysis</p>
        <p class="feature-desc">ERA, WHIP, K/9, and pitcher vs team history using official MLB Stats API data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🔥 Bullpen Strength</p>
        <p class="feature-desc">Bullpen ERA, recent usage, fatigue factors, and high-leverage reliever availability.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🏟️ Ballpark Factors</p>
        <p class="feature-desc">Park-adjusted scoring — Coors Field boost, Oracle Park suppression, and more.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">📊 Team Hitting (OPS)</p>
        <p class="feature-desc">On-base plus slugging splits — last 7 days, vs LHP/RHP, home/away performance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🏥 Injury Impact</p>
        <p class="feature-desc">Star player injuries weighted by position value — ace pitchers and cleanup hitters matter most.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">📈 12-Factor Model</p>
        <p class="feature-desc">Comprehensive scoring system combining all factors into edge signals with confidence tiers.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Edge Tiers Preview
st.markdown("### Edge Signal Tiers")

st.markdown("""
| Signal | Edge | Suggested Action |
|--------|------|------------------|
| 🟢 **STRONG EDGE** | +10%+ | Full position |
| 🔵 **SOLID EDGE** | +7-9% | Half position |
| 🟡 **SLIGHT EDGE** | +5-6% | Quarter position |
| ⚪ **NO EDGE** | <5% | Pass |
""")

st.markdown("---")

# Footer
st.markdown("""
<p class="footer">
    MLB Edge Finder • Kalshi Contract Analysis<br>
    <em>Informational only. Not financial advice.</em>
</p>
""", unsafe_allow_html=True)
