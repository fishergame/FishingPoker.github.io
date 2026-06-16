#!/usr/bin/env python3
"""Generate battleBalance.json + docs/BATTLE_BALANCE.md (对局时长；主城 HP/产金见 mainCity.json)"""
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
ATTACK_INTERVAL_BASE = 2.2
MAX_ATTACK_SPEED = 10
MATCH_DURATION_BASE = 90
MATCH_DURATION_STEP = 10
MATCH_DURATION_MAX = 180
SIEGE_TIME_RATIO = 0.45
MAIN_CITY_HP_L1 = 1500  # 与 mainCity.json 同步，用于攻城模拟
MAIN_CITY_GOLD_L1 = 2
GOLD_GROWTH = 1.10

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


def load_default_deck() -> list[str]:
    """从 heroes-config.js 提取开局默认编队（过滤空槽）。"""
    script = r"""
    const fs = require('fs');
    const code = fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.getStarterDeckIds()));
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


def main_city_hp(main_city_level: int) -> int:
    return round(MAIN_CITY_HP_L1 * (STAT_GROWTH ** (main_city_level - 1)))


def main_city_gold_per_sec(main_city_level: int) -> int:
    return max(1, round(MAIN_CITY_GOLD_L1 * (GOLD_GROWTH ** (main_city_level - 1))))


def siege_seconds(city_hp: int, dps: float) -> float | None:
    if dps <= 0:
        return None
    return city_hp / dps


def gen_battle_balance(heroes: list[dict], default_deck: list[str]) -> dict:
    heroes_map = {h["id"]: h for h in heroes}
    default_dps_l1 = deck_city_dps(heroes_map, default_deck, 1)

    arenas = []
    for aid in range(1, 11):
        arenas.append({
            "arenaId": aid,
            "matchDurationSec": match_duration_sec(aid),
        })

    return {
        "version": "2.0.0",
        "description": "对局时长按竞技场；主城 HP/产金见 mainCity.json",
        "mainCityConfig": "mainCity.json",
        "statGrowthRate": STAT_GROWTH,
        "defaultDeck": default_deck,
        "deckSize": 8,
        "starterGrantCount": len(default_deck),
        "starterEmptySlots": max(0, 8 - len(default_deck)),
        "formulas": {
            "matchDurationSec": f"{MATCH_DURATION_BASE} + (arenaId-1)*{MATCH_DURATION_STEP}, max {MATCH_DURATION_MAX}",
            "mainCityHp": f"mainCity.json → round({MAIN_CITY_HP_L1} * 1.15^(mainCityLevel-1))",
            "mainCityGoldPerSec": f"mainCity.json → round({MAIN_CITY_GOLD_L1} * 1.10^(mainCityLevel-1))",
            "unitCityDps": "attack * growth^(deckLevel-1) / (2.2/min(attackSpeed,10))",
            "siegeNote": "清场后全员集火主城；主城等级与卡组等级同档时理论拆城约 7.7s",
            "defaultDeckL1CityDps": round(default_dps_l1, 1),
        },
        "skillQualityReference": SKILL_QUALITY_REFERENCE,
        "heroSkillNote": HERO_SKILL_NOTE,
        "combatCaps": {
            "recommendedCityDpsMultiplierMax": 1.45,
            "note": "技能+羁绊对主城DPS合计倍率建议上限，见 docs/SKILL_BOND_REVIEW.md",
        },
        "arenas": arenas,
    }


def load_hero_factions() -> dict[str, str]:
    bond = json.loads((ROOT / "bond.json").read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for b in bond.get("bonds", []):
        if b.get("type") != "faction":
            continue
        label = b.get("name", b.get("faction", ""))
        for hid in b.get("heroIds", []):
            out[hid] = label
    return out


def gen_starter_deck_md(default_deck: list[str], heroes_map: dict, factions: dict[str, str], deck_size: int = 8) -> list[str]:
    """开局赠送卡组说明（从 heroes-config.js 同步）。"""
    empty_slots = max(0, deck_size - len(default_deck))
    lines = [
        "## 零、开局赠送卡组",
        "",
        "> 单一数据源：`heroes-config.js → DEFAULT_DECK`（`getStarterGrantIds()`）",
        f"> 新号赠送 **{len(default_deck)}** 张，卡组容量 **{deck_size}** 槽。",
        "",
        "| # | id | 名称 | 品质 | 类型 | 阵营 |",
        "|:---:|:---|:---|:---:|:---|:---|",
    ]
    for i, hid in enumerate(default_deck, 1):
        h = heroes_map.get(hid, {})
        q = h.get("quality", "?")
        faction = factions.get(hid, "无阵营" if hid == "gold_mine" else "—")
        lines.append(
            f"| {i} | `{hid}` | {h.get('name', '?')} | {q} | {h.get('type', '?')} | {faction} |"
        )
    for j in range(empty_slots):
        slot = len(default_deck) + j + 1
        lines.append(f"| {slot} | — | （空槽） | — | — | 待玩家装配 |")
    lines += [
        "",
        "阵营对照见 `bond.json`；`gold_mine` 不参与羁绊。",
        "",
        "---",
        "",
    ]
    return lines


def gen_markdown(data: dict, heroes_map: dict, factions: dict[str, str]) -> str:
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
    ]
    lines += gen_starter_deck_md(data["defaultDeck"], heroes_map, factions, data.get("deckSize", 8))
    lines += [
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
        "## 三、主城血量 · 产金（独立养成）",
        "",
        f"- 主城 HP：`{data['formulas']['mainCityHp']}`",
        f"- 产金/秒：`{data['formulas']['mainCityGoldPerSec']}`",
        "- 完整 1–30 级表：**[`docs/MAIN_CITY_PROGRESSION.md`](MAIN_CITY_PROGRESSION.md)** · 配表 `mainCity.json`",
        "",
        "---",
        "",
        "## 四、攻城模拟（清场后集火 · 主城等级=卡组等级）",
        "",
        f"**开局赠送**（{len(data['defaultDeck'])} 张，`heroes-config.js → DEFAULT_DECK`）：`{', '.join(data['defaultDeck'])}`",
        f"**L1 编队攻城 DPS**：{data['formulas']['defaultDeckL1CityDps']}",
        "",
        "| 主城/卡组等级 | 主城 HP | 编队 DPS | 理论拆城(s) |",
        "|:---:|:---:|:---:|:---:|",
    ]
    default_deck = data["defaultDeck"]
    for lv in [1, 5, 10, 15, 20, 25, 30]:
        hp = main_city_hp(lv)
        dps = deck_city_dps(heroes_map, default_deck, lv)
        t = siege_seconds(hp, dps)
        lines.append(f"| L{lv} | {hp:,} | {dps:.0f} | {t:.1f}s |")

    max_ids, max_dps = top_dps_deck(heroes_map, 30)
    lines += [
        "",
        "### 满配编队（8 张 L30 最高攻城 DPS）",
        "",
        f"卡牌：`{', '.join(max_ids)}` · DPS **{max_dps:.0f}**",
        f"· 拆 L30 主城（{main_city_hp(30):,} HP）约 **{siege_seconds(main_city_hp(30), max_dps):.1f}s**",
        "",
        "### 解读",
        "",
        "- 主城 HP 与编队 DPS **同用 1.15 成长**时，理论拆城时间全等级约 **7.7s**（仅清场后集火段）。",
        "- 实际对局含翻牌、清场、击杀判定；对局总时长由 **竞技场时长** 决定。",
        "- 产金随主城等级（1.10/级），详见 `mainCity.json`。",
        "",
    ]
    return "\n".join(lines)


def gen_final_table_md(data: dict) -> str:
    """重定向至主城独立配表。"""
    return "\n".join([
        "# 主城血量 · 对局时长",
        "",
        "> **主城 HP / 产金**已迁至独立养成：`mainCity.json`",
        "> 详见 **[`docs/MAIN_CITY_PROGRESSION.md`](MAIN_CITY_PROGRESSION.md)**",
        "",
        "> **对局时长**仍在本文件历史段落 / `battleBalance.json`：",
        "",
        "| 场次 | 青铜 | 白银 | 黄金 | 铂金 | 钻石 | 星耀 | 大师 | 宗师 | 王者 | 传奇 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        "| 时长 | 1:30 | 1:40 | 1:50 | 2:00 | 2:10 | 2:20 | 2:30 | 2:40 | 2:50 | 3:00 |",
        "",
    ])


if __name__ == "__main__":
    heroes = load_heroes()
    default_deck = load_default_deck()
    factions = load_hero_factions()
    heroes_map = {h["id"]: h for h in heroes}
    data = gen_battle_balance(heroes, default_deck)

    out = ROOT / "battleBalance.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    md = ROOT / "docs" / "BATTLE_BALANCE.md"
    md.write_text(gen_markdown(data, heroes_map, factions) + "\n", encoding="utf-8")
    print(f"Wrote {md}")

    final_md = ROOT / "docs" / "MAIN_CITY_MATCH_FINAL.md"
    final_md.write_text(gen_final_table_md(data) + "\n", encoding="utf-8")
    print(f"Wrote {final_md}")
