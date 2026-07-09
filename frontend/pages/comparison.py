import httpx
import streamlit as st
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import has_resume, has_jd
from frontend.components.charts import score_comparison


def render():
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Resume Version Comparison</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; margin-top: -0.3rem;'>"
        "Compare two analysis sessions side by side with score deltas and diff highlighting.</p>",
        unsafe_allow_html=True,
    )

    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    sessions = []
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/vault/sessions", headers=headers)
            if r.status_code == 200:
                sessions = r.json()
    except Exception:
        pass

    tab1, tab2 = st.tabs(["Vault Version Compare", "Manual Compare"])

    with tab1:
        st.markdown(
            "<p style='color: #6c6a64; font-size: 0.85rem;'>"
            "Select two analysis sessions from your resume vault to compare.</p>",
            unsafe_allow_html=True,
        )

        if len(sessions) < 2:
            st.info("Need at least 2 analysis sessions in the vault to compare versions.")
            return

        options = {f"#{s['id']} — ATS {s.get('ats_score', '?')} ({s['created_at'][:10]})": s["id"] for s in sessions}

        col1, col2 = st.columns(2)
        with col1:
            sel_a = st.selectbox("Version A (older)", options.keys(), index=len(sessions) - 2, key="v_a")
        with col2:
            sel_b = st.selectbox("Version B (newer)", options.keys(), index=len(sessions) - 1, key="v_b")

        v1_id = options[sel_a]
        v2_id = options[sel_b]

        if st.button("Compare Versions", type="primary", use_container_width=True):
            if v1_id == v2_id:
                st.warning("Select two different sessions to compare.")
                return

            with st.spinner("Computing version diff..."):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        r = client.get(
                            f"{BACKEND_URL}/api/vault/compare",
                            params={"v1": v1_id, "v2": v2_id},
                            headers=headers,
                        )
                        r.raise_for_status()
                        data = r.json()
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    return

            _render_diff_results(data)

    with tab2:
        resume_text = st.session_state.get("resume_text", "")
        jd_text = st.session_state.get("jd_text", "")
        result = st.session_state.get("analysis_result")
        rewrite = (result or {}).get("rewrite_result", {}) if result else None
        rewritten = (rewrite or {}).get("rewritten_resume", "")

        col1, col2 = st.columns(2)
        with col1:
            text_a = st.text_area(
                "Original Resume", resume_text or "Paste the original resume here...",
                height=250, key="comp_orig",
            )
        with col2:
            text_b = st.text_area(
                "Optimized Resume", rewritten or "Paste the optimized resume here...",
                height=250, key="comp_opt",
            )

        skills_a = st.session_state.get("parsed_skills", [])
        skills_b_input = st.text_input(
            "Skills (optimized, comma-separated)",
            value=", ".join(skills_a) if skills_a else "",
            key="comp_skills",
        )

        if st.button("Compare Text", type="primary", use_container_width=True):
            skills_b = [s.strip() for s in skills_b_input.split(",") if s.strip()]

            if not text_a or not text_b:
                st.warning("Both resume versions are required.")
                return

            with st.spinner("Computing diff..."):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        r = client.post(f"{BACKEND_URL}/api/compare/resumes", json={
                            "text_a": text_a,
                            "text_b": text_b,
                            "skills_a": skills_a,
                            "skills_b": skills_b,
                        }, headers=headers)
                        r.raise_for_status()
                        data = r.json()
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    return

            _render_text_diff(data)

    if not has_resume() and len(sessions) < 2:
        st.info("Upload a resume and run analysis to see comparison data, or check the vault for existing sessions.")


def _render_diff_results(data: dict):
    score_deltas = data.get("score_deltas", {})
    skills = data.get("skills", {})
    keywords = data.get("keywords", {})
    bullets = data.get("bullet_changes", {})
    projects = data.get("project_changes", {})
    summary = data.get("improvement_summary", "")

    st.markdown(
        f"<div style='background:#efe9de;border:1px solid #e6dfd8;border-radius:10px;padding:1rem;margin-bottom:1rem;'>"
        f"<div style='font-family:Playfair Display,serif;font-size:1rem;color:#141413;margin-bottom:0.3rem;'>Improvement Summary</div>"
        f"<p style='color:#3d3d3a;font-size:0.9rem;margin:0;'>{summary}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<h3 style='font-size:1.2rem;'>Score Deltas</h3>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    for col, name, key, color in [
        (sc1, "ATS", "ats", "#cc785c"),
        (sc2, "Recruiter", "recruiter", "#5db8a6"),
        (sc3, "HM", "hm", "#5db872"),
    ]:
        delta = score_deltas.get(key, 0)
        sign = "+" if delta > 0 else ""
        col.markdown(
            f"<div style='text-align:center;background:#f5f0e8;border-radius:8px;padding:0.8rem;'>"
            f"<div style='color:#6c6a64;font-size:0.7rem;text-transform:uppercase;'>{name}</div>"
            f"<div style='font-family:Playfair Display,serif;font-size:1.8rem;color:{color};'>{sign}{delta}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    fig = score_comparison(
        {"ats_score": data["version_a"]["score"] or 0, "recruiter_score": 0, "hm_score": 0},
        {"ats_score": data["version_b"]["score"] or 0, "recruiter_score": 0, "hm_score": 0},
    )
    if fig:
        st.plotly_chart(fig, width="stretch")

    if skills.get("added") or skills.get("removed"):
        st.markdown("**Skills Changes**")
        c1, c2 = st.columns(2)
        if skills["added"]:
            c1.markdown(
                "<div style='font-size:0.8rem;color:#2d7a3d;'>➕ Added</div>"
                + "".join(
                    f"<span style='background:#e8f5e0;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.15rem;display:inline-block;'>{s}</span>"
                    for s in skills["added"]
                ),
                unsafe_allow_html=True,
            )
        if skills["removed"]:
            c2.markdown(
                "<div style='font-size:0.8rem;color:#c64545;'>➖ Removed</div>"
                + "".join(
                    f"<span style='background:#fde8e8;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.15rem;display:inline-block;'>{s}</span>"
                    for s in skills["removed"]
                ),
                unsafe_allow_html=True,
            )

    if projects.get("added") or projects.get("removed"):
        st.markdown("**Project Changes**")
        pc1, pc2 = st.columns(2)
        if projects["added"]:
            pc1.markdown(
                "<div style='font-size:0.8rem;color:#2d7a3d;'>➕ New Projects</div>"
                + "".join(
                    f"<div style='font-size:0.8rem;color:#3d3d3a;padding:0.1rem 0;'>• {p}</div>"
                    for p in projects["added"]
                ),
                unsafe_allow_html=True,
            )
        if projects["removed"]:
            pc2.markdown(
                "<div style='font-size:0.8rem;color:#c64545;'>➖ Removed Projects</div>"
                + "".join(
                    f"<div style='font-size:0.8rem;color:#3d3d3a;padding:0.1rem 0;'>• {p}</div>"
                    for p in projects["removed"]
                ),
                unsafe_allow_html=True,
            )

    st.markdown("**Content Changes**")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Bullet Points Added", bullets.get("added", 0))
    cc2.metric("Bullet Points Removed", bullets.get("removed", 0))
    cc3.metric("Keywords Common", keywords.get("common_count", 0))


def _render_text_diff(data: dict):
    total = data["added_lines"] + data["removed_lines"] + data["unchanged_lines"]
    st.markdown(
        f"<div style='display:flex;gap:1rem;margin-bottom:1rem;'>"
        f"<span style='background:#e8f5e0;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.8rem;'>+{data['added_lines']} added</span>"
        f"<span style='background:#fde8e8;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.8rem;'>-{data['removed_lines']} removed</span>"
        f"<span style='background:#f5f0e8;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.8rem;'>{data['unchanged_lines']} unchanged</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    sk = data["skills"]
    if sk.get("added") or sk.get("removed"):
        st.markdown("**Skills Changes**")
        c1, c2 = st.columns(2)
        if sk["added"]:
            c1.markdown(
                "<div style='font-size:0.8rem;color:#2d7a3d;'>➕ Added</div>"
                + "".join(
                    f"<span style='background:#e8f5e0;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.15rem;display:inline-block;'>{s}</span>"
                    for s in sk["added"]
                ),
                unsafe_allow_html=True,
            )
        if sk["removed"]:
            c2.markdown(
                "<div style='font-size:0.8rem;color:#c64545;'>➖ Removed</div>"
                + "".join(
                    f"<span style='background:#fde8e8;border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.15rem;display:inline-block;'>{s}</span>"
                    for s in sk["removed"]
                ),
                unsafe_allow_html=True,
            )

    st.markdown("**Side-by-Side Diff**")
    diff_col1, diff_col2 = st.columns(2)

    def render_diff_col(lines, label, bg):
        html = f"<div style='background:{bg};border:1px solid #e6dfd8;border-radius:8px;padding:0.5rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;max-height:500px;overflow-y:auto;white-space:pre-wrap;'>"
        html += f"<div style='color:#6c6a64;font-size:0.65rem;margin-bottom:0.3rem;'>{label}</div>"
        for dl in lines:
            if dl["type"] == "insert":
                html += f"<div style='background:rgba(93,184,114,0.15);color:#2d7a3d;padding:1px 4px;'><span style='color:#5db872;'>+ </span>{dl['line'] or '⏎'}</div>"
            elif dl["type"] == "delete":
                html += f"<div style='background:rgba(198,69,69,0.1);color:#c64545;padding:1px 4px;'><span style='color:#c64545;'>- </span>{dl['line'] or '⏎'}</div>"
            else:
                html += f"<div style='color:#3d3d3a;padding:1px 4px;'>  {dl['line'] or '⏎'}</div>"
        html += "</div>"
        return html

    diff_col1.markdown(render_diff_col(data["lines_a"], "Original", "#faf9f5"), unsafe_allow_html=True)
    diff_col2.markdown(render_diff_col(data["lines_b"], "Optimized", "#faf9f5"), unsafe_allow_html=True)
