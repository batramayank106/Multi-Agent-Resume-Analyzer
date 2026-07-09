import threading
import time
import streamlit as st
from frontend.utils.state import init, can_analyze, page_guide
from frontend.utils.api_client import run_full_analysis, start_analysis_stream, poll_analysis_status
from frontend.utils.loading import show_pipeline_animation
from frontend.utils.sanitize import xss_escape
from frontend.components.charts import ats_gauge, SCORE_BADGES, CATEGORY_LABELS, CATEGORY_COLORS
from frontend.utils.state import page_guide

AGENTS = ["ATS", "Recruiter", "HM", "Simulator", "Skill Gap", "Truth", "Company", "Salary", "Rewrite", "Interview", "Famous Qs", "Selection"]

AGENT_BACKEND_KEYS = [
    "ats_agent", "recruiter_agent", "hiring_manager_agent",
    "simulator_agent", "skill_gap_agent", "truthfulness_agent",
    "company_agent", "salary_agent", "rewrite_agent",
    "interview_agent", "famous_questions_agent", "selection_agent",
]

AGENT_RESULT_KEYS = {
    "ats_agent": "ats_result",
    "recruiter_agent": "recruiter_result",
    "hiring_manager_agent": "hiring_manager_result",
    "simulator_agent": "simulator_results",
    "skill_gap_agent": "skill_gap_result",
    "truthfulness_agent": "truthfulness_result",
    "company_agent": "company_result",
    "salary_agent": "salary_result",
    "rewrite_agent": "rewrite_result",
    "interview_agent": "interview_result",
    "famous_questions_agent": "famous_questions_result",
    "selection_agent": "selection_probability",
}

AGENT_DISPLAY = dict(zip(AGENT_BACKEND_KEYS, AGENTS))

AGENT_PAGE_LINKS = {
    "ats_agent": "/ats",
    "recruiter_agent": "/recruiter",
    "hiring_manager_agent": "/hm",
    "simulator_agent": "/simulator",
    "skill_gap_agent": "/skill_gap",
    "truthfulness_agent": "/ai_insights",
    "company_agent": "/company",
    "salary_agent": "/company",
    "rewrite_agent": "/optimizer",
    "interview_agent": "/interview",
    "famous_questions_agent": "/interview",
    "selection_agent": "/ai_insights",
}


def _badge(score):
    for threshold, label, color in SCORE_BADGES:
        if score >= threshold:
            return label, color
    return "Poor", "#c64545"


def _display_ats_results(ats):
    overall = ats.get("overall_score", 0)
    label, label_color = _badge(overall)
    breakdown = ats.get("breakdown", {})
    evidence = ats.get("evidence", [])

    col1, col2 = st.columns([1, 1.5])
    with col1:
        fig = ats_gauge(overall)
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown(
            "<h3 style='font-size: 1.2rem; margin-bottom: 0.5rem;'>Score Breakdown</h3>",
            unsafe_allow_html=True,
        )
        for cat_key, cat_data in breakdown.items():
            cat_name = CATEGORY_LABELS.get(cat_key, cat_key)
            cat_score = cat_data.get("score", 0)
            cat_contrib = cat_data.get("contribution", 0)
            color = CATEGORY_COLORS.get(cat_key, "#6c6a64")
            pct = cat_score / 100
            bar_color = color if cat_score >= 50 else "#c64545"
            st.markdown(
                f"""
                <div style="margin-bottom: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                        <span style="color: #141413; font-weight: 500;">{cat_name}</span>
                        <span style="color: #6c6a64;">{cat_score} · +{cat_contrib:.1f}</span>
                    </div>
                    <div style="background: #e6dfd8; border-radius: 4px; height: 6px; width: 100%;">
                        <div style="background: {bar_color}; border-radius: 4px; height: 6px; width: {pct * 100}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h3 style='font-size: 1.2rem;'>Evidence & Deductions</h3>",
        unsafe_allow_html=True,
    )
    for ev in evidence:
        cat = ev.get("category", "")
        deductions = ev.get("deductions", [])
        cat_name = CATEGORY_LABELS.get(cat, cat)
        color = CATEGORY_COLORS.get(cat, "#6c6a64")
        with st.expander(f"\u25a0 {cat_name} ({len(deductions)} items)"):
            for d in deductions:
                if isinstance(d, dict):
                    detail = xss_escape(d.get("detail", str(d)))
                    kw_type = d.get("type", "")
                    icon = "\u2713" if kw_type == "matched" else "\u2717"
                    st.markdown(
                        f"<p style='font-size: 0.85rem; color: #3d3d3a; margin: 0.2rem 0;'>{icon} {detail}</p>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<p style='font-size: 0.85rem; color: #3d3d3a; margin: 0.2rem 0;'>\u2022 {xss_escape(str(d))}</p>",
                        unsafe_allow_html=True,
                    )


def _nav_buttons(results):
    has_any = any(results.get(rk) for rk in AGENT_RESULT_KEYS.values())
    if not has_any:
        return
    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='font-size: 1.2rem; margin-bottom: 0.5rem;'>Other Analysis Results</h3>",
        unsafe_allow_html=True,
    )
    page_map = st.session_state.get("_page_objects", {})
    items = []
    for bk, rk in AGENT_RESULT_KEYS.items():
        if results.get(rk) and bk != "ats_agent":
            page_url = AGENT_PAGE_LINKS.get(bk, "")
            label = AGENT_DISPLAY.get(bk, bk)
            page_obj = page_map.get(page_url.lstrip("/"))
            items.append((page_obj, page_url, label))
    if not items:
        return
    cols = st.columns(min(4, len(items)))
    for i, (page_obj, page_url, label) in enumerate(items):
        with cols[i % len(cols)]:
            try:
                if page_obj:
                    st.page_link(page_obj, label=f"\u2192 {label}", use_container_width=True)
                else:
                    st.page_link(page_url, label=f"\u2192 {label}", use_container_width=True)
            except Exception:
                st.markdown(f"<p style='font-size:0.8rem;color:#6c6a64;'>\u2192 {label}</p>", unsafe_allow_html=True)


def _get_completed_agents(results: dict) -> list[str]:
    completed = []
    for bk, rk in AGENT_RESULT_KEYS.items():
        if results.get(rk):
            completed.append(bk)
    return completed


def render():
    init()

    st.markdown(
        "<h1 style='font-size: 2.2rem;'>ATS Analysis</h1>",
        unsafe_allow_html=True,
    )

    page_guide(
        "ATS Analysis",
        "Runs a 12-agent pipeline that evaluates your resume across ATS scoring, recruiter/HM review, simulator, skill gaps, truthfulness, company research, salary, rewrite, interview questions, and selection probability.",
        "A progress bar shows each agent completing. After completion (~30-60s), scores appear: overall ATS score (0-100), category breakdowns, and evidence for deductions. Navigate to individual pages for detailed results.",
        "Upload a resume (and JD for best results), then click 'Run Full Analysis'. Wait for all 12 agents to complete. Visit each agent page to see details.",
    )

    if not can_analyze():
        st.warning("Upload a resume first to run the ATS analysis.")
        return

    has_results = st.session_state.get("analysis_result") is not None and st.session_state.analysis_result.get("status") in ("completed", "partial")
    is_running = st.session_state.get("analysis_running", False)
    run_id = st.session_state.get("_analysis_run_id")
    polling_started = st.session_state.get("_polling_started", False)

    auto_started = not st.session_state.get("_ats_run_btn", False) and st.session_state.get("_analysis_auto_started", False)

    if is_running:
        st.caption("\u2699\ufe0f Analysis pipeline is running in background \u2014 results appear automatically as agents complete.")
    elif has_results:
        if st.button("Re-run Analysis", type="secondary", use_container_width=True):
            st.session_state._ats_run_btn = True
            st.session_state.analysis_running = True
            st.session_state._polling_started = False
            st.session_state._stream_results = {}
            st.session_state._analysis_run_id = None
            st.session_state._ats_displayed = False

            resp = start_analysis_stream(
                resume_text=st.session_state.resume_text,
                jd_text=st.session_state.get("jd_text"),
            )
            if resp and resp.get("run_id"):
                st.session_state._analysis_run_id = resp["run_id"]
                st.session_state._polling_started = True
            else:
                def _run():
                    try:
                        result = run_full_analysis(
                            resume_text=st.session_state.resume_text,
                            jd_text=st.session_state.get("jd_text"),
                        )
                        st.session_state.analysis_result = result
                    except Exception:
                        st.session_state.analysis_result = {"status": "error", "errors": ["Analysis failed"]}
                    finally:
                        st.session_state.analysis_running = False
                threading.Thread(target=_run, daemon=True).start()
            st.rerun()
    else:
        if st.button("Run Analysis", type="primary", use_container_width=True, disabled=is_running):
            st.session_state._ats_run_btn = True
            st.session_state.analysis_running = True
            st.session_state._polling_started = False
            st.session_state._stream_results = {}
            st.session_state._analysis_run_id = None
            st.session_state._ats_displayed = False

            resp = start_analysis_stream(
                resume_text=st.session_state.resume_text,
                jd_text=st.session_state.get("jd_text"),
            )
            if resp and resp.get("run_id"):
                st.session_state._analysis_run_id = resp["run_id"]
                st.session_state._polling_started = True
            else:
                def _run():
                    try:
                        result = run_full_analysis(
                            resume_text=st.session_state.resume_text,
                            jd_text=st.session_state.get("jd_text"),
                        )
                        st.session_state.analysis_result = result
                    except Exception:
                        st.session_state.analysis_result = {"status": "error", "errors": ["Analysis failed"]}
                    finally:
                        st.session_state.analysis_running = False
                threading.Thread(target=_run, daemon=True).start()
            st.rerun()

    if is_running and polling_started and run_id:
        status_data = poll_analysis_status(run_id)
        poll_status = status_data.get("status", "not_found")

        if poll_status == "not_found":
            st.session_state.analysis_running = False
            st.session_state._analysis_run_id = None
            st.session_state._polling_started = False
            st.error("\u26a0\ufe0f Analysis tracking expired (server may have restarted). Click **Run Analysis** again.")
            st.rerun()
            return

        current_agent = status_data.get("current_agent", "")
        agent_index = status_data.get("current_agent_index", -1)
        results = status_data.get("results", {})
        poll_done = poll_status in ("completed", "error")

        if not poll_done and current_agent and agent_index >= 0:
            display_name = AGENT_DISPLAY.get(current_agent, current_agent)
            show_pipeline_animation(AGENTS, active_index=agent_index)
            st.info(f"\u2699\ufe0f Analyzing \u2014 currently running: **{display_name}**")
        elif not poll_done:
            show_pipeline_animation(AGENTS, active_index=0)
            st.info("\u2699\ufe0f Starting analysis...")
        else:
            show_pipeline_animation(AGENTS, active_index=len(AGENTS))

        ats_data = results.get("ats_result")
        if ats_data and not st.session_state.get("_ats_displayed"):
            st.session_state._ats_displayed = True
            st.session_state._stream_results = results
            st.success("\u2705 ATS Analysis complete! Results shown below. Other agents still running in background.")
            _display_ats_results(ats_data)
        elif ats_data and st.session_state.get("_ats_displayed"):
            _display_ats_results(ats_data)

        _nav_buttons(results)

        completed = _get_completed_agents(results)
        if completed and len(completed) > 1:
            with st.expander(f"\u2139\ufe0f Completed agents ({len(completed)}/12)", expanded=False):
                for bk in AGENT_BACKEND_KEYS:
                    rk = AGENT_RESULT_KEYS[bk]
                    if results.get(rk):
                        st.markdown(f"\u2705 **{AGENT_DISPLAY[bk]}** \u2014 done")

        if poll_done:
            st.session_state.analysis_running = False
            st.session_state.analysis_result = {
                "status": "completed" if poll_status == "completed" else "partial",
                **results,
            }
            st.session_state._analysis_run_id = None
            st.session_state._polling_started = False
            if poll_status == "completed":
                st.success("\u2705 Full analysis pipeline complete!")
            else:
                st.warning(f"\u26a0\ufe0f Analysis completed with {len(status_data.get('errors', []))} error(s).")
            if not st.session_state.get("_ats_displayed") and results.get("ats_result"):
                _display_ats_results(results["ats_result"])
            if has_any_other := any(results.get(rk) for rk in list(AGENT_RESULT_KEYS.values())[1:]):
                _nav_buttons(results)
            st.rerun()
        else:
            time.sleep(2)
            st.rerun()

    elif is_running and not polling_started:
        show_pipeline_animation(AGENTS, active_index=0)
        st.info("\u2699\ufe0f Analysis pipeline is running \u2014 this will update automatically once the ATS part is ready.")
        time.sleep(1)
        st.rerun()

    result = st.session_state.get("analysis_result")
    ats = (result or {}).get("ats_result", {}) if result else None

    if not ats and not is_running:
        st.markdown(
            "<p style='color: #6c6a64; margin-top: 1rem;'>Click <strong>Run Analysis</strong> above to see ATS results.</p>",
            unsafe_allow_html=True,
        )
        return

    if ats and not is_running:
        _display_ats_results(ats)
        _nav_buttons(result or {})
