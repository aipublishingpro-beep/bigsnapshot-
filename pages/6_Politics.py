import streamlit as st

st.set_page_config(
    page_title="Politics Edge - Coming Soon",
    page_icon="🏛️",
    layout="centered"
)

st.markdown("""
<style>
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
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
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }
    .feature-title {
        color: #667eea;
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
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
st.markdown('<p class="hero-title">🏛️ Politics Edge</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Structural Analysis Platform</p>', unsafe_allow_html=True)

st.markdown("""
<p class="tagline">
We don't predict outcomes. We track <strong>constraints</strong>, <strong>deadlines</strong>, 
and <strong>path exhaustion</strong> — the structural realities that move prices 
before narratives catch up.
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
        <p class="feature-title">⚖️ Constraint Tracking</p>
        <p class="feature-desc">Filing deadlines, certifications, legal rulings — know when outcomes become structurally locked before markets adjust.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">🔀 Path Counting</p>
        <p class="feature-desc">Every political outcome requires procedural steps. See which paths remain viable and which have collapsed.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">📡 Event Detection</p>
        <p class="feature-desc">Court rulings, withdrawals, and certifications mapped to impacted contracts in real-time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">⏱️ Market Lag Alerts</p>
        <p class="feature-desc">When structure resolves but price lingers, we surface the gap. You decide what to do.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Edge Philosophy
st.markdown("### The Edge Philosophy")

st.markdown("""
<div class="feature-box">
    <p class="feature-title">📊 Structure Over Opinion</p>
    <p class="feature-desc">
    Most traders read polls and pundit takes. We track procedural reality: 
    Has the filing deadline passed? Is the certification complete? 
    Did the legal challenge get dismissed? When structure resolves before price moves, edge exists.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<p class="footer">
    Politics Edge • Structural Analysis for Kalshi Political Markets<br>
    <em>Informational only. Not financial advice. Not affiliated with Kalshi.</em>
</p>
""", unsafe_allow_html=True)
