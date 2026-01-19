import streamlit as st

st.set_page_config(
    page_title="NHL Edge Finder - Coming Soon",
    page_icon="🏒",
    layout="centered"
)

st.markdown("""
<style>
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff 0%, #0099cc 50%, #006699 100%);
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
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }
    .feature-title {
        color: #00d4ff;
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
        background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        display: inline-block;
        margin: 1.5rem auto;
        text-align: center;
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
st.markdown('<p class="hero-title">🏒 NHL Edge Finder</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Kalshi NHL Contract Analysis</p>', unsafe_allow_html=True)

st.markdown("""
<p class="tagline">
Find mispriced NHL contracts on Kalshi using goaltender matchups, 
back-to-back fatigue, home ice advantage, and scoring trends.
</p>
""", unsafe_allow_html=True)

# Coming Soon Badge
st.markdown('<center><span class="coming-soon-badge">🚀 COMING SOON</span></center>', unsafe_allow_html=True)

st.markdown("---")

# Features Preview
st.markdown("### What's Coming")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🥅 Goaltender Analysis</p>
        <p class="feature-desc">Starting goalie confirmation, save percentages, recent form, and head-to-head matchup history.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">😴 Fatigue Detection</p>
        <p class="feature-desc">Back-to-back games, travel distance, and schedule density that impact performance.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">📊 Scoring Trends</p>
        <p class="feature-desc">Goals per game, power play efficiency, and over/under patterns by team and venue.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🏠 Home Ice Edge</p>
        <p class="feature-desc">Home vs away splits, altitude factors, and last change advantage analysis.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<p class="footer">
    NHL Edge Finder • Kalshi Contract Analysis<br>
    <em>Informational only. Not financial advice.</em>
</p>
""", unsafe_allow_html=True)
