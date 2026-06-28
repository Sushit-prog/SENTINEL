import streamlit as st

st.set_page_config(
    page_title="SENTINEL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ SENTINEL")
st.subheader("Digital Public Safety Intelligence Platform")

st.markdown("""
---
### Select a module from the sidebar to begin.

| Module | Description | Target User |
|--------|-------------|-------------|
| 🔍 SCAMWatch | Detect digital arrest and financial scams | Citizens |
| 💵 CURRENCYGuard | Authenticate Indian currency notes | Bank tellers, Field officers |
| 🕸️ FRAUDGraph | Map fraud networks and crime rings | Law enforcement |

---
*Built for ET AI Hackathon 2.0 — Economic Times*
""")
