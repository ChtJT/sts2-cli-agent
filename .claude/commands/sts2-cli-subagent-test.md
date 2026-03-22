Launch 5 subagents in parallel, each playing sts2-cli as a different character (Ironclad, Silent, Defect, Regent, Necrobinder). Each subagent plays $ARGUMENTS games (default: 3) by **making its own LLM decisions**.

## What to check for bugs

Each subagent must verify these mechanics work correctly:

### Card display
- **Stats**: damage, block, and other DynamicVars resolved in description (no `[VarName]` leaks)
- **Keywords**: Exhaust(消耗), Innate(固有), Ethereal(虚无), Retain(保留), Sly(奇巧), Eternal(永恒), Unplayable(不能被打出)
- **Enchantments**: Clone(克隆), Sharp(锋利), Nimble(灵巧), etc. — shown with name and amount
- **Afflictions**: Bound, Hexed, etc. — shown on affected cards
- **Upgrade preview**: stat changes, cost changes, keyword add/remove (e.g., Discovery removes Exhaust)
- **Star cost**: Regent cards show ⭐ cost

### Character mechanics
- **Defect**: orbs (Lightning/Frost/Dark/Plasma/Glass) with passive/evoke values, orb_slots count
- **Regent**: stars count, star-cost cards gated by can_play
- **Necrobinder**: Osty HP/MaxHP/Block/alive, grows per turn, resets per combat
- **Silent**: Neutralize deals damage + Weak (Harmony patched)

### Events & rewards
- Event names localized (涅奥 not Neow)
- Event option descriptions with resolved template vars ({Gold}→150)
- Card rewards let user choose (not auto-selected)
- Event-triggered card rewards (Lost Box, Brain Leech) block for user choice
- Scroll Boxes (bundle_select) respond quickly, not slow

### Map
- Current position shown (green [x] or "你在起点")
- Choices show column/row coordinates to match grid
- Connection lines between rows

### Display quality
- All text in correct language (zh or en based on LANG)
- No raw loc keys (UPPERCASE.dotted.paths)
- No BBCode tags ([gold]...[/gold])
- Potion descriptions resolved
- Relic descriptions resolved
- Deck view shows card effects and keywords

## How to play

```python
import json, subprocess, os
os.environ["STS2_GAME_DIR"] = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Slay the Spire 2/SlayTheSpire2.app/Contents/Resources/data_sts2_macos_arm64")
proc = subprocess.Popen([os.path.expanduser("~/.dotnet-arm64/dotnet"), "run", "--no-build", "--project", "Sts2Headless/Sts2Headless.csproj"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
def read():
    while True:
        l = proc.stdout.readline().strip()
        if not l: return None
        if l.startswith("{"): return json.loads(l)
def send(cmd):
    proc.stdin.write(json.dumps(cmd) + "\n"); proc.stdin.flush()
    return read()
```

**Commands**: start_run, select_map_node(col,row), play_card(card_index, target_index), end_turn, select_card_reward(card_index), skip_card_reward, choose_option(option_index), leave_room, select_cards(indices), select_bundle(bundle_index), use_potion(potion_index, target_index)

## After agents complete

1. Collect all bugs
2. Fix bugs
3. Run regression: `python3 python/play_full_run.py 5 <char>` for each char
4. Run quality test: `python3 python/test_quality.py`
5. Update learning.md
6. Commit (ask user first)
