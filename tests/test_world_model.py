#!/usr/bin/env python3
"""Regression tests for the route world model."""

from __future__ import annotations

import unittest

from agent.world_model import WorldModelPlanner


class WorldModelPlannerTests(unittest.TestCase):
    def test_low_hp_prefers_rest_route(self) -> None:
        planner = WorldModelPlanner("Ironclad")
        state = {
            "decision": "map_select",
            "choices": [
                {"col": 0, "row": 1, "type": "Elite"},
                {"col": 1, "row": 1, "type": "RestSite"},
            ],
            "player": {"hp": 24, "max_hp": 80, "gold": 130},
        }
        map_data = {
            "rows": [
                [
                    {"col": 0, "row": 1, "type": "Elite", "children": [{"col": 0, "row": 2}]},
                    {"col": 1, "row": 1, "type": "RestSite", "children": [{"col": 1, "row": 2}]},
                ],
                [
                    {"col": 0, "row": 2, "type": "Monster", "children": []},
                    {"col": 1, "row": 2, "type": "Shop", "children": []},
                ],
            ]
        }
        memory = {
            "facts": {"hp": 24, "max_hp": 80, "gold": 130},
            "deck_profile": {"starter_cards": 6, "smith_candidates": [{"name": "Pommel Strike"}]},
        }

        result = planner.plan(state, map_data, memory)

        self.assertEqual(result["strategy_mode"], "survival")
        self.assertEqual(result["recommended_choice"]["type"], "RestSite")

    def test_high_hp_can_prefer_elite_route(self) -> None:
        planner = WorldModelPlanner("Ironclad")
        state = {
            "decision": "map_select",
            "choices": [
                {"col": 0, "row": 1, "type": "Elite"},
                {"col": 1, "row": 1, "type": "Monster"},
            ],
            "player": {"hp": 74, "max_hp": 80, "gold": 70},
        }
        map_data = {
            "rows": [
                [
                    {"col": 0, "row": 1, "type": "Elite", "children": [{"col": 0, "row": 2}]},
                    {"col": 1, "row": 1, "type": "Monster", "children": [{"col": 1, "row": 2}]},
                ],
                [
                    {"col": 0, "row": 2, "type": "Treasure", "children": []},
                    {"col": 1, "row": 2, "type": "Unknown", "children": []},
                ],
            ]
        }
        memory = {
            "facts": {"hp": 74, "max_hp": 80, "gold": 70},
            "deck_profile": {
                "starter_cards": 3,
                "upgraded_cards": 3,
                "notable_cards": ["Pommel Strike", "Rage", "Burning Pact", "Fiend Fire"],
                "smith_candidates": [{"name": "Fiend Fire"}],
                "strength_sources": 1,
            },
        }

        result = planner.plan(state, map_data, memory)

        self.assertEqual(result["strategy_mode"], "elite_hunt")
        self.assertEqual(result["recommended_choice"]["type"], "Elite")

    def test_relic_signal_is_reflected_in_route_plan(self) -> None:
        planner = WorldModelPlanner("Ironclad")
        state = {
            "decision": "map_select",
            "choices": [
                {"col": 0, "row": 1, "type": "Elite"},
                {"col": 1, "row": 1, "type": "RestSite"},
            ],
            "player": {
                "hp": 58,
                "max_hp": 80,
                "gold": 95,
                "relics": [
                    {
                        "name": {"en": "War Drum"},
                        "description": {"en": "Gain strength each combat turn and improve damage output."},
                    }
                ],
            },
        }
        map_data = {
            "rows": [
                [
                    {"col": 0, "row": 1, "type": "Elite", "children": []},
                    {"col": 1, "row": 1, "type": "RestSite", "children": []},
                ]
            ]
        }
        memory = {
            "facts": {"hp": 58, "max_hp": 80, "gold": 95},
            "deck_profile": {"starter_cards": 4, "upgraded_cards": 2, "strength_sources": 1},
        }

        result = planner.plan(state, map_data, memory)

        self.assertIn("War Drum", result["player_relics"])
        self.assertGreaterEqual(result["relic_signals"]["tags"]["combat"], 1)
        self.assertEqual(result["recommended_choice"]["type"], "Elite")


if __name__ == "__main__":
    unittest.main()
