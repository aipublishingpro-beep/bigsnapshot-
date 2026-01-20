import streamlit as st
from datetime import datetime
import pytz

# ============================================================
# POLITICS EDGE - LANDING PAGE v1.0
# Structural Analysis for Kalshi Political Markets
# ============================================================

st.set_page_config(page_title="Politics Edge", page_icon="🏛️", layout="wide")

# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* Hero Section */
.hero-container {
    text-align: center;
    padding: 3rem 1rem;
    margin-bottom: 2rem;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}

.hero-tagline {
    font-size: 1.3rem;
    color: #a0a0a0;
    margin-bottom: 1.5rem;
    font-weight: 300;
}

.coming-soon-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 0.5rem 1.5rem;
    border-radius: 50px;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 1px;
    margin-bottom: 1rem;
}

/* Feature Boxes */
.feature-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, border-color 0.2s;
    min-height: 180px;
}

.feature-box:hover {
    transform: translateY(-4px);
    border-color: rgba(102, 126, 234, 0.4);
}

.feature-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
}

.feature-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.5rem;
}

.feature-desc {
    font-size: 0.85rem;
    color: #888;
    line-height: 1.4;
}

/* How It Works */
.step-box {
    background: rgba(102, 126, 234, 0.1);
    border: 1px solid rgba(102, 126, 234, 0.2);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    min-height: 140px;
}

.step-number {
    display: inline-block;
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 50%;
    color: white;
    font-weight: bold;
    line-height: 32px;
    margin-bottom: 0.75rem;
}

.step-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.25rem;
}

.step-desc {
    font-size: 0.8rem;
    color: #888;
}

/* Context Box */
.context-box {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin: 2rem 0;
}

.context-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #667eea;
    margin-bottom: 0.5rem;
}

.context-text {
    font-size: 0.9rem;
    color: #ccc;
    line-height: 1.5;
}

/* Waitlist Form */
.waitlist-container {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
}

.waitlist-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.5rem;
}

.waitlist-subtitle {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 1.5rem;
}

/* Social Proof */
.social-proof {
    text-align: center;
    padding: 1rem 0;
    color: #666;
    font-size: 0.85rem;
}

/* Integrations */
.integrations-bar {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
    padding: 1rem 0;
    color: #555;
    font-size: 0.8rem;
}

.integration-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Footer */
.footer-container {
    text-align: center;
    padding: 2rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 3rem;
}

.footer-links {
    margin-bottom: 1rem;
}

.footer-links a {
    color: #667eea;
    text-decoration: none;
    margin: 0 1rem;
    font-size: 0.9rem;
}

.footer-disclaimer {
    font-size: 0.75rem;
    color: #555;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.4;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.2rem;
    }
    .hero-tagline {
        font-size: 1rem;
    }
    .feature-box, .step-box {
        min-height: auto;
        margin-bottom: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div class="hero-container">
    <div class="coming-soon-badge">COMING SOON</div>
    <h1 class="hero-title">Politics Edge</h1>
    <p class="hero-tagline">Structural analysis for Kalshi political markets.<br>Not predictions. Resolution mechanics.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 2026 MIDTERMS CONTEXT
# ============================================================

st.markdown("""
<div class="context-box">
    <div class="context-title">🗳️ 2026 Midterms Are Already Trading</div>
    <div class="context-text">
        House and Senate control markets on Kalshi are seeing massive early volume.<br>
        Structural events — filing deadlines, certifications, court rulings — create the biggest price lags.<br>
        <strong>This is where edge lives.</strong>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PHILOSOPHY / FEATURES
# ============================================================

st.markdown("### What We Track")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">⚖️</div>
        <div class="feature-title">Constraint Detection</div>
        <div class="feature-desc">Track when rules, deadlines, or legal structures eliminate possible outcomes before markets adjust.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🔀</div>
        <div class="feature-title">Path Counting</div>
        <div class="feature-desc">Monitor remaining viable paths to each outcome. When paths collapse, prices should move.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">⏱️</div>
        <div class="feature-title">Market Lag Detection</div>
        <div class="feature-desc">Identify when structural resolution has occurred but market prices haven't caught up.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">📅</div>
        <div class="feature-title">Resolution Timeline</div>
        <div class="feature-desc">Visual countdowns for filing deadlines, certification dates, and court ruling windows.</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🚨</div>
        <div class="feature-title">Path Collapse Alerts</div>
        <div class="feature-desc">Real-time notifications when a branch dies — candidate withdraws, ruling issued, deadline passes.</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">Source Integration</div>
        <div class="feature-desc">Pull from official sources — state election offices, federal courts, FEC filings — automatically.</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HOW IT WORKS
# ============================================================

st.markdown("---")
st.markdown("### How It Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="step-box">
        <div class="step-number">1</div>
        <div class="step-title">Monitor Key Dates</div>
        <div class="step-desc">Deadlines, certifications, court rulings</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="step-box">
        <div class="step-number">2</div>
        <div class="step-title">Count Viable Paths</div>
        <div class="step-desc">Track remaining routes to each outcome</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="step-box">
        <div class="step-number">3</div>
        <div class="step-title">Detect Resolution</div>
        <div class="step-desc">Flag when structure locks before price moves</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="step-box">
        <div class="step-number">4</div>
        <div class="step-title">Quantify Edge</div>
        <div class="step-desc">Measure lag between reality and market</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# WAITLIST FORM
# ============================================================

st.markdown("---")

st.markdown("""
<div class="waitlist-container">
    <div class="waitlist-title">Get Early Access</div>
    <div class="waitlist-subtitle">Be first to know when Politics Edge launches + receive structural resolution alerts</div>
</div>
""", unsafe_allow_html=True)

with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        email = st.text_input("Email address", placeholder="you@example.com", label_visibility="collapsed")
    
    with col2:
        submitted = st.form_submit_button("Join Waitlist", type="primary", use_container_width=True)
    
    interest = st.selectbox(
        "Which markets interest you most?",
        ["All Political Markets", "2026 Midterms (House/Senate)", "Presidential 2028", "Fed/Economic Policy", "Supreme Court", "State Elections"],
        label_visibility="visible"
    )
    
    if submitted:
        if email and "@" in email:
            # In production: save to Google Sheets / Airtable / Supabase
            st.success(f"You're on the list! We'll notify you at {email} when Politics Edge launches.")
            # Log for now
            st.session_state["waitlist_signups"] = st.session_state.get("waitlist_signups", 0) + 1
        else:
            st.error("Please enter a valid email address.")

# Social proof
st.markdown("""
<div class="social-proof">
    <strong>Join 200+ traders</strong> tracking structural edges on Kalshi political markets
</div>
""", unsafe_allow_html=True)

# ============================================================
# INTEGRATIONS COMING
# ============================================================

st.markdown("---")
st.markdown("### Integrations Coming")

st.markdown("""
<div class="integrations-bar">
    <div class="integration-item">📊 Kalshi API</div>
    <div class="integration-item">⚖️ CourtListener</div>
    <div class="integration-item">📋 FEC Filings</div>
    <div class="integration-item">🗳️ Ballotpedia</div>
    <div class="integration-item">🏛️ State Election Offices</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# EXAMPLE PREVIEW (MOCK)
# ============================================================

st.markdown("---")
st.markdown("### Sneak Peek: Sample Analysis")

with st.container():
    st.markdown("""
    <div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
            <div>
                <span style='font-size: 1.2rem; font-weight: 600; color: #fff;'>🗳️ Arizona Senate 2026</span>
                <span style='background: #22c55e; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.75rem;'>EDGE DETECTED</span>
            </div>
            <span style='color: #888; font-size: 0.85rem;'>Updated 2 hours ago</span>
        </div>
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;'>
            <div style='background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; text-align: center;'>
                <div style='font-size: 0.8rem; color: #888;'>Filing Deadline</div>
                <div style='font-size: 1.1rem; font-weight: 600; color: #667eea;'>Apr 7, 2026</div>
                <div style='font-size: 0.75rem; color: #666;'>78 days remaining</div>
            </div>
            <div style='background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; text-align: center;'>
                <div style='font-size: 0.8rem; color: #888;'>Viable Paths</div>
                <div style='font-size: 1.1rem; font-weight: 600; color: #f59e0b;'>3 → 2</div>
                <div style='font-size: 0.75rem; color: #666;'>Path collapsed yesterday</div>
            </div>
            <div style='background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; text-align: center;'>
                <div style='font-size: 0.8rem; color: #888;'>Market Lag</div>
                <div style='font-size: 1.1rem; font-weight: 600; color: #22c55e;'>+8¢</div>
                <div style='font-size: 0.75rem; color: #666;'>Price hasn't adjusted</div>
            </div>
        </div>
        <div style='font-size: 0.85rem; color: #888; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1rem;'>
            <strong style='color: #ccc;'>Analysis:</strong> Leading challenger withdrew from primary Feb 15. Kalshi market still pricing 3-way race. Structural resolution suggests DEM path collapsed. Market lag detected.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer-container">
    <div class="footer-links">
        <a href="mailto:aipublishingpro@gmail.com">Contact</a>
        <a href="https://kalshi.com" target="_blank">Kalshi Markets</a>
        <a href="/">Back to BigSnapshot</a>
    </div>
    <div class="footer-disclaimer">
        <strong>Disclaimer:</strong> Politics Edge is not affiliated with Kalshi. This tool is for informational and educational purposes only. 
        Political prediction markets involve substantial risk of loss. Past structural analysis does not guarantee future results. 
        Not financial or legal advice. Trade responsibly.
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TIMEZONE FOOTER
# ============================================================

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
st.caption(f"🕐 {now.strftime('%I:%M %p ET')} | 📅 {now.strftime('%B %d, %Y')}")
