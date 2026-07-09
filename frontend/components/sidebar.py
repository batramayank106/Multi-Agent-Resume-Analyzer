import streamlit as st
from pathlib import Path
import base64

ICON_PATH = Path(__file__).parent.parent.parent / "media and images" / "Main icon transparent.png"
icon_b64 = base64.b64encode(Path(ICON_PATH).read_bytes()).decode()


def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
                <img src="data:image/png;base64,{icon_b64}"
                     style="width: 42px; height: auto; filter: drop-shadow(0 0 10px rgba(204, 120, 92, 0.35));"
                     alt="CV Chacha">
                <div style="color: #faf9f5; font-family: 'Playfair Display', serif;
                           font-size: 1.4rem; font-weight: 400; letter-spacing: -0.5px; line-height: 1.2;">
                    CV Chacha
                </div>
                <div style="color: #6c6a64; font-size: 0.65rem; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400; margin-top: 0.1rem;">
                    by Mayank Batra
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
