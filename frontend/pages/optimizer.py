import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.components.charts import improvement_waterfall




def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Resume Optimizer</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; margin-top: -0.3rem;'>"
        "Improvement suggestions based on agent feedback.</p>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Resume Optimizer",
        "Estimates the ATS score impact of each recommended improvement. Shows a waterfall chart of current vs expected scores for each suggestion category.",
        "A waterfall chart shows each improvement area with current score and expected score after the change. Below: rewritten resume text from the Rewrite agent.",
        "Run a full analysis first. Review the waterfall to prioritize changes with the biggest impact. Download the rewritten resume from the Generator page — but review and edit manually before using.",
    )

    result = st.session_state.get("analysis_result")
    rewrite = (result or {}).get("rewrite_result", {}) if result else None

    if not rewrite:
        st.info("Run a full analysis first to see optimization suggestions.")
        return

    ats = (result or {}).get("ats_result", {})
    current_ats = ats.get("overall_score", 0) if ats else 0

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>Improvement Impact Engine</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.5rem;'>"
        "Estimated score impact for each recommended improvement</p>",
        unsafe_allow_html=True,
    )

    improvements = []
    sg = (result or {}).get("skill_gap_result", {}) if result else {}
    missing_skills = sg.get("missing_skills", []) if sg else []
    jd_text = st.session_state.get("jd_text", "")
    for skill in missing_skills[:5]:
        improvements.append({
            "recommendation": f"Add missing skill: {skill}",
            "current": current_ats,
            "expected": min(current_ats + 6, 95),
            "gain": min(6, 95 - current_ats),
            "priority": "High" if skill in missing_skills[:3] else "Medium",
            "difficulty": "Medium",
            "confidence": "80%",
        })

    if not improvements and jd_text:
        improvements.append({
            "recommendation": "Review job description requirements and align resume keywords accordingly",
            "current": current_ats,
            "expected": min(current_ats + 8, 95),
            "gain": min(8, 95 - current_ats),
            "priority": "High",
            "difficulty": "Medium",
            "confidence": "85%",
        })

    # Impact cards
    for imp in improvements[:5]:
        gain_color = "#5db872" if imp["gain"] >= 5 else "#d4a017" if imp["gain"] >= 3 else "#6c6a64"
        priority_color = {"High": "#c64545", "Medium": "#d4a017", "Low": "#5db872"}.get(imp["priority"], "#6c6a64")
        diff_color = {"Low": "#5db872", "Medium": "#d4a017", "Hard": "#c64545"}.get(imp["difficulty"], "#6c6a64")

        st.markdown(
            f"""
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; margin-bottom: 0.6rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
                    <div style="flex: 1;">
                        <div style="font-size: 0.85rem; color: #141413; font-weight: 500;">{imp['recommendation']}</div>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.3rem; font-size: 0.75rem;">
                            <span style="color: #6c6a64;">Current: <strong>{imp['current']}</strong></span>
                            <span style="color: {gain_color};">→ Expected: <strong>{imp['expected']}</strong></span>
                            <span style="color: {gain_color};">Gain: <strong>+{imp['gain']}</strong></span>
                        </div>
                    </div>
                    <div style="text-align: right; font-size: 0.7rem; white-space: nowrap;">
                        <span style="background: {priority_color}15; color: {priority_color}; padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 500;">{imp['priority']}</span>
                        <span style="background: #f5f0e8; color: {diff_color}; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.3rem;">{imp['difficulty']}</span>
                        <div style="margin-top: 0.2rem; color: #6c6a64;">Conf: {imp['confidence']}</div>
                    </div>
                </div>
                <div style="margin-top: 0.5rem; background: #e6dfd8; border-radius: 4px; height: 6px; position: relative;">
                    <div style="background: #cc785c; border-radius: 4px; height: 6px; width: {imp['current']}%;"></div>
                    <div style="background: {gain_color}; border-radius: 4px; height: 6px; width: {imp['gain']}%; position: absolute; left: {imp['current']}%; opacity: 0.6;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Waterfall chart
    if improvements:
        st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Improvement Waterfall</h3>",
            unsafe_allow_html=True,
        )
        fig = improvement_waterfall(improvements[:5])
        if fig:
            st.plotly_chart(fig, width="stretch")

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)

    suggestions = rewrite.get("suggestions_summary", "")
    if suggestions:
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Feedback & Suggestions</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 1rem; "
            f"font-size: 0.9rem; color: #3d3d3a; line-height: 1.6;'>{suggestions}</div>",
            unsafe_allow_html=True,
        )

    rewritten = rewrite.get("rewritten_resume", "")
    if rewritten and "API key" not in rewritten:
        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-top: 1.5rem;'>Generated Resume</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 1rem; "
            f"font-family: JetBrains Mono, monospace; font-size: 0.8rem; color: #3d3d3a; "
            f"white-space: pre-wrap; max-height: 500px; overflow-y: auto;'>{rewritten}</div>",
            unsafe_allow_html=True,
        )

    if ats:
        missing = ats.get("missing_keywords", [])
        if missing:
            st.markdown(
                "<h3 style='font-size: 1.2rem; margin-top: 1.5rem;'>Priority: Add Missing Keywords</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='display: flex; flex-wrap: wrap; gap: 0.4rem;'>"
                + "".join(
                    f"<span style='background: rgba(198, 69, 69, 0.1); border: 1px solid rgba(198, 69, 69, 0.2); "
                    f"border-radius: 4px; padding: 0.2rem 0.6rem; font-size: 0.8rem; color: #c64545;'>{kw}</span>"
                    for kw in missing
                )
                + "</div>",
                unsafe_allow_html=True,
            )
