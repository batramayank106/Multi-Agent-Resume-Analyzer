import httpx
import streamlit as st
import pandas as pd
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import is_authenticated


def render():
    st.markdown("<h2>📂 Resume Vault</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6c6a64;'>Saved analysis sessions — view or delete past results.</p>",
        unsafe_allow_html=True,
    )

    if not is_authenticated():
        st.info("🔐 Sign in to save and view your analysis history.")
        return

    if "vault_refresh" not in st.session_state:
        st.session_state.vault_refresh = 0

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                f"{BACKEND_URL}/api/vault/sessions",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            )
            if r.status_code == 401:
                st.warning("Session expired. Please sign in again.")
                return
            r.raise_for_status()
            sessions = r.json()
    except Exception as e:
        st.error(f"Could not load vault: {e}")
        return

    if not sessions:
        st.info("No saved analyses yet. Run an analysis first!")
        return

    df = pd.DataFrame(sessions)
    if not df.empty and "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])

    # --- Advanced Filters ---
    st.markdown("<hr style='margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)
    with st.expander("🔍 Filters & Sort", expanded=False):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            search = st.text_input("Search by ID or text", placeholder="e.g. 42 or resume", label_visibility="collapsed")
        with fcol2:
            sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "ATS Score (high)", "ATS Score (low)", "Recruiter Score (high)", "Recruiter Score (low)"], label_visibility="collapsed")
        with fcol3:
            score_min = st.slider("Min ATS", 0, 100, 0, label_visibility="collapsed")
        with fcol4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.vault_refresh += 1
                st.rerun()

    # Apply filters
    filtered = df.copy()

    if search:
        mask = filtered.astype(str).apply(lambda row: row.str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    if score_min > 0:
        filtered = filtered[filtered["ats_score"].notna() & (filtered["ats_score"] >= score_min)]

    # Sort
    ascending = False
    sort_col = "created_at"
    if sort_by == "Date (oldest)":
        ascending = True
    elif sort_by == "ATS Score (high)":
        sort_col = "ats_score"
    elif sort_by == "ATS Score (low)":
        sort_col = "ats_score"
        ascending = True
    elif sort_by == "Recruiter Score (high)":
        sort_col = "recruiter_score"
    elif sort_by == "Recruiter Score (low)":
        sort_col = "recruiter_score"
        ascending = True

    if sort_col in filtered.columns:
        filtered = filtered.sort_values(sort_col, ascending=ascending)

    # Display count
    st.markdown(
        f"<p style='color: #6c6a64; font-size: 0.85rem;'>{len(filtered)} of {len(df)} sessions</p>",
        unsafe_allow_html=True,
    )

    # Format date for display
    display_df = filtered.copy()
    if not display_df.empty and "created_at" in display_df.columns:
        display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M")

    for _, row in display_df.iterrows():
        with st.container():
            cols = st.columns([3, 1, 1, 1, 0.8])
            ats_val = row.get("ats_score")
            ats = f"{ats_val:.0f}" if pd.notna(ats_val) else "—"
            rec_val = row.get("recruiter_score")
            rec = f"{rec_val:.0f}" if pd.notna(rec_val) else "—"
            cols[0].markdown(f"**Session #{row['id']}** — {row.get('created_at', '')}")
            cols[1].markdown(f"ATS: `{ats}`")
            cols[2].markdown(f"Recruiter: `{rec}`")
            with cols[3]:
                if st.button("👁 View", key=f"view_{row['id']}"):
                    st.session_state["selected_vault_session"] = int(row["id"])
            with cols[4]:
                if st.button("🗑", key=f"del_{row['id']}"):
                    try:
                        with httpx.Client(timeout=10.0) as client:
                            client.delete(
                                f"{BACKEND_URL}/api/vault/sessions/{row['id']}",
                                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                            )
                        st.session_state.vault_refresh += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
        st.markdown("<hr style='margin:0.3rem 0;'>", unsafe_allow_html=True)

    # Session viewer modal
    selected = st.session_state.get("selected_vault_session")
    if selected:
        with st.container():
            try:
                with httpx.Client(timeout=10.0) as client:
                    r = client.get(
                        f"{BACKEND_URL}/api/vault/sessions/{selected}",
                        headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                    )
                    r.raise_for_status()
                    detail = r.json()
            except Exception as e:
                st.error(f"Could not load session: {e}")
                return

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"<h3>Session #{selected} — Detail</h3>", unsafe_allow_html=True)

            if st.button("← Back to list"):
                del st.session_state["selected_vault_session"]
                st.rerun()

            tabs = st.tabs(["Resume & JD", "ATS", "Recruiter", "HM", "Skill Gap", "Truthfulness", "Selection"])

            with tabs[0]:
                if detail.get("resume_text"):
                    st.markdown("**Resume Text**")
                    st.text_area("", detail["resume_text"], height=200, key=f"sv_resume_{selected}")
                if detail.get("jd_text"):
                    st.markdown("**Job Description**")
                    st.text_area("", detail["jd_text"], height=200, key=f"sv_jd_{selected}")

            with tabs[1]:
                ats = detail.get("ats_result") or {}
                if ats:
                    score = ats.get("ats_score") or ats.get("score") or "—"
                    st.metric("ATS Score", f"{score:.1f}" if isinstance(score, (int, float)) else score)
                    bd = ats.get("breakdown") or {}
                    if bd:
                        st.json(bd)
                    ev = ats.get("evidence")
                    if ev:
                        st.markdown("**Evidence**")
                        st.json(ev)
                else:
                    st.info("No ATS data")

            with tabs[2]:
                rec = detail.get("recruiter_result") or {}
                if rec:
                    st.metric("Recruiter Score", rec.get("score", "—"))
                    st.markdown(f"**Decision:** {rec.get('decision', '—')}")
                    st.markdown(f"**Confidence:** {rec.get('confidence', '—')}")
                    if rec.get("reasoning"):
                        st.markdown(f"**Reasoning:** {rec['reasoning']}")
                else:
                    st.info("No recruiter data")

            with tabs[3]:
                hm = detail.get("hiring_manager_result") or {}
                if hm:
                    st.metric("HM Score", hm.get("score", "—"))
                    st.markdown(f"**Decision:** {hm.get('decision', '—')}")
                    if hm.get("reasoning"):
                        st.markdown(f"**Reasoning:** {hm['reasoning']}")
                else:
                    st.info("No HM data")

            with tabs[4]:
                sg = detail.get("skill_gap_result") or {}
                if sg:
                    st.json(sg)
                else:
                    st.info("No skill gap data")

            with tabs[5]:
                tr = detail.get("truthfulness_result") or {}
                if tr:
                    st.metric("Truthfulness Score", tr.get("score", "—"))
                    dets = tr.get("details") or tr.get("flagged_items")
                    if dets:
                        st.json(dets)
                else:
                    st.info("No truthfulness data")

            with tabs[6]:
                sp = detail.get("selection_probability") or {}
                if sp:
                    st.json(sp)
                else:
                    st.info("No selection probability data")
