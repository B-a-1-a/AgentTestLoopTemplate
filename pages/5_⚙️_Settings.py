from __future__ import annotations

import streamlit as st

from src.utils.config import load_yaml, save_yaml


st.title("Settings")
settings = load_yaml("config/settings.yaml")

max_iterations = st.number_input("Max Iterations", min_value=1, max_value=50, value=int(settings.get("max_iterations", 6)))
sandbox_timeout = st.number_input(
    "Sandbox Timeout (seconds)",
    min_value=5,
    max_value=300,
    value=int(settings.get("sandbox_timeout_seconds", 30)),
)

image = st.text_input("Sandbox image", value=str(settings.get("sandbox", {}).get("image", "agent-loop-sandbox:latest")))
network = st.text_input("Sandbox network", value=str(settings.get("sandbox", {}).get("network", "sandbox-net")))
memory = st.text_input("Sandbox memory", value=str(settings.get("sandbox", {}).get("memory", "256m")))
cpus = st.number_input("Sandbox CPUs", min_value=0.1, max_value=8.0, value=float(settings.get("sandbox", {}).get("cpus", 0.5)), step=0.1)
pids_limit = st.number_input("Sandbox pids limit", min_value=16, max_value=1024, value=int(settings.get("sandbox", {}).get("pids_limit", 64)), step=1)

if st.button("Save Settings"):
    settings["max_iterations"] = int(max_iterations)
    settings["sandbox_timeout_seconds"] = int(sandbox_timeout)
    settings.setdefault("sandbox", {})
    settings["sandbox"]["image"] = image
    settings["sandbox"]["network"] = network
    settings["sandbox"]["memory"] = memory
    settings["sandbox"]["cpus"] = float(cpus)
    settings["sandbox"]["pids_limit"] = int(pids_limit)
    save_yaml("config/settings.yaml", settings)
    st.success("Saved config/settings.yaml")
