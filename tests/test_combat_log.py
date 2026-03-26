#!/usr/bin/env python3
"""Regression tests for combat log capture."""

from __future__ import annotations

import tempfile
import unittest

from agent.combat_log import CombatLogRecorder


class CombatLogRecorderTests(unittest.TestCase):
    def test_writes_one_file_per_combat(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            recorder = CombatLogRecorder(tempdir)
            recorder.begin_run("run-xyz")
            state = {
                "decision": "combat_play",
                "round": 1,
                "energy": 3,
                "max_energy": 3,
                "player": {
                    "name": {"en": "The Ironclad"},
                    "hp": 80,
                    "max_hp": 80,
                    "block": 0,
                    "gold": 99,
                    "deck_size": 10,
                    "relics": [],
                    "potions": [],
                },
                "context": {"floor": 3, "room_type": "Monster"},
                "enemies": [
                    {
                        "index": 0,
                        "name": {"en": "Jaw Worm"},
                        "hp": 40,
                        "max_hp": 40,
                        "block": 0,
                        "intents": [{"type": "Attack", "damage": 11}],
                        "powers": [],
                    }
                ],
                "hand": [
                    {
                        "index": 0,
                        "name": {"en": "Strike"},
                        "cost": 1,
                        "type": "Attack",
                        "can_play": True,
                        "target_type": "AnyEnemy",
                        "stats": {"damage": 6},
                    }
                ],
            }
            response = {
                "decision": "card_reward",
                "gold_earned": 15,
                "player": state["player"],
                "cards": [
                    {
                        "index": 0,
                        "name": {"en": "Pommel Strike"},
                        "type": "Attack",
                        "cost": 1,
                        "stats": {"damage": 9, "cards": 1},
                    }
                ],
            }

            recorder.record(
                step=12,
                state=state,
                command={"cmd": "action", "action": "play_card", "args": {"card_index": 0, "target_index": 0}},
                decision_steps=["Only one target remains.", "Strike is the efficient lethal line."],
                rationale="Play Strike to finish the fight.",
            )
            completed_path = recorder.finalize(state, response)

            files = list((recorder.base_dir).glob("*.log"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            self.assertEqual(completed_path, files[0])
            self.assertEqual(recorder.current_or_last_path(), files[0])
            self.assertIn("Jaw Worm", content)
            self.assertIn("ACTION: play_card", content)
            self.assertIn("Pommel Strike", content)
            self.assertTrue("卡牌奖励" in content or "Card Reward" in content)


if __name__ == "__main__":
    unittest.main()
