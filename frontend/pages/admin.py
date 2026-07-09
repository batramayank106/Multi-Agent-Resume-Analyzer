import httpx
import streamlit as st
import pandas as pd
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import is_authenticated, is_super_admin


def render():
    st.markdown("<h2>🛡️ Admin Dashboard</h2>", unsafe_allow_html=True)

    if not is_authenticated():
        st.info("🔐 Sign in as super admin to access this page.")
        return
    if not is_super_admin():
        st.warning("Only super admins can access this page.")
        return

    tab1, tab2, tab3 = st.tabs(["Audit Logs", "User Management", "Security Status"])

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    with tab1:
        st.markdown("**API Request Audit Logs**")
        if st.button("🔄 Refresh", key="audit_refresh"):
            st.rerun()
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{BACKEND_URL}/api/auth/audit-logs", headers=headers)
                r.raise_for_status()
                logs = r.json()
        except Exception as e:
            st.error(f"Could not load audit logs: {e}")
            return

        if not logs:
            st.info("No audit logs yet.")
            return

        df = pd.DataFrame(logs)
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%H:%M:%S")
            df = df.rename(columns={
                "method": "Method", "path": "Path", "status_code": "Status",
                "user_email": "User", "ip_address": "IP", "duration_ms": "ms",
                "created_at": "Time",
            })
            st.dataframe(
                df[["Time", "Method", "Path", "Status", "User", "IP", "ms"]],
                use_container_width=True,
                height=400,
                hide_index=True,
            )

    with tab2:
        st.markdown("**Manage Users**")
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{BACKEND_URL}/api/auth/users", headers=headers)
                r.raise_for_status()
                users = r.json()
        except Exception as e:
            st.error(f"Could not load users: {e}")
            return

        for u in users:
            cols = st.columns([2, 1.5, 1, 1, 1])
            cols[0].markdown(f"**{u['email']}**")
            cols[1].markdown(f"`{u['role']}`")
            cols[2].markdown(f"{'✅ Active' if u['is_active'] else '❌ Inactive'}")
            with cols[3]:
                if st.button("Toggle Active", key=f"tog_{u['id']}"):
                    try:
                        with httpx.Client(timeout=10.0) as client:
                            client.patch(
                                f"{BACKEND_URL}/api/auth/users/{u['id']}/toggle-active",
                                headers=headers,
                            )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            with cols[4]:
                new_role = st.selectbox(
                    "Role", ["user", "admin", "super_admin"],
                    index=["user", "admin", "super_admin"].index(u["role"]),
                    key=f"role_{u['id']}", label_visibility="collapsed",
                )
                if new_role != u["role"]:
                    try:
                        with httpx.Client(timeout=10.0) as client:
                            client.patch(
                                f"{BACKEND_URL}/api/auth/users/{u['id']}/role",
                                json={"role": new_role},
                                headers=headers,
                            )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            st.markdown("<hr style='margin:0.2rem 0;'>", unsafe_allow_html=True)

    with tab3:
        st.markdown("**Security Configuration**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rate Limit", "60 req/min")
        col2.metric("Prompt Injection", "6 patterns tracked")
        col3.metric("Audit Logging", "Active")

        st.markdown("**Prompt Injection Patterns**")
        st.code(
            "• System override commands\n"
            "• Role switch attempts\n"
            "• Prompt leak attempts\n"
            "• Delimiter breaking\n"
            "• Token/key theft\n"
            "• Jailbreak prefixes",
            language="text",
        )

        st.markdown("**Rate Limiting**")
        st.info("Max 60 requests/min per IP (standard) or 120 requests/min (super admin). Applies to all API routes except /health.")
