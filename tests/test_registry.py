from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.providers.registry import ProviderRegistry


class _FakeProvider:
    def __init__(self, remote: list[str]) -> None:
        self._remote = remote

    def list_models_remote(self) -> list[str]:
        return self._remote


class RegistryTests(unittest.TestCase):
    def _write_config(self, path: Path) -> None:
        payload = {
            "providers": {
                "openai": {
                    "env_key": "OPENAI_API_KEY",
                    "models": [
                        {
                            "id": "gpt-5.2",
                            "name": "GPT-5.2",
                            "pinned": False,
                            "fallback_pinned_id": "gpt-5.2-20260115",
                            "default_params": {"temperature": 0.7, "max_tokens": 4096},
                        },
                        {
                            "id": "gpt-5.2-20260115",
                            "name": "GPT-5.2 pinned",
                            "pinned": True,
                            "default_params": {"temperature": 0.7, "max_tokens": 4096},
                        },
                    ],
                }
            }
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_marks_stale_when_missing_from_remote(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "models.yaml"
            self._write_config(config_path)

            registry = ProviderRegistry(models_path=config_path)
            with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-" + "x" * 50}, clear=False):
                with patch.object(registry, "_provider_instance", return_value=_FakeProvider(["some-other-model"])):
                    snapshot = registry.validate_models_from_api()

            stale = [m for m in snapshot.configured_models if m.stale_or_unavailable]
            self.assertTrue(stale)
            self.assertIn("gpt-5.2", [m.id for m in stale])

    def test_alias_falls_back_to_pinned_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "models.yaml"
            self._write_config(config_path)
            registry = ProviderRegistry(models_path=config_path)

            result = registry.resolve_model_id(
                provider_name="openai",
                requested_id="gpt-5.2",
                remote_ids=["gpt-5.2-20260115"],
            )
            self.assertTrue(result.used_fallback)
            self.assertEqual(result.selected_model_id, "gpt-5.2-20260115")


if __name__ == "__main__":
    unittest.main()
