#!/usr/bin/env python3
"""Capture full combat terminal views for later inspection."""

from __future__ import annotations

import io
import os
import re
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from python import play as terminal_play


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return cleaned or "combat"


def _extract_name(obj: Any) -> str:
    if isinstance(obj, dict):
        if obj.get("en"):
            return str(obj["en"])
        if obj.get("zh"):
            return str(obj["zh"])
    return str(obj or "")


def _capture(fn, state: Dict[str, Any]) -> str:
    terminal_play.LANG = os.environ.get("STS2_VIEW_LANG", "zh")
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        fn(state)
    return buffer.getvalue().rstrip() + "\n"


class CombatLogRecorder:
    """Persist each combat as a standalone terminal-style log file."""

    def __init__(self, state_dir: str) -> None:
        self.base_dir = Path(state_dir) / "combat_logs"
        self.run_id: Optional[str] = None
        self.combat_index = 0
        self.active_path: Optional[Path] = None
        self.last_completed_path: Optional[Path] = None

    def begin_run(self, run_id: str) -> None:
        self.run_id = run_id
        self.combat_index = 0
        self.active_path = None
        self.last_completed_path = None
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        step: int,
        state: Dict[str, Any],
        command: Dict[str, Any],
        decision_steps: Iterable[str],
        rationale: str,
    ) -> None:
        if state.get("decision") != "combat_play":
            return
        path = self._ensure_active_file(state)
        lines = [
            f"=== Step {step:03d} ===",
            _capture(terminal_play.show_combat, state).rstrip(),
            f"ACTION: {command.get('action')} {command.get('args', {})}",
        ]
        steps = [str(item).strip() for item in decision_steps if str(item).strip()]
        if steps:
            lines.append("REASONING: " + " | ".join(steps))
        if rationale:
            lines.append("RATIONALE: " + rationale)
        lines.append("")
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    def finalize(self, state: Dict[str, Any], response: Optional[Dict[str, Any]]) -> Optional[Path]:
        if state.get("decision") != "combat_play" or self.active_path is None:
            return None
        if response is not None and response.get("decision") == "combat_play":
            return None

        lines = []
        if response is not None and response.get("decision") == "card_reward":
            lines.append("=== Combat End ===")
            lines.append(_capture(terminal_play.show_card_reward, response).rstrip())
        elif response is not None and response.get("decision") == "game_over":
            lines.append("=== Combat End ===")
            lines.append("Result: game_over")
        else:
            next_state = None if response is None else response.get("decision", response.get("type"))
            lines.append("=== Combat End ===")
            lines.append(f"Result: {next_state}")

        completed_path = self.active_path
        with completed_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n\n")
        self.last_completed_path = completed_path
        self.active_path = None
        return completed_path

    def current_or_last_path(self) -> Optional[Path]:
        return self.active_path or self.last_completed_path

    def _ensure_active_file(self, state: Dict[str, Any]) -> Path:
        if self.active_path is not None:
            return self.active_path

        self.combat_index += 1
        floor = (state.get("context") or {}).get("floor", "?")
        enemy_names = ",".join(_slug(_extract_name(enemy.get("name", ""))) for enemy in state.get("enemies", []))
        enemy_names = enemy_names or "unknown-enemy"
        filename = f"{self.run_id or 'run'}_combat_{self.combat_index:03d}_floor_{floor}_{enemy_names}.log"
        self.active_path = self.base_dir / filename
        with self.active_path.open("w", encoding="utf-8") as handle:
            handle.write(f"Run: {self.run_id}\n")
            handle.write(f"Combat: {self.combat_index}\n")
            handle.write(f"Floor: {floor}\n")
            handle.write("\n")
        return self.active_path
