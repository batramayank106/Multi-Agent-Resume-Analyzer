import streamlit as st
import plotly.express as px
from frontend.utils.state import init, page_guide
from frontend.components.charts import missing_skills_treemap, skill_gap_radar


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Skill Gap Analysis</h1>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Skill Gap Analysis",
        "Compares your resume skills against the job description requirements. Identifies missing required skills, missing preferred skills, and priority levels for each gap.",
        "Gap severity (Low/Medium/High/Critical) is shown at top. A bar chart compares required vs preferred vs missing counts. Missing skills appear in a treemap and list. Priority levels show which skills to learn first.",
        "Run a full analysis with a JD uploaded. Focus on 'Missing Required' skills first — these are dealbreakers. Then work through 'Missing Preferred'. Use the priority levels to plan your learning roadmap.",
    )

    result = st.session_state.get("analysis_result")
    sg = (result or {}).get("skill_gap_result", {}) if result else None

    if not sg:
        st.info("Run a full analysis from the ATS Analysis page first.")
        return

    severity_raw = sg.get("gap_severity", "unknown")
    missing = sg.get("missing_skills", [])
    required = sg.get("required_skills", [])
    preferred = sg.get("preferred_skills", [])
    priority_levels = sg.get("priority_levels", {})

    if isinstance(severity_raw, dict):
        sev_values = [str(v).lower() for v in severity_raw.values()]
        sev_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        ranked = [(sev_rank.get(s, 0), s) for s in sev_values]
        severity = max(ranked, key=lambda x: x[0])[1] if ranked else "unknown"
    else:
        severity = str(severity_raw).lower()

    severity_color = {"high": "#c64545", "critical": "#c64545", "medium": "#d4a017", "low": "#5db872", "unknown": "#6c6a64"}.get(severity, "#6c6a64")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f"""
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1.5rem; text-align: center;">
                <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                            text-transform: uppercase; color: #6c6a64;">Gap Severity</div>
                <div style="font-family: Playfair Display, serif; font-size: 2rem; color: {severity_color};
                            margin: 0.3rem 0; text-transform: capitalize;">{severity}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if required or preferred or missing:
            cats = ["Required", "Preferred", "Missing"]
            counts = [len(required), len(preferred), len(missing)]
            priority_counts = {}
            for cat, skills in [("Required", required), ("Preferred", preferred), ("Missing", missing)]:
                h = sum(1 for s in skills if str(priority_levels.get(s, "low")).lower() == "high")
                m = sum(1 for s in skills if str(priority_levels.get(s, "low")).lower() == "medium")
                l = sum(1 for s in skills if str(priority_levels.get(s, "low")).lower() == "low")
                if h or m or l:
                    priority_counts[cat] = {"High": h, "Medium": m, "Low": l}
                else:
                    priority_counts[cat] = None

            if any(priority_counts.values()):
                import pandas as pd
                rows = []
                for cat in cats:
                    pc = priority_counts.get(cat)
                    if pc:
                        for level, cnt in pc.items():
                            rows.append({"Category": cat, "Priority": level, "Count": cnt})
                df = pd.DataFrame(rows)
                fig = px.bar(
                    df, x="Count", y="Category", color="Priority",
                    orientation="h",
                    color_discrete_map={"High": "#c64545", "Medium": "#d4a017", "Low": "#5db872"},
                    text="Count",
                    barmode="group",
                )
            else:
                fig = px.bar(
                    x=counts, y=cats,
                    orientation="h",
                    color=counts,
                    color_continuous_scale=["#5db8a6", "#e8a55a", "#c64545"],
                    text=counts,
                )
            fig.update_layout(
                height=200,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#6c6a64"},
                showlegend=True,
                legend={"orientation": "h", "y": -0.3, "x": 0, "font": {"size": 11}},
                xaxis={"showgrid": False, "visible": False},
                yaxis={"color": "#141413", "tickfont": {"size": 13}},
            )
            fig.update_traces(textfont={"color": "#141413", "size": 14})
            st.plotly_chart(fig, width="stretch")

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)

    if missing:
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Missing Skills — Treemap</h3>",
            unsafe_allow_html=True,
        )
        fig_tm = missing_skills_treemap(missing, [])
        if fig_tm:
            st.plotly_chart(fig_tm, width="stretch")

        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-top: 0.5rem;'>Missing Skills — List</h3>",
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        for i, skill in enumerate(missing[:12]):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="background: rgba(198, 69, 69, 0.08); border: 1px solid rgba(198, 69, 69, 0.2);
                                border-radius: 6px; padding: 0.4rem 0.8rem; text-align: center; margin-bottom: 0.4rem;
                                font-size: 0.85rem; color: #c64545;">
                        {skill}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if required:
        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-top: 1rem;'>Required Skills</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='display: flex; flex-wrap: wrap; gap: 0.4rem;'>"
            + "".join(
                f"<span style='background: #e6dfd8; border-radius: 4px; padding: 0.2rem 0.6rem; "
                f"font-size: 0.8rem; color: #3d3d3a;'>{s}</span>"
                for s in required
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    if preferred:
        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-top: 1rem;'>Preferred Skills</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='display: flex; flex-wrap: wrap; gap: 0.4rem;'>"
            + "".join(
                f"<span style='background: #efe9de; border: 1px solid #e6dfd8; border-radius: 4px; padding: 0.2rem 0.6rem; "
                f"font-size: 0.8rem; color: #6c6a64;'>{s}</span>"
                for s in preferred
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    if priority_levels:
        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-top: 1rem;'>Priority Levels</h3>",
            unsafe_allow_html=True,
        )
        for skill, level in priority_levels.items():
            level_color = {"high": "#c64545", "medium": "#d4a017", "low": "#5db872"}.get(level.lower(), "#6c6a64")
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 0.6rem; padding: 0.3rem 0;">
                    <span style="font-size: 0.85rem; color: #141413; min-width: 120px;">{skill}</span>
                    <div style="flex: 1; background: #e6dfd8; border-radius: 4px; height: 6px;">
                        <div style="background: {level_color}; border-radius: 4px; height: 6px; width: {'90' if level == 'critical' else '70' if level == 'high' else '50' if level == 'medium' else '30'}%;"></div>
                    </div>
                    <span style="font-size: 0.75rem; color: {level_color}; font-weight: 500; text-transform: capitalize; min-width: 60px;">{level}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    suggested = sg.get("suggested_additions", [])
    if suggested:
        st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Suggested Additions</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color: #6c6a64; font-size: 0.8rem; margin-top: -0.3rem;'>"
            "Complementary skills not in the JD that could strengthen your profile</p>",
            unsafe_allow_html=True,
        )
        for item in suggested:
            skill = item.get("skill", "")
            reason = item.get("reason", "")
            st.markdown(
                f"""
                <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 0.4rem;">
                    <div style="font-family: Inter, sans-serif; font-weight: 500; font-size: 0.85rem; color: #141413;">{skill}</div>
                    <div style="font-family: Inter, sans-serif; font-size: 0.78rem; color: #6c6a64; margin-top: 0.15rem;">{reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
