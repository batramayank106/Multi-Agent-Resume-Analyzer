import streamlit as st
import plotly.graph_objects as go
from frontend.utils.state import init, page_guide

AGENT_INFO = [
    ("ATS Agent", "LLM (Groq / fallback)", "Computes keyword, skill, experience, project, achievement, education, and formatting scores using LLM-driven analysis."),
    ("Recruiter Agent", "LLM (Groq / fallback)", "Evaluates readability, impact, leadership, communication, and achievement orientation."),
    ("HM Agent", "LLM (Groq / fallback)", "Assesses technical depth, project quality, and domain fit."),
    ("Simulator", "LLM (3 calls)", "Runs ATS, HR, and Engineering Manager personas and aggregates results."),
    ("Skill Gap", "LLM (Groq / fallback)", "Compares resume skills against JD requirements and classifies gaps."),
    ("Truthfulness", "LLM (Groq / fallback)", "Scans for exaggerated or misleading claims with classification."),
    ("Company Research", "LLM (Groq / fallback)", "Extracts company name from experience and analyzes via LLM."),
    ("Resume Rewrite", "LLM (Groq / fallback)", "Generates optimized bullet points from agent feedback suggestions."),
    ("Interview Prep", "LLM (Groq / fallback)", "Generates categorized interview questions with difficulty levels."),
    ("Selection Prob.", "LLM (Groq / fallback)", "Estimates hiring probability across stages using all prior scores."),
]

PIPELINE_STEPS = [
    ("ATS Scoring", "LLM evaluation", "#cc785c", "✓"),
    ("Recruiter Review", "LLM evaluation", "#5db8a6", "✓"),
    ("HM Review", "LLM evaluation", "#5db872", "✓"),
    ("Simulator", "3 persona LLM calls", "#e8a55a", "✓"),
    ("Skill Gap", "LLM comparison", "#a9583e", "✓"),
    ("Truthfulness", "LLM validation", "#8e8b82", "✓"),
    ("Company Research", "LLM analysis", "#6c6a64", "✓"),
    ("Resume Rewrite", "LLM generation", "#cc785c", "✎"),
    ("Interview Prep", "LLM generation", "#5db8a6", "✎"),
    ("Selection Prob.", "LLM estimation", "#5db872", "%"),
]

AGENT_SCORE_KEYS = [
    ("ats_result", "ATS Agent", "overall_score", None),
    ("recruiter_result", "Recruiter Agent", "recruiter_score", None),
    ("hiring_manager_result", "HM Agent", "hiring_manager_score", None),
    ("simulator_results", "Simulator", "overall_confidence", "overall_decision"),
    ("skill_gap_result", "Skill Gap", None, "gap_severity"),
    ("truthfulness_result", "Truthfulness", "truthfulness_score", None),
    ("company_result", "Company Research", None, "overall_suitability"),
    ("selection_probability", "Selection Prob.", "overall_probability", None),
]


def _score_display(value, label) -> str:
    if value is None:
        return '<span style="color:#6c6a64;font-size:0.8rem;">—</span>'
    return f'<span style="color:#141413;font-size:0.9rem;font-weight:500;">{value}</span>'


def _agent_score(agent_result: dict, num_key: str, label_key: str):
    if not agent_result or agent_result.get("error"):
        return None, "⚠ Error"
    val = agent_result.get(num_key) if num_key else None
    label = agent_result.get(label_key) if label_key else None
    if isinstance(label, dict):
        sev_values = [str(v).lower() for v in label.values()]
        sev_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        ranked = [(sev_rank.get(s, 0), s) for s in sev_values]
        label = max(ranked, key=lambda x: x[0])[1] if ranked else "unknown"
    display = label or val
    if display is None:
        display = "✓"
    if val is not None:
        return val, str(display)
    return None, str(display)


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>AI Engineering Insights</h1>",
        unsafe_allow_html=True,
    )
    page_guide(
        "AI Insights",
        "Technical overview of the 12-agent pipeline: shows the execution flow, confidence scores from each agent, agent descriptions, and a decision trail (which agents passed/failed/errored).",
        "Pipeline Flow diagram shows the sequential order. Confidence Scores table shows each agent's output. Agent Details expanders explain each agent's role. Decision Trail shows status per agent.",
        "Run a full analysis first. Use this page to understand which agents succeeded or failed. If an agent shows 'Error', check the reasoning or re-run the analysis. This is the best page for debugging pipeline issues.",
    )

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>System Architecture</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.5rem;'>"
        "High-level system overview — Frontend, Backend, Pipeline, and Storage layers</p>",
        unsafe_allow_html=True,
    )
    st.image(
        "diagrams/System Architecture - Transparent Background.png",
        use_container_width=True,
    )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>Pipeline Flow</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.5rem;'>"
        "Sequential 10-agent LangGraph state machine</p>",
        unsafe_allow_html=True,
    )

    nodes_html = ""
    for i, (step, engine, color, icon) in enumerate(PIPELINE_STEPS):
        nodes_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;gap:2px;min-width:80px;">
            <div style="width:36px;height:36px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;
                        font-size:0.85rem;color:white;font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.1);">{icon}</div>
            <span style="font-size:0.65rem;color:#3d3d3a;text-align:center;line-height:1.2;font-weight:500;">{step}</span>
            <span style="font-size:0.6rem;color:#6c6a64;text-align:center;">{engine}</span>
        </div>"""
        if i < len(PIPELINE_STEPS) - 1:
            nodes_html += '<div style="color:#6c6a64;font-size:1.2rem;flex-shrink:0;">→</div>'

    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:0.5rem;padding:1rem 0;">{nodes_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>Confidence Scores</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.5rem;'>"
        "Scores and confidence levels across all agents</p>",
        unsafe_allow_html=True,
    )

    result = st.session_state.get("analysis_result")
    scores_data = []
    score_labels = []
    if result:
        for key, label, num_key, label_key in AGENT_SCORE_KEYS:
            agent_res = result.get(key, {})
            val, display = _agent_score(agent_res, num_key, label_key)
            scores_data.append((label, val, display))
            if val is not None:
                score_labels.append(label)
    else:
        for key, label, num_key, label_key in AGENT_SCORE_KEYS:
            scores_data.append((label, None, "—"))

    cols = st.columns(len(scores_data))
    for i, (label, val, display) in enumerate(scores_data):
        with cols[i]:
            color = "#5db872" if (val is not None and val >= 60) or (isinstance(display, str) and display in ("PASS", "EXCELLENT", "GOOD", "low")) else "#6c6a64"
            if isinstance(display, str) and display in ("PASS", "CONDITIONAL", "REJECT"):
                color = {"PASS": "#5db872", "CONDITIONAL": "#d4a017", "REJECT": "#c64545"}.get(display, "#6c6a64")
            st.markdown(
                f"""
                <div style="background:#efe9de;border:1px solid #e6dfd8;border-radius:8px;padding:0.6rem;text-align:center;height:100%;">
                    <div style="font-family:Inter,sans-serif;font-size:0.6rem;letter-spacing:1px;text-transform:uppercase;color:#6c6a64;">{label}</div>
                    <div style="font-family:Playfair Display,serif;font-size:1.1rem;color:{color};margin:0.2rem 0;">{display}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if result and any(v is not None for _, v, _ in scores_data):
        numeric = [(l, v) for l, v, _ in scores_data if v is not None]
        if len(numeric) >= 2:
            fig = go.Figure(data=go.Bar(
                x=[l for l, v in numeric],
                y=[v for l, v in numeric],
                marker=dict(color=["#cc785c", "#5db8a6", "#5db872", "#e8a55a", "#a9583e", "#cc785c", "#5db8a6", "#5db872"]),
                text=[f"{v}" for l, v in numeric],
                textposition="outside",
            ))
            fig.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=10, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#6c6a64", "size": 11},
                xaxis={"showgrid": False, "tickfont": {"size": 10}},
                yaxis={"showgrid": True, "gridcolor": "#e6dfd8", "range": [0, 110]},
                showlegend=False,
            )
            st.plotly_chart(fig, width="stretch")

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>Agent Details</h2>",
        unsafe_allow_html=True,
    )

    for name, engine, desc in AGENT_INFO:
        with st.expander(f"**{name}** — {engine}"):
            st.markdown(
                f"<p style='font-size: 0.9rem; color: #3d3d3a; line-height: 1.6;'>{desc}</p>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.6rem;'>Decision Trail</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.5rem;'>"
        "Status and key output for every agent in the pipeline</p>",
        unsafe_allow_html=True,
    )

    if result:
        for key, label, num_key, label_key in AGENT_SCORE_KEYS:
            agent_res = result.get(key, {})
            if agent_res and not agent_res.get("error"):
                val, display = _agent_score(agent_res, num_key, label_key)
                dl = str(display).lower()
                if dl in ("high", "critical", "reject"):
                    icon = "✗"
                    icon_color = "#c64545"
                elif dl in ("medium", "conditional"):
                    icon = "≈"
                    icon_color = "#d4a017"
                else:
                    icon = "✓"
                    icon_color = "#5db872"
                st.markdown(
                    f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 6px; "
                    f"padding: 0.5rem 1rem; margin-bottom: 0.3rem; display: flex; justify-content: space-between; align-items: center;'>"
                    f"<span style='font-size: 0.85rem; color: #141413;'>{label}</span>"
                    f"<span style='font-size: 0.85rem; color: {icon_color};'>{display} {icon}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif agent_res and agent_res.get("error"):
                st.markdown(
                    f"<div style='background: #fce8e8; border: 1px solid rgba(198, 69, 69, 0.2); border-radius: 6px; "
                    f"padding: 0.5rem 1rem; margin-bottom: 0.3rem; display: flex; justify-content: space-between;'>"
                    f"<span style='font-size: 0.85rem; color: #141413;'>{label}</span>"
                    f"<span style='font-size: 0.85rem; color: #c64545;'>✗ {agent_res.get('error', 'Failed')}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Run a full analysis to see the decision trail.")
