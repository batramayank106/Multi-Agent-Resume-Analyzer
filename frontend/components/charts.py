import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

PRIMARY = "#cc785c"
PRIMARY_ACTIVE = "#a9583e"
SUCCESS = "#5db872"
WARNING = "#d4a017"
ERROR = "#c64545"
TEAL = "#5db8a6"
MUTED = "#6c6a64"
MUTED_SOFT = "#8e8b82"
HAIRLINE = "#e6dfd8"
INK = "#141413"
BODY = "#3d3d3a"
SURFACE_SOFT = "#f5f0e8"
SURFACE_CARD = "#efe9de"

SCORE_BADGES = [
    (90, "Exceptional", SUCCESS),
    (75, "Strong", TEAL),
    (60, "Good", WARNING),
    (40, "Average", "#e8a55a"),
    (0, "Poor", ERROR),
]

CATEGORY_COLORS = {
    "keyword_match": PRIMARY,
    "skill_match": TEAL,
    "experience_match": SUCCESS,
    "project_match": "#e8a55a",
    "achievements": PRIMARY_ACTIVE,
    "education": MUTED_SOFT,
    "formatting": MUTED,
}

CATEGORY_LABELS = {
    "keyword_match": "Keyword Match",
    "skill_match": "Skill Match",
    "experience_match": "Experience Match",
    "project_match": "Project Match",
    "achievements": "Achievements",
    "education": "Education",
    "formatting": "Formatting",
}


def _badge(score):
    for threshold, label, color in SCORE_BADGES:
        if score >= threshold:
            return label, color
    return "Poor", ERROR


def ats_gauge(score: float, height: int = 280) -> go.Figure:
    label, label_color = _badge(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"font": {"size": 48, "family": "Playfair Display, serif", "color": INK}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"size": 12}},
            "bar": {"color": PRIMARY, "thickness": 0.4},
            "bgcolor": SURFACE_SOFT,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#fce8e8"},
                {"range": [40, 60], "color": "#fdf0d8"},
                {"range": [60, 75], "color": "#e8f5e0"},
                {"range": [75, 90], "color": "#d0ede8"},
                {"range": [90, 100], "color": "#c8e6c0"},
            ],
            "threshold": {
                "line": {"color": PRIMARY_ACTIVE, "width": 3},
                "thickness": 0.6,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED},
        annotations=[
            go.layout.Annotation(
                x=0.5, y=0.15, xref="paper", yref="paper",
                text=f"<span style='font-family: Inter, sans-serif; font-weight: 500; color: {label_color};'>{label}</span>",
                showarrow=False,
            )
        ],
    )
    return fig


def score_gauge(score: float, title: str = "", height: int = 220) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"font": {"size": 36, "family": "Playfair Display, serif", "color": INK}},
        title={"text": title, "font": {"size": 14, "color": MUTED, "family": "Inter, sans-serif"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"size": 10}},
            "bar": {"color": PRIMARY, "thickness": 0.35},
            "bgcolor": SURFACE_SOFT,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#fce8e8"},
                {"range": [40, 60], "color": "#fdf0d8"},
                {"range": [60, 75], "color": "#e8f5e0"},
                {"range": [75, 90], "color": "#d0ede8"},
                {"range": [90, 100], "color": "#c8e6c0"},
            ],
        },
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED},
    )
    return fig


def breakdown_bars(breakdown: dict, height: int = 250) -> go.Figure:
    items = []
    scores = []
    colors = []
    for key, data in breakdown.items():
        name = key.replace("_", " ").title()
        items.append(name)
        scores.append(data.get("score", 0))
        colors.append(CATEGORY_COLORS.get(key, MUTED))

    fig = go.Figure(go.Bar(
        x=items,
        y=scores,
        marker_color=colors,
        text=scores,
        textposition="outside",
        hovertemplate="%{x}: %{y}/100<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor=HAIRLINE, title="Score"),
        xaxis=dict(tickangle=-30),
        showlegend=False,
    )
    return fig


def selection_funnel(stages: dict, height: int = 400) -> go.Figure:
    if not stages:
        return None
    stage_names = list(stages.keys())
    values = []
    for v in stages.values():
        try:
            pct_str = str(v).replace("%", "").split("-")[0].strip()
            values.append(float(pct_str))
        except (ValueError, AttributeError):
            values.append(50)

    fig = go.Figure(go.Funnel(
        y=stage_names,
        x=values,
        textposition="inside",
        textinfo="percent initial",
        marker={"color": [PRIMARY, TEAL, SUCCESS, WARNING, ERROR]},
        hovertemplate="%{y}: %{x}%<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
    )
    return fig


def skill_gap_radar(skills_present: list[str], skills_missing: list[str], height: int = 350) -> go.Figure:
    all_skills = list(set(skills_present[:8] + skills_missing[:8]))
    if not all_skills:
        return None
    present_vals = [100 if s in skills_present else 0 for s in all_skills]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[100] * len(all_skills),
        theta=all_skills,
        fill="toself",
        name="Required",
        line_color=HAIRLINE,
        opacity=0.3,
    ))
    fig.add_trace(go.Scatterpolar(
        r=present_vals,
        theta=all_skills,
        fill="toself",
        name="Present",
        line_color=PRIMARY,
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=40, r=40, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def missing_skills_treemap(missing_required: list[str], missing_preferred: list[str], height: int = 350) -> go.Figure:
    if not missing_required and not missing_preferred:
        return None
    labels = []
    parents = []
    values = []
    colors = []

    if missing_required:
        labels.append("Missing Required")
        parents.append("")
        values.append(len(missing_required))
        colors.append(ERROR)
        for s in missing_required[:15]:
            labels.append(s)
            parents.append("Missing Required")
            values.append(5)
            colors.append("#fce8e8")

    if missing_preferred:
        labels.append("Missing Preferred")
        parents.append("")
        values.append(len(missing_preferred))
        colors.append(WARNING)
        for s in missing_preferred[:15]:
            labels.append(s)
            parents.append("Missing Preferred")
            values.append(3)
            colors.append("#fdf0d8")

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker_colors=colors,
        textinfo="label+value",
        hovertemplate="%{label}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=5, r=5, t=5, b=5),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def persona_comparison(personas: list[dict], height: int = 300) -> go.Figure:
    if not personas:
        return None
    names = []
    decisions = []
    confidences = []
    colors = []
    for p in personas:
        if isinstance(p, dict):
            names.append(p.get("persona", p.get("name", "Unknown"))[:12])
            decision = p.get("decision", p.get("verdict", "N/A"))
            decisions.append(decision)
            confidences.append(p.get("confidence", 0) * 100 if p.get("confidence", 0) <= 1 else p.get("confidence", 0))
            colors.append(SUCCESS if "pass" in str(decision).lower() else (WARNING if "conditional" in str(decision).lower() else ERROR))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Confidence",
        x=names,
        y=confidences,
        marker_color=colors,
        text=[f"{c:.0f}%" for c in confidences],
        textposition="outside",
        hovertemplate="%{x}: %{y:.0f}%<br>Decision: %{text}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor=HAIRLINE, title="Confidence %"),
        showlegend=False,
    )
    return fig


def version_timeline(versions: list[dict], height: int = 300) -> go.Figure:
    if not versions:
        return None
    df = pd.DataFrame(versions)
    fig = go.Figure()
    score_cols = [c for c in ["ats", "recruiter", "hm", "ats_score", "recruiter_score", "hm_score"] if c in df.columns]
    colors_map = {"ats": PRIMARY, "recruiter": TEAL, "hm": SUCCESS, "ats_score": PRIMARY, "recruiter_score": TEAL, "hm_score": SUCCESS}
    labels_map = {"ats": "ATS", "recruiter": "Recruiter", "hm": "HM", "ats_score": "ATS", "recruiter_score": "Recruiter", "hm_score": "HM"}
    for col in score_cols:
        fig.add_trace(go.Scatter(
            x=df.get("version", df.index),
            y=df[col],
            mode="lines+markers",
            name=labels_map.get(col, col),
            line={"color": colors_map.get(col, MUTED), "width": 2},
            marker={"size": 8},
            hovertemplate="%{x}<br>%{y:.0f}/100<extra></extra>",
        ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor=HAIRLINE, title="Score"),
        xaxis=dict(title="Version"),
        hovermode="x unified",
    )
    return fig


def improvement_waterfall(items: list[dict], height: int = 350) -> go.Figure:
    if not items:
        return None
    names = []
    current_vals = []
    expected_vals = []
    for item in items:
        names.append(item.get("recommendation", item.get("name", "Item"))[:25])
        current_vals.append(item.get("current_score", item.get("current", 0)))
        expected_vals.append(item.get("expected_score", item.get("expected", 0)))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current",
        x=names,
        y=current_vals,
        marker_color=MUTED_SOFT,
        text=current_vals,
        textposition="outside",
        hovertemplate="%{x}<br>Current: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Expected",
        x=names,
        y=expected_vals,
        marker_color=PRIMARY,
        text=expected_vals,
        textposition="outside",
        hovertemplate="%{x}<br>Expected: %{y}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor=HAIRLINE, title="ATS Score"),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def persona_radar(personas: list[dict], height: int = 350) -> go.Figure:
    if not personas:
        return None
    dimensions = ["Keyword Match", "Formatting", "Technical Depth", "Communication", "Leadership", "Experience"]
    fig = go.Figure()
    colors_list = [PRIMARY, TEAL, SUCCESS, WARNING]
    for idx, p in enumerate(personas):
        if isinstance(p, dict):
            name = p.get("persona", p.get("name", f"Persona {idx+1}"))[:15]
            scores = []
            for dim in dimensions:
                dim_key = dim.lower().replace(" ", "_")
                scores.append(p.get(dim_key, p.get("scores", {}).get(dim_key, 70)))
            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=dimensions,
                fill="toself",
                name=name,
                line_color=colors_list[idx % len(colors_list)],
                opacity=0.7,
            ))
    fig.update_layout(
        height=height,
        margin=dict(l=40, r=40, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def score_comparison(scores_a: dict, scores_b: dict, height: int = 300) -> go.Figure:
    categories = []
    vals_a = []
    vals_b = []
    for key in ["ats_score", "recruiter_score", "hm_score", "truthfulness_score"]:
        label = key.replace("_", " ").title().replace("Hm", "HM")
        categories.append(label)
        vals_a.append(scores_a.get(key, 0))
        vals_b.append(scores_b.get(key, 0))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Version A", x=categories, y=vals_a, marker_color=MUTED_SOFT))
    fig.add_trace(go.Bar(name="Version B", x=categories, y=vals_b, marker_color=PRIMARY))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "family": "Inter, sans-serif"},
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor=HAIRLINE, title="Score"),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
