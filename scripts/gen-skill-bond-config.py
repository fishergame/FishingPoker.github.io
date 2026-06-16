#!/usr/bin/env python3
"""Generate skill.json, bond.json, heroBattle.json, docs/SKILL_SYSTEM.md (v3 unified)"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_skill_system_doc import gen_unified_skill_md  # noqa: E402

STAT_GROWTH = 1.15
FIRE_RATE_GROWTH = 1.02
PROJECTILE_SPEED_GROWTH = 1.03
SPECIAL_SKILL_MAX = 5
SPECIAL_SCALING_PER_LEVEL = 0.08
SKILL_UPGRADE_FRAGMENTS = [5, 8, 12, 18]  # 特技 L1→2 … L4→5

FACTIONS = ["wei", "shu", "wu", "qun"]
FACTION_CN = {"wei": "魏", "shu": "蜀", "wu": "吴", "qun": "群雄"}

CATEGORY_CN = {
    "attack": "攻击",
    "defense": "防御",
    "supply": "补给",
    "speed": "加速",
}

QUALITY_CN = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}
QUALITY_SPECIAL_SLOT = {
    "common": None,
    "rare": "rare",
    "epic": "epic",
    "legendary": "legendary",
}
QUALITY_POWER = {"common": 0.85, "rare": 1.0, "epic": 1.12, "legendary": 1.25}
SKILL_FRAG_Q_MULT = {"common": 1.0, "rare": 1.5, "epic": 2.5, "legendary": 4.0}

# 英雄 → 技能倾向、弹道表现（取消远近战战斗逻辑，仅表现）
HERO_PROFILE: dict[str, dict] = {
    "dragon_knight": {"category": "attack", "projectile": "arc", "weapon": "龙息火球，高抛弧线落点单格"},
    "demon_lord": {"category": "attack", "projectile": "arc", "weapon": "冰锥术，抛物线冻结打击"},
    "archmage": {"category": "attack", "projectile": "arc", "weapon": "雷球高抛，落点范围电弧"},
    "ranger": {"category": "attack", "projectile": "arc", "weapon": "荆棘箭雨，弧线覆盖单格"},
    "royal_knight": {"category": "defense", "projectile": "flat", "weapon": "圣盾光波，平直盾击"},
    "druid": {"category": "defense", "projectile": "flat", "weapon": "自然屏障，平直藤蔓盾"},
    "lich_queen": {"category": "attack", "projectile": "arc", "weapon": "幽魂炮，高抛灵魂弹"},
    "blademaster": {"category": "attack", "projectile": "flat", "weapon": "影刃直线突刺"},
    "frost_dragon": {"category": "attack", "projectile": "arc", "weapon": "巨锤冰陨，高空重砸"},
    "crusher": {"category": "attack", "projectile": "arc", "weapon": "破城锤，高抛砸击单格"},
    "helicopter": {"category": "attack", "projectile": "flat", "weapon": "机炮连射，平直子弹"},
    "dread_knight": {"category": "attack", "projectile": "flat", "weapon": "巨斧直线劈砍"},
    "warlord": {"category": "defense", "projectile": "flat", "weapon": "双头咆哮盾墙，平直冲击波"},
    "panda_monk": {"category": "attack", "projectile": "arc", "weapon": "炸药包高抛，落地爆炸"},
    "shaman": {"category": "supply", "projectile": "flat", "weapon": "治疗花粉，平直飘向友军"},
    "gargoyle": {"category": "defense", "projectile": "flat", "weapon": "石肤护壁，平直岩盾"},
    "skeleton_giant": {"category": "defense", "projectile": "flat", "weapon": "巨石屏障，平直岩块"},
    "sniper": {"category": "attack", "projectile": "flat", "weapon": "狙击弹，极快平直弹道"},
    "catapult_tower": {"category": "attack", "projectile": "arc", "weapon": "石弹高抛，经典抛物线"},
    "catapult": {"category": "attack", "projectile": "arc", "weapon": "自爆蜘蛛高抛投掷"},
    "cavalry": {"category": "attack", "projectile": "flat", "weapon": "骑枪冲锋，平直突刺"},
    "wyrmling": {"category": "attack", "projectile": "arc", "weapon": "幼龙火球，小抛物线"},
    "ballista": {"category": "attack", "projectile": "arc", "weapon": "弩炮重矢，高抛穿透"},
    "necromancer": {"category": "attack", "projectile": "arc", "weapon": "亡灵弹，弧线触发复活格"},
    "spear_orc": {"category": "attack", "projectile": "flat", "weapon": "鱼叉直线投掷"},
    "wolf_rider": {"category": "attack", "projectile": "flat", "weapon": "利爪直线扑击"},
    "skeleton_knight": {"category": "attack", "projectile": "flat", "weapon": "骨刃直线斩"},
    "archer": {"category": "attack", "projectile": "flat", "weapon": "魔法箭平直射击"},
    "infantry": {"category": "defense", "projectile": "flat", "weapon": "塔盾格挡，平直盾击"},
    "arrow_tower": {"category": "attack", "projectile": "arc", "weapon": "高射炮弹，高空抛物线"},
    "bear_warrior": {"category": "defense", "projectile": "flat", "weapon": "重锤平直挥击"},
    "skeleton_warrior": {"category": "defense", "projectile": "flat", "weapon": "刀盾平直格挡"},
    "goblin": {"category": "speed", "projectile": "flat", "weapon": "短矛轻快直线戳刺"},
    "blacksmith": {"category": "defense", "projectile": "flat", "weapon": "长枪平直突刺"},
    "militia": {"category": "attack", "projectile": "flat", "weapon": "短剑平直快攻"},
    "bone_archer": {"category": "attack", "projectile": "flat", "weapon": "火枪铅弹平直射击"},
    "gold_mine": {"category": "supply", "projectile": "flat", "weapon": "矿车补给，无攻击弹道"},
}


def load_heroes() -> list[dict]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


def profile_for(hero: dict) -> dict:
    hid = hero["id"]
    if hid in HERO_PROFILE:
        return HERO_PROFILE[hid]
    if hero["type"] == "resource":
        return {"category": "supply", "projectile": "flat", "weapon": "资源补给"}
    if hero["type"] == "building":
        return {"category": "attack", "projectile": "arc", "weapon": "建筑高抛炮击"}
    return {"category": "attack", "projectile": "flat", "weapon": "平直射击"}


def qscale(quality: str, base: float) -> float:
    return round(base * QUALITY_POWER.get(quality, 1.0), 3)


def skill_value_at_level(base: float, skill_level: int) -> float:
    return round(base * (1 + SPECIAL_SCALING_PER_LEVEL * (skill_level - 1)), 3)


def build_normal_skill(hero: dict, prof: dict) -> dict:
    q = hero["quality"]
    cat = prof["category"]
    hid = hero["id"]
    p = QUALITY_POWER[q]

    if cat == "attack":
        name, desc = "平直点射", "单点平直弹道，对目标兵卡造成基础攻击伤害（无抛物线）"
        vfx = "基础弹药**平直**射向单格目标；无高抛"
        effects = [{"type": "atkPct", "value": qscale(q, 0.05)}]
        attack_mode = "single"
    elif cat == "defense":
        name = "铁壁"
        desc = "仅抵挡平直弹道伤害；无法抵挡特技高抛攻击"
        vfx = f"{prof['weapon']}；护体光效贴身，**平直**格挡反馈"
        effects = [
            {
                "type": "damageReductionPct",
                "value": qscale(q, 0.06),
                "blocksTrajectory": ["flat"],
            }
        ]
        attack_mode = "self"
    elif cat == "supply":
        name, desc = "应急包扎", "主动为自身恢复少量生命（约20%最大生命）"
        vfx = "绿色光粒平直飞向自身；**补给粒子**"
        effects = [{"type": "healPct", "value": qscale(q, 0.20)}]
        attack_mode = "self"
    else:
        name, desc = "迅捷装填", "提升发射间隔效率（攻速补给），弹道更快出手"
        vfx = f"{prof['weapon']}；出手前摇缩短，弹道仍**平直**"
        effects = [{"type": "fireRatePct", "value": qscale(q, 0.08)}]
        attack_mode = "self"

    if hero["type"] == "resource":
        name, desc = "矿脉", "翻开获得额外金币，无战斗攻击"
        vfx = "金币从矿口平直弹出"
        effects = [{"type": "deployGold", "value": int(10 * p)}]
        attack_mode = "none"

    return {
        "skillId": f"skill_{hid}_normal",
        "heroId": hid,
        "slot": "normal",
        "skillKind": "normal",
        "category": cat,
        "categoryLabel": CATEGORY_CN[cat],
        "name": f"{hero['name']}·{name}",
        "description": desc,
        "visualDescription": vfx,
        "projectileStyle": prof["projectile"],
        "attackMode": attack_mode,
        "unlockLevel": 1,
        "upgradeable": False,
        "maxLevel": 1,
        "effects": effects,
        "tags": [q, cat, hero["type"]],
    }


def build_special_skill(hero: dict, prof: dict, slot: str) -> dict:
    q = hero["quality"]
    cat = prof["category"]
    hid = hero["id"]
    tier_power = {"rare": 1.0, "epic": 1.35, "legendary": 1.75}[slot]

    if cat == "attack":
        if slot == "rare":
            name, desc = "双联点射", "每次攻击额外命中1个相邻敌方兵卡（多目标伤害）"
            vfx = f"{prof['weapon']}；主目标+邻格溅射，{'高抛' if prof['projectile']=='arc' else '平直'}双道"
            effects = [{"type": "extraTargets", "value": 1}, {"type": "splashPct", "value": qscale(q, 0.15 * tier_power)}]
            attack_mode = "multi"
        elif slot == "epic":
            name, desc = "连锁穿透", "攻击可连锁2个敌方兵卡，造成递减伤害"
            vfx = f"{'高抛爆炸链' if prof['projectile']=='arc' else '平直穿透'}，依次命中2格"
            effects = [{"type": "chainTargets", "value": 2}, {"type": "atkPct", "value": qscale(q, 0.12 * tier_power)}]
            attack_mode = "chain"
        else:
            if hid == "necromancer" or "skeleton" in hid or hid == "lich_queen":
                name, desc = "亡灵收割", "击杀敌方兵卡后，翻开相邻已阵亡格并召唤亡灵单位"
                vfx = "幽绿弧线落下，阵亡格复燃翻出亡灵牌"
                effects = [{"type": "reviveAdjacentDead", "value": 1}, {"type": "executeThreshold", "value": 0.25}]
            else:
                name, desc = "高空重击", "高抛弹道，对单格造成巨额伤害并概率直接击杀低血兵卡；可穿透普通铁壁"
                vfx = f"{prof['weapon']}；**强抛物线**高空砸击，落地重击特效"
                effects = [
                    {"type": "atkPct", "value": qscale(q, 0.25 * tier_power)},
                    {"type": "executeThreshold", "value": 0.30},
                    {"type": "projectileArc", "value": 1},
                ]
            attack_mode = "single_kill"

    elif cat == "defense":
        if slot == "rare":
            name, desc = "单格护墙", "在自身前方生成护墙，阻挡单格敌方兵卡前进1回合；附加平直减伤"
            vfx = "石墙从地面平直升起，挡单格"
            effects = [
                {"type": "wallTiles", "value": 1},
                {
                    "type": "damageReductionPct",
                    "value": qscale(q, 0.10 * tier_power),
                    "blocksTrajectory": ["flat"],
                },
            ]
        elif slot == "epic":
            name, desc = "三格盾带", "护墙扩展至三格，范围内友军减伤（可挡平直与高抛）"
            vfx = "弧形盾带展开，覆盖三格"
            effects = [
                {"type": "wallTiles", "value": 3},
                {
                    "type": "allyDamageReductionPct",
                    "value": qscale(q, 0.12 * tier_power),
                    "blocksTrajectory": ["flat", "arc"],
                },
            ]
        else:
            name, desc = "全局圣域", "短时全队减伤（可挡平直与高抛），并阻挡敌方全局突进一次"
            vfx = "全场地坪升起光幕护罩，全局防护"
            effects = [
                {
                    "type": "globalDamageReductionPct",
                    "value": qscale(q, 0.15 * tier_power),
                    "blocksTrajectory": ["flat", "arc"],
                },
                {"type": "blockRush", "value": 1},
            ]
        attack_mode = "area_defense"

    elif cat == "supply":
        if slot == "rare":
            name, desc = "战地包扎", "为血量最低友军恢复30%生命"
            vfx = "治疗光带平直飞向友军"
            effects = [{"type": "healAllyPct", "value": qscale(q, 0.30 * tier_power)}]
        elif slot == "epic":
            name, desc = "群体复苏", "范围友军恢复50%生命"
            vfx = "绿色光环扩散，范围内友军回血"
            effects = [{"type": "healAreaPct", "value": qscale(q, 0.50 * tier_power)}]
        else:
            name, desc = "满血圣疗", "将目标友军恢复至满血，并净化一次减益"
            vfx = "金色光柱从天而降，满血恢复"
            effects = [{"type": "healFull", "value": 1}, {"type": "cleanse", "value": 1}]
        attack_mode = "heal"

    else:  # speed
        if slot == "rare":
            name, desc = "速射补给", "提升自身发射速度（缩短攻击间隔）15%"
            vfx = "装填火花，弹道连发更密"
            effects = [{"type": "fireRatePct", "value": qscale(q, 0.15 * tier_power)}]
        elif slot == "epic":
            name, desc = "弹速增压", "提升弹道飞行速度，并小幅提升攻速"
            vfx = "弹道拖尾加速，平直/高抛均更快到达"
            effects = [{"type": "projectileSpeedPct", "value": qscale(q, 0.20 * tier_power)}, {"type": "fireRatePct", "value": qscale(q, 0.10 * tier_power)}]
        else:
            name, desc = "狂热号令", "全队攻速提升，并翻开相邻1格"
            vfx = "战鼓音波扩散，相邻格翻开预览"
            effects = [{"type": "teamFireRatePct", "value": qscale(q, 0.18 * tier_power)}, {"type": "revealAdjacent", "value": 1}]
        attack_mode = "buff"

    base_effects = effects
    level_curve = []
    for lv in range(1, SPECIAL_SKILL_MAX + 1):
        scaled = []
        for e in base_effects:
            if e["type"] in ("extraTargets", "chainTargets", "wallTiles", "reviveAdjacentDead", "revealAdjacent", "healFull", "cleanse", "blockRush", "projectileArc"):
                scaled.append({**e})
            else:
                scaled.append({**e, "value": skill_value_at_level(e["value"], lv)})
        level_curve.append({"skillLevel": lv, "effects": scaled})

    skill = {
        "skillId": f"skill_{hid}_{slot}",
        "heroId": hid,
        "slot": slot,
        "skillKind": "special",
        "category": cat,
        "categoryLabel": CATEGORY_CN[cat],
        "name": f"{hero['name']}·{name}",
        "description": desc,
        "visualDescription": vfx,
        "projectileStyle": "arc" if slot == "legendary" and cat == "attack" else prof["projectile"],
        "attackMode": attack_mode,
        "unlockLevel": 1,
        "upgradeable": True,
        "maxLevel": SPECIAL_SKILL_MAX,
        "scalingPerSkillLevel": SPECIAL_SCALING_PER_LEVEL,
        "effects": level_curve[0]["effects"],
        "levelCurve": level_curve,
        "tags": [q, slot, cat, hero["type"]],
    }
    if cat == "attack" and any(e.get("type") == "projectileArc" for e in base_effects):
        skill["attackTrajectory"] = "arc"
        skill["bypassesNormalDefense"] = True
    return skill


def derive_combat_stats(hero: dict) -> dict:
    """旧 attackSpeed 作 fireRate；新 attackSpeed = 弹道速度。"""
    old_spd = hero.get("attackSpeed") or 1.0
    prof = profile_for(hero)
    if hero["type"] == "resource":
        return {"fireRateL1": None, "attackSpeedL1": None, "attackIntervalL1": None}
    if prof["projectile"] == "arc":
        projectile = min(10, max(4.0, old_spd + 2.5))
    else:
        projectile = min(10, max(5.0, old_spd + 3.0))
    fire_rate = round(old_spd, 2)
    interval = round(2.2 / fire_rate, 2) if fire_rate else None
    return {
        "fireRateL1": fire_rate,
        "attackSpeedL1": round(projectile, 2),
        "attackIntervalL1": interval,
        "projectileStyle": prof["projectile"],
        "weaponVfx": prof["weapon"],
    }


def stat_at_level(l1: float, level: int, growth: float = STAT_GROWTH) -> int:
    if l1 is None:
        return None
    return round(l1 * (growth ** (level - 1)))


def gen_skills(heroes: list[dict]) -> list[dict]:
    skills = []
    for h in heroes:
        prof = profile_for(h)
        skills.append(build_normal_skill(h, prof))
        slot = QUALITY_SPECIAL_SLOT.get(h["quality"])
        if slot:
            skills.append(build_special_skill(h, prof, slot))
    return skills


def skill_upgrade_table() -> dict:
    rows = []
    for from_lv, frag in enumerate(SKILL_UPGRADE_FRAGMENTS, start=1):
        row = {"fromLevel": from_lv, "toLevel": from_lv + 1, "baseFragments": frag, "byQuality": {}}
        for q, mult in SKILL_FRAG_Q_MULT.items():
            row["byQuality"][q] = max(1, round(frag * mult))
        rows.append(row)
    return {
        "specialSkillMaxLevel": SPECIAL_SKILL_MAX,
        "normalSkillUpgradeable": False,
        "scalingPerLevel": SPECIAL_SCALING_PER_LEVEL,
        "formula": "effect(L) = base * (1 + 0.08*(L-1))",
        "fragmentCost": rows,
        "goldCostFormula": "round(heroGoldNeed[level-1] * 0.15)  // 特技升级金币≈同级英雄升级的15%",
    }


def assign_faction(heroes: list[dict]) -> dict[str, str]:
    mapping = {}
    factions_cycle = FACTIONS * 20
    idx = 0
    for h in sorted(heroes, key=lambda x: x["id"]):
        if h["id"] == "gold_mine":
            continue
        mapping[h["id"]] = factions_cycle[idx % len(FACTIONS)]
        idx += 1
    return mapping


def gen_hero_battle(heroes: list[dict], skills: list[dict]) -> dict:
    factions = assign_faction(heroes)
    by_hero: dict[str, list] = {}
    for s in skills:
        by_hero.setdefault(s["heroId"], []).append(s)

    entries = {}
    for h in heroes:
        hid = h["id"]
        hs = by_hero.get(hid, [])
        by_slot = {s["slot"]: s["skillId"] for s in hs}
        prof = profile_for(h)
        combat = derive_combat_stats(h)
        q = h["quality"]
        skill_map = {"normal": by_slot.get("normal")}
        special = QUALITY_SPECIAL_SLOT.get(q)
        if special:
            skill_map[special] = by_slot.get(special)

        entries[hid] = {
            "heroId": hid,
            "name": h["name"],
            "quality": q,
            "qualityLabel": QUALITY_CN[q],
            "faction": factions.get(hid),
            "category": prof["category"],
            "categoryLabel": CATEGORY_CN[prof["category"]],
            "bondEligible": hid != "gold_mine",
            "combatStats": {
                **combat,
                "formulas": {
                    "attack": f"round(attackL1 * {STAT_GROWTH}^(heroLevel-1))",
                    "unitHp": f"round(unitHpL1 * {STAT_GROWTH}^(heroLevel-1))",
                    "buildingHp": f"round(buildingHpL1 * {STAT_GROWTH}^(heroLevel-1))",
                    "fireRate": f"round(fireRateL1 * {FIRE_RATE_GROWTH}^(heroLevel-1), 2)",
                    "attackSpeed": f"round(attackSpeedL1 * {PROJECTILE_SPEED_GROWTH}^(heroLevel-1), 2)  // 弹道速度",
                    "attackInterval": "2.2 / fireRate",
                },
                "attackL1": h.get("attack"),
                "unitHpL1": h.get("unitHp"),
                "buildingHpL1": h.get("buildingHp"),
                "samples": {
                    "L1": {
                        "attack": stat_at_level(h.get("attack"), 1),
                        "unitHp": stat_at_level(h.get("unitHp"), 1),
                        "fireRate": combat.get("fireRateL1"),
                        "attackSpeed": combat.get("attackSpeedL1"),
                    },
                    "L15": {
                        "attack": stat_at_level(h.get("attack"), 15),
                        "unitHp": stat_at_level(h.get("unitHp"), 15),
                        "fireRate": round((combat.get("fireRateL1") or 0) * (FIRE_RATE_GROWTH ** 14), 2) if combat.get("fireRateL1") else None,
                        "attackSpeed": round((combat.get("attackSpeedL1") or 0) * (PROJECTILE_SPEED_GROWTH ** 14), 2) if combat.get("attackSpeedL1") else None,
                    },
                    "L30": {
                        "attack": stat_at_level(h.get("attack"), 30),
                        "unitHp": stat_at_level(h.get("unitHp"), 30),
                        "fireRate": round((combat.get("fireRateL1") or 0) * (FIRE_RATE_GROWTH ** 29), 2) if combat.get("fireRateL1") else None,
                        "attackSpeed": round((combat.get("attackSpeedL1") or 0) * (PROJECTILE_SPEED_GROWTH ** 29), 2) if combat.get("attackSpeedL1") else None,
                    },
                },
            },
            "skills": skill_map,
            "skillSlotsByQuality": {
                "common": ["normal"],
                "rare": ["normal", "rare"],
                "epic": ["normal", "epic"],
                "legendary": ["normal", "legendary"],
            },
        }
    return {
        "version": "3.0.0",
        "description": "英雄战斗元数据 v3：品质决定特技槽；普通技不可升级，特技5级",
        "rules": {
            "noMeleeRangedLogic": True,
            "attackSpeedMeans": "弹道飞行速度（表现+命中时机）",
            "fireRateMeans": "发射频率（攻击间隔=2.2/fireRate）",
            "projectileStyle": "flat=平直射击 arc=高抛重击",
        },
        "heroes": entries,
    }


BOND_CATEGORY = [
    {"count": 2, "effects": [{"type": "atkPct", "value": 0.05}]},
    {"count": 4, "effects": [{"type": "atkPct", "value": 0.08}, {"type": "fireRatePct", "value": 0.05}]},
    {"count": 6, "effects": [{"type": "atkPct", "value": 0.12}, {"type": "healPct", "value": 0.05}]},
]


def gen_bond() -> dict:
    bonds = []
    for fid in FACTIONS:
        bonds.append({
            "bondId": f"faction_{fid}",
            "type": "faction",
            "name": FACTION_CN[fid],
            "faction": fid,
            "tiers": [
                {"count": 2, "effects": [{"type": "atkPct", "value": 0.05}]},
                {"count": 4, "effects": [{"type": "atkPct", "value": 0.08}, {"type": "unitHpPct", "value": 0.05}]},
                {"count": 6, "effects": [{"type": "atkPct", "value": 0.12}, {"type": "unitHpPct", "value": 0.08}]},
            ],
        })
    for cat, label in CATEGORY_CN.items():
        bonds.append({
            "bondId": f"category_{cat}",
            "type": "skillCategory",
            "name": f"{label}型",
            "category": cat,
            "tiers": BOND_CATEGORY,
        })
    return {
        "version": "2.0.0",
        "description": "羁绊：4阵营 + 4技能定位型；近战/远程羁绊已移除",
        "rules": {
            "deckSize": 8,
            "excludeHeroIds": ["gold_mine"],
            "tierActivation": "atCount4ActivateTier2And4",
            "maxActiveFactionBonds": 1,
            "maxActiveCategoryBonds": 1,
        },
        "bonds": bonds,
    }


if __name__ == "__main__":
    heroes = load_heroes()
    skills = gen_skills(heroes)
    upgrade = skill_upgrade_table()
    hero_battle = gen_hero_battle(heroes, skills)
    bond = gen_bond()

    (ROOT / "skill.json").write_text(
        json.dumps(
            {
                "version": "3.0.0",
                "description": "技能 v3：普通技+品质特技；攻击/防御/补给/加速",
                "categories": CATEGORY_CN,
                "combatRules": {
                    "trajectory": {
                        "flat": "平直弹道（普通攻击、双联/连锁特技）",
                        "arc": "高抛弹道（传奇攻击特技「高空重击」等）",
                        "defenseRule": "普通防御 blocksTrajectory 仅含 flat；史诗及以上特技防御含 flat+arc",
                    }
                },
                "skillUpgrade": upgrade,
                "skillCount": len(skills),
                "skills": skills,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ROOT / "heroBattle.json").write_text(
        json.dumps(hero_battle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "bond.json").write_text(json.dumps(bond, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs" / "SKILL_SYSTEM.md").write_text(
        gen_unified_skill_md(skills, hero_battle, upgrade, bond, len(skills)) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(skills)} skills, {len(hero_battle['heroes'])} heroes, docs/SKILL_SYSTEM.md (v3)")
