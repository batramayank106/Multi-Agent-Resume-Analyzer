import streamlit as st
from pathlib import Path
import base64
from frontend.utils.api_client import auth_login, auth_register, auth_me
from frontend.utils.state import login, logout, is_authenticated

ASSETS = Path(__file__).parent.parent.parent / "media and images"
icon_b64 = base64.b64encode((ASSETS / "Main icon transparent.png").read_bytes()).decode()


def render():
    if is_authenticated():
        user = st.session_state.user_info or {}
        st.markdown(
            f"<h2>Welcome, {user.get('username', 'User')}!</h2>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**Email:** {user.get('email', '—')}")
            st.markdown(f"**Role:** `{user.get('role', '—')}`")
        if st.button("Logout", type="primary"):
            logout()
            st.rerun()
        return

    st.markdown(f"""
    <style>
        .stApp {{
            background: var(--canvas) !important;
        }}
        .main > div {{
            background: transparent !important;
        }}
        section[data-testid="stSidebar"] {{
            z-index: 1 !important;
        }}
        .login-wrapper {{
            display: flex; justify-content: center; align-items: center;
            min-height: 70vh; padding: 1rem;
        }}
        .login-card {{
            max-width: 420px; width: 100%;
        }}
        .login-brand {{
            text-align: center; margin-bottom: 1.5rem;
        }}
        .login-brand img {{
            width: 80px; height: auto;
            display: block; margin: 0 auto;
            filter: drop-shadow(0 0 20px rgba(204, 120, 92, 0.3));
        }}
        .login-brand h1 {{
            font-family: 'Playfair Display', serif; font-size: 2.4rem;
            color: var(--ink); margin: 0.75rem 0 0.25rem; letter-spacing: -0.5px;
            font-weight: 700;
        }}
        .login-brand p {{
            font-family: 'Inter', sans-serif; font-size: 0.95rem;
            color: var(--muted); margin: 0 0 1.5rem;
            font-weight: 400;
            letter-spacing: 0.3px;
        }}
        .login-card .stTabs {{
            background: var(--surface-card);
            border-radius: 16px;
            padding: 1.5rem 1.5rem 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            position: relative;
            border: 1px solid var(--hairline);
        }}
        .login-card .stTabs [data-baseweb="tab-list"] {{
            border-bottom: 1px solid var(--hairline) !important;
            gap: 0 !important;
        }}
        .login-card .stTabs [data-baseweb="tab"] {{
            color: var(--muted) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            padding: 10px 20px !important;
            background: transparent !important;
        }}
        .login-card .stTabs [aria-selected="true"] {{
            color: var(--ink) !important;
            border-bottom: 2px solid var(--primary) !important;
        }}
        .login-card div[data-testid="stTextInput"] input {{
            background: var(--surface-soft) !important;
            border: 1px solid var(--hairline) !important;
            color: var(--ink) !important;
            border-radius: 8px !important;
            transition: all 0.3s !important;
        }}
        .login-card div[data-testid="stTextInput"] input:focus {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15) !important;
        }}
        .login-card div[data-testid="stTextInput"] input::placeholder {{
            color: var(--muted-soft) !important;
        }}
        .login-card div[data-testid="stTextInput"] label {{
            color: var(--ink) !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }}
        .login-card .stButton > button {{
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            background: var(--primary) !important;
            color: var(--on-primary) !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 20px !important;
            height: 46px !important;
            box-shadow: 0 4px 16px rgba(204, 120, 92, 0.3) !important;
        }}
        .login-card .stButton > button:hover {{
            background: var(--primary-active) !important;
            box-shadow: 0 6px 24px rgba(204, 120, 92, 0.4) !important;
        }}
        .login-card .stAlert {{
            border-radius: 8px !important;
            font-weight: 500 !important;
        }}
    </style>
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-brand">
                <img src="data:image/png;base64,{icon_b64}" alt="CV Chacha">
                <h1>CV Chacha</h1>
                <p>Multi-Agent Resume Intelligence</p>
                <p style="font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; opacity: 0.5; margin-top: -0.5rem;">by Mayank Batra</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        tab1, tab2 = st.tabs(["Sign In", "Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        result = auth_login(email, password)
                        if result["status"] == 200:
                            body = result["body"]
                            user_resp = auth_me(body["access_token"])
                            if user_resp["status"] == 200:
                                login(body["access_token"], body["refresh_token"], user_resp["body"])
                                st.success(f"Welcome, {user_resp['body']['username']}!")
                                st.rerun()
                            else:
                                st.error("Login succeeded but failed to fetch profile")
                        elif result["status"] == 423:
                            st.warning(result["body"].get("detail", "Account locked"))
                        else:
                            st.error(result["body"].get("detail", "Login failed"))

        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("Email", placeholder="you@example.com", key="reg_email_login")
                reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_username_login")
                reg_password = st.text_input("Password", type="password", key="reg_password_login",
                                             help="Min 8 chars, uppercase, lowercase, digit, special char")
                reg_submitted = st.form_submit_button("Register", type="primary", use_container_width=True)
                if reg_submitted:
                    if not reg_email or not reg_username or not reg_password:
                        st.error("Please fill in all fields")
                    else:
                        result = auth_register(reg_email, reg_username, reg_password)
                        if result["status"] == 201:
                            st.success("Registered! Switch to Sign In tab.")
                        else:
                            st.error(result["body"].get("detail", "Registration failed"))
