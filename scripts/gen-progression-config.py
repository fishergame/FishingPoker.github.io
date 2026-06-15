#!/usr/bin/env python3
"""Generate arena.json, accountLevel.json, chest.json, docs/PROGRESSION_TABLES.md"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 活动/新增角色不进随机未拥有池，由配表维护
DEFAULT_EXCLUDE_HERO_IDS: list[str] = []

# 三档品质比例：低 40% / 中 30% / 高 30%（固定 3 名不同英雄各一档）
QUALITY_MIX = {"low": 40, "mid": 30, "high": 30}

# 各宝箱三档品质（low, mid, high）
CHEST_HERO_TIERS = {
    "wooden": ("common", "common", "rare"),
    "silver": ("common", "rare", "rare"),
    "golden": ("common", "rare", "epic"),
    "platinum": ("rare", "epic", "legendary"),
    "diamond": ("rare", "epic", "legendary"),
    "epic": ("rare", "epic", "legendary"),
    "legendary": ("epic", "legendary", "legendary"),
}
PLATINUM_PLUS = {"platinum", "diamond", "epic", "legendary"}
CHEST_TOTAL_CARDS = 10
CHEST_TOTAL_CARDS_PLATINUM_PLUS = 20


def split_cards_by_mix(total: int) -> tuple[int, int, int]:
    """按 40/30/30 分配总卡数，保证相加等于 total。"""
    low = round(total * QUALITY_MIX["low"] / 100)
    mid = round(total * QUALITY_MIX["mid"] / 100)
    high = total - low - mid
    return low, mid, high


def exp_for_level(level: int) -> int:
    return round(18 + level * 3 + (level ** 1.42) * 2.2)


def chest_quality_for_level(level: int) -> str:
    if level <= 12:
        return "wooden"
    if level <= 24:
        return "silver"
    if level <= 36:
        return "golden"
    if level <= 48:
        return "platinum"
    if level <= 60:
        return "diamond"
    if level <= 72:
        return "epic"
    return "legendary"


def account_level_hero_tiers(level: int) -> tuple[str, str, str]:
    """账号偶数级：三档品质（低/中/高）随等级提升。"""
    if level <= 20:
        return ("common", "rare", "epic")
    if level <= 45:
        return ("rare", "epic", "legendary")
    if level <= 70:
        return ("rare", "epic", "legendary")
    return ("epic", "legendary", "legendary")


def build_random_single_card(low_q: str, mid_q: str, high_q: str, must_unowned: bool = True) -> dict:
    """账号偶数级卡包：仅 1 张卡，按低40%/中30%/高30%随机一种品质。"""
    return {
        "type": "randomHeroCard",
        "count": 1,
        "mustUnowned": must_unowned,
        "qualityMix": QUALITY_MIX,
        "qualityOptions": [
            {"tier": "low", "quality": low_q, "weight": QUALITY_MIX["low"]},
            {"tier": "mid", "quality": mid_q, "weight": QUALITY_MIX["mid"]},
            {"tier": "high", "quality": high_q, "weight": QUALITY_MIX["high"]},
        ],
    }


def chest_hero_grant(chest_id: str) -> dict:
    """
    宝箱：共 10 张卡（铂金起 20 张），按 40/30/30 分给 3 名不同英雄。
    例：10 张 = 低 4 + 中 3 + 高 3；20 张 = 低 8 + 中 6 + 高 6。
  每档 1 名英雄，承担该档全部张数。
    """
    low_q, mid_q, high_q = CHEST_HERO_TIERS[chest_id]
    total = CHEST_TOTAL_CARDS_PLATINUM_PLUS if chest_id in PLATINUM_PLUS else CHEST_TOTAL_CARDS
    low_n, mid_n, high_n = split_cards_by_mix(total)
    return {
        "type": "heroCardPack",
        "heroCount": 3,
        "mustDistinct": True,
        "mustUnowned": False,
        "totalCards": total,
        "qualityMix": QUALITY_MIX,
        "qualitySlots": [
            {"slot": "low", "quality": low_q, "cardCount": low_n, "weight": QUALITY_MIX["low"]},
            {"slot": "mid", "quality": mid_q, "cardCount": mid_n, "weight": QUALITY_MIX["mid"]},
            {"slot": "high", "quality": high_q, "cardCount": high_n, "weight": QUALITY_MIX["high"]},
        ],
    }


def level_reward(level: int) -> list:
    """奇数级：品质宝箱；偶数级：1 张随机品质卡牌（40/30/30）。"""
    if level % 2 == 1:
        return [{"type": "chest", "chestId": chest_quality_for_level(level)}]
    low, mid, high = account_level_hero_tiers(level)
    return [build_random_single_card(low, mid, high, must_unowned=True)]


LEGEND_TROPHY_SOFT_CAP = 12000


def arena_milestone_rewards(aid: int, node_index: int, node_count: int, progress: float, vg: int, chest: str) -> list:
    """
    段位内奖杯里程碑：金币 + 钻石 + 宝箱（品质随竞技场档位）。
    节点越靠后、段位越高，数值越高。
    """
    gold = round(vg * (0.5 + progress * 1.0 + node_index * 0.12 + aid * 0.06))
    diamond = round(3 + aid * 4 + node_index * 3 + progress * aid * 3)
    return [
        {"type": "gold", "amount": gold},
        {"type": "diamond", "amount": diamond},
        {"type": "chest", "chestId": chest},
    ]


def gen_trophy_milestones(aid: int, unlock: int, nxt: int | None, vg: int, chest: str) -> list:
    """段位内奖励节点数 = arenaId（青铜1个、白银2个…传奇10个），奖杯均匀分布。"""
    node_count = aid
    upper = nxt if nxt is not None else LEGEND_TROPHY_SOFT_CAP
    span = upper - unlock
    milestones = []
    for i in range(1, node_count + 1):
        progress = i / (node_count + 1)
        trophy = unlock + round(span * progress)
        milestones.append({
            "trophy": trophy,
            "rewards": arena_milestone_rewards(aid, i, node_count, progress, vg, chest),
        })
    return milestones


def gen_arena():
    meta = [
        (1, "青铜", "bronze", 0, 100),
        (2, "白银", "silver", 100, 300),
        (3, "黄金", "gold", 300, 600),
        (4, "铂金", "platinum", 600, 1000),
        (5, "钻石", "diamond", 1000, 1600),
        (6, "星耀", "star", 1600, 2500),
        (7, "大师", "master", 2500, 4000),
        (8, "宗师", "grandmaster", 4000, 6000),
        (9, "王者", "king", 6000, 9000),
        (10, "传奇", "legend", 9000, None),
    ]
    battle = [
        (30, 0, 20, 8, "wooden", 50, 500),
        (28, 5, 25, 10, "silver", 80, 800),
        (26, 8, 30, 12, "golden", 120, 1200),
        (25, 10, 35, 14, "platinum", 160, 1600),
        (24, 12, 40, 16, "diamond", 200, 2000),
        (23, 15, 45, 18, "diamond", 250, 2500),
        (22, 18, 50, 20, "epic", 300, 3000),
        (21, 20, 55, 22, "epic", 350, 3500),
        (20, 22, 60, 24, "legendary", 400, 4000),
        (19, 25, 70, 28, "legendary", 500, 5000),
    ]
    arenas = []
    for (aid, name, tier, unlock, nxt), (tw, tl, ew, el, chest, vg, cap) in zip(meta, battle):
        milestones = gen_trophy_milestones(aid, unlock, nxt, vg, chest)

        first_unlock = [
            {"type": "gold", "amount": vg * 5},
            {"type": "chest", "chestId": chest},
        ]
        if aid == 2:
            first_unlock.append({"type": "feature", "featureId": "artifact"})
        elif aid >= 3:
            first_unlock.append({"type": "pickOne", "optionCount": 3})

        arenas.append({
            "arenaId": aid,
            "name": name,
            "tier": tier,
            "unlockTrophy": unlock,
            "nextArenaTrophy": nxt,
            "battleReward": {
                "trophyWin": tw,
                "trophyLoss": tl,
                "expWin": ew,
                "expLoss": el,
                "expLossRatio": round(el / ew, 2),
                "victoryGold": vg,
                "dailyGoldCap": cap,
                "chestDropId": chest,
                "chestDropChance": 1.0,
            },
            "trophyMilestones": milestones,
            "firstUnlockRewards": first_unlock,
        })

    return {
        "version": "1.0.0",
        "description": "10个竞技场：奖杯解锁、对战收益、段位内里程碑（金币+钻石+宝箱）",
        "arenaCount": 10,
        "rules": {
            "trophyMin": 0,
            "legendTrophySoftCap": LEGEND_TROPHY_SOFT_CAP,
            "arenaNoDemotion": True,
            "tierNoDemotion": True,
            "trophyLossFormula": "max(0, currentTrophy - trophyLoss)",
            "matchmakingArena": "maxArenaUnlocked",
            "seasonResetRatio": 0.2,
        },
        "arenas": arenas,
    }


def gen_chest():
    # 钻石：木质起全档必给，每档 +10（参考 CR 前期奖杯路 5→10→50 的递进节奏，宝箱侧用稳定 +10）
    # wooden 10, silver 20, golden 30, platinum 40, diamond 50, epic 60, legendary 70
    tiers = [
        ("wooden", "木质宝箱", 5, [20, 50], 10, 5),
        ("silver", "白银宝箱", 30, [50, 120], 20, 10),
        ("golden", "黄金宝箱", 120, [100, 250], 30, 20),
        ("platinum", "铂金宝箱", 240, [200, 500], 40, 30),
        ("diamond", "钻石宝箱", 480, [400, 800], 50, 50),
        ("epic", "史诗宝箱", 720, [600, 1200], 60, 80),
        ("legendary", "传奇宝箱", 1440, [1000, 2000], 70, 100),
    ]
    chests = []
    for cid, name, minutes, gold, diamond_fixed, instant_diamond in tiers:
        grant = chest_hero_grant(cid)
        low, mid, high = CHEST_HERO_TIERS[cid]
        total = grant["totalCards"]
        low_n, mid_n, high_n = split_cards_by_mix(total)
        chests.append({
            "chestId": cid,
            "name": name,
            "unlockMinutes": minutes,
            "adReduceMinutes": 30,
            "instantOpenDiamond": instant_diamond,
            "rewards": {
                "gold": {"min": gold[0], "max": gold[1]},
                "diamond": {"min": diamond_fixed, "max": diamond_fixed},
                "heroCardGrant": grant,
                "description": (
                    f"钻石{diamond_fixed}；共{total}张卡：低{low}×{low_n}+中{mid}×{mid_n}+高{high}×{high_n}"
                ),
            },
        })
    return {
        "version": "2.3.0",
        "description": "宝箱：钻石木质10起每档+10；卡牌共10张(铂金起20)分3英雄",
        "slotCount": 4,
        "chests": chests,
    }


def gen_account_level():
    levels = []
    total_exp = 0
    for lv in range(1, 100):
        req = exp_for_level(lv)
        total_exp += req
        reward = level_reward(lv)
        levels.append({
            "level": lv,
            "expRequired": req,
            "cumulativeExp": total_exp,
            "rewardType": reward[0]["type"],
            "rewards": reward,
        })
    max_low, max_mid, max_high = account_level_hero_tiers(100)
    return {
        "version": "2.3.0",
        "description": "账号等级：奇数级宝箱 / 偶数级1张随机品质卡（40/30/30），交替发放",
        "levelMax": 100,
        "defaultLevel": 1,
        "rewardRules": {
            "pattern": "alternate",
            "oddLevel": {"type": "chest", "note": "开箱见 chest.json"},
            "evenLevel": {
                "type": "randomHeroCard",
                "count": 1,
                "mustUnowned": True,
                "qualityMix": QUALITY_MIX,
                "note": "按低40%/中30%/高30%随机一种品质，共1张",
            },
        },
        "heroRewardPool": {
            "excludeHeroIds": DEFAULT_EXCLUDE_HERO_IDS,
            "excludeTags": ["event"],
            "note": "活动新增角色写入 excludeHeroIds，不参与 randomHero 抽取",
        },
        "expFormula": "round(18 + level * 3 + level^1.42 * 2.2)",
        "expSource": "battle",
        "totalExpToMax": total_exp,
        "estimatedMatches": round(total_exp / 42),
        "levels": levels,
        "maxLevelReward": [
            build_random_single_card(max_low, max_mid, max_high, must_unowned=True),
        ],
    }


QUALITY_CN = {
    "common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇",
}
CHEST_CN = {
    "wooden": "木质", "silver": "白银", "golden": "黄金", "platinum": "铂金",
    "diamond": "钻石", "epic": "史诗", "legendary": "传奇",
}


def fmt_chest_grant(r: dict) -> str:
    slots = r.get("qualitySlots", [])
    parts = [f"{QUALITY_CN[s['quality']]}×{s['cardCount']}" for s in slots]
    suffix = "（未拥有）" if r.get("mustUnowned") else ""
    total = r.get("totalCards", sum(s["cardCount"] for s in slots))
    return f"共{total}张[{'/'.join(parts)}]3名不同英雄{suffix}"


def fmt_random_card(r: dict) -> str:
    opts = r.get("qualityOptions", [])
    qs = "/".join(f"{QUALITY_CN[o['quality']]}{o['weight']}%" for o in opts)
    suffix = "（未拥有）" if r.get("mustUnowned") else ""
    return f"随机1张[{qs}]{suffix}"


def fmt_reward(rewards: list) -> str:
    parts = []
    for r in rewards:
        if r["type"] == "chest":
            parts.append(f"{CHEST_CN[r['chestId']]}宝箱")
        elif r["type"] == "gold":
            parts.append(f"金币{r['amount']}")
        elif r["type"] == "diamond":
            parts.append(f"钻石{r['amount']}")
        elif r["type"] == "heroCardPack":
            parts.append(fmt_chest_grant(r))
        elif r["type"] == "randomHeroCard":
            parts.append(fmt_random_card(r))
    return " + ".join(parts) if parts else "—"


def fmt_milestone_rewards(rewards: list) -> str:
    return fmt_reward(rewards)


def gen_progression_tables_md(arena, chest, account, hero):
    lines = [
        "# 《代号x》养成与竞技数值汇总表",
        "",
        "> 配表：`arena.json` · `accountLevel.json` · `chest.json` · `heroLevel.json`",
        "> 生成：`python3 scripts/gen-progression-config.py`",
        "",
        "---",
        "",
        "## 一、10 个竞技场",
        "",
        "| 场次 | 名称 | 解锁奖杯 | 下一场 | 胜杯 | 败扣 | 胜经验 | 败经验 | 胜金币 | 日上限 | 掉落宝箱 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for a in arena["arenas"]:
        br = a["battleReward"]
        nxt = a["nextArenaTrophy"] if a["nextArenaTrophy"] else "—"
        lines.append(
            f"| {a['arenaId']} | {a['name']} | {a['unlockTrophy']} | {nxt} | "
            f"+{br['trophyWin']} | -{br['trophyLoss']} | {br['expWin']} | {br['expLoss']} | "
            f"{br['victoryGold']} | {br['dailyGoldCap']} | {br['chestDropId']} |"
        )

    lines += [
        "",
        "### 段位内奖杯里程碑",
        "",
        "每个段位内奖励节点数 = **场次编号**（青铜 1 个、白银 2 个 … 传奇 10 个），",
        "奖杯在 `[解锁, 下一段/软上限]` 区间内均匀分布；每项奖励含 **金币 + 钻石 + 宝箱**。",
        "",
        "| 场次 | 名称 | 节点数 | 奖杯 | 奖励 |",
        "|:---:|:---:|:---:|:---:|:---|",
    ]
    for a in arena["arenas"]:
        ms_list = a.get("trophyMilestones", [])
        if not ms_list:
            lines.append(f"| {a['arenaId']} | {a['name']} | 0 | — | — |")
            continue
        for idx, ms in enumerate(ms_list):
            name_cell = a["name"] if idx == 0 else ""
            count_cell = str(len(ms_list)) if idx == 0 else ""
            lines.append(
                f"| {a['arenaId'] if idx == 0 else ''} | {name_cell} | {count_cell} | "
                f"{ms['trophy']} | {fmt_milestone_rewards(ms['rewards'])} |"
            )

    lines += [
        "",
        "---",
        "",
        "## 二、宝箱产出（金币 + 钻石 + 卡牌共10/20张）",
        "",
        "3名不同英雄；总卡数按低40%/中30%/高30%分配。木质~黄金共**10张**；铂金起共**20张**。",
        "",
        "| ID | 名称 | 总卡数 | 低档 | 中档 | 高档 | 金币 | 钻石 |",
        "|:---|:---|:---:|:---|:---|:---|:---|:---|",
    ]
    for c in chest["chests"]:
        g = c["rewards"]["gold"]
        d = c["rewards"]["diamond"]
        hg = c["rewards"]["heroCardGrant"]
        slots = hg["qualitySlots"]
        total = hg["totalCards"]
        cols = [f"{QUALITY_CN[s['quality']]}×{s['cardCount']}" for s in slots]
        while len(cols) < 3:
            cols.append("—")
        lines.append(
            f"| {c['chestId']} | {c['name']} | {total} | {cols[0]} | {cols[1]} | {cols[2]} | "
            f"{g['min']}-{g['max']} | {d['min']}-{d['max']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 三、英雄卡牌升级（四品质 ×30 级）",
        "",
        "碎片共用；金币按品质 × 系数。详见 `heroLevel.json`。",
        "",
        "---",
        "",
        "## 四、账号等级 1→100（交替奖励）",
        "",
        "**规则：**",
        "- **奇数级**：品质宝箱（共10/20张卡分3名英雄，见 chest.json）",
        "- **偶数级**：**随机1张卡**（低40%/中30%/高30%三档品质抽其一，优先未拥有）",
        "- 活动角色写入 `heroRewardPool.excludeHeroIds`，不参与随机",
        "",
        f"- 经验公式：`{account['expFormula']}`",
        f"- 满级总经验：**{account['totalExpToMax']:,}**",
        "",
        "| 等级 | 类型 | 需经验 | 累计经验 | 奖励 |",
        "|:---:|:---:|:---:|:---:|:---|",
    ]
    type_cn = {"chest": "宝箱", "randomHeroCard": "随机1卡", "heroCardPack": "卡包"}
    for lv in account["levels"]:
        rt = lv["rewardType"]
        lines.append(
            f"| {lv['level']}→{lv['level']+1} | {type_cn.get(rt, rt)} | "
            f"{lv['expRequired']} | {lv['cumulativeExp']:,} | {fmt_reward(lv['rewards'])} |"
        )
    lines.append(
        f"| **100 MAX** | 随机1卡 | — | {account['totalExpToMax']:,} | "
        f"{fmt_reward(account['maxLevelReward'])} |"
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    arena = gen_arena()
    chest = gen_chest()
    account = gen_account_level()
    hero_path = ROOT / "heroLevel.json"
    hero = json.loads(hero_path.read_text(encoding="utf-8")) if hero_path.exists() else {}

    for name, data in [
        ("arena.json", arena),
        ("chest.json", chest),
        ("accountLevel.json", account),
    ]:
        path = ROOT / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")

    md_path = ROOT / "docs" / "PROGRESSION_TABLES.md"
    md_path.write_text(gen_progression_tables_md(arena, chest, account, hero) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")
