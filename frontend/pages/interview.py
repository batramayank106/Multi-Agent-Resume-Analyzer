import re
import json
import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.utils.api_client import llm_chat
from frontend.utils.sanitize import xss_escape

ROLES = {
    "Data Analyst": {
        "technical": ["SQL proficiency", "statistical analysis", "data visualization", "ETL pipelines", "A/B testing"],
        "behavioral": ["stakeholder communication", "business acumen", "problem-solving approach"],
    },
    "Software Engineer": {
        "technical": ["data structures & algorithms", "system design", "API design", "database optimization", "testing"],
        "behavioral": ["team collaboration", "project ownership", "technical communication"],
    },
    "Engineering Manager": {
        "technical": ["system architecture", "code review", "technical strategy", "incident management"],
        "behavioral": ["team leadership", "mentorship", "stakeholder management", "conflict resolution", "hiring"],
    },
    "Product Manager": {
        "technical": ["technical feasibility", "data-driven decisions", "A/B testing"],
        "behavioral": ["cross-functional leadership", "customer empathy", "prioritization", "communication"],
    },
    "General": {
        "technical": ["role-specific fundamentals"],
        "behavioral": ["general interview preparation"],
    },
}


def _extract_company(jd_text: str) -> str:
    patterns = [
        r"(?:at|for|with)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s*(?:is|are|we|the|an?|a|,|\.|$))",
        r"^([A-Z][A-Za-z0-9\s&.]+?)\s*(?:is|are|we|hiring|seeks)",
        r"(?:company|organization|firm)\s*[:is]+\s*([A-Z][A-Za-z0-9\s&.]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
        if m:
            candidate = m.group(1).strip()
            if 2 < len(candidate) < 60:
                return candidate
    return ""


def _build_prompt(resume_text, jd_text, role, company, github, portfolio, other_links):
    return f"""You are a senior technical interviewer at {company or "the company"}. Generate interview questions.

Role: {role}
Company: {company or "Not specified"}

Candidate Resume:
{resume_text[:3000]}

Job Description:
{jd_text[:2000]}

Links:
- GitHub: {github or "N/A"}
- Portfolio: {portfolio or "N/A"}
- Other: {other_links or "N/A"}

Generate 10-14 questions across ALL these categories:

1. **Technical** — role-specific depth questions for {role}
2. **Behavioral** — past experience, teamwork, conflict resolution STAR questions
3. **Project & Portfolio** — questions about the candidate's SPECIFIC projects from their resume and links
4. **System Design / Case Study** — architecture or analytical problem-solving
5. **Company-Specific** — questions tailored to {company or "the company"} (values, tech stack, culture from JD)
6. **Resume-Based Recruiter** — questions a recruiter would ask about specific resume items (gaps, job hops, achievements, claims)

Return ONLY valid JSON. No markdown. No explanation.
{{"questions": [
  {{"category": "Technical", "question": "...", "difficulty": "Easy|Medium|Hard", "rationale": "..."}}
]}}"""


def render():
    init()

    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Interview Preparation</h1>",
        unsafe_allow_html=True,
    )
    page_guide(
        "Interview Preparation",
        "Generates role-specific interview questions using your resume, JD, project links, and company context. Covers Technical, Behavioral, Project & Portfolio, System Design, Company-Specific, and Resume-Based categories. Also includes Famous Questions from top tech firms.",
        "Select a role and optionally enter company/project links. Click 'Generate Questions' to get 10-14 questions with difficulty labels and rationale. Famous Questions tab shows company-specific well-known questions.",
        "Upload resume + JD first for context. Select your target role and company. Add GitHub/portfolio links for project-specific questions. Click 'Generate Questions'. Practice answering aloud — the rationale tells you what the interviewer is looking for.",
    )
    result = st.session_state.get("analysis_result")
    iv = (result or {}).get("interview_result", {}) if result else None
    resume_text = st.session_state.get("resume_text", "")
    jd_text = st.session_state.get("jd_text", "")

    if "interview_role" not in st.session_state:
        st.session_state.interview_role = "General"
    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = None
    if "interview_company" not in st.session_state:
        st.session_state.interview_company = ""

    detected_company = _extract_company(jd_text)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("<p style='font-size:0.8rem;color:#6c6a64;margin-bottom:0.2rem;'>Role</p>", unsafe_allow_html=True)
        role_options = list(ROLES.keys())
        role = st.selectbox("", role_options, index=role_options.index("General"), label_visibility="collapsed")
        if role != st.session_state.interview_role:
            st.session_state.interview_role = role
            st.session_state.interview_questions = None

    with col2:
        st.markdown("<p style='font-size:0.8rem;color:#6c6a64;margin-bottom:0.2rem;'>Company</p>", unsafe_allow_html=True)
        if detected_company:
            st.markdown(f"<div style='background:#efe9de;border:1px solid #e6dfd8;border-radius:6px;padding:0.5rem 0.8rem;font-size:0.85rem;color:#141413;'>{xss_escape(detected_company)}</div>", unsafe_allow_html=True)
            st.session_state.interview_company = detected_company
        else:
            manual_company = st.text_input("", placeholder="Company name (optional)", label_visibility="collapsed", key="iv_company_input")
            if manual_company:
                st.session_state.interview_company = manual_company

    with col3:
        web_search_url = ""
        company_search = st.session_state.get("interview_company", "")
        if company_search:
            query = f"{company_search} interview questions glassdoor".replace(" ", "+")
            web_search_url = f"https://www.google.com/search?q={query}"
        st.markdown("<p style='font-size:0.8rem;color:#6c6a64;margin-bottom:0.2rem;'>Web Search</p>", unsafe_allow_html=True)
        if web_search_url:
            st.markdown(f"<a href='{web_search_url}' target='_blank' style='background:#efe9de;border:1px solid #e6dfd8;border-radius:6px;padding:0.5rem 0.8rem;display:block;text-align:center;font-size:0.85rem;color:#cc785c;text-decoration:none;'>🔍 Search {xss_escape(company_search)} questions</a>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#f5f0e8;border:1px solid #e6dfd8;border-radius:6px;padding:0.5rem 0.8rem;font-size:0.85rem;color:#6c6a64;text-align:center;'>Enter company above</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.8rem 0;'>", unsafe_allow_html=True)

    st.markdown("<p style='font-size:0.85rem;color:#6c6a64;margin-bottom:0.5rem;'><strong>Project Links</strong> — add GitHub/portfolio links for project-specific questions</p>", unsafe_allow_html=True)
    link_cols = st.columns(3)
    with link_cols[0]:
        github = st.text_input("GitHub URL", placeholder="https://github.com/...", label_visibility="collapsed", key="iv_github")
    with link_cols[1]:
        portfolio = st.text_input("Portfolio / Blog", placeholder="https://...", label_visibility="collapsed", key="iv_portfolio")
    with link_cols[2]:
        other_links = st.text_input("Other (LinkedIn, etc.)", placeholder="https://...", label_visibility="collapsed", key="iv_other")

    gen_col1, gen_col2 = st.columns([3, 1])
    with gen_col2:
        generate_clicked = st.button("Generate Questions", type="primary", use_container_width=True)

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)

    questions = st.session_state.interview_questions

    if generate_clicked:
        if not resume_text:
            st.warning("Upload a resume first to generate personalized questions.")
        else:
            company_name = st.session_state.get("interview_company", "")
            with st.spinner("Generating interview questions..."):
                prompt = _build_prompt(resume_text, jd_text, role, company_name, github, portfolio, other_links)
                resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7)
                content = resp.get("content", "")
            content_clean = content.strip()
            if content_clean.startswith("```"):
                content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
                content_clean = re.sub(r'\s*```$', '', content_clean)
            try:
                parsed = json.loads(content_clean)
                questions = parsed.get("questions", [])
                st.session_state.interview_questions = questions
            except json.JSONDecodeError:
                st.error("Could not parse generated questions. The LLM returned an unexpected format.")
                st.code(content[:2000], language="text")
                questions = None

    if iv and not questions:
        st.markdown("<p style='color:#6c6a64;font-size:0.85rem;margin-bottom:0.5rem;'>Pre-generated questions from pipeline. Click <strong>Generate Questions</strong> for role-company-project specific ones.</p>", unsafe_allow_html=True)
        questions = iv.get("questions", [])

    # Famous questions from pipeline
    fqr = (result or {}).get("famous_questions_result", {}) if result else None
    famous_qs = (fqr or {}).get("questions", []) if fqr else []

    if questions or famous_qs:
        tab_labels = ["Generated Questions"]
        if famous_qs:
            tab_labels.append(f"Famous Questions ({len(famous_qs)})")
        iv_tabs = st.tabs(tab_labels)

        with iv_tabs[0]:
            count = len(questions)
            company_name = st.session_state.get("interview_company", "")
            st.markdown(f"<p style='color:#6c6a64;font-size:0.85rem;'>{count} questions · Role: {xss_escape(role)}{' · Company: ' + xss_escape(company_name) if company_name else ''}</p>", unsafe_allow_html=True)

            categories = {}
            for q in questions:
                cat = q.get("category", "General")
                categories.setdefault(cat, []).append(q)

            cat_order = ["Technical", "Behavioral", "Project & Portfolio", "System Design / Case Study", "Company-Specific", "Resume-Based Recruiter", "General"]
            ordered_cats = [c for c in cat_order if c in categories] + [c for c in categories if c not in cat_order]

            if ordered_cats:
                subtabs = st.tabs(ordered_cats)
                for ti, cat in enumerate(ordered_cats):
                    with subtabs[ti]:
                        icon_map = {
                            "Technical": "💻", "Behavioral": "🧠", "Project & Portfolio": "📂",
                            "System Design / Case Study": "🏗️", "Company-Specific": "🏢", "Resume-Based Recruiter": "👔",
                        }
                        icon = icon_map.get(cat, "📌")
                        st.markdown(f"<p style='font-size:0.9rem;color:#6c6a64;margin-bottom:0.8rem;'>{icon} {cat}</p>", unsafe_allow_html=True)
                        for q in categories[cat]:
                            text = q.get("question", q.get("text", ""))
                            difficulty = q.get("difficulty", "Medium")
                            rationale = q.get("rationale", "")
                            diff_color = {"Easy": "#5db872", "Medium": "#d4a017", "Hard": "#c64545"}.get(difficulty, "#6c6a64")
                            st.markdown(
                                f"""
                                <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 8px;
                                            padding: 0.8rem 1rem; margin-bottom: 0.6rem;">
                                    <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
                                        <div style="font-size: 0.9rem; color: #141413; line-height: 1.5;">{xss_escape(text)}</div>
                                        <span style="background: {diff_color}15; color: {diff_color}; font-size: 0.7rem;
                                                    font-weight: 500; padding: 0.15rem 0.5rem; border-radius: 4px;
                                                    white-space: nowrap;">{xss_escape(difficulty)}</span>
                                    </div>
                                    {f'<div style="font-size:0.75rem;color:#6c6a64;margin-top:0.4rem;line-height:1.4;">Why: {xss_escape(rationale)}</div>' if rationale else ''}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

        if famous_qs:
            with iv_tabs[1]:
                fq_company = xss_escape(fqr.get("company", st.session_state.get("interview_company", "the company")))
                st.markdown(f"<p style='font-size:0.85rem;color:#6c6a64;margin-bottom:0.8rem;'>Well-known interview questions from <strong>{fq_company}</strong></p>", unsafe_allow_html=True)
                sources = {}
                for q in famous_qs:
                    src = q.get("source", "General")
                    sources.setdefault(src, []).append(q)
                sorted_sources = sorted(sources.keys())
                if sorted_sources:
                    src_tabs = st.tabs(sorted_sources)
                    for si, src in enumerate(sorted_sources):
                        with src_tabs[si]:
                            for q in sources[src]:
                                text = q.get("question", "")
                                difficulty = q.get("difficulty", "Medium")
                                round_label = q.get("round", "")
                                diff_color = {"Easy": "#5db872", "Medium": "#d4a017", "Hard": "#c64545"}.get(difficulty, "#6c6a64")
                                st.markdown(
                                    f"""
                                    <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 8px;
                                                padding: 0.8rem 1rem; margin-bottom: 0.6rem;">
                                        <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
                                            <div style="font-size: 0.9rem; color: #141413; line-height: 1.5;">{xss_escape(text)}</div>
                                            <span style="background: {diff_color}15; color: {diff_color}; font-size: 0.7rem;
                                                        font-weight: 500; padding: 0.15rem 0.5rem; border-radius: 4px;
                                                        white-space: nowrap;">{xss_escape(difficulty)}</span>
                                        </div>
                                        {f'<div style="font-size:0.75rem;color:#6c6a64;margin-top:0.3rem;">Round: {xss_escape(round_label)}</div>' if round_label else ''}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
    else:
        if not generate_clicked and not iv:
            st.markdown(
                """
                <div style="background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 10px;
                            padding: 2rem; text-align: center; margin-top: 1rem;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎤</div>
                    <p style="color: #6c6a64; font-size: 0.9rem;">
                        Upload a resume and job description, add project links, then click <strong>Generate Questions</strong>.
                        Questions will cover technical, behavioral, project, company-specific, and resume-based categories.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
