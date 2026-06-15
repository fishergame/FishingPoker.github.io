#!/usr/bin/env python3
"""Generate arena.json, accountLevel.json, chest.json, docs/PROGRESSION_TABLES.md"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 活动/新增角色不进随机未拥有池，由配表维护
DEFAULT_EXCLUDE_HERO_IDS: list[str] = []

# 三档品质比例：低 40% / 中 30% / 高 30%（固定 3 名不同英雄各一档）
QUALITY_MIX = {"low": 40, "mid": 30, "high": 30}

# 各宝箱三档品质（low, mid, high）；铂金起 cardsPerHero 翻倍
CHEST_HERO_TIERS = {
    "wooden": ("common", "common", "rare"),
    "silver": ("common", "rare", "rare"),
    "golden": ("common", "rare", "epic"),
    "platinum": ("rare", "epic", "legendary"),
    "diamond": ("rare", "epic", "legendary"),
    "epic": ("rare", "epic", "legendary"),
    "legendary": ("epic", "legendary", "legendary"),
}
CHEST_CARDS_PER_HERO = {
    "wooden": 5, "silver": 5, "golden": 5,
    "platinum": 10, "diamond": 10, "epic": 10, "legendary": 10,
}
PLATINUM_PLUS = {"platinum", "diamond", "epic", "legendary"}


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


def build_hero_card_pack(
    low_q: str, mid_q: str, high_q: str,
    cards_per_hero: int,
    must_unowned: bool = False,
) -> dict:
    return {
        "type": "heroCardPack",
        "heroCount": 3,
        "mustDistinct": True,
        "mustUnowned": must_unowned,
        "cardsPerHero": cards_per_hero,
        "qualityMix": QUALITY_MIX,
        "qualitySlots": [
            {"slot": "low", "quality": low_q, "weight": QUALITY_MIX["low"]},
            {"slot": "mid", "quality": mid_q, "weight": QUALITY_MIX["mid"]},
            {"slot": "high", "quality": high_q, "weight": QUALITY_MIX["high"]},
        ],
    }


def chest_hero_grant(chest_id: str) -> dict:
    low, mid, high = CHEST_HERO_TIERS[chest_id]
    return build_hero_card_pack(low, mid, high, CHEST_CARDS_PER_HERO[chest_id], must_unowned=False)


def level_reward(level: int) -> list:
    """奇数级：品质宝箱；偶数级：3 张不同未拥有英雄（低/中/高各一）。"""
    if level % 2 == 1:
        return [{"type": "chest", "chestId": chest_quality_for_level(level)}]
    low, mid, high = account_level_hero_tiers(level)
    return [build_hero_card_pack(low, mid, high, cards_per_hero=1, must_unowned=True)]


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
        milestones = []
        if nxt:
            span = nxt - unlock
            for pct in [0.25, 0.5, 0.75, 1.0]:
                ms = {
                    "trophy": unlock + round(span * pct),
                    "rewards": [{"type": "gold", "amount": round(vg * (1 + pct))}],
                }
                if pct == 1.0:
                    ms["rewards"].append({"type": "chest", "chestId": chest})
                milestones.append(ms)

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
        "description": "10个竞技场：奖杯解锁、对战收益、宝箱掉落",
        "arenaCount": 10,
        "rules": {
            "trophyMin": 0,
            "arenaNoDemotion": True,
            "tierNoDemotion": True,
            "trophyLossFormula": "max(0, currentTrophy - trophyLoss)",
            "matchmakingArena": "maxArenaUnlocked",
            "seasonResetRatio": 0.2,
        },
        "arenas": arenas,
    }


def gen_chest():
    tiers = [
        ("wooden", "木质宝箱", 5, [20, 50], [0, 0], 5),
        ("silver", "白银宝箱", 30, [50, 120], [0, 1], 10),
        ("golden", "黄金宝箱", 120, [100, 250], [1, 3], 20),
        ("platinum", "铂金宝箱", 240, [200, 500], [2, 5], 30),
        ("diamond", "钻石宝箱", 480, [400, 800], [5, 10], 50),
        ("epic", "史诗宝箱", 720, [600, 1200], [8, 15], 80),
        ("legendary", "传奇宝箱", 1440, [1000, 2000], [15, 30], 100),
    ]
    chests = []
    for cid, name, minutes, gold, diamond, instant_diamond in tiers:
        grant = chest_hero_grant(cid)
        low, mid, high = CHEST_HERO_TIERS[cid]
        n = CHEST_CARDS_PER_HERO[cid]
        doubled = "（铂金+翻倍）" if cid in PLATINUM_PLUS else ""
        chests.append({
            "chestId": cid,
            "name": name,
            "unlockMinutes": minutes,
            "adReduceMinutes": 30,
            "instantOpenDiamond": instant_diamond,
            "rewards": {
                "gold": {"min": gold[0], "max": gold[1]},
                "diamond": {"min": diamond[0], "max": diamond[1]},
                "heroCardGrant": grant,
                "description": (
                    f"3名不同英雄：低{low}/中{mid}/高{high}，各×{n}{doubled}"
                ),
            },
        })
    return {
        "version": "2.1.0",
        "description": "宝箱：金币+钻石+3名不同英雄卡牌（低40%/中30%/高30%）；铂金起每人×10",
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
        "version": "2.1.0",
        "description": "账号等级：奇数级宝箱 / 偶数级3张不同未拥有英雄，交替发放",
        "levelMax": 100,
        "defaultLevel": 1,
        "rewardRules": {
            "pattern": "alternate",
            "oddLevel": {"type": "chest", "note": "开箱见 chest.json：3名不同英雄+金币+钻石"},
            "evenLevel": {
                "type": "heroCardPack",
                "heroCount": 3,
                "mustDistinct": True,
                "mustUnowned": True,
                "cardsPerHero": 1,
                "qualityMix": QUALITY_MIX,
                "note": "低40%/中30%/高30%各1名不同英雄",
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
            build_hero_card_pack(max_low, max_mid, max_high, cards_per_hero=1, must_unowned=True),
        ],
    }


QUALITY_CN = {
    "common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇",
}
CHEST_CN = {
    "wooden": "木质", "silver": "白银", "golden": "黄金", "platinum": "铂金",
    "diamond": "钻石", "epic": "史诗", "legendary": "传奇",
}


def fmt_pack(r: dict) -> str:
    slots = r.get("qualitySlots", [])
    qs = "/".join(QUALITY_CN[s["quality"]] for s in slots)
    n = r.get("cardsPerHero", 1)
    suffix = "（未拥有）" if r.get("mustUnowned") else ""
    per = f"各×{n}" if n > 1 else "各×1"
    return f"3名不同英雄[{qs}]{per}{suffix}"


def fmt_reward(rewards: list) -> str:
    parts = []
    for r in rewards:
        if r["type"] == "chest":
            parts.append(f"{CHEST_CN[r['chestId']]}宝箱")
        elif r["type"] in ("heroCardPack", "randomHero"):
            parts.append(fmt_pack(r))
    return " + ".join(parts) if parts else "—"


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
        "---",
        "",
        "## 二、宝箱产出（金币 + 钻石 + 3名不同英雄）",
        "",
        "低/中/高比例 40%/30%/30%；木质~黄金各×5，**铂金起×10（翻倍）**。",
        "",
        "| ID | 名称 | 开启 | 金币 | 钻石 | 低/中/高品质 | 每人卡数 | 秒开钻 |",
        "|:---|:---|:---:|:---|:---|:---|:---:|:---:|",
    ]
    for c in chest["chests"]:
        g = c["rewards"]["gold"]
        d = c["rewards"]["diamond"]
        hg = c["rewards"]["heroCardGrant"]
        slots = hg["qualitySlots"]
        qs = "/".join(QUALITY_CN[s["quality"]] for s in slots)
        n = hg["cardsPerHero"]
        lines.append(
            f"| {c['chestId']} | {c['name']} | {c['unlockMinutes']}分 | "
            f"{g['min']}-{g['max']} | {d['min']}-{d['max']} | {qs} | ×{n} | {c['instantOpenDiamond']} |"
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
        "- **奇数级**：品质宝箱（金币+钻石+**3名不同英雄**，见 chest.json）",
        "- **偶数级**：**3张不同未拥有英雄**（低40%/中30%/高30%各1名，各×1）",
        "- 活动角色写入 `heroRewardPool.excludeHeroIds`，不参与随机",
        "",
        f"- 经验公式：`{account['expFormula']}`",
        f"- 满级总经验：**{account['totalExpToMax']:,}**",
        "",
        "| 等级 | 类型 | 需经验 | 累计经验 | 奖励 |",
        "|:---:|:---:|:---:|:---:|:---|",
    ]
    type_cn = {"chest": "宝箱", "heroCardPack": "3卡包", "randomHero": "3卡包"}
    for lv in account["levels"]:
        lines.append(
            f"| {lv['level']}→{lv['level']+1} | {type_cn[lv['rewardType']]} | "
            f"{lv['expRequired']} | {lv['cumulativeExp']:,} | {fmt_reward(lv['rewards'])} |"
        )
    lines.append(
        f"| **100 MAX** | 随机英雄 | — | {account['totalExpToMax']:,} | "
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
