#!/usr/bin/env python3
"""Generate mainCity.json + docs/MAIN_CITY_PROGRESSION.md

主城独立养成 v2.1：
- 战斗：HP ×1.15/级（L1=1500）；产金每秒 +0.5/级（2.0→16.5，仅 .0/.5）
- 升级：翻格外扩一圈；**单格砖头** × **本级格数** = 升级总砖（非「升一级固定总砖」）
- 对局掉落：金币 + 砖头 + 经验；主城 PvE 建筑额外奖励
- 对局时长：仍仅由竞技场决定（battleBalance.json）
- 砖头商店：见 shop.json（基础区 · 钻石四档）
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
LEVEL_MAX = 30

MAIN_CITY_HP_L1 = 1500
GOLD_PER_SEC_L1 = 2.0
GOLD_PER_SEC_STEP = 0.5  # 每级 +0.5，仅 x.0 / x.5

# 升级：外扩一圈需翻格数（L1 起约 8 格邻接圈，随等级略增）
TILES_BASE = 8
TILES_STEP_EVERY = 4  # 每 4 级 +1 格
TILES_MAX = 14

# 单格翻开消耗砖头（主口径）；L1=7，每级 +1
BRICK_BASE_PER_TILE = 7

BRICK_BATTLE_BASE = 5
BRICK_BATTLE_GROWTH = 1.11
GOLD_BATTLE_BASE = 28
GOLD_BATTLE_GROWTH = 1.11
XP_BATTLE_BASE = 12
XP_BATTLE_GROWTH = 1.10
ARENA_RESOURCE_STEP = 0.06
LOSE_REWARD_RATIO = 0.4
PVE_BRICK_MULTIPLIER = 2.5
PVE_GOLD_MULTIPLIER = 2.0

ARENA_NAMES = ["青铜", "白银", "黄金", "铂金", "钻石", "星耀", "大师", "宗师", "王者", "传奇"]

DECOR_CATEGORIES = [
    {"id": "plant", "name": "植物树木", "weight": 35, "role": "decoration"},
    {"id": "landscape", "name": "景观小品", "weight": 25, "role": "decoration"},
    {"id": "castle_decor", "name": "城堡装饰", "weight": 15, "role": "decoration"},
    {"id": "brick_factory_decor", "name": "砖头厂（装饰）", "weight": 12, "role": "decoration", "note": "无产砖功能"},
    {"id": "gold_mine_decor", "name": "金矿厂（装饰）", "weight": 13, "role": "decoration", "note": "无产金功能"},
]


def load_heroes() -> list[dict]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


def load_match_durations() -> dict[int, int]:
    p = ROOT / "battleBalance.json"
    if p.exists():
        data = json.loads(p.read_text())
        return {a["arenaId"]: a["matchDurationSec"] for a in data.get("arenas", [])}
    return {i: min(180, 90 + (i - 1) * 10) for i in range(1, 11)}


def main_city_hp(level: int) -> int:
    return round(MAIN_CITY_HP_L1 * (STAT_GROWTH ** (level - 1)))


def gold_per_sec(level: int) -> float:
    return round(GOLD_PER_SEC_L1 + (level - 1) * GOLD_PER_SEC_STEP, 1)


def flip_brick_cost(level: int) -> int:
    """从 level 升到 level+1 时，翻开**单格**消耗砖头（主口径）。"""
    return BRICK_BASE_PER_TILE + (level - 1)


def tiles_to_level_up(level: int) -> int:
    """从 level 升到 level+1 时需翻开的格数（外扩一圈）。"""
    return min(TILES_MAX, TILES_BASE + (level - 1) // TILES_STEP_EVERY)


def total_bricks_to_level_up(level: int) -> int:
    """升级总砖 = 本级格数 × 单格砖（派生，非独立配表）。"""
    return tiles_to_level_up(level) * flip_brick_cost(level)


def pve_building_count(level: int) -> int:
    return 2 if level <= 12 else 3


def reference_arena(level: int) -> int:
    """该主城等级玩家的典型竞技场场次（用于时长/掉落参考）。"""
    return min(10, max(1, (level + 2) // 3))


def arena_multiplier(arena_id: int) -> float:
    return 1.0 + ARENA_RESOURCE_STEP * (arena_id - 1)


def battle_bricks(main_city_level: int, arena_id: int, won: bool = True) -> int:
    val = BRICK_BATTLE_BASE * (BRICK_BATTLE_GROWTH ** (main_city_level - 1)) * arena_multiplier(arena_id)
    n = max(1, round(val))
    return n if won else max(1, round(n * LOSE_REWARD_RATIO))


def battle_gold(main_city_level: int, arena_id: int, won: bool = True) -> int:
    val = GOLD_BATTLE_BASE * (GOLD_BATTLE_GROWTH ** (main_city_level - 1)) * arena_multiplier(arena_id)
    n = max(5, round(val))
    return n if won else max(2, round(n * LOSE_REWARD_RATIO))


def battle_xp(main_city_level: int, arena_id: int, won: bool = True) -> int:
    val = XP_BATTLE_BASE * (XP_BATTLE_GROWTH ** (main_city_level - 1)) * (1 + 0.04 * (arena_id - 1))
    n = max(3, round(val))
    return n if won else max(1, round(n * LOSE_REWARD_RATIO))


def est_wins_to_level(level: int) -> float:
    need = total_bricks_to_level_up(level)
    ar = reference_arena(level)
    per = battle_bricks(level, ar, True)
    return round(need / per, 1) if per else 0


def deck_city_dps_simple(heroes_map: dict, level: int) -> float:
    deck_ids = [
        "dragon_knight", "archer", "infantry", "arrow_tower", "bear_warrior", "skeleton_warrior",
    ]
    total = 0.0
    for hid in deck_ids:
        h = heroes_map.get(hid)
        if not h or not h.get("attack"):
            continue
        spd = min(h.get("attackSpeed") or 1, 10)
        total += h["attack"] * (STAT_GROWTH ** (level - 1)) / (2.2 / spd)
    return total


def gen_levels(heroes_map: dict) -> list[dict]:
    durations = load_match_durations()
    rows = []
    for lv in range(1, LEVEL_MAX + 1):
        ar = reference_arena(lv)
        dps = deck_city_dps_simple(heroes_map, lv)
        hp = main_city_hp(lv)
        rows.append({
            "level": lv,
            "hp": hp,
            "goldPerSec": gold_per_sec(lv),
            "flip": {
                "tilesPerLevel": tiles_to_level_up(lv),
                "brickCostPerTile": flip_brick_cost(lv),
                "totalBricksToNext": total_bricks_to_level_up(lv),
                "pveBuildingCount": pve_building_count(lv),
                "decorPool": DECOR_CATEGORIES,
            },
            "referenceArena": {
                "arenaId": ar,
                "arenaName": ARENA_NAMES[ar - 1],
                "matchDurationSec": durations.get(ar, 180),
            },
            "battleRewards": {
                "win": {
                    "bricks": battle_bricks(lv, ar, True),
                    "gold": battle_gold(lv, ar, True),
                    "accountXp": battle_xp(lv, ar, True),
                },
                "lose": {
                    "bricks": battle_bricks(lv, ar, False),
                    "gold": battle_gold(lv, ar, False),
                    "accountXp": battle_xp(lv, ar, False),
                },
                "pveBuildingWin": {
                    "bricks": max(2, round(battle_bricks(lv, ar, True) * PVE_BRICK_MULTIPLIER)),
                    "gold": max(5, round(battle_gold(lv, ar, True) * PVE_GOLD_MULTIPLIER)),
                    "note": "主城地图 PvE 建筑胜利一次性奖励",
                },
            },
            "pacing": {
                "estimatedWinsToLevel": est_wins_to_level(lv),
                "note": "仅按参考场次胜场砖头粗算，不含 PvE/商店",
            },
            "referenceSiege": {
                "defaultDeckDps": round(dps, 1),
                "siegeSeconds": round(hp / dps, 1) if dps else None,
            },
        })
    return rows


def gen_main_city() -> dict:
    heroes = load_heroes()
    heroes_map = {h["id"]: h for h in heroes}
    levels = gen_levels(heroes_map)
    cumulative_bricks = sum(r["flip"]["totalBricksToNext"] for r in levels[:-1])

    return {
        "version": "2.1.0",
        "description": "主城养成：翻格升级（单格砖×格数）、战斗 HP/产金",
        "levelMax": LEVEL_MAX,
        "gameplay": {
            "upgradeMode": "flipTiles",
            "tileCostCurrency": "brick",
            "upgradeLogic": "每升 1 级外扩一圈，逐格翻开；单格耗砖随等级涨，格数随外扩略增",
            "flipBrickCostFormula": f"{BRICK_BASE_PER_TILE} + (mainCityLevel - 1)  // 单格",
            "tilesPerLevelFormula": f"min({TILES_MAX}, {TILES_BASE} + floor((mainCityLevel-1)/{TILES_STEP_EVERY}))",
            "totalBricksFormula": "tilesPerLevel × flipBrickCost  // 派生",
            "tileLoot": {
                "decoration": DECOR_CATEGORIES,
                "pveBuilding": "每级 2–3 个，翻开触发 PvE；胜利额外给砖头/金币",
            },
            "shopBrickPacksRef": "shop.json → zones.basic.brickPacks（钻石四档）",
        },
        "formulas": {
            "hp": f"round({MAIN_CITY_HP_L1} * {STAT_GROWTH}^(mainCityLevel-1))",
            "goldPerSec": f"{GOLD_PER_SEC_L1} + (mainCityLevel-1)*{GOLD_PER_SEC_STEP}",
            "flipBrickCost": f"{BRICK_BASE_PER_TILE} + (mainCityLevel-1)",
            "tilesPerLevel": f"min({TILES_MAX}, {TILES_BASE} + floor((mainCityLevel-1)/{TILES_STEP_EVERY}))",
            "totalBricksToNext": "tilesPerLevel × flipBrickCost",
            "battleBricksWin": f"round({BRICK_BATTLE_BASE} * {BRICK_BATTLE_GROWTH}^(L-1) * arenaMul)",
            "battleGoldWin": f"round({GOLD_BATTLE_BASE} * {GOLD_BATTLE_GROWTH}^(L-1) * arenaMul)",
            "loseRewardRatio": LOSE_REWARD_RATIO,
        },
        "cumulativeBricksToMax": cumulative_bricks,
        "levels": levels,
        "hpByLevel": {str(r["level"]): r["hp"] for r in levels},
        "goldPerSecByLevel": {str(r["level"]): r["goldPerSec"] for r in levels},
    }


def fmt_gold(g: float) -> str:
    return str(int(g)) if g == int(g) else f"{g:.1f}"


def gen_markdown(data: dict) -> str:
    lines = [
        "# 主城养成数值（翻格 · 砖头 · 统一总表）",
        "",
        "> 配表：`mainCity.json` · 生成：`python3 scripts/gen-main-city-config.py`",
        "> 对局时长：`battleBalance.json`（仅竞技场）",
        "",
        "---",
        "",
        "## 一、玩法摘要",
        "",
        "| 模块 | 规则 |",
        "|:---|:---|",
        "| **升级方式** | 外扩一圈逐格翻开；**升级总砖 = 单格砖 × 本级格数** |",
        "| **本级格数** | 邻接圈约 **8 格** 起，每 4 级 +1，上限 **14** |",
        "| **单格砖头** | `7 + (当前主城等级 - 1)`，等级越高越贵 |",
        "| **格内掉落** | 多为装饰（植物/景观/城堡/砖头厂/金矿厂）；每级 **2–3 个 PvE 建筑** 可实战 |",
        "| **PvE 奖励** | 胜利额外砖头 ≈ 胜场 ×2.5、金币 ≈ ×2 |",
        "| **PvP 奖励** | 胜利给 砖头 + 金币 + 账号经验；失败给 **40%** |",
        "| **战斗 HP** | 随主城等级 ×1.15；**产金/秒** 每级 **+0.5**（2.0→16.5） |",
        "| **对局时长** | 仅看竞技场（青铜 90s → 传奇 180s） |",
        "",
        "### 公式",
        "",
        "```",
        "mainCityHp(L)       = round(1500 × 1.15^(L-1))",
        "goldPerSec(L)       = 2.0 + (L-1) × 0.5",
        "flipBrickCost(L)    = 7 + (L-1)          // 单格翻开（主口径）",
        "tilesPerLevel(L)    = min(14, 8 + floor((L-1)/4))  // 外扩格数",
        "bricksToLevelUp(L)  = tilesPerLevel(L) × flipBrickCost(L)",
        "battleBricksWin     = round(5 × 1.11^(L-1) × (1+0.06×(场次-1)))",
        "battleGoldWin       = round(28 × 1.11^(L-1) × (1+0.06×(场次-1)))",
        "```",
        "",
        f"**满级累计砖头（L1→L30）**：**{data['cumulativeBricksToMax']:,}**",
        "",
        "---",
        "",
        "## 二、统一总表（L1–L30）",
        "",
        "| 等级 | 战斗HP | 产金/s | 单格砖 | 本级格数 | 升级总砖 | PvE数 | 参考场次 | 对局时长 | 胜·砖 | 胜·金 | 负·砖 | 估胜场/级 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in data["levels"]:
        lv = r["level"]
        ar = r["referenceArena"]
        fl = r["flip"]
        rw = r["battleRewards"]["win"]
        rl = r["battleRewards"]["lose"]
        dur = ar["matchDurationSec"]
        m, s = divmod(dur, 60)
        lines.append(
            f"| **L{lv}** | {r['hp']:,} | {fmt_gold(r['goldPerSec'])} | {fl['brickCostPerTile']} "
            f"| {fl['tilesPerLevel']} | {fl['totalBricksToNext']:,} | {fl['pveBuildingCount']} "
            f"| {ar['arenaId']} {ar['arenaName']} | {m}:{s:02d} | {rw['bricks']} | {rw['gold']} "
            f"| {rl['bricks']} | {r['pacing']['estimatedWinsToLevel']} |"
        )

    lines += [
        "",
        "> **单格砖** = 翻开一格消耗；**本级格数** = 升这一级需翻几格；**升级总砖** = 二者相乘。",
        "> **估胜场/级** = 升级总砖 ÷ 参考场次胜场砖头（不含 PvE 与商店）。",
        "",
        "---",
        "",
        "## 三、关键等级对照",
        "",
        "| 等级 | HP | 产金/s | 升级总砖 | 参考时长 | 胜场砖头 | PvE胜利砖头 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for lv in [1, 5, 10, 15, 20, 25, 30]:
        r = data["levels"][lv - 1]
        pve = r["battleRewards"]["pveBuildingWin"]
        ar = r["referenceArena"]
        m, s = divmod(ar["matchDurationSec"], 60)
        lines.append(
            f"| **L{lv}** | {r['hp']:,} | {fmt_gold(r['goldPerSec'])} "
            f"| {r['flip']['totalBricksToNext']:,} | {m}:{s:02d} "
            f"| {r['battleRewards']['win']['bricks']} | {pve['bricks']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 四、翻格掉落（装饰 vs PvE）",
        "",
        "| 类型 | 说明 | 权重/数量 |",
        "|:---|:---|:---|",
    ]
    for d in DECOR_CATEGORIES:
        note = d.get("note", "仅外观")
        lines.append(f"| {d['name']} | {note} | 装饰池 {d['weight']}% |")
    lines += [
        "| **PvE 建筑** | 可发起对战，胜利额外资源 | 每级 2 个（L13 起 3 个） |",
        "",
        "---",
        "",
        "## 五、商店 · 砖头礼包（钻石 · 四档）",
        "",
        "配表见 **`shop.json`** → `zones.basic.brickPacks`（仅钻石购买，大包单价更低）。",
        "",
        "| 商品 | 砖头 | 钻石 | 单价 | 限购 | 说明 |",
        "|:---|:---:|:---:|:---:|:---:|:---|",
        "| 砖头×40 | 40 | 25 | 0.63 | 日3 | 约 L1 升级量 70% |",
        "| 砖头×100 | 100 | 58 | 0.58 | 日2 | 约 L1–L3 一级量 |",
        "| 砖头×250 | 250 | 128 | 0.51 | 日1 | 中后期补仓 |",
        "| 砖头×600 | 600 | 268 | 0.45 | 周2 | 大包优惠 |",
    ]

    lines += [
        "",
        "---",
        "",
        "## 六、对局时长（竞技场 · 不变）",
        "",
        "| 场次 | 名称 | 秒 | 显示 |",
        "|:---:|:---|:---:|:---:|",
    ]
    durations = load_match_durations()
    for aid in range(1, 11):
        sec = durations.get(aid, 90)
        m, s = divmod(sec, 60)
        lines.append(f"| {aid} | {ARENA_NAMES[aid-1]} | {sec} | **{m}:{s:02d}** |")

    lines += [
        "",
        "---",
        "",
        "## 七、与卡牌/账号关系",
        "",
        "- **主城等级**：右侧「主城」页；翻格耗砖升级 → 提高 **局内 HP + 产金**",
        "- **卡牌等级**：只影响翻出单位强度",
        "- **竞技场**：只调 **对局倒计时** 与掉落场次系数",
        "- **账号经验**：对局胜利/失败均获得（见总表，独立养成线）",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    heroes = load_heroes()
    heroes_map = {h["id"]: h for h in heroes}
    data = gen_main_city()
    # refresh siege reference with heroes_map
    for row in data["levels"]:
        lv = row["level"]
        dps = deck_city_dps_simple(heroes_map, lv)
        hp = row["hp"]
        row["referenceSiege"]["defaultDeckDps"] = round(dps, 1)
        row["referenceSiege"]["siegeSeconds"] = round(hp / dps, 1) if dps else None

    (ROOT / "mainCity.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "docs" / "MAIN_CITY_PROGRESSION.md").write_text(
        gen_markdown(data) + "\n", encoding="utf-8"
    )
    print(f"Wrote mainCity.json v{data['version']}, docs/MAIN_CITY_PROGRESSION.md")
    print(f"L1: HP={data['hpByLevel']['1']} gold/s={data['goldPerSecByLevel']['1']} bricks/level={data['levels'][0]['flip']['totalBricksToNext']}")
    print(f"L30: HP={data['hpByLevel']['30']} gold/s={data['goldPerSecByLevel']['30']} cumulative bricks={data['cumulativeBricksToMax']}")
