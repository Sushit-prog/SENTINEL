"""SCAMWatch frontend — scam detection interface."""

import streamlit as st
import httpx
import json
from backend.config import get_settings

st.set_page_config(
    page_title="SCAMWatch — SENTINEL",
    page_icon="🔍",
    layout="wide"
)

settings = get_settings()
BACKEND_URL = settings.backend_url

st.title("🔍 SCAMWatch")
st.caption("AI-powered scam detection. Paste any suspicious message or call transcript below.")

RISK_COLORS = {
    "LOW": ("🟢", "green", "#d4edda"),
    "MEDIUM": ("🟡", "orange", "#fff3cd"),
    "HIGH": ("🔴", "red", "#f8d7da"),
    "CRITICAL": ("🚨", "darkred", "#f5c6cb"),
}

SAMPLE_TEXTS = {
    "Digital Arrest Scam": """Sir, I am calling from CBI headquarters. Your Aadhaar number has been used 
to open 47 illegal bank accounts involved in money laundering. An arrest warrant has been issued 
in your name. You are under digital arrest. Do not disconnect the call or inform anyone. 
Our officer will contact you on video call. You must transfer Rs 5 lakh as security deposit 
to prove your innocence. This is Supreme Court order 2024.""",

    "Fake KYC SMS": """URGENT: Your SBI account KYC is expired. Your account will be blocked within 
24 hours. Click here to update KYC immediately: http://sbi-kyc-update.xyz/verify 
Enter your account details and OTP to restore access. Ignore this message at your own risk.""",

    "Fake Investment": """Hello! I am from WealthGrow Investment Group. Our members are earning 
40% monthly returns through our exclusive crypto arbitrage program. 
Only 5 slots remaining. Minimum investment Rs 10,000. WhatsApp investment group 
has made 500 members rich already. Guaranteed returns. Join today, limited time offer."""
}

with st.sidebar:
    st.header("⚙️ Settings")
    channel = st.selectbox(
        "Input Channel",
        ["unknown", "whatsapp", "sms", "call", "email", "social_media"],
        help="Where did you receive this message?"
    )
    st.divider()
    st.header("📋 Sample Scams")
    st.caption("Click to load a sample")
    for name in SAMPLE_TEXTS:
        if st.button(name, use_container_width=True):
            st.session_state["sample_text"] = SAMPLE_TEXTS[name]

default_text = st.session_state.get("sample_text", "")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Input")
    text_input = st.text_area(
        "Paste suspicious message or call transcript",
        value=default_text,
        height=280,
        placeholder="Paste WhatsApp message, SMS, email, or call transcript here...",
        label_visibility="collapsed"
    )

    char_count = len(text_input)
    st.caption(f"{char_count} characters")

    analyze_clicked = st.button(
        "🔍 Analyze for Scam",
        type="primary",
        use_container_width=True,
        disabled=char_count < 10
    )

with col2:
    st.subheader("📊 Analysis Result")

    if analyze_clicked and text_input:
        with st.spinner("Running SENTINEL intelligence pipeline..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/api/scamwatch/analyze",
                    json={
                        "text": text_input,
                        "channel": channel,
                        "language": "en"
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    data = response.json()
                    risk_level = data["risk_level"]
                    emoji, color, bg = RISK_COLORS.get(risk_level, ("⚪", "gray", "#f8f9fa"))

                    st.markdown(f"""
                    <div style="background-color:{bg}; padding:16px; border-radius:8px; margin-bottom:16px;">
                        <h2 style="margin:0; color:{color};">{emoji} {risk_level} RISK</h2>
                        <p style="margin:4px 0 0 0; font-size:14px;">Risk Score: {data['risk_score']:.2f} / 1.00</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if data.get("scam_type"):
                        st.info(f"**Scam Type Detected:** {data['scam_type'].replace('_', ' ').title()}")

                    st.markdown(f"**Verdict:** {data['verdict']}")
                    st.markdown(f"**Recommended Action:** {data['recommended_action']}")

                    if data.get("similar_patterns_found", 0) > 0:
                        st.warning(f"⚠️ {data['similar_patterns_found']} similar scam patterns found in intelligence database")

                    if data.get("indicators"):
                        st.subheader("🚩 Risk Indicators")
                        for ind in data["indicators"]:
                            ind_emoji, ind_color, ind_bg = RISK_COLORS.get(
                                ind["severity"], ("⚪", "gray", "#f8f9fa")
                            )
                            st.markdown(f"""
                            <div style="background:{ind_bg}; padding:10px; border-radius:6px; margin-bottom:8px;">
                                <strong>{ind_emoji} {ind['indicator']}</strong> — {ind['severity']}<br>
                                <small>{ind['explanation']}</small>
                            </div>
                            """, unsafe_allow_html=True)

                    st.caption(f"Analysis ID: {data['analysis_id']}")

                else:
                    st.error(f"Backend error: {response.status_code} — {response.text}")

            except httpx.ConnectError:
                st.error("Cannot connect to SENTINEL backend. Ensure backend is running on port 8000.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.markdown("""
        <div style="background:#f8f9fa; padding:40px; border-radius:8px; text-align:center; color:#6c757d;">
            <h3>Awaiting Input</h3>
            <p>Paste a suspicious message on the left and click Analyze</p>
            <p>Or load a sample from the sidebar</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption("🛡️ SENTINEL SCAMWatch — ET AI Hackathon 2.0 | No government agency conducts digital arrests.")
