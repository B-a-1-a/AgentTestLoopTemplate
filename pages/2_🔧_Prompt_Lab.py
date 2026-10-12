from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

PROMPT_DIR = Path("config/prompts")
PROMPT_DIR.mkdir(parents=True, exist_ok=True)

st.title("Prompt Lab")

prompt_files = sorted(PROMPT_DIR.glob("*.yaml"))
prompt_names = [p.name for p in prompt_files]

selected = st.selectbox("Prompt template", options=prompt_names or ["code_agent.yaml"])
selected_path = PROMPT_DIR / selected

if selected_path.exists():
    data = yaml.safe_load(selected_path.read_text(encoding="utf-8")) or {}
else:
    data = {
        "name": "code_agent",
        "system_prompt_file": "config/prompts/default_system.txt",
        "user_template": "{{user_query}}",
        "defaults": {"temperature": 0.7, "top_p": 1.0, "max_tokens": 4096},
    }

system_prompt_path = Path(data.get("system_prompt_file", "config/prompts/default_system.txt"))
if not system_prompt_path.exists():
    system_prompt_path.write_text("You are a helpful coding agent.", encoding="utf-8")

system_prompt = st.text_area("System Prompt", value=system_prompt_path.read_text(encoding="utf-8"), height=220)
user_template = st.text_area("User Template", value=data.get("user_template", "{{user_query}}"), height=220)

col1, col2, col3 = st.columns(3)
with col1:
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, step=0.1, value=float(data.get("defaults", {}).get("temperature", 0.7)))
with col2:
    top_p = st.slider("Top P", min_value=0.0, max_value=1.0, step=0.05, value=float(data.get("defaults", {}).get("top_p", 1.0)))
with col3:
    max_tokens = st.number_input("Max Tokens", min_value=128, max_value=65536, value=int(data.get("defaults", {}).get("max_tokens", 4096)), step=128)

preview_query = st.text_input("Preview user_query", value="List files and summarize project status")
preview_workspace = st.text_area("Preview workspace_files", value="README.md\nsrc/agent/loop.py")

preview_text = (
    user_template.replace("{{user_query}}", preview_query).replace("{{workspace_files}}", preview_workspace)
)
st.subheader("Interpolated Preview")
st.code(preview_text)

if st.button("Save Template"):
    system_prompt_path.write_text(system_prompt, encoding="utf-8")
    payload = {
        "name": data.get("name", "code_agent"),
        "system_prompt_file": str(system_prompt_path),
        "user_template": user_template,
        "defaults": {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": int(max_tokens),
        },
    }
    selected_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    st.success(f"Saved {selected_path}")
