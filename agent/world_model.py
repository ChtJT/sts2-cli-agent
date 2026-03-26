#!/usr/bin/env python3
"""Route planning and global path heuristics for the STS2 agent."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _extract_name(obj: Any) -> str:
    if isinstance(obj, dict):
        if obj.get("en"):
            return str(obj["en"])
        if obj.get("zh"):
            return str(obj["zh"])
    return str(obj or "")


def _node_key(col: int, row: int) -> Tuple[int, int]:
    return (int(col), int(row))


def _extract_relics(player: Dict[str, Any]) -> List[Dict[str, str]]:
    relics: List[Dict[str, str]] = []
    for relic in player.get("relics", []):
        if not isinstance(relic, dict):
            continue
        relics.append(
            {
                "name": _extract_name(relic.get("name")),
                "description": _extract_name(relic.get("description")),
            }
        )
    return relics


def _relic_signals(relics: List[Dict[str, str]]) -> Dict[str, Any]:
    tags = {
        "sustain": 0,
        "economy": 0,
        "upgrade": 0,
        "elite": 0,
        "combat": 0,
    }
    notable: List[str] = []

    for relic in relics:
        name = relic["name"]
        haystack = f"{name} {relic['description']}".lower()
        if any(term in haystack for term in ["heal", "hp", "rest", "recover"]):
            tags["sustain"] += 1
            notable.append(f"{name}: sustain")
        if any(term in haystack for term in ["gold", "shop", "discount", "price"]):
            tags["economy"] += 1
            notable.append(f"{name}: economy")
        if any(term in haystack for term in ["upgrade", "smith"]):
            tags["upgrade"] += 1
            notable.append(f"{name}: smith")
        if any(term in haystack for term in ["elite", "boss", "rare"]):
            tags["elite"] += 1
            notable.append(f"{name}: elite-upside")
        if any(term in haystack for term in ["strength", "damage", "attack", "combat", "turn"]):
            tags["combat"] += 1
            notable.append(f"{name}: combat")

    return {"tags": tags, "notable": notable[:5]}


class WorldModelPlanner:
    """A small world-model style planner for map routing."""

    def __init__(self, character: str) -> None:
        self.character = character

    def plan(
        self,
        state: Dict[str, Any],
        map_data: Dict[str, Any],
        memory: Dict[str, Any],
    ) -> Dict[str, Any]:
        player = state.get("player", {})
        facts = memory.get("facts", {})
        deck_profile = memory.get("deck_profile", {})
        relics = _extract_relics(player)
        relic_signals = _relic_signals(relics)
        hp = int(player.get("hp") or facts.get("hp") or 0)
        max_hp = int(player.get("max_hp") or facts.get("max_hp") or 1)
        gold = int(player.get("gold") or facts.get("gold") or 0)
        hp_ratio = hp / max(max_hp, 1)

        preferences = self._room_preferences(hp_ratio, gold, deck_profile, relic_signals)
        graph = self._build_graph(map_data)
        choices = state.get("choices", [])
        scored_choices = [
            self._score_choice(choice, graph, preferences, hp_ratio, gold, deck_profile)
            for choice in choices
        ]
        scored_choices.sort(key=lambda item: item["score"], reverse=True)

        strategic_goals = self._strategic_goals(hp_ratio, gold, deck_profile)
        recommended = scored_choices[0] if scored_choices else None

        return {
            "character": self.character,
            "strategy_mode": preferences["mode"],
            "hp_ratio": round(hp_ratio, 3),
            "gold": gold,
            "player_relics": [relic["name"] for relic in relics],
            "relic_signals": relic_signals,
            "strategic_goals": strategic_goals,
            "room_preferences": preferences["order"],
            "recommended_choice": recommended,
            "scored_choices": scored_choices,
        }

    def _room_preferences(
        self,
        hp_ratio: float,
        gold: int,
        deck_profile: Dict[str, Any],
        relic_signals: Dict[str, Any],
    ) -> Dict[str, Any]:
        starter_cards = int(deck_profile.get("starter_cards", 0))
        smith_candidates = deck_profile.get("smith_candidates", [])
        strong_deck = (
            int(deck_profile.get("upgraded_cards", 0)) >= 2
            or len(deck_profile.get("notable_cards", [])) >= 4
            or int(deck_profile.get("strength_sources", 0)) >= 1
        )
        tags = relic_signals.get("tags", {})

        mode = "balanced"
        base = {
            "Monster": 8.0,
            "Elite": 6.0,
            "RestSite": 5.0,
            "Shop": 5.0,
            "Treasure": 7.0,
            "Event": 6.0,
            "Unknown": 6.0,
            "Ancient": 7.0,
            "Boss": 20.0,
        }

        if hp_ratio <= 0.45:
            mode = "survival"
            base["RestSite"] += 9
            base["Shop"] += 5
            base["Unknown"] += 2
            base["Treasure"] += 2
            base["Elite"] -= 8
        elif hp_ratio <= 0.65:
            mode = "stabilize"
            base["RestSite"] += 5
            base["Shop"] += 4
            base["Elite"] -= 3
        elif strong_deck and starter_cards <= 4:
            mode = "elite_hunt"
            base["Elite"] += 8
            base["RestSite"] -= 2
            base["Monster"] += 2

        if gold >= 150:
            base["Shop"] += 7
        elif gold >= 90:
            base["Shop"] += 3

        if smith_candidates and hp_ratio >= 0.6:
            base["RestSite"] += 2

        if int(tags.get("sustain", 0)) >= 1 and hp_ratio >= 0.55:
            base["RestSite"] -= 2
            base["Elite"] += 1
        if int(tags.get("economy", 0)) >= 1:
            base["Shop"] += 2
        if int(tags.get("upgrade", 0)) >= 1 and smith_candidates:
            base["RestSite"] += 2
        if int(tags.get("elite", 0)) >= 1 and hp_ratio >= 0.65:
            base["Elite"] += 3
        if int(tags.get("combat", 0)) >= 2 and hp_ratio >= 0.65:
            base["Monster"] += 1
            base["Elite"] += 1

        order = [name for name, _ in sorted(base.items(), key=lambda item: item[1], reverse=True)]
        return {"mode": mode, "scores": base, "order": order}

    def _strategic_goals(self, hp_ratio: float, gold: int, deck_profile: Dict[str, Any]) -> List[str]:
        goals: List[str] = []
        if hp_ratio <= 0.45:
            goals.append("Preserve HP and reach the next rest or shop safely.")
        elif hp_ratio <= 0.65:
            goals.append("Avoid over-greedy routing until HP is more stable.")

        if gold >= 150 and int(deck_profile.get("starter_cards", 0)) >= 4:
            goals.append("Look for a shop to remove starter cards or buy a premium discounted piece.")

        if int(deck_profile.get("starter_cards", 0)) <= 4 and hp_ratio >= 0.7:
            goals.append("Take stronger fights when the route offers elite upside.")

        smith_candidates = deck_profile.get("smith_candidates", [])
        if smith_candidates:
            goals.append(f"Next rest site upgrade target: {smith_candidates[0]['name']}.")

        if not goals:
            goals.append("Maintain a balanced route with card quality and survivability in mind.")
        return goals[:4]

    def _build_graph(self, map_data: Dict[str, Any]) -> Dict[Tuple[int, int], Dict[str, Any]]:
        graph: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for row in map_data.get("rows", []):
            for node in row:
                key = _node_key(node.get("col", 0), node.get("row", 0))
                graph[key] = {
                    "type": node.get("type", "Unknown"),
                    "children": [
                        _node_key(child.get("col", 0), child.get("row", 0))
                        for child in node.get("children", [])
                    ],
                }
        return graph

    def _score_choice(
        self,
        choice: Dict[str, Any],
        graph: Dict[Tuple[int, int], Dict[str, Any]],
        preferences: Dict[str, Any],
        hp_ratio: float,
        gold: int,
        deck_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        key = _node_key(choice.get("col", 0), choice.get("row", 0))
        immediate_type = choice.get("type", "Unknown")
        immediate_score = preferences["scores"].get(immediate_type, 5.0)
        lookahead_score, path_mix = self._best_future_path(key, graph, preferences["scores"], depth=4)

        score = immediate_score + lookahead_score
        reasons = [f"Immediate room is {immediate_type}."]

        if immediate_type == "Elite":
            if hp_ratio <= 0.55:
                score -= 6
                reasons.append("Elite is risky at the current HP.")
            else:
                reasons.append("HP is high enough to consider elite reward.")
        if immediate_type == "RestSite":
            if hp_ratio <= 0.6:
                reasons.append("Rest site matches the current survival pressure.")
            else:
                reasons.append("Rest site is mainly useful for smithing, not emergency healing.")
        if immediate_type == "Shop":
            if gold >= 120:
                reasons.append("Gold is high enough for meaningful shop value.")
            else:
                reasons.append("Shop is lower value because gold is still modest.")

        if path_mix:
            summary = ", ".join(f"{room}:{count}" for room, count in path_mix[:3])
            reasons.append(f"Best downstream path leans toward {summary}.")

        if int(deck_profile.get("starter_cards", 0)) >= 5 and immediate_type == "Shop" and gold >= 75:
            score += 3
            reasons.append("Starter-heavy deck makes card removal especially valuable.")

        return {
            "col": choice.get("col"),
            "row": choice.get("row"),
            "type": immediate_type,
            "score": round(score, 2),
            "reasons": reasons[:4],
            "downstream_mix": path_mix[:4],
        }

    def _best_future_path(
        self,
        start: Tuple[int, int],
        graph: Dict[Tuple[int, int], Dict[str, Any]],
        scores: Dict[str, float],
        depth: int,
    ) -> Tuple[float, List[Tuple[str, int]]]:
        visited: Dict[Tuple[Tuple[int, int], int], Tuple[float, Dict[str, int]]] = {}

        def walk(node: Tuple[int, int], remaining: int) -> Tuple[float, Dict[str, int]]:
            cache_key = (node, remaining)
            if cache_key in visited:
                return visited[cache_key]

            info = graph.get(node)
            if info is None:
                return (0.0, {})

            node_type = info.get("type", "Unknown")
            own_score = scores.get(node_type, 5.0) * 0.35
            own_mix = {node_type: 1}
            children = info.get("children", [])
            if remaining <= 0 or not children:
                visited[cache_key] = (own_score, own_mix)
                return visited[cache_key]

            best_child_score = -999.0
            best_child_mix: Dict[str, int] = {}
            for child in children:
                child_score, child_mix = walk(child, remaining - 1)
                if child_score > best_child_score:
                    best_child_score = child_score
                    best_child_mix = child_mix

            merged_mix = dict(best_child_mix)
            merged_mix[node_type] = merged_mix.get(node_type, 0) + 1
            visited[cache_key] = (own_score + best_child_score, merged_mix)
            return visited[cache_key]

        _, mix = walk(start, depth)
        score, _ = walk(start, depth)
        ordered_mix = sorted(mix.items(), key=lambda item: item[1], reverse=True)
        return (round(score, 2), ordered_mix)
