from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from src.providers.registry import ProviderRegistry


load_dotenv()

st.set_page_config(page_title="Agent Test Loop", page_icon="🧪", layout="wide")

st.title("Agent Test Loop Template")
st.caption("Local-first playground for agent loop iteration with model freshness checks.")

if "provider_registry" not in st.session_state:
    st.session_state.provider_registry = ProviderRegistry()

registry: ProviderRegistry = st.session_state.provider_registry

if "provider_snapshot" not in st.session_state:
    st.session_state.provider_snapshot = registry.validate_models_from_api()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Providers")
    for status in st.session_state.provider_snapshot.provider_statuses:
        indicator = "🟢" if status.configured else "🔴"
        if status.stale_models:
            indicator = "🟡"
        st.write(f"{indicator} **{status.provider}** - {status.message}")

with col2:
    st.subheader("Configured Models")
    for model in st.session_state.provider_snapshot.configured_models:
        label = "⚠️ stale_or_unavailable" if model.stale_or_unavailable else "✅"
        st.write(f"{label} `{model.id}` ({model.provider})")

st.info("Use the sidebar pages for Dashboard, Prompt Lab, Agent Run, Files, and Settings.")
