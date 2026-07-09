import io
import re
import streamlit as st
from PIL import Image
from frontend.utils.state import init, auto_trigger_analysis, has_resume
from frontend.utils.sanitize import xss_escape
from services.ocr_service import extract_text_from_image, is_ocr_available, ocr_status_html

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False


def _parse_sections(text: str) -> dict:
    sections = {
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "achievements": [],
    }
    lines = text.split("\n")
    current_section = None
    section_keywords = {
        "skills": ["skill", "technical", "technology", "tool", "language", "framework", "competenc", "expertise"],
        "experience": ["experience", "employment", "work history", "work experience", "professional experience", "career"],
        "projects": ["project", "portfolio", "github", "open source"],
        "education": ["education", "academic", "degree", "university", "college", "school", "bachelor", "master", "phd", "certification", "course"],
        "achievements": ["achievement", "accomplishment", "award", "honor", "recognition", "certification"],
    }

    for line in lines:
        stripped = line.strip().rstrip("-| \t")
        if not stripped:
            continue
        lower = stripped.lower()
        found_section = False
        for section, keywords in section_keywords.items():
            if any(kw in lower for kw in keywords) and len(stripped) < 60:
                current_section = section
                found_section = True
                break
        if found_section:
            continue
        if current_section and not stripped.startswith("---"):
            if len(stripped) > 3 and not re.match(r'^[\d\s\.\,\;\:\!\?]+$', stripped):
                sections.setdefault(current_section, []).append(stripped)

    return sections


def _render_editable_table(label, data, key):
    if not data:
        return
    st.markdown(f"<p style='font-size:0.9rem;font-weight:500;color:#141413;margin-top:0.8rem;'>{label}</p>", unsafe_allow_html=True)
    if HAS_AGGRID and len(data) > 3:
        import pandas as pd
        df = pd.DataFrame({label: data})
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, resizable=True)
        gb.configure_grid_options(domLayout="autoHeight")
        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            height=min(50 * len(data) + 40, 300),
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            key=key,
        )
        updated = grid_response["data"][label].tolist() if grid_response["data"] is not None else data
        st.session_state[f"parsed_{key}"] = updated
    else:
        cols = st.columns(2)
        for i, item in enumerate(data):
            with cols[i % 2]:
                st.markdown(
                f"<div style='background:#f5f0e8;border:1px solid #e6dfd8;border-radius:6px;"
                f"padding:0.4rem 0.7rem;margin-bottom:0.3rem;font-size:0.82rem;color:#3d3d3a;'>{xss_escape(item)}</div>",
                    unsafe_allow_html=True,
                )


def render():
    init()

    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Upload Resume</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #6c6a64; margin-top: -0.3rem;'>"
        "Upload a resume file (PDF, TEX, TXT, MD, JPEG, PNG) or paste the text directly.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(f"<p style='margin-bottom:0.5rem;'>{ocr_status_html()}</p>", unsafe_allow_html=True)

    upload_method = st.radio("Input method", ["Paste Text", "Upload File"], horizontal=True, label_visibility="collapsed")

    text = st.session_state.get("resume_text", "")

    if upload_method == "Paste Text":
        text_input = st.text_area(
            "Resume content",
            value=text,
            height=350,
            placeholder="Paste resume content here — LaTeX source, plain text, or markdown...",
        )
        if text_input:
            st.session_state.resume_text = text_input
            text = text_input
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #e6dfd8; border-radius: 12px; padding: 2rem; text-align: center;
                        background: #f5f0e8; margin-bottom: 0.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">📄</div>
                <p style="color: #6c6a64; font-size: 0.85rem;">Drop a file here or click to browse</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Choose a file",
            type=["txt", "pdf", "tex", "md", "docx", "jpg", "jpeg", "png"],
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
            st.session_state.resume_text = text
            auto_trigger_analysis()

    if text:
        st.markdown(
            f"<p style='color: #5db872; font-size: 0.82rem;'>✓ {len(text)} characters loaded</p>",
            unsafe_allow_html=True,
        )

        parsed = _parse_sections(text)
        if any(parsed.values()):
            st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
            st.markdown(
                "<h3 style='font-size: 1.2rem;'>Parsed Data</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='color: #6c6a64; font-size: 0.82rem; margin-top: -0.3rem;'>"
                "Edit parsed sections below. Changes are saved automatically.</p>",
                unsafe_allow_html=True,
            )

            sections_config = [
                ("skills", "Skills & Technologies"),
                ("experience", "Experience"),
                ("projects", "Projects"),
                ("education", "Education"),
                ("achievements", "Achievements"),
            ]
            sec_cols = st.columns(2)
            for idx, (section_name, section_label) in enumerate(sections_config):
                with sec_cols[idx % 2]:
                    _render_editable_table(section_label, parsed.get(section_name, []), f"{section_name}")

        st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:500;font-size:0.9rem;color:#141413;'>Preview</p>", unsafe_allow_html=True)
        preview = text[:3000]
        st.markdown(
            f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; "
            f"padding: 1rem; font-family: JetBrains Mono, monospace; font-size: 0.8rem; "
            f"color: #3d3d3a; white-space: pre-wrap; max-height: 300px; overflow-y: auto;'>{xss_escape(preview)}</div>",
            unsafe_allow_html=True,
        )

    if has_resume():
        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        if st.button("Submit Resume", type="primary", use_container_width=True, disabled=st.session_state.get("_resume_submitted", False)):
            st.session_state._resume_submitted = True
            st.rerun()
        if st.session_state.get("_resume_submitted"):
            st.caption("✅ Resume submitted")

    if st.session_state.get("analysis_running"):
        st.caption("⏳ Analysis pipeline running in background...")
    elif st.session_state.get("analysis_result"):
        st.caption("✅ Analysis complete — view results on each page.")
