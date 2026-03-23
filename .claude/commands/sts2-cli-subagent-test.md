# STS2-CLI Continuous Improvement Loop

Run a continuous play→fix→test loop until all 5 characters (Ironclad, Silent, Defect, Regent, Necrobinder) can **beat Act 3 final boss** (victory=true) at difficulty 0.

Games per character per iteration: $ARGUMENTS (default: 1).

## Architecture

Each play-subagent interacts with the game **one decision at a time via HTTP bridge** — the LLM IS the player, reasoning about each game state with full learning context.

```
Game Process ←→ sts2_bridge.py (local HTTP) ←→ Subagent (curl + LLM reasoning per decision)
```

## HARD REQUIREMENTS

1. **LLM decides every action** — subagent uses `curl` to send one command, reads the JSON response, reasons about the best play, sends next command. NO writing Python scripts with hardcoded strategy.
2. **NEVER write .py/.sh files** — subagents must NOT create any script files. NO bash loops, NO automation scripts, NO run_in_background for game commands.
3. **BE EXTREMELY CONCISE** — subagents must minimize reasoning text to save context window. Write AT MOST 1-2 lines per action (state → decision). Do NOT repeat JSON responses. This is critical for completing full games.
4. **Learning files are per-character** — `agent/learning_general.md` + `agent/learning_<character>.md`. Bilingual (EN + 中文). Use official translations from `localization_zhs/`.
5. **agent/bug.md** tracks code/protocol issues separately.
6. **Before each game**, subagent reads its character's learning file + general learning file.
7. **After each game**, subagent updates its character's learning file with new insights (deduplicate, consolidate).
8. **Before first iteration**, build: `~/.dotnet-arm64/dotnet build Sts2Headless/Sts2Headless.csproj`
9. **Seeds**: always random (use `uuid4` hex or similar).

---

## Setup: HTTP Bridge

Each subagent needs its own bridge instance (separate port, separate game process).

### Start bridge
```bash
# Use --compact for AI agents (strips descriptions, reduces JSON ~60%)
python3 /Users/haowu/Workspace/sts2-cli/agent/sts2_bridge.py <PORT> --compact &
# Wait for startup
sleep 5
```

### Send commands
```bash
# Start a run
curl -s localhost:<PORT> -d '{"cmd":"start_run","character":"Ironclad","seed":"abc123"}'

# Action commands
curl -s localhost:<PORT> -d '{"cmd":"action","action":"play_card","args":{"card_index":0,"target_index":0}}'
curl -s localhost:<PORT> -d '{"cmd":"action","action":"end_turn"}'
curl -s localhost:<PORT> -d '{"cmd":"action","action":"select_map_node","args":{"col":2,"row":1}}'

# Info commands
curl -s localhost:<PORT> -d '{"cmd":"get_map"}'
curl -s localhost:<PORT> -d '{"cmd":"action","action":"quit"}'
```

---

## LOOP: Repeat until all 5 characters have at least 1 victory

### Phase 1: PLAY (5 parallel subagents)

Launch 5 subagents in parallel, each assigned one character and a unique bridge port (9871-9875).

**Subagent prompt must include:**
- Instructions to start bridge on its assigned port
- The "Game Protocol Reference" section below
- Character assignment and number of games
- Instruction to read `agent/learning_general.md` + `agent/learning_<character>.md` before playing
- Instruction to update `agent/learning_<character>.md` after each game
- The play loop structure (below)

**Subagent play loop (for each game):**
```
1. Read agent/learning_general.md and agent/learning_<character>.md (absorb silently, don't repeat)
2. Start bridge: python3 agent/sts2_bridge.py <PORT> --compact &
3. Start run: curl -s localhost:<PORT> -d '{"cmd":"start_run","character":"...","seed":"<random>"}'
4. Decision loop:
   a. Parse the JSON response — check "type" and "decision" fields
   b. If game_over → record result, break
   c. If error → try proceed/leave_room recovery
   d. Otherwise: reason BRIEFLY (1-2 lines) about game state, decide best action
   e. Send action via curl, get next state
   f. Repeat from (a)
5. After game:
   a. If loss: analyze death — what killed you, which decisions were wrong
   b. Read current learning file, MERGE new insights into existing sections (don't just append!)
   c. DEDUPLICATE: if an insight already exists, strengthen/update it instead of adding a duplicate
   d. ORGANIZE by topic: Combat, Map, Card Picks, Enemy-Specific, Boss-Specific, etc.
   e. PRUNE: remove per-game logs (e.g. "Game 3 (seed xxx): LOSS...") — keep only distilled insights
   f. KEEP FILE UNDER 120 LINES — if longer, consolidate aggressively
   g. Format: EVERY entry MUST be bilingual (EN + 中文 on same line or adjacent lines)
      Example: "- **Byrdonis** (多尼斯异鸟, 94hp) — Strength scales exponentially, must kill in 4-5 turns"
      Use official translations from localization_zhs/ (cards.json, monsters.json, keywords.json)
      NEVER invent translations — look them up
   h. Only add actionable insights with concrete thresholds, not vague advice
6. Kill bridge process, start new one for next game
```

**CONCISENESS: subagent must write AT MOST this per action:**
```
F5 R1: HP 65/80, 3e. Nibbit 45hp(atk11). Inc=11. → Bash(i1,t0)
F5 R1: HP 65/80, 2e. Nibbit 39hp(vuln). → Strike(i0,t0)
F5 R1: HP 65/80, 1e. Nibbit 33hp. → Defend(i3). end_turn.
```
Do NOT dump full JSON. Do NOT explain known card effects. Just: state → decision → action.

**How subagent reasons about combat_play (most important decision):**
```
Given: hand cards, enemies with intents, energy, HP, block, character-specific state
1. Calculate total incoming damage from enemy intents
2. Assess threat level: lethal? danger? safe?
3. Decide play order:
   - 0-cost cards first (free value)
   - If lethal: block/survive only
   - If safe: powers first, then damage
   - Use potions if HP critical or boss fight
4. For each card to play: determine target (highest-threat enemy, or one-shottable)
5. Send play_card commands one at a time, reading state after each
6. When out of energy or no good plays: end_turn
```

**Subagent report format:**
```
## Results
- Game 1: [WIN/LOSS] Act X Floor Y, HP xx/xx, Deck xx cards, seed=xxx
  Key moments: [brief summary of critical decisions]

## Bugs Found
- BUG-XXX: [title] | Decision: [type] | Error: [msg] | Repro: [steps]

## Death Analysis (for each loss)
- Game N: [what killed you, what could have been done differently]

## Learning Updates
- [list of new insights added to learning file]
```

### Phase 2: CURATE (main agent)

After all 5 subagents complete:

**agent/bug.md** — Read current file (create if missing). For each new bug reported by subagents:
- Check if already listed → skip duplicate
- Add with status `[OPEN]` and date
- Format:
```markdown
## [OPEN] BUG-XXX: Title (YYYY-MM-DD)
- **Decision type**: combat_play / map_select / etc.
- **Description**: what went wrong
- **Repro**: steps to reproduce (character, seed, floor)
- **Relevant code**: file:line if identifiable
```
- When fixed: change `[OPEN]` → `[FIXED]`, add fix date and description

**agent/learning_*.md** — CRITICAL: Review and curate what subagents wrote. Files MUST stay under 120 lines each:
- **Deduplicate**: don't add what's already there
- **Consolidate**: if multiple agents learned the same thing, strengthen the existing entry
- **Filter**: only keep insights that directly affect AI decision-making at a decision point
- **Organize**: by topic (Combat, Map Navigation, Card Picks, Enemy-Specific, Boss-Specific, etc.)
- **PRUNE per-game logs**: Remove "Game N (seed xxx): LOSS..." entries. Distill into reusable insights only.
- **LINE LIMIT**: If any file exceeds 120 lines, aggressively merge/remove low-value entries
- **Quantify**: prefer concrete thresholds ("block when incoming > 20") over vague advice ("block sometimes")
- **Bilingual**: every section must have both English and 中文. Use official game translations from `localization_zhs/` for card names (cards.json), enemy names (monsters.json), keywords (keywords.json), relics (relics.json), potions (potions.json). NEVER invent translations — look them up.
- **Cross-pollinate**: if a character-specific insight applies generally, add to `learning_general.md` too
- **Prune**: remove learnings proven wrong by later games

### Phase 3: FIX (subagents as needed)

If `agent/bug.md` has `[OPEN]` bugs:
1. Launch fix-subagent(s) with bug description + relevant code
2. After fixes, rebuild: `~/.dotnet-arm64/dotnet build Sts2Headless/Sts2Headless.csproj`
3. Update agent/bug.md: `[OPEN]` → `[FIXED]`

### Phase 4: VERIFY

```bash
STS2_GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Slay the Spire 2/SlayTheSpire2.app/Contents/Resources/data_sts2_macos_arm64" python3 python/play_full_run.py 2 <character>
```
All 5 characters must complete 2/2 with no crashes.

### Exit check

Loop exits when all 5 characters have at least 1 `victory: true`.

Report progress after each iteration:
```
Iteration N complete. Victories: Ironclad ✓, Silent ✗, ...
Best results: ...
```

---

## Game Protocol Reference

### All commands

| Command | Args | Description |
|---------|------|-------------|
| `start_run` | `character`, `seed` | Start new game. Characters: Ironclad, Silent, Defect, Regent, Necrobinder |
| `select_map_node` | `col`, `row` | Choose map node |
| `play_card` | `card_index`, `target_index`? | Play card. `target_index` required when `target_type == "AnyEnemy"` |
| `end_turn` | — | End combat turn |
| `select_card_reward` | `card_index` | Pick card reward |
| `skip_card_reward` | — | Skip card reward |
| `choose_option` | `option_index` | Choose event/rest option |
| `leave_room` | — | Leave room (shop, event) |
| `select_cards` | `indices` (string) | Select cards, e.g. `"0"` or `"0,1,2"` |
| `select_bundle` | `bundle_index` | Choose card pack |
| `use_potion` | `potion_index`, `target_index`? | Use potion |
| `buy_card` | `card_index` | Buy card in shop |
| `buy_relic` | `relic_index` | Buy relic in shop |
| `buy_potion` | `potion_index` | Buy potion in shop |
| `remove_card` | — | Remove card in shop |
| `get_map` | — | Get full map (info only) |
| `proceed` | — | Force advance (error recovery) |
| `quit` | — | End session |

**Format**: `curl -s localhost:<PORT> -d '{"cmd":"action","action":"<command>","args":{...}}'`
**Start run**: `curl -s localhost:<PORT> -d '{"cmd":"start_run","character":"...","seed":"..."}'`
**Get map**: `curl -s localhost:<PORT> -d '{"cmd":"get_map"}'`

### Decision types

#### `map_select`
```json
{"decision": "map_select", "choices": [{"col": 2, "row": 1, "type": "Monster"}]}
```
Node types: Monster, Elite, Boss, RestSite, Shop, Treasure, Event, Unknown, Ancient

#### `combat_play`
```json
{
  "decision": "combat_play", "round": 1, "energy": 3, "max_energy": 3,
  "hand": [{"index": 0, "name": {"en":"Strike","zh":"打击"}, "stats": {"damage": 6}, "cost": 1, "can_play": true, "type": "Attack", "target_type": "AnyEnemy", "keywords": [], "star_cost": 0}],
  "enemies": [{"index": 0, "name": {"en":"Jaw Worm","zh":"颚虫"}, "hp": 40, "max_hp": 40, "block": 0, "intents": [{"type": "Attack", "damage": 11, "hits": 1}], "powers": []}],
  "orbs": [], "orb_slots": 0,  // Defect
  "stars": 0,                   // Regent
  "osty": null                  // Necrobinder
}
```
- Only play cards where `can_play == true` and `cost <= energy`
- `target_index` required only when `target_type == "AnyEnemy"`
- Known bug: Regent's Particle Wall and Astral Pulse may report wrong `can_play` — verify star cost manually

#### `card_reward`
```json
{"decision": "card_reward", "cards": [{"index": 0, "name": {...}, "cost": 1, "type": "Attack", "rarity": "Common", "stats": {...}}]}
```

#### `event_choice`
```json
{"decision": "event_choice", "event_name": {"en":"Neow","zh":"涅奥"}, "options": [{"index": 0, "title": {...}, "description": {...}, "is_locked": false}]}
```
Only choose `is_locked == false` options.

#### `rest_site`
```json
{"decision": "rest_site", "options": [{"index": 0, "option_id": "HEAL", "name": "Heal 30% HP", "is_enabled": true}]}
```
Only choose `is_enabled == true` options.

#### `shop`
```json
{"decision": "shop", "cards": [...], "relics": [...], "potions": [...], "card_removal_cost": 75}
```

#### `bundle_select`, `card_select`, `game_over`
Standard handling. `game_over` has `victory` bool.

### Error handling
On `{"type": "error"}`: try `proceed` → `leave_room` → `end_turn`

### Character mechanics

| Character | Mechanic | State fields |
|-----------|----------|-------------|
| Ironclad | Strength, self-heal (Burning Blood: +6 HP/combat) | standard |
| Silent | Poison, Weak (Neutralize), Burst | standard |
| Defect | Orbs (Frost/Lightning/Dark/Plasma/Glass), Focus | `orbs`, `orb_slots` |
| Regent | Stars resource, star-cost cards | `stars`, card `star_cost` |
| Necrobinder | Osty companion (grows each turn, resets each combat) | `osty` {hp, max_hp, block, alive} |
