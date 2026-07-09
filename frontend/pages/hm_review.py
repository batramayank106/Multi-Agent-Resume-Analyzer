import re
import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.components.charts import score_gauge


def _extract_dimensions(hm: dict) -> list:
    dims = ["Technical Depth", "Project Quality", "Domain Fit", "Growth Trajectory"]
    dim_scores = hm.get("dimension_scores", {}) or {}
    if dim_scores:
        return [(d, dim_scores.get(d, 50)) for d in dims]
    reasoning = hm.get("reasoning", "")
    scores = []
    for dim in dims:
        dl = dim.lower()
        if dl in reasoning.lower():
            idx = reasoning.lower().index(dl)
            nums = re.findall(r'(\d{1,2})(?:\s*\/\s*100|\s*%)?', reasoning[idx:idx+100])
            score = int(nums[0]) if nums else 65
        else:
            score = 50
        scores.append((dim, score))
    return scores


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Hiring Manager Review</h1>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Hiring Manager Review",
        "An LLM evaluates technical depth, project quality, domain fit, and growth trajectory — simulating a hiring manager's perspective. More technically rigorous than the Recruiter Review.",
        "A gauge shows HM score (0-100) with PASS/REJECT. Four dimension scores (Technical Depth, Project Quality, Domain Fit, Growth Trajectory) are displayed. Review notes explain the reasoning.",
        "Run a full analysis first. HM may REJECT where the Simulator PASSes — this is normal (different criteria). Focus on low dimension scores and the review notes for specific improvement areas. HM feedback is the most technically detailed.",
    )

    result = st.session_state.get("analysis_result")
    hm = (result or {}).get("hiring_manager_result", {}) if result else None

    if not hm:
        st.info("Run a full analysis from the ATS Analysis page first.")
        return

    score = hm.get("hiring_manager_score", 0)
    decision = hm.get("decision", "REJECT")
    reasoning = hm.get("reasoning", "")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        fig = score_gauge(score, title="HM Score", height=250)
        st.plotly_chart(fig, width="stretch")

    with col2:
        decision_color = "#5db872" if decision == "PASS" else "#c64545"
        st.markdown(
            f"""
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1.5rem;">
                <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                            text-transform: uppercase; color: #6c6a64;">Technical Depth Assessment</div>
                <div style="font-family: Playfair Display, serif; font-size: 2rem; color: {decision_color}; margin: 0.5rem 0;">
                    {decision}</div>
                <div style="font-family: Inter, sans-serif; font-size: 0.8rem; color: #6c6a64; line-height: 1.5;">
                    Evaluated on technical depth, project quality, domain fit, and growth trajectory.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)

    dimensions = _extract_dimensions(hm)
    st.markdown("<h3 style='font-size: 1rem;'>Evaluation Dimensions</h3>", unsafe_allow_html=True)
    dim_cols = st.columns(len(dimensions))
    for i, (dim, val) in enumerate(dimensions):
        with dim_cols[i]:
            bar_color = "#5db872" if val >= 60 else "#6c6a64"
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <div style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: {bar_color};">{val}%</div>
                    <div style="font-family: Inter, sans-serif; font-size: 0.7rem; color: #6c6a64; text-transform: uppercase;
                                letter-spacing: 1px;">{dim}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='font-size: 1.2rem;'>Review Notes</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 1rem; "
        f"font-size: 0.9rem; color: #3d3d3a; line-height: 1.6;'>{reasoning}</div>",
        unsafe_allow_html=True,
    )
