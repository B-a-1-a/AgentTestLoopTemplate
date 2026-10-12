from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.utils.key_detection import validate_api_key


class KeyDetectionTests(unittest.TestCase):
    def test_placeholder_is_detected(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-your-key-here"}, clear=False):
            result = validate_api_key("openai", "OPENAI_API_KEY")
        self.assertFalse(result.configured)
        self.assertEqual(result.state, "placeholder")

    def test_openai_valid_format(self) -> None:
        fake_key = "sk-" + "x" * 40
        with patch.dict(os.environ, {"OPENAI_API_KEY": fake_key}, clear=False):
            result = validate_api_key("openai", "OPENAI_API_KEY")
        self.assertTrue(result.configured)
        self.assertEqual(result.state, "valid")

    def test_missing_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            result = validate_api_key("anthropic", "ANTHROPIC_API_KEY")
        self.assertFalse(result.configured)
        self.assertEqual(result.state, "missing")


if __name__ == "__main__":
    unittest.main()
