#!/usr/bin/env python3
"""Regression tests for agent provider command shapes."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from agent.providers import OpenAIProvider
from agent.runner import AgentRunner


class OpenAIProviderShapeTests(unittest.TestCase):
    def setUp(self) -> None:
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)
        self.provider = OpenAIProvider()

    def test_single_card_select_exposes_single_card_tool(self) -> None:
        state = {
            "decision": "card_select",
            "min_select": 1,
            "max_select": 1,
            "cards": [{"index": 0}, {"index": 9}],
        }

        self.assertEqual(self.provider._tool_names(state), ["select_single_card_action"])

    def test_single_card_select_normalizes_to_indices_command(self) -> None:
        decision = self.provider._normalize_tool_call(
            "select_single_card_action",
            {
                "card_index": 9,
                "decision_steps": ["Pick the strongest early card."],
                "rationale": "Bash is stronger than a basic Strike.",
                "memory_note": "Picked Bash from Neow transform.",
            },
        )

        self.assertEqual(
            decision.command,
            {"cmd": "action", "action": "select_cards", "args": {"indices": "9"}},
        )

    def test_runner_accepts_normalized_single_card_command(self) -> None:
        state = {
            "decision": "card_select",
            "min_select": 1,
            "max_select": 1,
            "cards": [{"index": 0}, {"index": 9}],
        }
        decision = self.provider._normalize_tool_call(
            "select_single_card_action",
            {
                "card_index": 9,
                "decision_steps": ["Pick the strongest early card."],
                "rationale": "Bash is stronger than a basic Strike.",
                "memory_note": "Picked Bash from Neow transform.",
            },
        )

        runner = AgentRunner.__new__(AgentRunner)
        validated = runner._validate_command(state, decision.command)

        self.assertEqual(
            validated,
            {"cmd": "action", "action": "select_cards", "args": {"indices": "9"}},
        )


if __name__ == "__main__":
    unittest.main()
