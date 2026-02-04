import streamlit as st
import requests
from auth import require_login, auth_headers
from layout import render_sidebar

API = "http://localhost:8000"

st.set_page_config(page_title="My Resumes", layout="wide")
require_login()
render_sidebar()

st.title("📄 My Resumes")
st.caption("Upload, manage, preview, and share your resumes")

# ---------------- UPLOAD ----------------
with st.container(border=True):
    st.subheader("⬆ Upload Resume")
    file = st.file_uploader(
        "Supported formats: PDF, DOC, DOCX (Max 5MB)",
        ["pdf", "doc", "docx"],
    )

    if file and st.button("Upload Resume", use_container_width=True):
        with st.spinner("Uploading resume..."):
            res = requests.post(
                f"{API}/resume/upload",
                files={"file": (file.name, file, file.type)},
                headers=auth_headers(),
            )
            if res.ok:
                st.success("Resume uploaded successfully")
                st.rerun()
            else:
                st.error(res.text)

st.divider()

# ---------------- FETCH RESUMES ----------------
res = requests.get(f"{API}/resume/my-resumes", headers=auth_headers())

if not res.ok:
    st.error("Failed to load resumes")
    st.stop()

resumes = res.json().get("resumes", [])

if not resumes:
    st.info("No resumes uploaded yet.")
    st.stop()

st.subheader("📂 Uploaded Resumes")

# ---------------- RESUME LIST ----------------
for r in resumes:
    resume_id = r["resume_id"]
    preview_key = f"preview_{resume_id}"
    share_key = f"share_{resume_id}"

    with st.container(border=True):
        left, right = st.columns([4, 2])

        # -------- LEFT --------
        with left:
            st.markdown(f"### 📄 {r.get('display_name') or r.get('filename')}")
            st.caption(f"Uploaded on: {r['uploaded_at']}")

            if r.get("tags"):
                st.markdown(f"🏷 **Tags:** {r['tags']}")

            st.markdown(f"🔗 **Shared:** {r.get('share_count', 0)} times")

            if r["is_primary"]:
                st.success("⭐ Primary Resume")

        # -------- RIGHT --------
        with right:
            if st.button("👁 Preview", key=f"btn_preview_{resume_id}", use_container_width=True):
                link_res = requests.get(
                    f"{API}/resume/access/{resume_id}",
                    headers=auth_headers(),
                )
                if link_res.ok:
                    st.session_state[preview_key] = link_res.json()["url"]
                else:
                    st.error("Failed to load preview")

            if st.button("🔗 Share", key=f"btn_share_{resume_id}", use_container_width=True):
                link_res = requests.get(
                    f"{API}/resume/access/{resume_id}",
                    headers=auth_headers(),
                )
                if link_res.ok:
                    st.session_state[share_key] = link_res.json()["url"]
                else:
                    st.error("Failed to generate share link")

            if not r["is_primary"]:
                if st.button(
                    "⭐ Set as Primary",
                    key=f"btn_primary_{resume_id}",
                    use_container_width=True,
                ):
                    requests.post(
                        f"{API}/resume/set-primary/{resume_id}",
                        headers=auth_headers(),
                    )
                    st.rerun()

            with st.expander("✏ Rename Resume"):
                new_name = st.text_input(
                    "New resume name",
                    value=r.get("display_name") or "",
                    key=f"rename_input_{resume_id}",
                )
                if st.button("Save Name", key=f"save_name_{resume_id}"):
                    requests.patch(
                        f"{API}/resume/rename/{resume_id}",
                        params={"name": new_name},
                        headers=auth_headers(),
                    )
                    st.success("Name updated")
                    st.rerun()

            with st.expander("🗑 Delete Resume"):
                st.warning("This action cannot be undone.")
                if st.button(
                    "Confirm Delete",
                    key=f"delete_{resume_id}",
                    use_container_width=True,
                ):
                    requests.delete(
                        f"{API}/resume/delete/{resume_id}",
                        headers=auth_headers(),
                    )
                    st.success("Resume deleted")
                    st.rerun()

        # -------- PREVIEW / SHARE OUTPUT --------
        if preview_key in st.session_state:
            st.markdown(
                f"👉 **Preview:** [Open Resume]({st.session_state[preview_key]})"
            )

        if share_key in st.session_state:
            st.markdown("🔗 **Share Link:**")
            st.code(st.session_state[share_key])
