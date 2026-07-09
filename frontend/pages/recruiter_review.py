import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.components.charts import score_gauge


def _extract_dimensions(rec: dict) -> list:
    dims = ["Readability", "Impact", "Leadership", "Communication", "Achievement"]
    dim_scores = rec.get("dimension_scores", {}) or {}
    if dim_scores:
        return [(d, dim_scores.get(d, 50)) for d in dims]
    reasoning = rec.get("reasoning", "")
    scores = []
    for dim in dims:
        dl = dim.lower()
        if dl in reasoning.lower():
            idx = reasoning.lower().index(dl)
            snippet = reasoning[idx:idx+100]
            import re
            nums = re.findall(r'(\d{1,2})(?:\s*\/\s*100|\s*%)?', snippet)
            score = int(nums[0]) if nums else 60
        else:
            score = 50
        scores.append((dim, score))
    return scores


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Recruiter Review</h1>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Recruiter Review",
        "An LLM evaluates your resume as a human recruiter would — scoring readability, impact, leadership, communication, and achievement orientation. Each dimension scored 0-100.",
        "A gauge shows the overall recruiter score (0-100). Below it: PASS/REJECT decision, confidence %, and 5 dimension bars. The reasoning panel explains why each score was given.",
        "Run a full analysis first. Review the dimension scores to see which areas need improvement (e.g., low Leadership score → add people-management achievements). Use the reasoning text for specific rewrite suggestions.",
    )

    result = st.session_state.get("analysis_result")
    rec = (result or {}).get("recruiter_result", {}) if result else None

    if not rec:
        st.info("Run a full analysis from the ATS Analysis page first.")
        return

    score = rec.get("recruiter_score", 0)
    decision = rec.get("decision", "REJECT")
    confidence = rec.get("confidence", 0)
    reasoning = rec.get("reasoning", "")

    col1, col2, col3 = st.columns(3)
    with col1:
        fig = score_gauge(score, title="Recruiter Score", height=250)
        st.plotly_chart(fig, width="stretch")

    with col2:
        decision_color = "#5db872" if decision == "PASS" else "#c64545"
        st.markdown(
            f"""
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1.5rem; text-align: center;">
                <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                            text-transform: uppercase; color: #6c6a64;">Decision</div>
                <div style="font-family: Playfair Display, serif; font-size: 2rem; color: {decision_color}; margin: 0.3rem 0;">
                    {decision}</div>
                <div style="font-family: Inter, sans-serif; font-size: 0.8rem; color: #6c6a64;">
                    Confidence: {confidence}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        dimensions = _extract_dimensions(rec)
        for dim, val in dimensions:
            bar_color = "#5db8a6" if val >= 60 else "#6c6a64"
            st.markdown(
                f"""
                <div style="margin-bottom: 0.4rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem;">
                        <span style="color: #141413;">{dim}</span>
                        <span style="color: #6c6a64;">{val}%</span>
                    </div>
                    <div style="background: #e6dfd8; border-radius: 3px; height: 4px; width: 100%;">
                        <div style="background: {bar_color}; border-radius: 3px; height: 4px; width: {val}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='font-size: 1.2rem;'>Reasoning</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 1rem; "
        f"font-size: 0.9rem; color: #3d3d3a; line-height: 1.6;'>{reasoning}</div>",
        unsafe_allow_html=True,
    )
