import time
import streamlit as st
from frontend.utils.api_client import health_check, list_llm_models, get_llm_stats, DEMO_SAMPLE_DATA, run_full_analysis
from frontend.utils.state import auto_trigger_analysis

AGENT_DESCRIPTIONS = [
    ("ATS Scoring Engine",
     "Rule-based evaluation across 7 weighted categories with evidence-backed deductions",
     "Scores the resume against the job description using keyword/skill/experience matching. Each of 7 categories is scored 0-100 and weighted to produce an overall score (0-100). Deductions cite specific missing items. Expect: score + category label + evidence list. If no JD is uploaded, it scores against inferred role requirements."),
    ("Recruiter Review",
     "LLM-powered assessment of readability, impact, and achievement orientation",
     "An LLM reads the resume as a recruiter would and scores 5 dimensions (Readability, Impact, Leadership, Communication, Achievement) 0-100. Returns: score, PASS/REJECT, confidence%, reasoning text, dimension scores. Different from HM: focuses on presentation, career narrative, and soft skills rather than technical depth."),
    ("Hiring Manager Review",
     "Technical depth and domain fit evaluation via language model",
     "An LLM evaluates technical depth, project quality, domain fit, and growth trajectory. Returns: score, PASS/REJECT, reasoning, dimension scores. Stricter than Recruiter — focuses on actual technical experience. May REJECT where Simulator PASSes because it evaluates hands-on technical capability vs persona-based quick checks."),
    ("Recruiter Simulator",
     "Three-perspective simulation: ATS, HR, and Engineering Manager personas",
     "Three separate LLM calls, each role-playing a different evaluator. Each returns a PASS/REJECT + confidence%. Aggregated: 3/3 PASS = PASS, 2/3 = CONDITIONAL, <2 = REJECT. Quick, persona-based — meant for broad signal, not deep analysis. May differ from dedicated agents (different prompts, single-pass)."),
    ("Skill Gap Analysis",
     "Identifies missing and preferred skills relative to job requirements",
     "LLM compares resume skills vs JD requirements. Returns: required_skills, preferred_skills, missing_skills, gap_severity (low/medium/high/critical), priority_levels per skill. Expect: a list of what to learn next. Gap severity is computed from the worst-category severity across all skills."),
    ("Truthfulness Validation",
     "Flags potentially exaggerated or misleading claims in the resume",
     "LLM scans each claim in the resume and classifies as Safe / Needs Verification / Potentially Misleading. Returns: truthfulness_score (0-100) + flagged_items list with reasoning. Does NOT verify external facts — it flags implausible claims (e.g. 'led 200-person team as an intern')."),
    ("Company Research",
     "Analyzes company culture, growth opportunities, and red flags from job description",
     "LLM extracts company name from JD or resume experience, then researches it. Returns: overview, culture_fit_indicators, growth_opportunities, red_flags, employee review insights (culture_score, pros/cons, WLB, career_growth), overall_suitability rating. Useful for interview prep and deciding if the company fits you."),
    ("Salary Estimation",
     "Market-based compensation analysis with confidence scoring (₹INR/LPA)",
     "LLM estimates salary range for the role × company × location in the Indian market. Returns: salary_range in ₹LPA, currency (INR), confidence (Low/Medium/High), factors list. Based on LLM training data — not real-time market data. Use as a rough benchmark, not a definitive offer."),
    ("Resume Rewrite",
     "Generates optimized bullet points and descriptions based on agent feedback",
     "Takes the original resume + suggestions from other agents and rewrites bullet points for stronger impact. Returns: rewritten_resume text. Does NOT change layout/template — only content. Use after running the full pipeline to get a draft; review and edit manually before using."),
    ("Interview Preparation",
     "Generates technical, behavioral, and project-based interview questions",
     "LLM generates 10-14 questions across Technical, Behavioral, Project & Portfolio, System Design, Company-Specific, and Resume-Based categories. Each question has difficulty (Easy/Medium/Hard) and rationale. Customizable by role, company, and project links. Famous Questions sub-feature pulls company-specific well-known questions."),
    ("Famous Questions",
     "Company-specific famous interview questions from top tech firms",
     "LLM generates well-known interview questions specific to the company (e.g. Amazon Leadership Principles, Google System Design, Meta Behavioral). Questions tagged by source (company LP/round name), difficulty, and interview round. Run after uploading a JD to get company-targeted questions."),
    ("Selection Probability",
     "Estimates hiring probability across stages from ATS screen to offer",
     "LLM estimates probability (0-100%) of advancing through each hiring stage: ATS Screen → Recruiter Review → HM Review → On-site Interview → Offer. Uses all prior agent scores as input. Returns: overall_probability, stage_probabilities, key_factors, recommendations. Expect a funnel-shaped chart showing drop-off at each stage."),
]

MODEL_CAPABILITIES = [
    ("Groq Cloud (llama-3.3-70b)", "Fast cloud inference", "Primary provider — 70B model, free tier"),
    ("Qwen2.5 7B Instruct (HF)", "32K context", "Strong general reasoning & instruction following"),
    ("DeepSeek-R1 Distill 7B (HF)", "16K context", "Deep reasoning with chain-of-thought"),
    ("Qwen2.5 Coder 7B (HF)", "16K context", "Code-specialized generation"),
    ("Llama 3.1 8B Instruct (HF)", "128K context", "Long-document analysis, fallback model"),
    ("Qwen2.5 72B (HF)", "32K context", "High-quality reasoning (larger model)"),
]


def render():
    placeholder = st.empty()

    with placeholder.container():
        st.markdown(
            "<h1 style='font-size: 2.8rem; letter-spacing: -1px; margin-bottom: 0.2rem;'>CV Chacha</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color: #6c6a64; font-size: 1.1rem; margin-top: -0.5rem;'>"
            "Multi-agent resume intelligence platform</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color: #8e8b82; font-size: 0.75rem; margin-top: -0.3rem; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400;'>"
            "by Mayank Batra</p>",
            unsafe_allow_html=True,
        )

        progress_bar = st.progress(0, text="Connecting to inference engine...")
        for pct in [20, 40, 60, 80]:
            time.sleep(0.15)
            progress_bar.progress(pct, text="Loading model registry...")
        backend_online = health_check()
        models_info = list_llm_models() if backend_online else None
        progress_bar.progress(100, text="Ready")
        time.sleep(0.1)
        progress_bar.empty()

    st.markdown(
        "<h2 style='font-size: 1.6rem; margin-top: 0.5rem;'>Model Capabilities</h2>",
        unsafe_allow_html=True,
    )

    if backend_online and models_info:
        current = models_info.get("current", "—")
        st.markdown(
            f"<p style='color: #6c6a64; font-size: 0.85rem;'>Active model: <strong style='color: #141413;'>{current}</strong>"
            f" · {len(models_info.get('models', []))} models available</p>",
            unsafe_allow_html=True,
        )

    for i, (name, ctx, desc) in enumerate(MODEL_CAPABILITIES):
        cols = st.columns([1, 2, 4])
        with cols[0]:
            st.markdown(
                f"<div style='font-family: Inter, sans-serif; font-weight: 500; font-size: 0.85rem; color: #141413;'>{name}</div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(
                f"<div style='font-family: Inter, sans-serif; font-size: 0.8rem; color: #6c6a64;'>{ctx}</div>",
                unsafe_allow_html=True,
            )
        with cols[2]:
            st.markdown(
                f"<div style='font-family: Inter, sans-serif; font-size: 0.8rem; color: #6c6a64;'>{desc}</div>",
                unsafe_allow_html=True,
            )
        if i < len(MODEL_CAPABILITIES) - 1:
            st.markdown(
                "<hr style='margin: 0.3rem 0; border-color: #e6dfd8;'>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.8rem;'>Agent Pipeline</h2>",
        unsafe_allow_html=True,
    )

    cols_per_row = 2
    for i in range(0, len(AGENT_DESCRIPTIONS), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx >= len(AGENT_DESCRIPTIONS):
                break
            name, tagline, explanation = AGENT_DESCRIPTIONS[idx]
            with cols[j]:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px;
                                    padding: 1rem 1.2rem; margin-bottom: 0.4rem;">
                            <div style="font-family: 'Inter', sans-serif; font-weight: 500; font-size: 0.9rem;
                                        color: #141413;">{name}</div>
                            <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #6c6a64;
                                        margin-top: 0.3rem; line-height: 1.5;">{tagline}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("How it works & what to expect", expanded=False):
                        st.markdown(
                            f"<div style='font-size:0.8rem;color:#3d3d3a;line-height:1.6;'>{explanation}</div>",
                            unsafe_allow_html=True,
                        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='font-size: 1.8rem;'>Architecture</h2>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; text-align: center;">
                <div style="font-size: 1.5rem; font-family: 'Playfair Display', serif; color: #141413;">Frontend</div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #6c6a64; margin-top: 0.5rem;">
                    Streamlit<br>21 pages · Warm canvas theme
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; text-align: center;">
                <div style="font-size: 1.5rem; font-family: 'Playfair Display', serif; color: #141413;">Backend</div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #6c6a64; margin-top: 0.5rem;">
                    FastAPI · LangGraph<br>12 agents · ChromaDB RAG
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; text-align: center;">
                <div style="font-size: 1.5rem; font-family: 'Playfair Display', serif; color: #141413;">Inference</div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #6c6a64; margin-top: 0.5rem;">
                    Groq Cloud → HF API → Ollama<br>6 models · Auto-failover
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    with st.expander("📊 AI Monitoring Dashboard", expanded=False):
        stats = get_llm_stats() if backend_online else {}
        if stats:
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.metric("API Calls", stats.get("api_calls", 0))
            with mcol2:
                st.metric("Failed Calls", stats.get("failed_calls", 0))
            with mcol3:
                st.metric("Total Tokens", stats.get("total_tokens", 0))
            with mcol4:
                st.metric("Total Cost", f"${stats.get('total_cost', 0):.6f}")

            mcol5, mcol6 = st.columns(2)
            with mcol5:
                st.metric("Input Tokens", stats.get("total_input_tokens", 0))
            with mcol6:
                st.metric("Output Tokens", stats.get("total_output_tokens", 0))

            last_used = stats.get("last_used")
            if last_used:
                st.caption(f"🕒 Last API use: {last_used}")
            st.caption(f"Current model: {stats.get('current_model', '—')}")
        else:
            st.info("Backend offline — stats unavailable. Start the backend to see monitoring data.")

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    with st.expander("🚀 Demo Mode", expanded=False):
        st.markdown(
            "<p style='color: #6c6a64; font-size: 0.9rem;'>"
            "Load pre-filled sample data to instantly test the platform.</p>",
            unsafe_allow_html=True,
        )
        if st.button("Load Sample Resume & JD", type="primary"):
            for key, value in DEMO_SAMPLE_DATA.items():
                st.session_state[key] = value
            st.session_state["demo_loaded"] = True
            st.success("Sample data loaded! Running full analysis pipeline...")
            st.link_button("✅ → Go to ATS Analysis", "/ats", type="primary")
            auto_trigger_analysis()

        if st.session_state.get("demo_loaded"):
            st.info("Sample data already loaded in session. Run an analysis to see results.")

    st.markdown(
        "<hr style='margin: 2rem 0 0.5rem 0;'>"
        "<p style='text-align: center; color: #8e8b82; font-size: 0.75rem; font-family: Inter, sans-serif;'>"
        "Created by Mayank Batra</p>",
        unsafe_allow_html=True,
    )
