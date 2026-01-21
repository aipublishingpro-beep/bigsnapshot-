import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    .stLinkButton > a {background-color: #00aa00 !important;border-color: #00aa00 !important;color: white !important;}
    .stLinkButton > a:hover {background-color: #00cc00 !important;border-color: #00cc00 !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    div[data-testid="stMarkdownContainer"] > div {
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

def buy_button(url, text="BUY"):
    return f'''<a href="{url}" target="_blank" style="
        display: block;
        background: linear-gradient(135deg, #00c853, #00a844);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        text-align: center;
        margin: 5px 0;
    ">{text}</a>'''

def link_button(url, text="View"):
    return f'''<a href="{url}" target="_blank" style="
        display: block;
        background: linear-gradient(135deg, #1e3a5f, #0f2744);
        color: #88ccff;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 500;
        text-align: center;
        margin: 5px 0;
        border: 1px solid #335577;
    ">{text}</a>'''
