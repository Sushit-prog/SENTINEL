"""SCAMWatch frontend — scam detection interface."""

import streamlit as st
import httpx
import json
import sys
import os

# Add project root to Python path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

# How It Works section
with st.expander("How SCAMWatch Works", expanded=False):
    st.markdown("""
    **SCAMWatch** uses a 5-step AI pipeline to detect scams:

    1. **Rule-based Classification** — Fast pattern matching against 7 Indian scam types (zero API cost)
    2. **LLM Deep Analysis** — Groq Llama 3.3 70B analyzes semantic meaning and context
    3. **Risk Scoring** — Multi-signal engine combining keywords, urgency, authority impersonation
    4. **Intelligence Storage** — High-risk patterns stored in ChromaDB for cross-module correlation
    5. **Citizen Alert** — Structured alert with emergency contacts and MHA payload

    **Supported Scam Types:** Digital Arrest, Fake KYC, Fake Investment, Fake Job, Fake Lottery, Impersonation, Romance Scam

    **Languages:** English, Hindi, Tamil, Bengali, Telugu
    """)

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
    st.header("Settings")
    channel = st.selectbox(
        "Input Channel",
        ["unknown", "whatsapp", "sms", "call", "email", "social_media"],
        help="Where did you receive this message?"
    )
    language = st.selectbox(
        "Output Language",
        ["en", "hi", "ta", "bn", "te"],
        format_func=lambda x: {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "bn": "Bengali",
            "te": "Telugu",
        }.get(x, x),
        help="Language for verdict and advisory text"
    )
    st.divider()
    st.header("Sample Scams")
    st.caption("Click to load a sample")
    for name in SAMPLE_TEXTS:
        if st.button(name, use_container_width=True):
            st.session_state["sample_text"] = SAMPLE_TEXTS[name]
    # Auto-load first sample if nothing selected
    if "sample_text" not in st.session_state:
        st.session_state["sample_text"] = SAMPLE_TEXTS["Digital Arrest Scam"]

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
                        "language": language
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

                    # Show translated verdict if available
                    if data.get("translated_verdict") and data.get("target_language") != "en":
                        lang_names = {"hi": "Hindi", "ta": "Tamil", "bn": "Bengali", "te": "Telugu"}
                        lang_name = lang_names.get(data["target_language"], data["target_language"])
                        st.markdown(f"---")
                        st.markdown(f"**Translated Verdict ({lang_name}):**")
                        st.info(data["translated_verdict"])
                        if data.get("translated_actions"):
                            st.markdown(f"**Translated Actions ({lang_name}):**")
                            for action in data["translated_actions"]:
                                st.markdown(f"- {action}")

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

                    # ── CITIZEN ALERT SECTION ────────────────────────────────
                    st.markdown("---")
                    st.subheader("🚨 Citizen Alert")

                    if st.button("📤 Generate Citizen Alert", use_container_width=True, key="gen_alert"):
                        with st.spinner("Generating citizen alert..."):
                            try:
                                alert_resp = httpx.post(
                                    f"{BACKEND_URL}/api/scamwatch/alert/{data['analysis_id']}",
                                    timeout=15.0
                                )
                                if alert_resp.status_code == 200:
                                    alert = alert_resp.json()
                                    st.session_state["citizen_alert"] = alert
                                    st.session_state["alert_analysis_id"] = data["analysis_id"]
                                else:
                                    st.error(f"Alert generation failed: {alert_resp.status_code}")
                            except Exception as e:
                                st.error(f"Alert error: {e}")

                    # Render alert if available and for current analysis
                    alert = st.session_state.get("citizen_alert")
                    alert_aid = st.session_state.get("alert_analysis_id")
                    if alert and alert_aid == data["analysis_id"]:
                        # Verdict banner
                        alert_rl = alert.get("risk_level", "MEDIUM")
                        a_emoji, a_color, a_bg = RISK_COLORS.get(alert_rl, ("⚪", "gray", "#f8f9fa"))
                        # Use translated verdict if available
                        display_verdict = alert.get("translated_verdict") or alert.get("one_line_verdict", "")
                        display_actions = alert.get("translated_actions") or alert.get("recommended_actions", [])
                        a_lang = alert.get("target_language", "en")
                        lang_label = {"hi": "Hindi", "ta": "Tamil", "bn": "Bengali", "te": "Telugu"}.get(a_lang, "English")

                        st.markdown(f"""
                        <div style="background:{a_bg}; padding:20px; border-radius:10px; border-left:6px solid {a_color}; margin:12px 0;">
                            <div style="font-size:0.7rem; color:#888; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px;">
                                VERDICT {f'({lang_label})' if a_lang != 'en' else ''}
                            </div>
                            <div style="font-size:1.3rem; font-weight:bold; color:{a_color};">
                                {a_emoji} {display_verdict}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Recommended actions checklist
                        st.markdown(f"**Recommended Actions ({lang_label}):**")
                        for action in display_actions:
                            st.checkbox(action, key=f"action_{hash(action)}", disabled=True)

                        # Emergency contacts
                        st.markdown("**Emergency Contacts:**")
                        contacts = alert.get("emergency_contacts", [])
                        if contacts:
                            contact_cols = st.columns(min(len(contacts), 3))
                            for i, contact in enumerate(contacts):
                                with contact_cols[i % 3]:
                                    st.markdown(f"""
                                    <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:12px; margin:4px 0;">
                                        <div style="font-weight:bold; color:#e5e7eb;">{contact.get('name', '')}</div>
                                        <div style="color:#00aaff; font-size:1.1rem; font-weight:bold;">{contact.get('number', '')}</div>
                                        <div style="color:#6b7280; font-size:0.75rem;">{contact.get('description', '')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        # MHA Alert Payload
                        with st.expander("📋 MHA Alert Payload (JSON) — Simulated", expanded=False):
                            st.caption("This is the structured payload that would be transmitted to MHA/NCRB intake systems.")
                            st.json(alert.get("mha_alert_payload", {}))

                        # Copy as WhatsApp Message
                        st.markdown("**Share Alert:**")
                        wa_verdict = display_verdict
                        wa_actions = display_actions[:2]
                        whatsapp_text = f"SENTINEL SCAM ALERT\n"
                        whatsapp_text += f"{'=' * 30}\n"
                        whatsapp_text += f"{wa_verdict}\n\n"
                        whatsapp_text += f"Actions:\n"
                        for i, action in enumerate(wa_actions, 1):
                            whatsapp_text += f"{i}. {action}\n"
                        whatsapp_text += f"\nReport: Cyber Crime Helpline 1930 | cybercrime.gov.in"
                        whatsapp_text += f"\n\n(Sent via SENTINEL - AI for Digital Public Safety)"

                        st.code(whatsapp_text, language=None)
                        st.caption("Copy the text above and share via WhatsApp to warn others.")

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
