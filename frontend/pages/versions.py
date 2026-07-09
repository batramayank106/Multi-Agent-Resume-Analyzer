import httpx
import streamlit as st
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import init, page_guide
from frontend.components.charts import version_timeline


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Resume Versions</h1>",
        unsafe_allow_html=True,
    )
    page_guide(
        "Score Trends & Versions",
        "Tracks scores (ATS, Recruiter, HM) across multiple analysis runs on the same resume. Each run creates a new version with incremented version number.",
        "A line chart shows score trends across versions. Below: version history cards showing scores per run. If only one version exists, the chart shows a single point — run more analyses to see trends.",
        "Run multiple analyses on the same resume (make edits between runs) to track improvement over time. Each analysis auto-saves as a new version with scores from all agents.",
    )
    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    versions = []
    sessions = []
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/vault/versions", headers=headers)
            if r.status_code == 200:
                versions = r.json()
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/vault/sessions", headers=headers)
            if r.status_code == 200:
                sessions = r.json()
    except Exception:
        pass

    result = st.session_state.get("analysis_result")
    ats = (result or {}).get("ats_result", {}) if result else None
    rec = (result or {}).get("recruiter_result", {}) if result else None
    hm = (result or {}).get("hiring_manager_result", {}) if result else None

    if not versions and not sessions and not ats:
        st.info("Run a full analysis first to see version tracking.")
        st.markdown(
            """
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1.5rem; text-align: center; margin-top: 0.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📅</div>
                <p style="color: #6c6a64; font-size: 0.85rem;">
                    Version tracking records scores each time you run an analysis.<br>
                    Each analysis creates a new version with all scores.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    versions_data = []
    seen = set()
    label_counter = 1
    for v in versions:
        vkey = (v.get("ats_score"), v.get("recruiter_score"), v.get("hiring_manager_score"))
        if vkey not in seen:
            seen.add(vkey)
            versions_data.append({
                "version": f"v{label_counter}",
                "ats": v.get("ats_score") or 0,
                "recruiter": v.get("recruiter_score") or 0,
                "hm": v.get("hiring_manager_score") or 0,
            })
            label_counter += 1
    for s in sessions:
        vkey = (s.get("ats_score"), s.get("recruiter_score"), s.get("hm_score"))
        if vkey not in seen:
            seen.add(vkey)
            versions_data.append({
                "version": f"v{label_counter}",
                "ats": s.get("ats_score") or 0,
                "recruiter": s.get("recruiter_score") or 0,
                "hm": s.get("hm_score") or 0,
            })
            label_counter += 1
    if not versions_data and ats:
        current_ats_val = ats.get("overall_score", 0) or ats.get("ats_score", 0)
        current_rec_val = rec.get("recruiter_score", 0) if rec else 0
        current_hm_val = hm.get("hiring_manager_score", 0) if hm else 0
        versions_data.append({
            "version": "v1 (current)",
            "ats": current_ats_val,
            "recruiter": current_rec_val,
            "hm": current_hm_val,
        })

    if versions_data:
        st.markdown(
            "<h2 style='font-size: 1.4rem;'>Score Trends</h2>",
            unsafe_allow_html=True,
        )

        fig = version_timeline(versions_data)
        if fig:
            st.plotly_chart(fig, width="stretch")

        st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Version History</h3>",
            unsafe_allow_html=True,
        )

        for v in versions_data:
            st.markdown(
                f"""
                <div style="background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 0.7rem 1rem; margin-bottom: 0.4rem;
                            display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: #141413; font-weight: 500;">{v['version']}</span>
                    <span style="font-size: 0.8rem; color: #6c6a64;">
                        ATS: <strong style="color:#cc785c;">{v['ats']}</strong> &nbsp;·&nbsp;
                        Recruiter: <strong style="color:#5db8a6;">{v['recruiter']}</strong> &nbsp;·&nbsp;
                        HM: <strong style="color:#5db872;">{v['hm']}</strong>
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if len(versions_data) >= 2:
            first_ats = versions_data[0]["ats"]
            last_ats = versions_data[-1]["ats"]
            change = last_ats - first_ats
            sign = "+" if change > 0 else ""
            st.markdown(
                f"""
                <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; text-align: center; margin-top: 0.5rem;">
                    <div style="font-size: 0.8rem; color: #6c6a64; margin-bottom: 0.3rem;">ATS Score Change (all versions)</div>
                    <div style="font-family: Playfair Display, serif; font-size: 1.5rem; color: {"#5db872" if change >= 0 else "#c64545"};">{sign}{change} points</div>
                    <div style="font-size: 0.75rem; color: #6c6a64;">{first_ats} → {last_ats} across {len(versions_data)} version(s)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
