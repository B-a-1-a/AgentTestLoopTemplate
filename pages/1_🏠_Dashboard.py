from __future__ import annotations

import streamlit as st

from src.providers.registry import ProviderRegistry


st.title("Dashboard")

if "provider_registry" not in st.session_state:
    st.session_state.provider_registry = ProviderRegistry()

registry: ProviderRegistry = st.session_state.provider_registry
snapshot = registry.validate_models_from_api()
st.session_state.provider_snapshot = snapshot

st.subheader("Provider Status")
for status in snapshot.provider_statuses:
    if status.configured and not status.stale_models:
        badge = "🟢"
    elif status.configured and status.stale_models:
        badge = "🟡"
    else:
        badge = "🔴"

    st.write(f"{badge} **{status.provider}** - {status.message}")

    if status.available_remote_models:
        st.caption(f"Remote model list count: {len(status.available_remote_models)}")

st.subheader("Configured Model Validation")
for model in snapshot.configured_models:
    if model.stale_or_unavailable:
        st.warning(f"{model.provider}: `{model.id}` marked stale_or_unavailable")
        if model.suggested_ids:
            st.caption(f"Suggested replacements: {', '.join(model.suggested_ids)}")
    else:
        st.success(f"{model.provider}: `{model.id}` available")
