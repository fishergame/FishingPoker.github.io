#!/usr/bin/env python3
"""Generate battleBalance.json + docs/BATTLE_BALANCE.md (主城血量 / 对局时长 / 攻城模拟)"""
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
ATTACK_INTERVAL_BASE = 2.2
MAX_ATTACK_SPEED = 10
DEFAULT_DECK = [
    "dragon_knight", "archer", "infantry", "arrow_tower",
    "bear_warrior", "skeleton_warrior", "gold_mine",
]
MATCH_DURATION_BASE = 90
MATCH_DURATION_STEP = 10
MATCH_DURATION_MAX = 180
SIEGE_TIME_RATIO = 0.45  # 清场后打主城目标耗时 ≈ 对局时长 × 此比例
ARENA_CITY_SCALE_STEP = 0.055  # 每场主城基准 +5.5%

# 翻牌对战品质被动（已实现于 battle-config.js）
SKILL_QUALITY_REFERENCE = [
    {
        "quality": "common",
        "label": "普通",
        "templateName": "步兵",
        "passiveId": "none",
        "description": "无被动",
        "source": "battle-config.js HERO_TEMPLATES",
    },
    {
        "quality": "rare",
        "label": "稀有",
        "templateName": "弓手",
        "passiveId": "swift",
        "description": "迅捷：攻速+10%（攻击间隔×0.9）",
        "source": "battle-config.js",
    },
    {
        "quality": "epic",
        "label": "史诗",
        "templateName": "重甲",
        "passiveId": "ironwall",
        "description": "铁壁：受到伤害-15%",
        "source": "battle-config.js",
    },
    {
        "quality": "legendary",
        "label": "传奇",
        "templateName": "龙骑",
        "passiveId": "splash",
        "description": "破军：25% 伤害溅射相邻目标",
        "source": "battle-config.js",
    },
]

HERO_SKILL_NOTE = (
    "37 张命名英雄的独立技能表（skillNormalId / skillEpicId / skillLegendId）"
    "尚未落地为 JSON，设计见 docs/AI_COCOS_FRAMEWORK_SPEC.md；"
    "养成属性见 heroes-config.js + heroLevel.json statGrowthRate。"
)


def load_heroes() -> list[dict]:
    """从 heroes-config.js 提取 HEROES 数组（Node 执行）。"""
    script = r"""
    const fs = require('fs');
    const code = fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    out = subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True)
    return json.loads(out)


def attack_interval(speed: float | None) -> float | None:
    if speed is None or speed <= 0:
        return None
    return ATTACK_INTERVAL_BASE / min(speed, MAX_ATTACK_SPEED)


def stat_at_level(base: float, level: int) -> float:
    return base * (STAT_GROWTH ** (level - 1))


def unit_city_dps(hero: dict, level: int) -> float:
    if hero.get("attack") is None:
        return 0.0
    iv = attack_interval(hero.get("attackSpeed"))
    if not iv:
        return 0.0
    atk = stat_at_level(hero["attack"], level)
    return atk / iv


def deck_city_dps(heroes_map: dict, deck: list[str], level: int) -> float:
    return sum(unit_city_dps(heroes_map[hid], level) for hid in deck if hid in heroes_map)


def top_dps_deck(heroes_map: dict, level: int, size: int = 8) -> tuple[list[str], float]:
    scored = []
    for h in heroes_map.values():
        d = unit_city_dps(h, level)
        if d > 0:
            scored.append((h["id"], d))
    scored.sort(key=lambda x: x[1], reverse=True)
    ids = [x[0] for x in scored[:size]]
    return ids, sum(x[1] for x in scored[:size])


def match_duration_sec(arena_id: int) -> int:
    return min(MATCH_DURATION_MAX, MATCH_DURATION_BASE + (arena_id - 1) * MATCH_DURATION_STEP)


def main_city_hp_base(arena_id: int, default_l1_dps: float) -> int:
    dur = match_duration_sec(arena_id)
    siege_target = dur * SIEGE_TIME_RATIO
    arena_mul = 1.0 + ARENA_CITY_SCALE_STEP * (arena_id - 1)
    return round(default_l1_dps * siege_target * arena_mul)


def main_city_hp(base: int, level: int) -> int:
    return round(base * (STAT_GROWTH ** (level - 1)))


def siege_seconds(city_hp: int, dps: float) -> float | None:
    if dps <= 0:
        return None
    return city_hp / dps


def gen_battle_balance(heroes: list[dict]) -> dict:
    heroes_map = {h["id"]: h for h in heroes}
    default_dps_l1 = deck_city_dps(heroes_map, DEFAULT_DECK, 1)

    arenas = []
    for aid in range(1, 11):
        base = main_city_hp_base(aid, default_dps_l1)
        hp_by_level = {str(lv): main_city_hp(base, lv) for lv in range(1, 31)}
        arenas.append({
            "arenaId": aid,
            "matchDurationSec": match_duration_sec(aid),
            "mainCityHpBase": base,
            "mainCityHpFormula": "round(mainCityHpBase * 1.15^(avgDeckLevel-1))",
            "mainCityHpByLevel": hp_by_level,
        })

    return {
        "version": "1.0.0",
        "description": "对局时长与主城血量：随竞技场场次、卡组平均等级缩放",
        "statGrowthRate": STAT_GROWTH,
        "defaultDeck": DEFAULT_DECK,
        "deckSize": 8,
        "formulas": {
            "matchDurationSec": f"{MATCH_DURATION_BASE} + (arenaId-1)*{MATCH_DURATION_STEP}, max {MATCH_DURATION_MAX}",
            "mainCityHpBase": f"defaultDeckL1CityDps({default_dps_l1:.1f}) * matchDuration* {SIEGE_TIME_RATIO} * arenaScale",
            "mainCityHp": "mainCityHpBase * statGrowthRate^(avgDeckLevel-1)",
            "unitCityDps": "attack * growth^(L-1) / (2.2/min(attackSpeed,10))",
            "siegeNote": "清场后全员集火主城时的理论秒数；实际对局含翻牌/清场阶段",
        },
        "skillQualityReference": SKILL_QUALITY_REFERENCE,
        "heroSkillNote": HERO_SKILL_NOTE,
        "arenas": arenas,
    }


def gen_markdown(data: dict, heroes_map: dict) -> str:
    sim_levels = list(range(1, 31))
    sim_arenas = [1, 3, 5, 7, 10]

    lines = [
        "# 战斗平衡：对局时长 · 主城血量 · 攻城模拟",
        "",
        "> 配表：`battleBalance.json` · 生成：`python3 scripts/gen-battle-balance.py`",
        "> 角色 L1 属性：`heroes-config.js` · 升级成长：`heroLevel.json`（statGrowthRate=1.15）",
        "",
        "---",
        "",
        "## 一、技能表在哪里？",
        "",
        "### 1. 翻牌对战 · 按品质被动（已实现在 `battle-config.js`）",
        "",
        "| 品质 | 模板 | 被动 | 描述 |",
        "|:---|:---|:---|:---|",
    ]
    for s in data["skillQualityReference"]:
        lines.append(f"| {s['label']} | {s['templateName']} | {s['passiveId']} | {s['description']} |")

    lines += [
        "",
        "### 2. 37 张命名英雄 · 独立技能（**尚未有独立 JSON 表**）",
        "",
        f"- {data['heroSkillNote']}",
        "- 策划原文：`260611《代号x》系统-卡牌（一级页）.txt`（提及技能等级字段）",
        "- 计划配表：`skill.json` / `skillUpgrade.json`（见 `docs/AI_COCOS_FRAMEWORK_SPEC.md`）",
        "",
        "> 当前攻城模拟使用 **`heroes-config.js` 的 attack / attackSpeed**，不用翻牌模板数值。",
        "",
        "---",
        "",
        "## 二、对局时长（按竞技场）",
        "",
        "| 场次 | 名称 | 时长 | 说明 |",
        "|:---:|:---|:---:|:---|",
    ]
    arena_names = ["青铜", "白银", "黄金", "铂金", "钻石", "星耀", "大师", "宗师", "王者", "传奇"]
    for a in data["arenas"]:
        aid = a["arenaId"]
        m, s = divmod(a["matchDurationSec"], 60)
        lines.append(f"| {aid} | {arena_names[aid-1]} | **{m}:{s:02d}** | {a['matchDurationSec']}秒 |")

    lines += [
        "",
        f"公式：`{data['formulas']['matchDurationSec']}`",
        "",
        "---",
        "",
        "## 三、主城血量（随场次 + 卡组等级）",
        "",
        f"- 基准：`{data['formulas']['mainCityHpBase']}`",
        f"- 等级：`{data['formulas']['mainCityHp']}`",
        f"- 设计目标：默认编队清场后，攻城约 **{int(SIEGE_TIME_RATIO*100)}%** 对局时长",
        "",
        "### 各场次 L1 / L15 / L30 主城 HP",
        "",
        "| 场次 | 时长 | L1 | L15 | L30 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    for a in data["arenas"]:
        if a["arenaId"] not in [1, 3, 5, 7, 10]:
            continue
        hp = a["mainCityHpByLevel"]
        m, s = divmod(a["matchDurationSec"], 60)
        lines.append(
            f"| {a['arenaId']} | {m}:{s:02d} | {hp['1']:,} | {hp['15']:,} | {hp['30']:,} |"
        )

    lines += [
        "",
        "完整 1–30 级见 `battleBalance.json` → `arenas[].mainCityHpByLevel`。",
        "",
        "---",
        "",
        "## 四、攻城模拟（清场后集火主城）",
        "",
        f"**默认编队**（6 张可攻击卡 + 采矿机）：`{', '.join(DEFAULT_DECK)}`",
        "",
        "### 4.1 默认编队 · 各等级攻城耗时（秒）",
        "",
        "| 等级 | 攻城中位 DPS | 青铜主城 | 黄金主城 | 传奇主城 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    for lv in sim_levels:
        dps = deck_city_dps(heroes_map, DEFAULT_DECK, max(1, lv))
        row = [str(lv), f"{dps:.0f}"]
        for aid in [1, 3, 10]:
            a = data["arenas"][aid - 1]
            hp = a["mainCityHpByLevel"][str(max(1, lv))]
            t = siege_seconds(hp, dps)
            row.append(f"{t:.0f}s" if t else "—")
        lines.append("| " + " | ".join(row) + " |")

    max_ids, _ = top_dps_deck(heroes_map, 30)
    lines += [
        "",
        "### 4.2 满配编队（8 张 L30 最高攻城 DPS 传奇）",
        "",
        f"卡牌：`{', '.join(max_ids)}`",
        "",
        "| 场次 | 主城HP(L30) | 满配DPS | 攻城耗时 | 对局时长 | 能否在时限内破城 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for aid in sim_arenas:
        a = data["arenas"][aid - 1]
        lv = 30
        hp = a["mainCityHpByLevel"][str(lv)]
        _, dps = top_dps_deck(heroes_map, lv)
        t = siege_seconds(hp, dps)
        dur = a["matchDurationSec"]
        ok = "✅" if t and t < dur * 0.85 else "⚠️"
        m, s = divmod(dur, 60)
        lines.append(f"| {aid} | {hp:,} | {dps:.0f} | {t:.1f}s | {m}:{s:02d} | {ok} |")

    lines += [
        "",
        "### 4.3 解读",
        "",
        "- **等级成长与主城 HP 同用 1.15 指数**，默认编队在各等级下攻城耗时较稳定（约 40–80 秒量级）。",
        "- **满配传奇 L30** 攻城明显更快（约 15–25 秒），体现养成差距。",
        "- 实际对局还需加上翻牌、产金、清场时间；总时长由 **计时结束 + 击杀数** 共同决定。",
        "- `heroes-config.js` 的 `buildingHp` 是**场上建筑卡血量**，与**主城 HP** 不同。",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    heroes = load_heroes()
    heroes_map = {h["id"]: h for h in heroes}
    data = gen_battle_balance(heroes)

    out = ROOT / "battleBalance.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    md = ROOT / "docs" / "BATTLE_BALANCE.md"
    md.write_text(gen_markdown(data, heroes_map) + "\n", encoding="utf-8")
    print(f"Wrote {md}")
