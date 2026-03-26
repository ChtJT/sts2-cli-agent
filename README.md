# sts2-cli

<details open>
<summary><b>English</b></summary>

A CLI for Slay the Spire 2.

Runs the real game engine headless in your terminal — all damage, card effects, enemy AI, relics, and RNG are identical to the actual game.

![demo](docs/demo_en.gif)

## Setup

Requirements:
- [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) on Steam
- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- Python 3.9+

Version note:
- The project currently targets `net10.0`.
- It does not target `net11.0`.
- If your machine only has a newer `.NET 11` SDK/runtime, it may still run because `Sts2Headless` enables `RollForward=LatestMajor`, but `.NET 10` remains the recommended setup.

```bash
git clone https://github.com/wuhao21/sts2-cli.git
cd sts2-cli
./setup.sh      # copies DLLs from Steam → IL patches → builds
```

Or just run `python3 python/play.py` — it auto-detects and sets up on first run.

## Play

```bash
python3 python/play.py                # interactive (Chinese)
python3 python/play.py --lang en      # interactive (English)
```

Type `help` in-game:

```
  help     — show help
  map      — show map
  deck     — show deck
  potions  — show potions
  relics   — show relics
  quit     — quit

  Map:     enter path number (0, 1, 2)
  Combat:  card index / e (end turn) / p0 (use potion)
  Reward:  card index / s (skip)
  Rest:    option index
  Event:   option index / leave
  Shop:    c0 (card) / r0 (relic) / p0 (potion) / rm (remove) / leave
```

## JSON Protocol

For programmatic control (AI agents, RL, etc.), communicate via stdin/stdout JSON:

```bash
dotnet run --project Sts2Headless/Sts2Headless.csproj
```

```json
{"cmd": "start_run", "character": "Ironclad", "seed": "test", "ascension": 0}
{"cmd": "action", "action": "play_card", "args": {"card_index": 0, "target_index": 0}}
{"cmd": "action", "action": "end_turn"}
{"cmd": "action", "action": "select_map_node", "args": {"col": 3, "row": 1}}
{"cmd": "action", "action": "skip_card_reward"}
{"cmd": "quit"}
```

Each command returns a JSON decision point (`map_select` / `combat_play` / `card_reward` / `rest_site` / `event_choice` / `shop` / `game_over`). All names are bilingual (en/zh).

## Future Development Requirements

The table below is a roadmap for future AI-agent development on top of `sts2-cli`. These items describe intended requirements and expansion directions; they should not be read as "already complete".

| Area | Requirement | Goal | Notes |
|---|---|---|---|
| World model | Add a higher-level route planner that evaluates the whole map, not only the next click | Re-plan at each floor and after major state changes such as relic acquisition, HP swings, gold spikes, or key card rewards | Should feed `map_select`, elite risk control, boss preparation, and path preference |
| Memory architecture | Evolve memory beyond step logs into layered memory: working, episodic, strategic, semantic, and skill memory | Preserve short-term run context while accumulating reusable long-term knowledge | Needs summarization, retrieval, promotion rules, and per-run reflection |
| Shop / rest-site policy | Build explicit decision policies for shop, card removal, potion buying, relic buying, and rest-site heal vs smith | Reduce noisy model choices and make economic decisions consistent with deck, HP, boss, and relic state | Should become part of world-model and memory-driven planning, not only per-step prompting |
| Combat archive | Save one full terminal-style combat file per battle | Make debugging, replay review, and training-data collection easier | Keep the original terminal rendering rather than compressing into JSON summaries |
| Multi-agent architecture | Support multiple cooperating agents with distinct roles such as planner, actor, evaluator, reflector, or skill specialist | Separate long-horizon planning from local action execution and post-run learning | This can also support one agent per player seat in future multiplayer/co-op scenarios |
| Online / multiplayer development | Prepare an orchestration layer for future networked or co-op play | Allow one agent to represent one human/player, with synchronized shared state and per-player local context | Requires turn ownership, conflict handling, coordination messages, and shared-memory rules |
| Evaluation and self-improvement | Add offline reflection, run scoring, seed-based benchmarking, and candidate-policy promotion | Let the system improve from real runs instead of ad hoc prompt edits | Candidate skills or policies should be validated across multiple runs before promotion |
| Provider / API isolation | Keep model providers behind a clean interface while preserving a stable game-control API | Make it easy to swap OpenAI, Codex, local models, or hybrid systems without rewriting the runtime | The runtime and validation layer should remain model-agnostic |

## Supported Characters

| Character | Status |
|---|---|
| Ironclad | Fully playable |
| Silent | Fully playable |
| Defect | Fully playable |
| Necrobinder | Fully playable |
| Regent | Fully playable |

## Architecture

```
Your code (Python / JS / LLM)
    │  JSON stdin/stdout
    ▼
Sts2Headless (C#)
    │  RunSimulator.cs
    ▼
sts2.dll (game engine, IL patched)
  + GodotStubs (replaces GodotSharp.dll)
  + Harmony patches (localization)
```

</details>

<details>
<summary><b>中文</b></summary>

杀戮尖塔2的命令行版本。

在终端里运行真实游戏引擎 — 所有伤害计算、卡牌效果、敌人AI、遗物触发、随机数都和真实游戏一致。

![demo](docs/demo_zh.gif)

## 安装

需要：
- [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) (Steam)
- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- Python 3.9+

版本说明：
- 当前项目 target framework 是 `net10.0`。
- 不是 `net11.0`。
- 如果你机器上只有更新的 `.NET 11` SDK/runtime，通常也可以运行，因为 `Sts2Headless` 开了 `RollForward=LatestMajor`；但推荐环境仍然是 `.NET 10`。

```bash
git clone https://github.com/wuhao21/sts2-cli.git
cd sts2-cli
./setup.sh      # 从 Steam 复制 DLL → IL patch → 编译
```

或者直接运行 `python3 python/play.py`，首次会自动完成 setup。

## 玩

```bash
python3 python/play.py              # 中文交互模式
python3 python/play.py --lang en    # English
```

游戏内输入 `help` 查看所有命令：

```
  help     — 帮助
  map      — 显示地图
  deck     — 查看牌组
  potions  — 查看药水
  relics   — 查看遗物
  quit     — 退出

  地图:    输入编号 (0, 1, 2)
  战斗:    输入卡牌编号 / e 结束回合 / p0 使用药水
  奖励:    输入卡牌编号 / s 跳过
  休息:    输入选项编号
  事件:    输入选项编号 / leave 离开
  商店:    c0 买卡 / r0 买遗物 / p0 买药水 / rm 移除 / leave 离开
```

## 角色支持

| 角色 | 状态 |
|---|---|
| 铁甲战士 (Ironclad) | 完全可玩 |
| 静默猎手 (Silent) | 完全可玩 |
| 故障机器人 (Defect) | 完全可玩 |
| 亡灵契约师 (Necrobinder) | 完全可玩 |
| 储君 (Regent) | 完全可玩 |

## JSON 协议

除了交互模式，也可以通过 stdin/stdout JSON 协议编程控制（写 AI agent、RL 训练等）：

```bash
dotnet run --project Sts2Headless/Sts2Headless.csproj
```

```json
{"cmd": "start_run", "character": "Ironclad", "seed": "test", "ascension": 0}
{"cmd": "action", "action": "play_card", "args": {"card_index": 0, "target_index": 0}}
{"cmd": "action", "action": "end_turn"}
{"cmd": "action", "action": "select_map_node", "args": {"col": 3, "row": 1}}
{"cmd": "action", "action": "skip_card_reward"}
{"cmd": "quit"}
```

每个命令返回一个 JSON decision point（`map_select` / `combat_play` / `card_reward` / `rest_site` / `event_choice` / `shop` / `game_over`），所有名称都是中英双语。

## 未来开发需求

下面这张表是基于 `sts2-cli` 往上做 AI agent 的后续研发需求，不代表这些能力都已经完成，而是作为未来开发的目标和边界。

| 方向 | 需求 | 目标 | 备注 |
|---|---|---|---|
| World Model | 增加一个更高层的全局路线规划器，不只看下一步怎么点 | 在每一层、以及拿到遗物、血量大幅变化、金币变化、关键卡牌奖励后重新规划路线 | 应直接影响 `map_select`、精英风险控制、Boss 前准备和路径偏好 |
| Memory 架构 | 把 memory 从“步骤日志”升级成分层 memory：工作记忆、情节记忆、战略记忆、语义记忆、skill memory | 一边保留当前 run 的上下文，一边沉淀可复用的长期知识 | 需要配套摘要、检索、晋升规则，以及每局结束后的 reflection |
| 商店 / 篝火策略 | 为商店、删牌、买药水、买遗物、篝火回血还是强化建立显式策略 | 让经济决策和资源决策更稳定，而不是每步都临时拍脑袋 | 应由 world model 和 memory 驱动，而不是只靠单步 prompt |
| 战斗归档 | 每场战斗单独保存一份完整终端画面文件 | 方便调试、复盘、数据集整理和训练样本分析 | 保留原始 terminal 呈现，不压缩成简单 JSON 摘要 |
| 多 Agent 架构 | 支持多个协作 agent，例如 planner、actor、evaluator、reflector、skill specialist | 把长线规划、局内执行和局后反思拆开，降低单 agent 负担 | 这也能扩展到未来“一个 agent 代表一个玩家/一个人”的模式 |
| 联机 / 协同开发 | 为未来联机或 cooperative 玩法预留 orchestration 层 | 允许一个 agent 对应一个玩家，共享全局状态，同时保留各自局部视角 | 需要处理回合归属、冲突解决、协作消息和共享 memory 规则 |
| 评估与自进化 | 增加离线 reflection、run 评分、seed 基准测试、候选策略晋升机制 | 让系统通过真实 run 自我改进，而不是只改 prompt | 候选 skill 或策略应先多局验证，再进入正式策略库 |
| Provider / API 解耦 | 保持模型 provider 可替换，同时维持稳定的游戏控制接口 | 方便切换 OpenAI、Codex、本地模型或混合方案，而不重写 runtime | runtime、校验层、游戏协议应尽量保持 model-agnostic |

## 架构

```
你的代码 (Python / JS / LLM)
    │  JSON stdin/stdout
    ▼
Sts2Headless (C#)
    │  RunSimulator.cs
    ▼
sts2.dll (游戏引擎, IL patched)
  + GodotStubs (替代 GodotSharp.dll)
  + Harmony patches (本地化)
```

</details>
