# AgentTestLoopTemplate

Local-first template for iterating on LLM agent loops with a Streamlit UI, multi-provider model support, and Docker-based sandboxed code execution.

## Model Freshness Check (Required)

Before using this template, verify provider model IDs in official docs and update `config/models.yaml` when needed.

- Verified at: **2026-02-17**
- OpenAI docs: <https://platform.openai.com/docs/models>
- OpenAI latest model guide: <https://platform.openai.com/docs/guides/latest-model>
- Anthropic models docs: <https://docs.anthropic.com/en/docs/about-claude/models/all-models>
- Google Gemini models docs: <https://ai.google.dev/models/gemini>

Default IDs are alias-first and validated at runtime against provider list endpoints when API keys are configured.

## Quickstart

1. Create and activate a virtualenv.
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```bash
   cp .env.example .env
   ```
4. Build sandbox image:
   ```bash
   docker build -t agent-loop-sandbox:latest ./sandbox
   ```
5. Run app:
   ```bash
   streamlit run app.py
   ```

## Refresh Model IDs Workflow

1. Check latest model docs for OpenAI, Anthropic, and Google.
2. Update `config/models.yaml` IDs and `verified_at` comment/date.
3. Keep latest aliases as defaults.
4. Optionally add pinned snapshot IDs with `pinned: true` and `fallback_pinned_id` for reproducibility.
5. Start the app and verify dashboard badges show no stale configured models.

## Security Baseline

- Sandbox runs as non-root user.
- `--cap-drop=ALL` and `--security-opt no-new-privileges`.
- Resource limits: memory/CPU/PIDs.
- Code mounted read-only into sandbox container.
- Callback result channel over HTTP to host callback server.
- Workspace file tools restricted to `workspace/`.

## Scope

Implemented now:
- Streamlit multipage app
- Provider registry and status dashboard
- OpenAI / Anthropic / Google provider implementations
- Agent loop with JSON tool-call parser
- Sandbox manager and callback server
- Core file tools and workspace manager
- Unit tests for freshness and parser/path safety

Extension points:
- Additional providers
- More tools
- History persistence and eval framework
