import io
import re
import streamlit as st
from PIL import Image
from frontend.utils.state import init, auto_trigger_analysis
from frontend.utils.sanitize import xss_escape
from services.ocr_service import extract_text_from_image, is_ocr_available, ocr_status_html


def _extract_requirements(text: str) -> dict:
    sections = {
        "required_skills": [],
        "preferred_skills": [],
        "responsibilities": [],
        "qualifications": [],
    }
    lines = text.split("\n")
    current = None
    section_markers = {
        "required_skills": ["required skill", "requirement", "must have", "what you need", "minimum qualif", "ideal candidate", "candidate should possess", "you should have"],
        "preferred_skills": ["preferred", "nice to have", "good to have", "bonus", "plus"],
        "responsibilities": ["responsibilit", "what you will do", "key duties", "role includes", "job role include", "job description", "your role"],
        "qualifications": ["qualification", "education", "degree", "background", "certification"],
    }
    end_markers = ["about the company", "about us", "benefits", "perks", "apply", "equal opportunity", "how to apply", "we offer"]
    garbage_pattern = re.compile(r'^[^a-zA-Z0-9]{2,}$|^[A-Z\s]{2,6}$|(.)\1{3,}')
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 4:
            continue
        if garbage_pattern.search(stripped):
            continue
        lower = stripped.lower()
        is_header = False
        for section, markers in section_markers.items():
            if any(kw in lower for kw in markers):
                current = section
                is_header = True
                break
        if is_header:
            continue
        if any(kw in lower for kw in end_markers):
            current = None
            continue
        if not current:
            continue

        clean = re.sub(r'^[\s\-*•–—\d\.\)\"\�\xef\xbb\xbf\x00-\x1f%&=\*\+\~\�]+', '', stripped).strip()
        if len(clean) > 5 and (clean != stripped or len(clean) > 10):
            words = clean.split()
            short_ratio = sum(1 for w in words if len(w) <= 3) / max(len(words), 1)
            if len(clean) < 20 and short_ratio > 0.5:
                continue
            sections[current].append(clean.rstrip(".,; "))

    return sections


def _detect_role(jd_text: str) -> str:
    jd_lower = jd_text.lower()
    roles = {
        "Customer Service": ["customer service", "customer support", "service representative", "client support", "help desk", "support specialist", "call center"],
        "Data Analyst": ["data analyst", "analytics", "sql", "tableau", "power bi", "dashboards", "data visualization", "business analyst"],
        "Software Engineer": ["software engineer", "software developer", "sde", "backend", "frontend", "full stack", "api developer", "microservices"],
        "Engineering Manager": ["engineering manager", "tech lead", "head of engineering", "vp engineering", "engineering lead"],
        "Product Manager": ["product manager", "pm", "product owner", "product lead", "program manager"],
        "Data Scientist": ["data scientist", "machine learning", "deep learning", "nlp"],
        "DevOps": ["devops", "ci/cd", "kubernetes", "docker", "terraform", "infrastructure", "site reliability", "sre"],
        "Designer": ["designer", "ux", "ui", "figma", "user experience", "product design", "graphic designer"],
        "Marketing": ["marketing", "marketing manager", "growth", "seo", "content", "digital marketing", "brand"],
        "Sales": ["sales", "account executive", "business development", "sales representative", "account manager"],
        "HR": ["hr", "human resources", "recruiter", "talent acquisition", "people operations", "hr manager"],
        "Finance": ["finance", "accountant", "financial analyst", "controller", "auditor", "cfa"],
        "Project Manager": ["project manager", "project lead", "scrum master", "agile coach", "pmp"],
        "Healthcare": ["nurse", "doctor", "physician", "healthcare", "clinical", "medical", "pharmacist"],
    }
    scores = {}
    for role, keywords in roles.items():
        score = sum(kw in jd_lower for kw in keywords)
        scores[role] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


def render():
    init()

    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Upload Job Description</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; margin-top: -0.3rem;'>"
        "What is a JD? A <strong>Job Description (JD)</strong> is a document that lists the requirements, responsibilities, "
        "and qualifications for a specific role. The ATS engine, Skill Gap, Recruiter, and HM agents compare your resume "
        "against this JD to score fit. Upload one to get targeted analysis — without a JD, agents score against inferred "
        "role expectations (less accurate).</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.2rem;'>"
        "Paste text or upload a file (TXT, PDF, DOCX, image with OCR) below.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(f"<p style='margin-bottom:0.5rem;'>{ocr_status_html()}</p>", unsafe_allow_html=True)

    upload_method = st.radio("Input method", ["Paste Text", "Upload File"], horizontal=True, label_visibility="collapsed")

    text = st.session_state.get("jd_text", "")

    if upload_method == "Paste Text":
        text_input = st.text_area(
            "Job description",
            value=text,
            height=300,
            placeholder="Paste the job description here...",
        )
        if text_input:
            st.session_state.jd_text = text_input
            text = text_input
    else:
        uploaded = st.file_uploader(
            "Choose a file", type=["txt", "pdf", "tex", "md", "docx", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        if uploaded:
            raw = uploaded.read()
            ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
            try:
                if ext == "pdf":
                    import fitz
                    doc = fitz.open(stream=raw, filetype="pdf")
                    text = "".join(page.get_text() for page in doc)
                elif ext == "docx":
                    from docx import Document
                    doc = Document(io.BytesIO(raw))
                    text = "\n".join(p.text for p in doc.paragraphs)
                elif ext in ("jpg", "jpeg", "png"):
                    if is_ocr_available():
                        img = Image.open(io.BytesIO(raw))
                        st.image(img, caption="Uploaded image", width=400)
                        text = extract_text_from_image(raw)
                        if not text:
                            text = "[OCR returned no text. Ensure the image has clear text.]"
                    else:
                        text = "[OCR not available. Install Tesseract OCR and restart the app for image text extraction.]"
                else:
                    text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("utf-8", errors="replace")
            st.session_state.jd_text = text
            auto_trigger_analysis()

    if text:
        st.markdown(
            f"<p style='color: #5db872; font-size: 0.82rem;'>✓ {len(text)} characters loaded</p>",
            unsafe_allow_html=True,
        )

        role = _detect_role(text)
        requirements = _extract_requirements(text)

        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.2rem;'>Analysis Breakdown</h3>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div style="background:#efe9de;border:1px solid #e6dfd8;border-radius:8px;padding:1rem;text-align:center;">
                    <div style="font-size:0.7rem;letter-spacing:1.5px;text-transform:uppercase;color:#6c6a64;">Role</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.2rem;color:#141413;margin-top:0.2rem;">{role}</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with col2:
            total_reqs = sum(len(v) for v in requirements.values())
            st.markdown(
                f"""
                <div style="background:#efe9de;border:1px solid #e6dfd8;border-radius:8px;padding:1rem;text-align:center;">
                    <div style="font-size:0.7rem;letter-spacing:1.5px;text-transform:uppercase;color:#6c6a64;">Requirements</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.2rem;color:#141413;margin-top:0.2rem;">{total_reqs}</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with col3:
            word_count = len(text.split())
            st.markdown(
                f"""
                <div style="background:#efe9de;border:1px solid #e6dfd8;border-radius:8px;padding:1rem;text-align:center;">
                    <div style="font-size:0.7rem;letter-spacing:1.5px;text-transform:uppercase;color:#6c6a64;">Length</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.2rem;color:#141413;margin-top:0.2rem;">{word_count} words</div>
                </div>
                """, unsafe_allow_html=True,
            )

        if any(requirements.values()):
            st.markdown("<hr style='margin:0.8rem 0;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='font-size:1rem;'>Structured Requirements</h3>", unsafe_allow_html=True)

            req_labels = {
                "required_skills": ("Required Skills", "#c64545"),
                "preferred_skills": ("Preferred Skills", "#d4a017"),
                "responsibilities": ("Responsibilities", "#141413"),
                "qualifications": ("Qualifications", "#5db8a6"),
            }
            for key, (label, color) in req_labels.items():
                items = requirements.get(key, [])
                if items:
                    st.markdown(f"<p style='font-size:0.82rem;color:{color};font-weight:500;margin-top:0.6rem;'>{label} ({len(items)})</p>", unsafe_allow_html=True)
                    st.markdown(
                        "<div style='display:flex;flex-wrap:wrap;gap:0.3rem;'>"
                        + "".join(
                            f"<span style='background:#f5f0e8;border:1px solid #e6dfd8;border-radius:4px;"
                            f"padding:0.25rem 0.6rem;font-size:0.78rem;color:#3d3d3a;'>{xss_escape(item[:80])}{'…' if len(item)>80 else ''}</span>"
                            for item in items
                        )
                        + "</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:500;font-size:0.9rem;color:#141413;'>Preview</p>", unsafe_allow_html=True)
        preview = text[:3000]
        st.markdown(
            f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; "
            f"padding: 1rem; font-family: JetBrains Mono, monospace; font-size: 0.8rem; "
            f"color: #3d3d3a; white-space: pre-wrap; max-height: 250px; overflow-y: auto;'>{xss_escape(preview)}</div>",
            unsafe_allow_html=True,
        )

    if text:
        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        if st.button("Submit JD", type="primary", use_container_width=True, disabled=st.session_state.get("_jd_submitted", False)):
            st.session_state._jd_submitted = True
            st.rerun()
        if st.session_state.get("_jd_submitted"):
            st.caption("✅ JD submitted")

    if st.session_state.get("analysis_running"):
        st.caption("⏳ Analysis pipeline running in background...")
    elif st.session_state.get("analysis_result"):
        st.caption("✅ Analysis complete — view results on each page.")
