#!/usr/bin/env python3
"""Generate mainCity.json + docs/MAIN_CITY_PROGRESSION.md

主城独立养成 v2.2：
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

# 单格翻开消耗：12 + 3×(等级-1)；L1=12，L10=39，L30=99
BRICK_BASE_PER_TILE = 12
BRICK_PER_TILE_STEP = 3

BRICK_BATTLE_BASE = 5
BRICK_BATTLE_GROWTH = 1.11
GOLD_BATTLE_BASE = 28
GOLD_BATTLE_GROWTH = 1.11
XP_BATTLE_BASE = 12
XP_BATTLE_GROWTH = 1.10
ARENA_RESOURCE_STEP = 0.06
LOSE_REWARD_RATIO = 0.4
PVE_BRICK_MULTIPLIER = 1.6  # 下调，避免后期 PvE 返还溢出
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
    return BRICK_BASE_PER_TILE + (level - 1) * BRICK_PER_TILE_STEP


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


def blended_bricks_per_match(main_city_level: int, arena_id: int, win_rate: float) -> float:
    w = battle_bricks(main_city_level, arena_id, True)
    l = battle_bricks(main_city_level, arena_id, False)
    return win_rate * w + (1 - win_rate) * l


def level_pacing_detail(row: dict, win_rate: float = 0.6) -> dict:
    """单级升级：扣 PvE 后还需多少场 PvP、多少活跃分钟。"""
    lv = row["level"]
    if lv >= LEVEL_MAX:
        return {}
    ar = row["referenceArena"]["arenaId"]
    need = row["flip"]["totalBricksToNext"]
    pve_n = row["flip"]["pveBuildingCount"]
    pve_per = row["battleRewards"]["pveBuildingWin"]["bricks"]
    pve_total = pve_n * pve_per
    pvp_need = max(0, need - pve_total)
    per_match = blended_bricks_per_match(lv, ar, win_rate)
    matches = round(pvp_need / per_match, 1) if per_match else 0.0
    dur = row["referenceArena"]["matchDurationSec"]
    return {
        "pveBricksTotal": pve_total,
        "pvpBricksNeeded": pvp_need,
        "blendedBricksPerMatch": round(per_match, 1),
        "pvpMatchesAfterPve": matches,
        "activeMinutes": round(matches * dur / 60, 0),
    }


PLAYER_ARCHETYPES = [
    {"id": "casual", "label": "轻度", "dailyMatches": 5, "winRate": 0.50, "note": "约 15–20 分钟/日"},
    {"id": "regular", "label": "常规", "dailyMatches": 10, "winRate": 0.55, "note": "约 30–35 分钟/日"},
    {"id": "active", "label": "活跃", "dailyMatches": 15, "winRate": 0.60, "note": "约 45–50 分钟/日"},
    {"id": "hardcore", "label": "重度", "dailyMatches": 25, "winRate": 0.65, "note": "约 70–90 分钟/日"},
]

REFERENCE_WIN_RATE = 0.60


def simulate_level_flips(
    row: dict,
    bank: float,
    win_rate: float,
) -> tuple[float, float, float]:
    """逐格翻砖：PvE 奖励在翻到对应格时返还。返回 (新增场次, 新增秒, 期末银行)。"""
    lv = row["level"]
    ar = row["referenceArena"]["arenaId"]
    tiles = row["flip"]["tilesPerLevel"]
    tile_cost = row["flip"]["brickCostPerTile"]
    pve_n = row["flip"]["pveBuildingCount"]
    pve_per = row["battleRewards"]["pveBuildingWin"]["bricks"]
    per_match = blended_bricks_per_match(lv, ar, win_rate)
    dur = row["referenceArena"]["matchDurationSec"]

    # PvE 建筑均匀落在本级格子中（如 8 格 2 个 → 第 4、8 格）
    pve_tiles = set()
    if pve_n > 0:
        for k in range(1, pve_n + 1):
            idx = round(k * tiles / (pve_n + 1))
            pve_tiles.add(max(1, min(tiles, idx)))

    matches = 0.0
    active_sec = 0.0
    for t in range(1, tiles + 1):
        if bank < tile_cost:
            need = tile_cost - bank
            m = need / per_match if per_match else 0
            matches += m
            active_sec += m * dur
            bank += need
        bank -= tile_cost
        if t in pve_tiles:
            bank += pve_per
    return matches, active_sec, bank


def load_chest_bricks() -> dict[str, int]:
    p = ROOT / "chest.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for c in data.get("chests", []):
        brick = c.get("rewards", {}).get("brick", {})
        out[c["chestId"]] = brick.get("min", brick.get("amount", 0))
    return out


def load_account_level_exp() -> list[dict]:
    p = ROOT / "accountLevel.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("levels", [])


def load_arena_battle_rewards() -> dict[int, dict]:
    p = ROOT / "arena.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {a["arenaId"]: a["battleReward"] for a in data.get("arenas", [])}


def account_brick_bonus(account_level: int) -> int:
    """账号升级奖励中的固定砖头（见 gen-progression-config.py）。"""
    return 6 + (account_level - 1) // 2


def pve_tile_indices(tiles: int, pve_n: int) -> set[int]:
    pve_tiles = set()
    if pve_n > 0:
        for k in range(1, pve_n + 1):
            idx = round(k * tiles / (pve_n + 1))
            pve_tiles.add(max(1, min(tiles, idx)))
    return pve_tiles


def simulate_journey_full(
    levels: list[dict],
    daily_matches: int,
    win_rate: float,
    chest_bricks: dict[str, int],
    account_levels: list[dict],
    arena_battle: dict[int, dict],
) -> dict:
    """日循环：PvP 砖 + 宝箱砖 + 账号升级砖 + PvE 返还 → 逐格翻主城。"""
    upgrade_rows = [r for r in levels if r["level"] < LEVEL_MAX]
    city_idx = 0
    tile_idx = 0
    city_lv = 1
    bank = 0.0
    days = 0
    matches = 0
    income = {"pvp": 0.0, "chest": 0.0, "account": 0.0, "pve": 0.0}

    account_lv = 1
    account_exp = 0.0
    exp_idx = 0
    exp_to_next = account_levels[0]["expRequired"] if account_levels else 999999

    while city_lv < LEVEL_MAX and days < 150:
        days += 1
        for _ in range(daily_matches):
            matches += 1
            ar = reference_arena(city_lv)
            br = arena_battle.get(ar, {})
            w_b = battle_bricks(city_lv, ar, True)
            l_b = battle_bricks(city_lv, ar, False)
            gain = win_rate * w_b + (1 - win_rate) * l_b
            bank += gain
            income["pvp"] += gain

            chest_id = br.get("chestDropId", "wooden")
            c_gain = chest_bricks.get(chest_id, 0) * win_rate
            bank += c_gain
            income["chest"] += c_gain

            exp_gain = win_rate * br.get("expWin", 20) + (1 - win_rate) * br.get("expLoss", 8)
            account_exp += exp_gain
            while account_levels and account_lv <= len(account_levels) and account_exp >= exp_to_next:
                account_exp -= exp_to_next
                bonus = account_brick_bonus(account_lv)
                bank += bonus
                income["account"] += bonus
                account_lv += 1
                if account_lv <= len(account_levels):
                    exp_to_next = account_levels[account_lv - 1]["expRequired"]

            while city_idx < len(upgrade_rows):
                row = upgrade_rows[city_idx]
                tiles = row["flip"]["tilesPerLevel"]
                tile_cost = row["flip"]["brickCostPerTile"]
                pve_n = row["flip"]["pveBuildingCount"]
                pve_per = row["battleRewards"]["pveBuildingWin"]["bricks"]
                pve_set = pve_tile_indices(tiles, pve_n)
                if tile_idx >= tiles:
                    city_idx += 1
                    tile_idx = 0
                    city_lv += 1
                    if city_lv >= LEVEL_MAX or city_idx >= len(upgrade_rows):
                        break
                    continue
                if bank < tile_cost:
                    break
                bank -= tile_cost
                tile_idx += 1
                if tile_idx in pve_set:
                    bank += pve_per
                    income["pve"] += pve_per
            if city_lv >= LEVEL_MAX:
                break
        if city_lv >= LEVEL_MAX:
            break

    total_in = sum(income.values())
    return {
        "daysToMax": days if city_lv >= LEVEL_MAX else None,
        "totalMatches": matches,
        "accountLevelAtMax": account_lv,
        "income": {k: round(v, 0) for k, v in income.items()},
        "incomeShare": {k: round(100 * v / total_in, 1) if total_in else 0 for k, v in income.items()},
        "reachedMax": city_lv >= LEVEL_MAX,
    }


def simulate_full_progression(levels: list[dict]) -> dict:
    """L1→L30：逐格翻砖 + 砖头银行逐级模拟。"""
    upgrade_rows = [r for r in levels if r["level"] < LEVEL_MAX]
    total_bricks = sum(r["flip"]["totalBricksToNext"] for r in upgrade_rows)
    total_pve_bricks = sum(
        r["flip"]["pveBuildingCount"] * r["battleRewards"]["pveBuildingWin"]["bricks"]
        for r in upgrade_rows
    )

    def run_bank_sim(win_rate: float) -> dict:
        bank = 0.0
        pvp_matches = 0.0
        active_sec = 0.0
        level_trace: list[dict] = []
        for row in upgrade_rows:
            m, sec, bank = simulate_level_flips(row, bank, win_rate)
            pvp_matches += m
            active_sec += sec
            level_trace.append({
                "level": row["level"],
                "flipCost": row["flip"]["totalBricksToNext"],
                "pveReturn": row["flip"]["pveBuildingCount"] * row["battleRewards"]["pveBuildingWin"]["bricks"],
                "pvpMatches": round(m, 1),
                "bankAfter": round(bank, 0),
            })
        return {
            "totalPvpMatches": round(pvp_matches, 0),
            "totalActiveHours": round(active_sec / 3600, 1),
            "endingBank": round(bank, 0),
            "levelTrace": level_trace,
        }

    ref = run_bank_sim(REFERENCE_WIN_RATE)
    chest_bricks = load_chest_bricks()
    account_levels = load_account_level_exp()
    arena_battle = load_arena_battle_rewards()

    archetypes = []
    for a in PLAYER_ARCHETYPES:
        sim_pvp = run_bank_sim(a["winRate"])
        full = simulate_journey_full(
            levels, a["dailyMatches"], a["winRate"],
            chest_bricks, account_levels, arena_battle,
        )
        days_pvp_only = round(sim_pvp["totalPvpMatches"] / a["dailyMatches"], 1)
        archetypes.append({
            **a,
            "totalPvpMatches": sim_pvp["totalPvpMatches"],
            "totalActiveHours": sim_pvp["totalActiveHours"],
            "endingBrickBank": sim_pvp["endingBank"],
            "daysToMaxPvpOnly": days_pvp_only,
            "daysToMax": full["daysToMax"],
            "weeksToMax": round(full["daysToMax"] / 7, 1) if full["daysToMax"] else None,
            "totalMatches": full["totalMatches"],
            "accountLevelAtMax": full["accountLevelAtMax"],
            "income": full["income"],
            "incomeShare": full["incomeShare"],
        })

    # 含 PvE 抵扣后的「净外部砖」= 累计升级砖 - PvE 返还（可为负，表示 PvE 溢出）
    net_external_bricks = total_bricks - total_pve_bricks

    return {
        "referenceWinRate": REFERENCE_WIN_RATE,
        "totalBricksToMax": total_bricks,
        "totalPveBricks": total_pve_bricks,
        "netExternalBricks": net_external_bricks,
        "pveOffsetPercent": round(100 * total_pve_bricks / total_bricks, 1),
        "referencePvpMatches": ref["totalPvpMatches"],
        "referenceActiveHours": ref["totalActiveHours"],
        "referenceEndingBank": ref["endingBank"],
        "referenceDaysAt15PerDay": round(ref["totalPvpMatches"] / 15, 1),
        "fullJourneyReference": simulate_journey_full(
            levels, 10, 0.55, chest_bricks, account_levels, arena_battle,
        ),
        "brickIncomeSources": ["pvpBattle", "arenaChest", "accountLevel", "mainCityPve"],
        "archetypes": archetypes,
        "levelTrace": ref["levelTrace"],
    }


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
                **level_pacing_detail({
                    "level": lv,
                    "flip": {
                        "totalBricksToNext": total_bricks_to_level_up(lv),
                        "pveBuildingCount": pve_building_count(lv),
                    },
                    "referenceArena": {"arenaId": ar, "matchDurationSec": durations.get(ar, 180)},
                    "battleRewards": {
                        "pveBuildingWin": {
                            "bricks": max(2, round(battle_bricks(lv, ar, True) * PVE_BRICK_MULTIPLIER)),
                        },
                    },
                }, REFERENCE_WIN_RATE),
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
    pacing_summary = simulate_full_progression(levels)

    return {
        "version": "2.2.0",
        "description": "主城养成：翻格升级（单格砖×格数）、战斗 HP/产金",
        "levelMax": LEVEL_MAX,
        "gameplay": {
            "upgradeMode": "flipTiles",
            "tileCostCurrency": "brick",
            "upgradeLogic": "每升 1 级外扩一圈，逐格翻开；单格耗砖随等级涨，格数随外扩略增",
            "flipBrickCostFormula": f"{BRICK_BASE_PER_TILE} + (mainCityLevel-1)*{BRICK_PER_TILE_STEP}  // 单格",
            "tilesPerLevelFormula": f"min({TILES_MAX}, {TILES_BASE} + floor((mainCityLevel-1)/{TILES_STEP_EVERY}))",
            "totalBricksFormula": "tilesPerLevel × flipBrickCost  // 派生",
            "tileLoot": {
                "decoration": DECOR_CATEGORIES,
                "pveBuilding": "每级 2–3 个，翻开触发 PvE；胜利额外给砖头/金币",
            },
            "shopBrickPacksRef": "shop.json → zones.basic.brickPacks（钻石四档）",
            "dailyQuestRef": "dailyQuest.json · docs/MAIN_CITY_DAILY_QUEST.md（登录连签+对战任务，独立文档）",
        },
        "formulas": {
            "hp": f"round({MAIN_CITY_HP_L1} * {STAT_GROWTH}^(mainCityLevel-1))",
            "goldPerSec": f"{GOLD_PER_SEC_L1} + (mainCityLevel-1)*{GOLD_PER_SEC_STEP}",
            "flipBrickCost": f"{BRICK_BASE_PER_TILE} + (mainCityLevel-1)*{BRICK_PER_TILE_STEP}",
            "tilesPerLevel": f"min({TILES_MAX}, {TILES_BASE} + floor((mainCityLevel-1)/{TILES_STEP_EVERY}))",
            "totalBricksToNext": "tilesPerLevel × flipBrickCost",
            "battleBricksWin": f"round({BRICK_BATTLE_BASE} * {BRICK_BATTLE_GROWTH}^(L-1) * arenaMul)",
            "battleGoldWin": f"round({GOLD_BATTLE_BASE} * {GOLD_BATTLE_GROWTH}^(L-1) * arenaMul)",
            "loseRewardRatio": LOSE_REWARD_RATIO,
        },
        "cumulativeBricksToMax": cumulative_bricks,
        "pacingSummary": pacing_summary,
        "levels": levels,
        "hpByLevel": {str(r["level"]): r["hp"] for r in levels},
        "goldPerSecByLevel": {str(r["level"]): r["goldPerSec"] for r in levels},
    }


def fmt_gold(g: float) -> str:
    return str(int(g)) if g == int(g) else f"{g:.1f}"


def gen_markdown(data: dict) -> str:
    ps = data["pacingSummary"]
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
        "| **单格砖头** | `12 + (当前主城等级 - 1) × 3`，L1=12 砖/格 |",
        "| **砖头来源** | 对局胜负 + **竞技场宝箱** + **账号升级** + 主城 PvE |",
        "| **PvE 奖励** | 胜利额外砖头 ≈ 胜场 ×**1.6**、金币 ≈ ×2 |",
        "| **PvP 奖励** | 胜利给 砖头 + 金币 + 账号经验；失败给 **40%** |",
        "| **战斗 HP** | 随主城等级 ×1.15；**产金/秒** 每级 **+0.5**（2.0→16.5） |",
        "| **对局时长** | 仅看竞技场（青铜 90s → 传奇 180s） |",
        "",
        "### 公式",
        "",
        "```",
        "mainCityHp(L)       = round(1500 × 1.15^(L-1))",
        "goldPerSec(L)       = 2.0 + (L-1) × 0.5",
        "flipBrickCost(L)    = 12 + (L-1) × 3       // 单格翻开（主口径）",
        "tilesPerLevel(L)    = min(14, 8 + floor((L-1)/4))  // 外扩格数",
        "bricksToLevelUp(L)  = tilesPerLevel(L) × flipBrickCost(L)",
        "battleBricksWin     = round(5 × 1.11^(L-1) × (1+0.06×(场次-1)))",
        "battleGoldWin       = round(28 × 1.11^(L-1) × (1+0.06×(场次-1)))",
        "```",
        "",
        f"**满级累计砖头（L1→L30）**：**{data['cumulativeBricksToMax']:,}**（PvE 全清可返还约 **{ps['totalPveBricks']:,}** 砖，折合抵扣 **{ps['pveOffsetPercent']}%**）",
        "",
        f"**参考满级（常规 · 10 场/日 · 55% 胜 · 含宝箱/账号/PvE）**：约 **{ps['fullJourneyReference']['daysToMax']} 天** · {ps['fullJourneyReference']['totalMatches']} 场 · 账号约 L{ps['fullJourneyReference']['accountLevelAtMax']}",
        "",
        "---",
        "",
        "## 二、统一总表（L1–L30）",
        "",
        "| 等级 | 战斗HP | 产金/s | 单格砖 | 本级格数 | 升级总砖 | PvE·砖 | 胜·砖 | 负·砖 | 60%场/级 | 本级·分 | 参考场次 | 时长 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    trace = {t["level"]: t for t in ps.get("levelTrace", [])}
    for r in data["levels"]:
        lv = r["level"]
        ar = r["referenceArena"]
        fl = r["flip"]
        rw = r["battleRewards"]["win"]
        rl = r["battleRewards"]["lose"]
        pc = r["pacing"]
        dur = ar["matchDurationSec"]
        m, s = divmod(dur, 60)
        pve_b = pc.get("pveBricksTotal", "—")
        tr = trace.get(lv)
        if tr:
            matches = tr["pvpMatches"]
            mins = round(tr["pvpMatches"] * dur / 60, 0)
        else:
            matches = "—"
            mins = "—"
        lines.append(
            f"| **L{lv}** | {r['hp']:,} | {fmt_gold(r['goldPerSec'])} | {fl['brickCostPerTile']} "
            f"| {fl['tilesPerLevel']} | {fl['totalBricksToNext']:,} | {pve_b} "
            f"| {rw['bricks']} | {rl['bricks']} | {matches} | {mins} "
            f"| {ar['arenaId']} {ar['arenaName']} | {m}:{s:02d} |"
        )

    lines += [
        "",
        "> **PvE·砖** = 本级 PvE 建筑全清一次性返还；**60%场/级** = 砖头银行模拟下为凑够本级翻格需打的 PvP 场；**本级·分** = 上述场次 × 参考对局时长。",
        "> 不含商店购砖、不含账号经验线；失败砖头为胜利的 40%。",
        "",
        "### 满级耗时 · 玩家画像（全渠道砖头 · L1→L30）",
        "",
        "| 画像 | 日场次 | 胜率 | 满级天数 | 总场次 | 账号级 | PvP砖% | 宝箱砖% | 账号砖% | PvE砖% |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for a in ps["archetypes"]:
        sh = a.get("incomeShare", {})
        lines.append(
            f"| **{a['label']}** | {a['dailyMatches']} | {int(a['winRate']*100)}% "
            f"| **{a['daysToMax']}** | {a.get('totalMatches', '—')} | {a.get('accountLevelAtMax', '—')} "
            f"| {sh.get('pvp', '—')} | {sh.get('chest', '—')} | {sh.get('account', '—')} | {sh.get('pve', '—')} |"
        )

    reg = next(a for a in ps["archetypes"] if a["id"] == "regular")
    lines += [
        "",
        "### 曲线评价（设计自检）",
        "",
        "| 维度 | 结论 | 说明 |",
        "|:---|:---|:---|",
        f"| **满级节奏** | **≈1 个月** | 常规玩家（10 场/日）约 **{reg['daysToMax']} 天**满级，符合目标 |",
        "| **砖头来源** | 四渠道均衡 | PvP ≈33% · 宝箱 ≈34% · PvE ≈30% · 账号 ≈2%（稳定补充） |",
        "| **早期（L1–L10）** | 稳定 | 单级升级 96–240 砖；约 2–3 天/级（常规） |",
        "| **中后期** | 宝箱+P vP 成长 | 场次升高、胜场砖增加，后期 PvE 覆盖部分本级消耗 |",
        "| **与卡牌线** | 并行 | 主城 1 月满级 vs 卡牌核心满级数月；定位更快副养成 |",
        "| **付费补齐** | 可选 | 钻石四档日限约 790 砖，约 0.5–1 级，不破坏月满节奏 |",
        "",
        "---",
        "",
        "## 三、砖头产出分布",
        "",
        "### 3.1 对局胜负（已有 · `mainCity.json`）",
        "",
        "见 §二总表 **胜·砖 / 负·砖**；失败 = 胜利 × 40%。",
        "",
        "### 3.2 竞技场宝箱（`chest.json` · 胜利掉落）",
        "",
        "| 宝箱 | 木质 | 白银 | 黄金 | 铂金 | 钻石 | 史诗 | 传奇 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    chest_data = json.loads((ROOT / "chest.json").read_text(encoding="utf-8")) if (ROOT / "chest.json").exists() else {}
    brick_row = "| **砖头** |"
    for cid in ["wooden", "silver", "golden", "platinum", "diamond", "epic", "legendary"]:
        amt = "—"
        for c in chest_data.get("chests", []):
            if c["chestId"] == cid:
                amt = str(c["rewards"].get("brick", {}).get("min", "—"))
                break
        brick_row += f" {amt} |"
    lines.append(brick_row)
    lines += [
        "",
        "> 胜利必掉对应场次宝箱（`arena.json` → `chestDropId`），开箱时与金币/钻石/卡牌一并发放。",
        "",
        "### 3.3 账号等级（`accountLevel.json` · 每级固定）",
        "",
        "**公式**：`6 + floor((账号等级 - 1) / 2)`，与奇数宝箱/偶数卡牌**同时发放**。",
        "",
        "| 账号等级 | 1 | 5 | 10 | 15 | 20 | 25 | 30 | 50 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        "| **砖头** | 6 | 8 | 10 | 13 | 15 | 18 | 20 | 30 |",
        "",
        "### 3.4 主城 PvE 建筑",
        "",
        "见总表 **PvE·砖** = 本级 PvE 建筑全清返还；倍率 **胜场砖 × 1.6**。",
        "",
        "---",
        "",
        "## 四、关键等级对照",
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
        "## 五、翻格掉落（装饰 vs PvE）",
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
        "## 六、商店 · 砖头礼包（钻石 · 四档）",
        "",
        "配表见 **`shop.json`** → `zones.basic.brickPacks`（仅钻石购买，大包单价更低）。",
        "",
        "| 商品 | 砖头 | 钻石 | 单价 | 限购 | 说明 |",
        "|:---|:---:|:---:|:---:|:---:|:---|",
        "| 砖头×40 | 40 | 25 | 0.63 | 日3 | 约 L1 升级量 40% |",
        "| 砖头×100 | 100 | 58 | 0.58 | 日2 | 约 L1–L3 一级量 |",
        "| 砖头×250 | 250 | 128 | 0.51 | 日1 | 中后期补仓 |",
        "| 砖头×600 | 600 | 268 | 0.45 | 周2 | 大包优惠 |",
    ]

    lines += [
        "",
        "---",
        "",
        "## 七、对局时长（竞技场 · 不变）",
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
        "## 八、与卡牌/账号关系",
        "",
        "- **主城等级**：右侧「主城」页；翻格耗砖升级 → 提高 **局内 HP + 产金**",
        "- **卡牌等级**：只影响翻出单位强度",
        "- **竞技场**：只调 **对局倒计时** 与掉落场次系数",
        "- **账号升级**：每级额外发砖头（见 §三.3），与宝箱/卡牌并列",
        "",
        "---",
        "",
        "## 九、满级推演（`pacingSummary`）",
        "",
        "| 指标 | 数值 |",
        "|:---|:---|",
        f"| 累计升级砖 | {ps['totalBricksToMax']:,} |",
        f"| 常规玩家满级天数 | **{reg['daysToMax']} 天**（10 场/日 · 55% 胜） |",
        f"| 满级时账号等级 | 约 L{ps['fullJourneyReference']['accountLevelAtMax']} |",
        f"| 满级总对局场次 | {ps['fullJourneyReference']['totalMatches']} |",
        "",
        "**满级旅程砖头收入（常规玩家）**：",
        "",
        "| 渠道 | 砖头 | 占比 |",
        "|:---|:---:|:---:|",
    ]
    inc = reg.get("income", {})
    ish = reg.get("incomeShare", {})
    for key, label in [("pvp", "对局胜负"), ("chest", "竞技场宝箱"), ("account", "账号升级"), ("pve", "主城 PvE")]:
        lines.append(f"| {label} | {inc.get(key, 0):,.0f} | {ish.get(key, 0)}% |")
    lines += [
        "",
        "---",
        "",
        "## 十、汇总调整表（本轮数值变更）",
        "",
        "| 模块 | 文件 | 调整项 | 原值 | 新值 | 目的 |",
        "|:---|:---|:---|:---|:---|:---|",
        "| 主城翻格 | `mainCity.json` | 单格砖公式 | `7+(L-1)` | **`12+(L-1)×3`** | 拉长久期；L1=12/格 |",
        "| 主城翻格 | `mainCity.json` | L1 升级总砖 | 56 | **96** | 8 格 × 12 砖 |",
        "| 主城翻格 | `mainCity.json` | 满级累计砖 | 7,252 | **18,858** | 对齐约 1 月满级 |",
        "| 主城 PvE | `mainCity.json` | 胜利砖倍率 | ×2.5 | **×1.6** | 抑制后期白嫖溢出 |",
        "| 竞技场宝箱 | `chest.json` | 各档砖头 | 无 | **8~100** | 胜利开箱产砖 |",
        "| 账号等级 | `accountLevel.json` | 每级砖头 | 无 | **`6+⌊(L-1)/2⌋`** | 升级里程碑补充 |",
        "| 商店 | `shop.json` | 砖头购买 | 金币+钻石 | **钻石四档** | 付费可选加速 |",
        "| 节奏 | 模拟 | 常规满级 | ~11 天 | **~27 天** | 目标约 1 个月 |",
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
