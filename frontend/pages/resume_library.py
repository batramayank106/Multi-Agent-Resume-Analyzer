import io
import httpx
import streamlit as st
from frontend.utils.api_client import BACKEND_URL
from frontend.utils.state import is_authenticated


def render():
    st.markdown("<h2>📚 Resume Library</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6c6a64;'>Uploaded resume files — encrypted at rest.</p>",
        unsafe_allow_html=True,
    )

    if not is_authenticated():
        st.info("🔐 Sign in to use the Resume Library.")
        return

    if "lib_refresh" not in st.session_state:
        st.session_state.lib_refresh = 0

    tab1, tab2 = st.tabs(["Upload", "My Files"])

    with tab1:
        uploaded = st.file_uploader(
            "Choose a resume file",
            type=["txt", "pdf", "tex", "md", "doc", "docx", "json"],
            key="lib_uploader",
        )
        if uploaded:
            with st.spinner("Encrypting and saving..."):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                        r = client.post(
                            f"{BACKEND_URL}/api/library/upload",
                            files=files,
                            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                        )
                        if r.status_code == 200:
                            st.success(f"Saved: {uploaded.name}")
                            st.session_state.lib_refresh += 1
                            st.rerun()
                        elif r.status_code == 413:
                            st.error("File too large (max 10MB)")
                        else:
                            st.error(r.json().get("detail", "Upload failed"))
                except Exception as e:
                    st.error(f"Upload error: {e}")

    with tab2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.lib_refresh += 1
            st.rerun()

        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(
                    f"{BACKEND_URL}/api/library/files",
                    headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                )
                r.raise_for_status()
                files = r.json()
        except Exception as e:
            st.error(f"Could not load library: {e}")
            return

        if not files:
            st.info("No files uploaded yet. Use the Upload tab to add files.")
            return

        for f in files:
            cols = st.columns([3, 1, 1.5, 1])
            cols[0].markdown(f"**{f['original_filename']}**")
            cols[1].markdown(f"`{f['size_display']}`")
            cols[2].markdown(f"<span style='font-size:0.8rem;color:#6c6a64;'>{f['created_at'][:10]}</span>", unsafe_allow_html=True)
            with cols[3]:
                if st.button("Download", key=f"dl_{f['id']}"):
                    try:
                        with httpx.Client(timeout=30.0) as client:
                            r = client.get(
                                f"{BACKEND_URL}/api/library/files/{f['id']}",
                                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                            )
                            r.raise_for_status()
                            st.download_button(
                                label="Save File",
                                data=io.BytesIO(r.content),
                                file_name=f["original_filename"],
                                mime="application/octet-stream",
                                key=f"save_{f['id']}",
                            )
                    except Exception as e:
                        st.error(f"Download failed: {e}")
            with cols[3]:
                if st.button("🗑", key=f"del_{f['id']}"):
                    try:
                        with httpx.Client(timeout=10.0) as client:
                            client.delete(
                                f"{BACKEND_URL}/api/library/files/{f['id']}",
                                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                            )
                        st.session_state.lib_refresh += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
            st.markdown("<hr style='margin:0.3rem 0;'>", unsafe_allow_html=True)
