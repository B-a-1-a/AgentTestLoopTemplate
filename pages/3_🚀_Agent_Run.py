from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from src.agent.loop import AgentLoopEngine
from src.providers.registry import ProviderRegistry
from src.sandbox.manager import SandboxManager
from src.sandbox.security import SandboxSecurityConfig
from src.utils.config import load_yaml
from src.utils.file_manager import WorkspaceFileManager


st.title("Agent Run")

if "provider_registry" not in st.session_state:
    st.session_state.provider_registry = ProviderRegistry()

registry: ProviderRegistry = st.session_state.provider_registry
snapshot = registry.validate_models_from_api()

settings = load_yaml("config/settings.yaml")
security = SandboxSecurityConfig(
    memory=str(settings.get("sandbox", {}).get("memory", "256m")),
    cpus=float(settings.get("sandbox", {}).get("cpus", 0.5)),
    pids_limit=int(settings.get("sandbox", {}).get("pids_limit", 64)),
    network=str(settings.get("sandbox", {}).get("network", "sandbox-net")),
)

if "sandbox_manager" not in st.session_state:
    st.session_state.sandbox_manager = SandboxManager(
        image=str(settings.get("sandbox", {}).get("image", "agent-loop-sandbox:latest")),
        callback_host=str(settings.get("callback_server", {}).get("host", "127.0.0.1")),
        callback_port=int(settings.get("callback_server", {}).get("port", 8765)),
        security=security,
    )

sandbox_manager: SandboxManager = st.session_state.sandbox_manager

configured = [s for s in snapshot.provider_statuses if s.configured]
if not configured:
    st.error("No configured providers. Set API keys in .env first.")
    st.stop()

provider_name = st.selectbox("Provider", options=[s.provider for s in configured])
provider_models = [m for m in snapshot.configured_models if m.provider == provider_name]
selected_model = st.selectbox("Model", options=[m.id for m in provider_models])

for m in provider_models:
    if m.id == selected_model and m.stale_or_unavailable:
        st.warning("Selected model is stale_or_unavailable.")
        if m.suggested_ids:
            st.caption(f"Suggestions: {', '.join(m.suggested_ids)}")

prompt_template_path = Path("config/prompts/code_agent.yaml")
prompt_data = yaml.safe_load(prompt_template_path.read_text(encoding="utf-8")) or {}
system_path = Path(prompt_data.get("system_prompt_file", "config/prompts/default_system.txt"))
system_prompt = system_path.read_text(encoding="utf-8") if system_path.exists() else "You are a coding agent."

user_query = st.text_area("User query", value="List files in workspace and explain what to do next.", height=120)

defaults = prompt_data.get("defaults", {})
col1, col2, col3 = st.columns(3)
with col1:
    temperature = st.slider("Temperature", 0.0, 2.0, float(defaults.get("temperature", 0.7)), 0.1)
with col2:
    top_p = st.slider("Top P", 0.0, 1.0, float(defaults.get("top_p", 1.0)), 0.05)
with col3:
    max_tokens = st.number_input("Max Tokens", min_value=128, max_value=65536, value=int(defaults.get("max_tokens", 4096)), step=128)

max_iterations = st.number_input(
    "Max Iterations",
    min_value=1,
    max_value=25,
    value=int(settings.get("max_iterations", 6)),
)

workspace_manager = WorkspaceFileManager(settings.get("workspace_root", "workspace"))
workspace_listing = workspace_manager.list_files(".")
workspace_files_string = "\n".join(workspace_listing)

rendered_user = (
    prompt_data.get("user_template", "{{user_query}}")
    .replace("{{user_query}}", user_query)
    .replace("{{workspace_files}}", workspace_files_string)
)

if st.button("Run Agent"):
    engine = AgentLoopEngine(registry=registry, workspace_root=settings.get("workspace_root", "workspace"))
    with st.spinner("Running agent loop..."):
        result = engine.run(
            provider_name=provider_name,
            model_id=selected_model,
            user_query=rendered_user,
            system_prompt=system_prompt,
            max_iterations=int(max_iterations),
            params={"temperature": temperature, "top_p": top_p, "max_tokens": int(max_tokens)},
            sandbox_manager=sandbox_manager,
        )

    st.subheader("Result")
    st.write(f"Stop reason: `{result.stop_reason}` | Iterations: `{result.iterations}`")
    st.text_area("Final answer", value=result.final_answer, height=220)

    st.subheader("Trace")
    st.json(result.trace)
