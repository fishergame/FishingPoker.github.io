#!/usr/bin/env python3
"""Generate arena.json, accountLevel.json, chest.json"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def exp_for_level(level: int) -> int:
    return round(18 + level * 3 + (level ** 1.42) * 2.2)


def level_reward(level: int) -> list:
    if level % 10 == 0:
        chest_map = {
            10: "silver", 20: "golden", 30: "platinum", 40: "diamond",
            50: "epic", 60: "epic", 70: "legendary", 80: "legendary",
            90: "legendary", 100: "legendary",
        }
        rewards = [{"type": "chest", "chestId": chest_map[level]}]
        rewards.append({"type": "gold", "amount": level * 50})
        return rewards
    if level % 5 == 0:
        if level <= 15:
            chest_id = "wooden"
        elif level <= 30:
            chest_id = "silver"
        elif level <= 45:
            chest_id = "golden"
        elif level <= 60:
            chest_id = "platinum"
        elif level <= 75:
            chest_id = "diamond"
        else:
            chest_id = "epic"
        return [{"type": "chest", "chestId": chest_id}]
    if level <= 25:
        quality, count = "common", 2 + level // 8
    elif level <= 50:
        quality = "rare" if level % 2 else "common"
        count = 2 + level // 12
    elif level <= 75:
        quality = "epic" if level % 3 == 0 else "rare"
        count = 1 + level // 18
    else:
        quality = "legendary" if level % 4 == 0 else "epic"
        count = 1 + level // 25
    return [
        {"type": "card", "quality": quality, "count": count},
        {"type": "gold", "amount": 50 + level * 20},
    ]


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
        ("wooden", "木质宝箱", 5, [20, 50], {"common": [2, 4]}, [0, 0], 5),
        ("silver", "白银宝箱", 30, [50, 120], {"common": [4, 8], "rare": [0, 1]}, [0, 1], 10),
        ("golden", "黄金宝箱", 120, [100, 250], {"common": [6, 10], "rare": [1, 2]}, [1, 3], 20),
        ("platinum", "铂金宝箱", 240, [200, 500], {"rare": [2, 4], "epic": [0, 1]}, [2, 5], 30),
        ("diamond", "钻石宝箱", 480, [400, 800], {"rare": [4, 6], "epic": [1, 2]}, [5, 10], 50),
        ("epic", "史诗宝箱", 720, [600, 1200], {"epic": [2, 4], "legendary": [0, 1]}, [8, 15], 80),
        ("legendary", "传奇宝箱", 1440, [1000, 2000], {"epic": [3, 5], "legendary": [1, 2]}, [15, 30], 100),
    ]
    chests = []
    for cid, name, minutes, gold, cards, diamond, instant_diamond in tiers:
        chests.append({
            "chestId": cid,
            "name": name,
            "unlockMinutes": minutes,
            "adReduceMinutes": 30,
            "instantOpenDiamond": instant_diamond,
            "rewards": {
                "gold": {"min": gold[0], "max": gold[1]},
                "diamond": {"min": diamond[0], "max": diamond[1]},
                "cards": {q: {"min": v[0], "max": v[1]} for q, v in cards.items()},
            },
        })
    return {
        "version": "1.0.0",
        "description": "宝箱品质与开启时间、产出配置",
        "slotCount": 4,
        "chests": chests,
    }


def gen_account_level():
    levels = []
    total_exp = 0
    for lv in range(1, 100):
        req = exp_for_level(lv)
        total_exp += req
        levels.append({
            "level": lv,
            "expRequired": req,
            "cumulativeExp": total_exp,
            "rewards": level_reward(lv),
        })
    return {
        "version": "1.0.0",
        "description": "账号英雄等级 1-100：经验曲线与升级奖励",
        "levelMax": 100,
        "defaultLevel": 1,
        "expFormula": "round(18 + level * 3 + level^1.42 * 2.2)",
        "expSource": "battle",
        "totalExpToMax": total_exp,
        "estimatedMatches": round(total_exp / 42),
        "levels": levels,
    }


if __name__ == "__main__":
    for name, data in [
        ("arena.json", gen_arena()),
        ("chest.json", gen_chest()),
        ("accountLevel.json", gen_account_level()),
    ]:
        path = ROOT / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")
