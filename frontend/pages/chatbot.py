import streamlit as st
from frontend.utils.state import init, has_resume, page_guide
from frontend.utils.api_client import rag_chat

EXAMPLE_PROMPTS = [
    "How can I improve my ATS score?",
    "What skills should I add to my resume?",
    "Rewrite this bullet point: 'Was responsible for testing'",
    "What projects should I build for a data science role?",
    "How do I explain a gap year in my resume?",
    "Is my resume good enough for FAANG companies?",
    "What keywords am I missing for a Python developer role?",
    "How should I format my experience section?",
]


def _summarize_history(messages: list[dict], max_tokens: int = 500) -> str:
    text = ""
    for m in messages:
        role = "User" if m["role"] == "user" else "Assistant"
        text += f"{role}: {m['content']}\n"
    if len(text) > max_tokens:
        text = "..." + text[-max_tokens:]
    return text


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Resume Chatbot</h1>",
        unsafe_allow_html=True,
    )
    page_guide(
        "Resume Chatbot",
        "Ask questions about your resume, ATS scores, skill gaps, interview prep, or career advice. Uses your uploaded resume context AND a RAG knowledge base for answers.",
        "Type any question in the chat input. The bot uses your resume + job description as context. If it retrieves relevant documents from the knowledge base, citations appear below the response.",
        "Upload a resume first for personalized advice. Ask specific questions (see examples below). If the answer seems off, rephrase. The bot prioritizes your resume context — if retrieved docs seem irrelevant, it should ignore them.",
    )
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_citations = {}

    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                citations = st.session_state.chat_citations.get(i, [])
                if citations:
                    with st.expander(f"📚 {len(citations)} sources", expanded=False):
                        for c in citations:
                            src = c.get("source", "knowledge base")
                            score = c.get("score", 0)
                            content = c.get("content", "")[:200]
                            st.markdown(
                                f"<div style='font-size:0.8rem;color:#6c6a64;padding:0.3rem 0;'>"
                                f"<strong>{src}</strong> (relevance: {score:.2f})<br>{content}</div>",
                                unsafe_allow_html=True,
                            )

    if st.session_state.chat_history:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.chat_citations = {}
                st.rerun()

    has_resume_text = has_resume()
    if not has_resume_text:
        st.info("💡 Tip: Upload a resume first for personalized coaching.")

    with st.expander("💡 Example questions", expanded=not st.session_state.chat_history):
        example_cols = st.columns(2)
        for idx, prompt in enumerate(EXAMPLE_PROMPTS):
            with example_cols[idx % 2]:
                if st.button(prompt, use_container_width=True, key=f"eg_{idx}"):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    st.rerun()

    prompt = st.chat_input("Ask about your resume, ATS, career advice...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        resume_ctx = st.session_state.get("resume_text", "")[:3000]
        history = _summarize_history(st.session_state.chat_history[:-1])

        messages = [{"role": "user", "content": f"Previous conversation:\n{history}\n\nQuestion: {prompt}"}]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag_chat(
                    messages=messages,
                    resume_context=resume_ctx,
                    temperature=0.7,
                )
                content = response.get("content", "I'm not able to answer right now. Set up HF_API_KEY for live responses.")
                citations = response.get("citations", [])
                st.markdown(content)
                if citations:
                    with st.expander(f"📚 {len(citations)} sources", expanded=False):
                        for c in citations:
                            src = c.get("source", "knowledge base")
                            score = c.get("score", 0)
                            c_content = c.get("content", "")[:200]
                            st.markdown(
                                f"<div style='font-size:0.8rem;color:#6c6a64;padding:0.3rem 0;'>"
                                f"<strong>{src}</strong> (relevance: {score:.2f})<br>{c_content}</div>",
                                unsafe_allow_html=True,
                            )

                msg_idx = len(st.session_state.chat_history)
                st.session_state.chat_history.append({"role": "assistant", "content": content})
                st.session_state.chat_citations[msg_idx] = citations
