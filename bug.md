# STS2-CLI Bug Tracker

## [FIXED] BUG-001: Potion index shifts after use, causing invalid index errors (2026-03-22, fixed 2026-03-22)
- **Decision type**: combat_play
- **Description**: After using a potion at index 0, remaining potions shift indices but the old indices are still referenced.
- **Fix**: Changed verification from index-based check to reference-based `Contains(potion)` check in `DoUsePotion`.
- **Relevant code**: Sts2Headless/RunSimulator.cs:~775

## [FIXED] BUG-002: Potion use_potion fails silently for some potion types (2026-03-22, fixed 2026-03-22)
- **Decision type**: combat_play
- **Description**: Potions with TargetType.None/All (Attack Potion, Fortifier, Lucky Tonic) had incorrect auto-targeting.
- **Fix**: Removed catch-all else branch that forced `target = player.Creature`. Now only Self/AnyEnemy get auto-targets; others correctly leave target as null.
- **Relevant code**: Sts2Headless/RunSimulator.cs (DoUsePotion auto-targeting)

## [OPEN] BUG-003: EOF crash during Leaf Slime combat (2026-03-22)
- **Decision type**: combat_play
- **Description**: Simulator occasionally crashes (returns EOF) during combat with Leaf Slime groups, possibly related to slime splitting mechanics or card interactions during split.
- **Repro**: Fight Leaf Slime group with seed=silent_run_3
- **Reported by**: Silent agent
- **Relevant code**: Sts2Headless/RunSimulator.cs (combat resolution)

## [FIXED] BUG-004: Cards reported as can_play=true infinitely, causing infinite play loop (2026-03-22, fixed 2026-03-22)
- **Decision type**: combat_play
- **Description**: PlayCardAction failing silently left card in hand, causing infinite play attempts.
- **Fix**: Added post-play verification in DoPlayCard — if card is still in hand at same index after action, returns error "Card could not be played" instead of looping.
- **Relevant code**: Sts2Headless/RunSimulator.cs (DoPlayCard)

## [OPEN] BUG-005: game_over state reports hp == max_hp even when player died (2026-03-22)
- **Decision type**: game_over
- **Description**: The game_over JSON response shows player.hp equal to player.max_hp (e.g. 80/80) even when the player died. The actual HP at death is not captured.
- **Reported by**: Ironclad agent (iteration 2)
- **Relevant code**: Sts2Headless/RunSimulator.cs (GameOverState / PlayerSummary)

## [OPEN] BUG-006: Regent Particle Wall card can_play=true but fails to play (2026-03-22)
- **Decision type**: combat_play
- **Description**: Particle Wall (Regent card) reports can_play=true but when played returns "Card could not be played (still in hand after action)". May require special target or condition not captured by can_play.
- **Reported by**: Regent agent (iteration 2)
- **Relevant code**: Sts2Headless/RunSimulator.cs (card play handling)

## [OPEN] BUG-007: Regent Astral Pulse StarCostTooHigh despite can_play not checking (2026-03-22)
- **Decision type**: combat_play
- **Description**: Astral Pulse reports StarCostTooHigh error, suggesting can_play doesn't fully account for star cost requirements.
- **Reported by**: Regent agent (iteration 2)
- **Relevant code**: Sts2Headless/RunSimulator.cs (card play validation)

## [FIXED] BUG-008: Map/context missing boss encounter name (2026-03-22, fixed 2026-03-22)
- **Decision type**: map_select / all decisions
- **Description**: Boss node in map data and RunContext had no boss name/type info, only "Boss" label.
- **Fix**: Added boss encounter extraction from Act.BossEncounter, with localized name via Monster() lookup. Boss info now in both get_map response and every decision's context field.
- **Relevant code**: Sts2Headless/RunSimulator.cs (GetFullMap, RunContext)

## [FIXED] BUG-009: BBCode tags in card/relic descriptions (2026-03-22, fixed 2026-03-22)
- **Decision type**: all
- **Description**: Card and relic descriptions contained raw BBCode tags like [gold], [/blue], [b], [sine].
- **Fix**: Added StripBBCode() to LocLookup.Bilingual() that strips all BBCode tags.
- **Relevant code**: Sts2Headless/RunSimulator.cs (LocLookup class)

## [FIXED] BUG-011: NullReferenceException on select_map_node after leaving shop (2026-03-22, fixed 2026-03-22)
- **Decision type**: map_select
- **Description**: After leaving shop, selecting an Elite node causes NullReferenceException.
- **Fix**: 4 changes: (1) DoMapSelect uses direct EnterMapCoord instead of action executor, (2) null check for player.Creature in DetectDecisionPoint, (3) null check for map.GetPoint in MapSelectState, (4) WaitForActionExecutor after EnterRoom in DoLeaveRoom.
- **Relevant code**: Sts2Headless/RunSimulator.cs

## [FIXED] BUG-012: Boss name/ID empty in context.boss throughout entire run (2026-03-22, fixed 2026-03-22)
- **Decision type**: all decisions
- **Description**: `context.boss.name` was empty because code used non-existent `BossId` property.
- **Fix**: Changed `_runState.Act?.BossId.Entry` to `_runState.Act?.BossEncounter?.Id?.Entry` in both RunContext and GetFullMap. Also restructured output to `{id, name}` dict.
- **Relevant code**: Sts2Headless/RunSimulator.cs (lines ~1990, ~2670)

## [FIXED] BUG-010: Vantom boss EndTurn deadlock (2026-03-22, fixed 2026-03-22)
- **Decision type**: combat_play (end_turn during Vantom boss fight)
- **Description**: Simulator deadlocked during EndTurn in Vantom boss fight. Task.Yield() posted continuations to ThreadPool that never completed.
- **Fix**: Re-enabled PatchTaskYield() Harmony patch (was commented out). Added targeted SuppressYield=true only during EndTurn (try/finally), disabled during map navigation. This forces Task.Yield() continuations to run inline synchronously during enemy turn processing.
- **Verification**: 15/15 regression runs pass (all 5 characters × 3 runs), 0 timeouts.
- **Relevant code**: Sts2Headless/RunSimulator.cs (DoEndTurn, EnsureModelDbInitialized, YieldPatches)
