#!/usr/bin/env python3
"""Generate mainCity.json + docs/MAIN_CITY_PROGRESSION.md

主城独立养成（1–30 级）：
- 血量：与卡牌同用 statGrowthRate 1.15，L1=1500（约为旧青铜场 L1 的 19%）
- 产金：独立成长 1.10/级，L1=2/秒
- 对局时长：仍由 battleBalance.json 按竞技场决定
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
GOLD_GROWTH = 1.10
LEVEL_MAX = 30

# 青铜 L1 体感锚点（用户反馈 ~1500）
MAIN_CITY_HP_L1 = 1500
MAIN_CITY_GOLD_L1 = 2

DEFAULT_DECK = [
    "dragon_knight", "archer", "infantry", "arrow_tower",
    "bear_warrior", "skeleton_warrior", "gold_mine",
]
ATTACK_INTERVAL_BASE = 2.2
MAX_ATTACK_SPEED = 10
SIEGE_TIME_RATIO = 0.45

ARENA_NAMES = ["青铜", "白银", "黄金", "铂金", "钻石", "星耀", "大师", "宗师", "王者", "传奇"]


def load_heroes() -> list[dict]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


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
    return stat_at_level(hero["attack"], level) / iv


def deck_city_dps(heroes_map: dict, level: int) -> float:
    return sum(unit_city_dps(heroes_map[hid], level) for hid in DEFAULT_DECK if hid in heroes_map)


def main_city_hp(level: int) -> int:
    return round(MAIN_CITY_HP_L1 * (STAT_GROWTH ** (level - 1)))


def main_city_gold_per_sec(level: int) -> int:
    return max(1, round(MAIN_CITY_GOLD_L1 * (GOLD_GROWTH ** (level - 1))))


def upgrade_gold_need(level: int) -> int:
    """主城升级金币（从 level → level+1），略低于普通英雄同档。"""
    base = round(27.5 * level**2 - 47.5 * level + 25)
    return max(10, round(base * 0.85))


def upgrade_material_need(level: int) -> int:
    """主城升级材料「城砖」（从 level → level+1）。"""
    base_table = [
        8, 12, 16, 20, 24, 28, 32, 36, 40, 44,
        48, 52, 56, 60, 64, 68, 74, 80, 88, 96,
        108, 120, 135, 150, 168, 188, 210, 235, 260, 290,
    ]
    return base_table[level - 1] if 1 <= level <= LEVEL_MAX else None


def match_duration(arena_id: int) -> int:
    return min(180, 90 + (arena_id - 1) * 10)


def gen_main_city(heroes: list[dict]) -> dict:
    heroes_map = {h["id"]: h for h in heroes}
    levels = []
    for lv in range(1, LEVEL_MAX + 1):
        hp = main_city_hp(lv)
        gold = main_city_gold_per_sec(lv)
        dps = deck_city_dps(heroes_map, lv)
        siege_sec = hp / dps if dps > 0 else None
        levels.append({
            "level": lv,
            "hp": hp,
            "goldPerSec": gold,
            "upgradeGold": upgrade_gold_need(lv) if lv < LEVEL_MAX else None,
            "upgradeMaterial": upgrade_material_need(lv) if lv < LEVEL_MAX else None,
            "referenceSiege": {
                "note": "默认编队同等级清场后集火主城的理论秒数",
                "defaultDeckDps": round(dps, 1),
                "siegeSeconds": round(siege_sec, 1) if siege_sec else None,
            },
        })

    return {
        "version": "1.0.0",
        "description": "主城独立养成：血量与产金随主城等级；对局时长见 battleBalance.json",
        "levelMax": LEVEL_MAX,
        "formulas": {
            "hp": f"round({MAIN_CITY_HP_L1} * {STAT_GROWTH}^(mainCityLevel-1))",
            "goldPerSec": f"round({MAIN_CITY_GOLD_L1} * {GOLD_GROWTH}^(mainCityLevel-1))",
            "hpGrowthRate": STAT_GROWTH,
            "goldGrowthRate": GOLD_GROWTH,
            "designNote": "L1 HP=1500 约为旧场次×卡组方案的 1/5；与英雄攻击同指数，同等级对局攻城节奏稳定",
        },
        "levels": levels,
        "hpByLevel": {str(lv): main_city_hp(lv) for lv in range(1, LEVEL_MAX + 1)},
        "goldPerSecByLevel": {str(lv): main_city_gold_per_sec(lv) for lv in range(1, LEVEL_MAX + 1)},
    }


def gen_markdown(data: dict, heroes_map: dict) -> str:
    lines = [
        "# 主城养成数值（独立系统）",
        "",
        "> 配表：`mainCity.json` · 生成：`python3 scripts/gen-main-city-config.py`",
        "> 运行时：`MainCityConfig.hp(level)` / `goldPerSec(level)`",
        "> **对局时长**仍按竞技场：`BattleBalanceConfig.matchDurationSec(arenaId)`",
        "",
        "---",
        "",
        "## 一、设计原则",
        "",
        "| 维度 | 规则 |",
        "|:---|:---|",
        f"| **主城血量** | L1 **{MAIN_CITY_HP_L1:,}** × `1.15^(等级-1)`，与卡牌攻击成长对齐 |",
        f"| **每秒产金** | L1 **{MAIN_CITY_GOLD_L1}** × `1.10^(等级-1)`，成长略低于血量 |",
        "| **对局时长** | 仅由竞技场决定（青铜 90s → 传奇 180s） |",
        "| **与旧方案** | 旧青铜 L1 主城 ~7,877；新 L1 **1,500** ≈ **19%**，体感拆城更快 |",
        "",
        "### 公式",
        "",
        "```",
        f"mainCityHp(L)     = round({MAIN_CITY_HP_L1} × 1.15^(L-1))",
        f"mainCityGoldPerSec = round({MAIN_CITY_GOLD_L1} × 1.10^(L-1))",
        "matchDuration      = battleBalance.arenas[arenaId].matchDurationSec",
        "```",
        "",
        "---",
        "",
        "## 二、主城等级全表（L1–L30）",
        "",
        "| 等级 | 主城 HP | 产金/秒 | 升级城砖 | 升级金币 | 默认同级攻城(s) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for row in data["levels"]:
        lv = row["level"]
        mat = row["upgradeMaterial"] if row["upgradeMaterial"] is not None else "—"
        gold = f"{row['upgradeGold']:,}" if row["upgradeGold"] is not None else "—"
        siege = row["referenceSiege"]["siegeSeconds"]
        siege_s = f"{siege:.1f}" if siege else "—"
        lines.append(
            f"| **L{lv}** | {row['hp']:,} | {row['goldPerSec']} | {mat} | {gold} | {siege_s} |"
        )

    lines += [
        "",
        "> **默认同级攻城(s)**：默认 6 卡编队、主城等级=卡组等级、已清场后纯拆城理论时间（约 **7.7s** 全等级恒定）。",
        "",
        "---",
        "",
        "## 三、关键等级对照",
        "",
        "| 等级 | 主城 HP | 产金/秒 | 青铜90s被动金 | 传奇180s被动金 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    for lv in [1, 5, 10, 15, 20, 25, 30]:
        row = data["levels"][lv - 1]
        g = row["goldPerSec"]
        lines.append(
            f"| **L{lv}** | {row['hp']:,} | {g} | {g * 90:,} | {g * 180:,} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 四、各竞技场 × 主城等级：破城时间占比（估）",
        "",
        "假设清场+翻牌占 **55%** 对局，拆城占 **45%**；默认同级对手。",
        "",
        "| 场次 | 时长 | 目标拆城窗 | L1 | L10 | L20 | L30 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for aid in [1, 3, 5, 7, 10]:
        dur = match_duration(aid)
        target = dur * SIEGE_TIME_RATIO
        cols = []
        for lv in [1, 10, 20, 30]:
            hp = main_city_hp(lv)
            dps = deck_city_dps(heroes_map, lv)
            t = hp / dps if dps else 0
            pct = t / target * 100
            cols.append(f"{t:.1f}s ({pct:.0f}%)")
        m, s = divmod(dur, 60)
        lines.append(f"| {aid} {ARENA_NAMES[aid-1]} | {m}:{s:02d} | {target:.0f}s | {' | '.join(cols)} |")

    lines += [
        "",
        "---",
        "",
        "## 五、与卡牌养成关系",
        "",
        "- **主城等级**：战斗右侧「主城」页升级，影响 **己方主城 HP** 与 **局内每秒产金**",
        "- **卡牌等级**：影响翻出单位的攻击/生命，不影响主城 HP",
        "- **竞技场场次**：只调 **对局总时长**，不调主城 HP",
        "- PvP 时：双方各自读取自己的主城等级 HP / 产金",
        "",
        "---",
        "",
        "## 六、升级消耗（城砖 + 金币）",
        "",
        "- 材料「城砖」：主城玩法产出（待接系统），消耗见上表",
        "- 金币：约为同档普通英雄升级的 **85%**",
        "- 满级 L30 累计城砖约 **3,200**、金币约 **120,000**（粗算）",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    heroes = load_heroes()
    heroes_map = {h["id"]: h for h in heroes}
    data = gen_main_city(heroes)

    (ROOT / "mainCity.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "docs" / "MAIN_CITY_PROGRESSION.md").write_text(
        gen_markdown(data, heroes_map) + "\n", encoding="utf-8"
    )
    print(f"Wrote mainCity.json, docs/MAIN_CITY_PROGRESSION.md")
    print(f"L1 HP={data['hpByLevel']['1']}, L30 HP={data['hpByLevel']['30']}")
    print(f"L1 gold/s={data['goldPerSecByLevel']['1']}, L30={data['goldPerSecByLevel']['30']}")
