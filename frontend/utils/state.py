import threading
import streamlit as st
from frontend.utils.api_client import run_full_analysis, start_analysis_stream


def init():
    if "resume_text" not in st.session_state:
        st.session_state.resume_text = ""
        st.session_state.jd_text = ""
        st.session_state.analysis_result = None
        st.session_state.analysis_running = False
        st.session_state.demo_loaded = False
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_info = None
        st.session_state._analysis_auto_started = False
        st.session_state._stream_results = {}
        st.session_state._ats_displayed = False
        st.session_state._polling_started = False
        st.session_state._analysis_run_id = None
        st.session_state._ats_run_btn = False


def has_resume() -> bool:
    return bool(st.session_state.get("resume_text", ""))


def has_jd() -> bool:
    return bool(st.session_state.get("jd_text", ""))


def can_analyze() -> bool:
    return has_resume()


def auto_trigger_analysis():
    if st.session_state.get("_analysis_auto_started"):
        return
    if not has_resume() or not has_jd():
        return
    if st.session_state.get("analysis_running"):
        return
    if st.session_state.get("analysis_result") is not None:
        return

    st.session_state._analysis_auto_started = True
    st.session_state.analysis_running = True
    st.session_state._stream_results = {}
    st.session_state._ats_displayed = False
    st.session_state._analysis_run_id = None
    st.session_state._polling_started = False
    st.session_state._ats_run_btn = False

    resp = start_analysis_stream(
        resume_text=st.session_state.resume_text,
        jd_text=st.session_state.jd_text,
    )
    if resp and resp.get("run_id"):
        st.session_state._analysis_run_id = resp["run_id"]
        st.session_state._polling_started = True
    else:
        def _run():
            try:
                result = run_full_analysis(
                    resume_text=st.session_state.resume_text,
                    jd_text=st.session_state.jd_text,
                )
                st.session_state.analysis_result = result
            except Exception:
                st.session_state.analysis_result = {"status": "error", "errors": ["Analysis failed"]}
            finally:
                st.session_state.analysis_running = False

        threading.Thread(target=_run, daemon=True).start()


def is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))


def login(access_token: str, refresh_token: str, user_info: dict):
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.user_info = user_info


def logout():
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_info = None


def is_super_admin() -> bool:
    info = st.session_state.get("user_info")
    return bool(info and info.get("role") == "super_admin")


INFO_ICON = """
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6c6a64" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""


def page_guide(title: str, what: str, expect: str, todo: str):
    import streamlit as st
    st.markdown(
        f"<div style='background:#f5f0e8;border:1px solid #e6dfd8;border-radius:8px;padding:0.5rem 1rem;margin-bottom:1rem;'>"
        f"<div style='display:flex;gap:0.5rem;align-items:flex-start;'>"
        f"<div style='flex-shrink:0;margin-top:1px;'>{INFO_ICON}</div>"
        f"<div style='font-size:0.82rem;color:#3d3d3a;line-height:1.5;'>"
        f"<strong style='color:#141413;'>{title}</strong><br>"
        f"<strong>What it does:</strong> {what}<br>"
        f"<strong>What to expect:</strong> {expect}<br>"
        f"<strong>What to do:</strong> {todo}"
        f"</div></div>",
        unsafe_allow_html=True,
    )
