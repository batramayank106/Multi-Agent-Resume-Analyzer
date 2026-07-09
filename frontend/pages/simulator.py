import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.components.charts import persona_comparison, persona_radar


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Recruiter Simulator</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; margin-top: -0.3rem;'>"
        "Three-perspective simulation: ATS, HR, and Engineering Manager personas.</p>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Recruiter Simulator",
        "Three separate LLM calls role-play as ATS, HR Professional, and Engineering Manager — each scoring your resume independently. Aggregated: 3/3 PASS = PASS, 2/3 = CONDITIONAL, <2 = REJECT.",
        "Each persona shows PASS/REJECT + confidence %. The aggregate decision and confidence are shown at top. A comparison chart visualizes all three. Each persona has its own explanation and suggestions.",
        "Run a full analysis first. If personas disagree, read each explanation to understand why. Different agents in the pipeline may give different results (HM is more technically strict than the EM persona here). Use suggestions from each persona for targeted improvements.",
    )

    result = st.session_state.get("analysis_result")
    sim = (result or {}).get("simulator_results", {}) if result else None

    if not sim:
        st.info("Run a full analysis from the ATS Analysis page first.")
        return

    overall = sim.get("overall_decision", "REJECT")
    confidence = sim.get("overall_confidence", 0)
    persona_results = sim.get("persona_results", {})

    decision_color = {"PASS": "#5db872", "CONDITIONAL": "#d4a017", "REJECT": "#c64545"}.get(overall, "#6c6a64")

    st.markdown(
        f"""
        <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px;
                    padding: 1.2rem; text-align: center; margin-bottom: 1.5rem;">
            <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                        text-transform: uppercase; color: #6c6a64;">Aggregate Decision</div>
            <div style="font-family: Playfair Display, serif; font-size: 2.2rem; color: {decision_color};
                        margin: 0.3rem 0;">{overall}</div>
            <div style="font-family: Inter, sans-serif; font-size: 0.85rem; color: #6c6a64;">
                Confidence: {confidence}% · {sim.get('summary', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    persona_labels = {"ATS": "ATS System", "HR": "HR Professional", "Engineering Manager": "Engineering Manager"}
    persona_icons = {"ATS": "🤖", "HR": "👔", "Engineering Manager": "👥"}

    for idx, (persona, pr) in enumerate(persona_results.items()):
        with cols[idx]:
            p_decision = pr.get("decision", "REJECT")
            p_conf = pr.get("confidence", 0)
            p_suggestions = pr.get("suggestions", "")
            p_explanation = pr.get("explanation", "")
            p_color = {"PASS": "#5db872", "CONDITIONAL": "#d4a017", "REJECT": "#c64545"}.get(p_decision, "#6c6a64")
            icon = persona_icons.get(persona, "🎭")

            with st.expander(f"{icon} **{persona_labels.get(persona, persona)}** — {p_decision}", expanded=True):
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                            <span style="font-family: Playfair Display, serif; font-size: 1.5rem; color: {p_color};">{p_decision}</span>
                            <span style="font-family: Inter, sans-serif; font-size: 0.85rem; color: #6c6a64;">Confidence: {p_conf}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if p_explanation:
                    st.markdown(
                        f"<div style='font-size:0.85rem;color:#3d3d3a;line-height:1.5;margin-bottom:0.5rem;'><strong>Explanation:</strong><br>{p_explanation}</div>",
                        unsafe_allow_html=True,
                    )
                if p_suggestions:
                    st.markdown(
                        f"<div style='background:#f5f0e8;border:1px solid #e6dfd8;border-radius:6px;padding:0.5rem 0.7rem;font-size:0.8rem;color:#6c6a64;line-height:1.5;'><strong>Suggestions:</strong><br>{p_suggestions}</div>",
                        unsafe_allow_html=True,
                    )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h3 style='font-size: 1.2rem;'>Persona Comparison</h3>",
        unsafe_allow_html=True,
    )

    persona_list = []
    for persona, pr in persona_results.items():
        persona_list.append({
            "persona": persona,
            "decision": pr.get("decision", "REJECT"),
            "confidence": pr.get("confidence", 0),
        })
    fig = persona_comparison(persona_list)
    if fig:
        st.plotly_chart(fig, width="stretch")

    decisions = [pr.get("decision", "REJECT") for pr in persona_results.values()]
    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.2rem;'>Decision Summary</h3>", unsafe_allow_html=True)
    for persona, pr in persona_results.items():
        p_decision = pr.get("decision", "REJECT")
        p_color = {"PASS": "#5db872", "CONDITIONAL": "#d4a017", "REJECT": "#c64545"}.get(p_decision, "#6c6a64")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; padding: 0.4rem 0;">
                <span style="font-family: Inter, sans-serif; font-size: 0.85rem; color: #141413; min-width: 140px;">{persona_labels.get(persona, persona)}</span>
                <div style="flex:1; background: #e6dfd8; border-radius: 4px; height: 8px;">
                    <div style="background: {p_color}; border-radius: 4px; height: 8px; width: {pr.get('confidence', 0)}%;"></div>
                </div>
                <span style="font-family: Inter, sans-serif; font-size: 0.8rem; color: {p_color}; font-weight: 500; min-width: 80px; text-align: right;">{p_decision} ({pr.get('confidence', 0)}%)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
