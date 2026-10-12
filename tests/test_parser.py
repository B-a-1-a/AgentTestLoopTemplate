from __future__ import annotations

import unittest

from src.agent.parser import parse_agent_response


class ParserTests(unittest.TestCase):
    def test_parse_valid_tool_calls(self) -> None:
        text = '{"tool_calls":[{"id":"1","name":"list_files","arguments":{"path":"."}}],"final_answer":""}'
        result = parse_agent_response(text)
        self.assertIsNone(result.error)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "list_files")

    def test_parse_invalid_json(self) -> None:
        text = "{not-json}"
        result = parse_agent_response(text)
        self.assertIsNotNone(result.error)

    def test_parse_final_answer_only(self) -> None:
        text = '{"tool_calls":[],"final_answer":"done"}'
        result = parse_agent_response(text)
        self.assertIsNone(result.error)
        self.assertEqual(result.final_answer, "done")


if __name__ == "__main__":
    unittest.main()
