import httpx
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import init

COLORS = {"primary": "#cc785c", "teal": "#5db8a6", "green": "#5db872", "gold": "#d4a017", "red": "#c64545", "muted": "#6c6a64", "ink": "#141413"}


def _fetch_sessions():
    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/vault/sessions", headers=headers)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return []


def _trend_chart(df):
    if df.empty or "created_at" not in df.columns:
        return None
    plot_df = df.copy()
    plot_df["created_at"] = pd.to_datetime(plot_df["created_at"])
    plot_df = plot_df.sort_values("created_at")
    fig = go.Figure()
    for col, name, color in [("ats_score", "ATS", COLORS["primary"]), ("recruiter_score", "Recruiter", COLORS["teal"]), ("hm_score", "HM", COLORS["green"])]:
        if col in plot_df.columns:
            valid = plot_df[plot_df[col].notna()]
            if not valid.empty:
                fig.add_trace(go.Scatter(x=valid["created_at"], y=valid[col], mode="lines+markers", name=name, line=dict(color=color, width=2), marker=dict(size=6)))
    fig.update_layout(
        title="Score Trends Across Sessions",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["ink"], size=12),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    fig.update_xaxes(gridcolor="#e6dfd8")
    fig.update_yaxes(gridcolor="#e6dfd8")
    return fig


def _benchmark_gauge(current, avg, label, color):
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current,
        delta=dict(reference=avg, increasing=dict(color=COLORS["green"]), decreasing=dict(color=COLORS["red"])),
        title=dict(text=label, font=dict(size=14)),
        number=dict(font=dict(size=28, color=color)),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))
    fig.update_layout(height=140, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def _build_category_df(df):
    rows = []
    for _, row in df.iterrows():
        bd = row.get("ats_breakdown") or {}
        if not isinstance(bd, dict):
            continue
        for cat_key in ["keyword_match", "skill_match", "experience_match", "project_match", "achievements", "education", "formatting"]:
            score = None
            if isinstance(bd, dict):
                if cat_key in bd and isinstance(bd[cat_key], dict):
                    score = bd[cat_key].get("score")
                elif cat_key in bd and isinstance(bd[cat_key], (int, float)):
                    score = bd[cat_key]
            if score is not None:
                created = pd.to_datetime(row.get("created_at")).strftime("%Y-%m-%d") if pd.notna(row.get("created_at")) else "Unknown"
                rows.append({"Session": created, "Category": cat_key.replace("_", " ").title(), "Score": score})
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def render():
    init()
    st.markdown("<h1 style='font-size: 2.2rem;'>Vault Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6c6a64; margin-top: -0.3rem;'>Score trends, benchmarks, and insights across all analysis sessions.</p>", unsafe_allow_html=True)

    sessions = _fetch_sessions()
    if not sessions:
        st.info("No vault sessions found. Run some analyses first to see analytics.")
        return

    df = pd.DataFrame(sessions)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])

    current = st.session_state.get("analysis_result", {})
    current_ats = (current.get("ats_result") or {}).get("overall_score") if current else None

    st.markdown("<hr style='margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    avg_ats = df["ats_score"].mean() if "ats_score" in df.columns else 0
    avg_rec = df["recruiter_score"].mean() if "recruiter_score" in df.columns else 0
    avg_hm = df["hm_score"].mean() if "hm_score" in df.columns else 0
    mcol1.metric("Total Sessions", len(df))
    mcol2.metric("Avg ATS Score", f"{avg_ats:.0f}" if avg_ats else "—")
    mcol3.metric("Avg Recruiter", f"{avg_rec:.0f}" if avg_rec else "—")
    mcol4.metric("Avg HM", f"{avg_hm:.0f}" if avg_hm else "—")

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)

    trend_fig = _trend_chart(df)
    if trend_fig:
        st.plotly_chart(trend_fig, use_container_width=True)

    if current_ats is not None:
        st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size:1.2rem;'>Current Session vs Vault Averages</h3>", unsafe_allow_html=True)
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.plotly_chart(_benchmark_gauge(current_ats, avg_ats, "ATS Score", COLORS["primary"]), use_container_width=True)
        current_rec = (current.get("recruiter_result") or {}).get("overall_score")
        with bcol2:
            if current_rec:
                st.plotly_chart(_benchmark_gauge(current_rec, avg_rec, "Recruiter", COLORS["teal"]), use_container_width=True)
        current_hm = (current.get("hiring_manager_result") or {}).get("overall_score")
        with bcol3:
            if current_hm:
                st.plotly_chart(_benchmark_gauge(current_hm, avg_hm, "HM", COLORS["green"]), use_container_width=True)

    cat_df = _build_category_df(df)
    if not cat_df.empty:
        st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size:1.2rem;'>Category Score Heatmap</h3>", unsafe_allow_html=True)
        pivot = cat_df.pivot_table(index="Category", columns="Session", values="Score", aggfunc="first")
        if not pivot.empty:
            fig = px.imshow(
                pivot,
                text_auto=".0f",
                aspect="auto",
                color_continuous_scale=["#f5f0e8", "#cc785c", "#a9583e"],
                labels=dict(x="Session Date", y="Category", color="Score"),
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=COLORS["ink"], size=11),
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    if "ats_score" in df.columns:
        st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size:1.2rem;'>Score Distribution</h3>", unsafe_allow_html=True)
        dist_data = []
        for col, label in [("ats_score", "ATS"), ("recruiter_score", "Recruiter"), ("hm_score", "HM")]:
            if col in df.columns:
                for val in df[col].dropna():
                    dist_data.append({"Score": val, "Metric": label})
        dist_df = pd.DataFrame(dist_data)
        if not dist_df.empty:
            fig = px.histogram(dist_df, x="Score", color="Metric", nbins=10, barmode="overlay", opacity=0.6, color_discrete_map={"ATS": COLORS["primary"], "Recruiter": COLORS["teal"], "HM": COLORS["green"]})
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["ink"], size=12), margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(gridcolor="#e6dfd8")
            fig.update_yaxes(gridcolor="#e6dfd8")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size:1.2rem;'>Key Insights</h3>", unsafe_allow_html=True)
    insights = []
    if "ats_score" in df.columns:
        best_idx = df["ats_score"].idxmax()
        worst_idx = df["ats_score"].idxmin()
        insights.append(f"🏆 Best ATS score: **{df.loc[best_idx, 'ats_score']:.0f}** (Session #{int(df.loc[best_idx, 'id'])})")
        insights.append(f"📉 Lowest ATS score: **{df.loc[worst_idx, 'ats_score']:.0f}** (Session #{int(df.loc[worst_idx, 'id'])})")
        if avg_ats >= 70:
            insights.append(f"✅ Overall performance: **Strong** (avg ATS {avg_ats:.0f}/100)")
        elif avg_ats >= 50:
            insights.append(f"⚡ Overall performance: **Average** (avg ATS {avg_ats:.0f}/100)")
        else:
            insights.append(f"🔻 Overall performance: **Needs improvement** (avg ATS {avg_ats:.0f}/100)")
    for ins in insights:
        st.markdown(f"<p style='font-size:0.9rem;color:#3d3d3a;margin:0.2rem 0;'>{ins}</p>", unsafe_allow_html=True)
