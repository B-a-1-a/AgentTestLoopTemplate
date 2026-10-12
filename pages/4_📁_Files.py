from __future__ import annotations

import streamlit as st

from src.utils.config import load_yaml
from src.utils.file_manager import WorkspaceFileManager


st.title("Files")
settings = load_yaml("config/settings.yaml")
manager = WorkspaceFileManager(settings.get("workspace_root", "workspace"))

uploads = st.file_uploader("Upload files", accept_multiple_files=True)
if uploads:
    for upload in uploads:
        manager.write_text(upload.name, upload.getvalue().decode("utf-8", errors="replace"))
    st.success(f"Uploaded {len(uploads)} file(s)")

st.subheader("Workspace Browser")
files = manager.list_files(".")
if not files:
    st.info("No files in workspace")
else:
    selected = st.selectbox("Select file", options=files)
    content = manager.read_text(selected)
    st.text_area("Preview", value=content, height=400)

st.subheader("Quick Create / Edit")
path = st.text_input("Relative path", value="notes.txt")
content = st.text_area("Content", value="")
if st.button("Write File"):
    written = manager.write_text(path, content)
    st.success(f"Saved {written}")
