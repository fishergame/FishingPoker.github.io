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

SPECIAL_UNLOCK_HERO_LEVEL = {"rare": 5, "epic": 10, "legendary": 20}
SKILL_DIAMOND_PREMIUM = {"rare": 2.0, "epic": 2.5, "legendary": 3.0}
GOLD_TO_DIAMOND_RATE = 0.045

FACTIONS = ["human", "beast", "undead", "mechanical"]
FACTION_CN = {"human": "人族", "beast": "兽族", "undead": "亡灵", "mechanical": "机械"}

FACTION_COUNTER_BONUS = 0.10
FACTION_COUNTER_CYCLE = {
    "human": "mechanical",
    "mechanical": "beast",
    "beast": "undead",
    "undead": "human",
}
FACTION_COUNTER_LABEL = {
    "human": "人族 → 机械（含建筑）",
    "mechanical": "机械 → 兽族",
    "beast": "兽族 → 亡灵",
    "undead": "亡灵 → 人族",
}

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

# 英雄 → 种族、技能定位、弹道表现
HERO_FACTION: dict[str, str] = {
    # 人族
    "royal_knight": "human", "druid": "human", "infantry": "human", "blacksmith": "human",
    "militia": "human", "bone_archer": "human", "archer": "human", "archmage": "human",
    "blademaster": "human",
    # 兽族
    "warlord": "beast", "dread_knight": "beast", "wolf_rider": "beast", "spear_orc": "beast",
    "goblin": "beast", "wyrmling": "beast", "dragon_knight": "beast", "bear_warrior": "beast",
    "cavalry": "beast",
    # 亡灵
    "lich_queen": "undead", "necromancer": "undead", "skeleton_giant": "undead",
    "skeleton_warrior": "undead", "skeleton_knight": "undead", "frost_dragon": "undead",
    "crusher": "undead", "catapult": "undead", "demon_lord": "undead",
    # 机械
    "helicopter": "mechanical", "catapult_tower": "mechanical", "arrow_tower": "mechanical",
    "ballista": "mechanical", "gold_mine": "mechanical", "panda_monk": "mechanical",
    "sniper": "mechanical", "gargoyle": "mechanical", "ranger": "mechanical",
    "shaman": "human",
}

# 英雄 → 技能倾向、弹道表现（定位：攻击15 / 防御9 / 补给6 / 加速6）
HERO_PROFILE: dict[str, dict] = {
    "dragon_knight": {"category": "attack", "projectile": "arc", "weapon": "龙息火球，高抛弧线落点单格"},
    "demon_lord": {"category": "attack", "projectile": "arc", "weapon": "冰锥术，抛物线冻结打击"},
    "archmage": {"category": "attack", "projectile": "arc", "weapon": "雷球高抛，落点范围电弧"},
    "ranger": {"category": "supply", "projectile": "flat", "weapon": "荆棘花粉，平直洒向友军"},
    "royal_knight": {"category": "defense", "projectile": "flat", "weapon": "圣盾光波，平直盾击"},
    "druid": {"category": "supply", "projectile": "flat", "weapon": "自然花粉，平直治疗波"},
    "lich_queen": {"category": "attack", "projectile": "arc", "weapon": "幽魂炮，高抛灵魂弹"},
    "blademaster": {"category": "attack", "projectile": "flat", "weapon": "影刃直线突刺"},
    "frost_dragon": {"category": "attack", "projectile": "arc", "weapon": "巨锤冰陨，高空重砸"},
    "crusher": {"category": "attack", "projectile": "arc", "weapon": "破城锤，高抛砸击单格"},
    "helicopter": {"category": "speed", "projectile": "flat", "weapon": "机炮连射，平直子弹"},
    "dread_knight": {"category": "attack", "projectile": "flat", "weapon": "巨斧直线劈砍"},
    "warlord": {"category": "defense", "projectile": "flat", "weapon": "双头咆哮盾墙，平直冲击波"},
    "panda_monk": {"category": "attack", "projectile": "arc", "weapon": "炸药包高抛，落地爆炸"},
    "shaman": {"category": "supply", "projectile": "flat", "weapon": "治疗花粉，平直飘向友军"},
    "gargoyle": {"category": "defense", "projectile": "flat", "weapon": "石肤护壁，平直岩盾"},
    "skeleton_giant": {"category": "defense", "projectile": "flat", "weapon": "巨石屏障，平直岩块"},
    "sniper": {"category": "attack", "projectile": "flat", "weapon": "狙击弹，极快平直弹道"},
    "catapult_tower": {"category": "defense", "projectile": "arc", "weapon": "石弹高抛，经典抛物线"},
    "catapult": {"category": "attack", "projectile": "arc", "weapon": "自爆蜘蛛高抛投掷"},
    "cavalry": {"category": "speed", "projectile": "flat", "weapon": "骑枪冲锋，平直突刺"},
    "wyrmling": {"category": "attack", "projectile": "arc", "weapon": "幼龙火球，小抛物线"},
    "ballista": {"category": "defense", "projectile": "arc", "weapon": "弩炮护墙，高抛拦截弹道"},
    "necromancer": {"category": "supply", "projectile": "arc", "weapon": "亡灵弹，弧线触发复活格"},
    "spear_orc": {"category": "attack", "projectile": "flat", "weapon": "鱼叉直线投掷"},
    "wolf_rider": {"category": "speed", "projectile": "flat", "weapon": "利爪直线扑击"},
    "skeleton_knight": {"category": "speed", "projectile": "flat", "weapon": "骨刃直线斩"},
    "archer": {"category": "attack", "projectile": "flat", "weapon": "魔法箭平直射击"},
    "infantry": {"category": "defense", "projectile": "flat", "weapon": "塔盾格挡，平直盾击"},
    "arrow_tower": {"category": "defense", "projectile": "arc", "weapon": "高射炮弹，高空抛物线"},
    "bear_warrior": {"category": "defense", "projectile": "flat", "weapon": "重锤平直挥击"},
    "skeleton_warrior": {"category": "defense", "projectile": "flat", "weapon": "刀盾平直格挡"},
    "goblin": {"category": "speed", "projectile": "flat", "weapon": "短矛轻快直线戳刺"},
    "blacksmith": {"category": "supply", "projectile": "flat", "weapon": "锻造火花，平直补给友军"},
    "militia": {"category": "speed", "projectile": "flat", "weapon": "短剑平直快攻"},
    "bone_archer": {"category": "supply", "projectile": "flat", "weapon": "急救包，平直飞向受伤友军"},
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


def hero_atk_l1(hero: dict) -> int:
    return int(hero.get("attack") or 0)


def hero_hp_l1(hero: dict) -> int:
    return int(hero.get("unitHp") or hero.get("buildingHp") or 0)


def pct_label(value: float) -> str:
    return f"{int(round(value * 100))}%"


def effect_val(effects: list[dict], etype: str, default=0.0) -> float:
    for e in effects:
        if e.get("type") == etype:
            return float(e.get("value") or 0)
    return default


def enrich_special_description(
    hero: dict,
    cat: str,
    slot: str,
    base_desc: str,
    effects: list[dict],
    prof: dict,
    skill_name: str,
) -> str:
    """为稀有/史诗/传奇特技补充基于 L1 属性的具体数值说明。"""
    slot_cn = {"rare": "稀有", "epic": "史诗", "legendary": "传奇"}[slot]
    atk = hero_atk_l1(hero)
    hp = hero_hp_l1(hero)
    parts = [base_desc.rstrip("。")]

    if cat == "attack":
        if slot == "rare":
            splash = effect_val(effects, "splashPct")
            splash_dmg = round(atk * splash) if atk else 0
            parts.append(
                f"【{slot_cn}】主目标造成100%攻击力"
                f"{'（约' + str(atk) + '点）' if atk else ''}；"
                f"邻格溅射{pct_label(splash)}攻击力"
                f"{'（约' + str(splash_dmg) + '点）' if atk else ''}"
            )
        elif slot == "epic":
            atk_b = effect_val(effects, "atkPct")
            boosted = round(atk * (1 + atk_b)) if atk else 0
            parts.append(
                f"【{slot_cn}】单次伤害提升至{pct_label(1 + atk_b)}攻击力"
                f"{'（' + str(atk) + '→' + str(boosted) + '点）' if atk else ''}，连锁命中2格"
            )
        else:
            if "亡灵收割" in skill_name:
                exec_t = effect_val(effects, "executeThreshold", 0.25)
                parts.append(
                    f"【{slot_cn}】依托基础攻击"
                    f"{'（约' + str(atk) + '点/击）' if atk else ''}；"
                    f"击杀后复燃相邻阵亡格；目标≤{pct_label(exec_t)}生命时更易斩杀"
                )
            else:
                atk_b = effect_val(effects, "atkPct")
                boosted = round(atk * (1 + atk_b)) if atk else 0
                exec_t = effect_val(effects, "executeThreshold", 0.30)
                parts.append(
                    f"【{slot_cn}】造成{pct_label(1 + atk_b)}攻击力伤害"
                    f"{'（' + str(atk) + '→' + str(boosted) + '点）' if atk else ''}；"
                    f"目标生命≤{pct_label(exec_t)}时触发斩杀加成"
                )
    elif cat == "defense":
        if slot == "rare":
            dr = effect_val(effects, "damageReductionPct")
            parts.append(
                f"【{slot_cn}】附加减伤{pct_label(dr)}"
                f"（例：受击100点→实际约{round(100 * (1 - dr))}点）"
            )
        elif slot == "epic":
            dr = effect_val(effects, "allyDamageReductionPct")
            parts.append(
                f"【{slot_cn}】范围友军减伤{pct_label(dr)}"
                f"（例：受击100点→约{round(100 * (1 - dr))}点）"
            )
        else:
            dr = effect_val(effects, "globalDamageReductionPct")
            parts.append(
                f"【{slot_cn}】全队减伤{pct_label(dr)}"
                f"（例：受击100点→约{round(100 * (1 - dr))}点）"
            )
    elif cat == "supply":
        if slot == "rare":
            heal = effect_val(effects, "healAllyPct")
            heal_amt = round(hp * heal) if hp else 0
            parts.append(
                f"【{slot_cn}】为友军恢复{pct_label(heal)}最大生命"
                f"{'（例：HP' + str(hp) + '→约+' + str(heal_amt) + '点）' if hp else ''}"
            )
        elif slot == "epic":
            heal = effect_val(effects, "healAreaPct")
            heal_amt = round(hp * heal) if hp else 0
            parts.append(
                f"【{slot_cn}】范围友军恢复{pct_label(heal)}生命"
                f"{'（例：HP' + str(hp) + '→约+' + str(heal_amt) + '点）' if hp else ''}"
            )
        else:
            parts.append(
                f"【{slot_cn}】将目标恢复至满血"
                f"{'（例：HP' + str(hp) + '拉满）' if hp else ''}，并净化减益"
            )
    else:  # speed
        fire_rate = float(hero.get("attackSpeed") or 1.0)
        interval = round(2.2 / fire_rate, 2) if fire_rate else None
        if slot == "rare":
            fr = effect_val(effects, "fireRatePct")
            new_iv = round(interval / (1 + fr), 2) if interval else None
            parts.append(
                f"【{slot_cn}】发射频率+{pct_label(fr)}"
                f"{f'（间隔{interval}s→约{new_iv}s）' if interval and new_iv else ''}"
            )
        elif slot == "epic":
            ps = effect_val(effects, "projectileSpeedPct")
            fr = effect_val(effects, "fireRatePct")
            new_iv = round(interval / (1 + fr), 2) if interval else None
            parts.append(
                f"【{slot_cn}】弹道速度+{pct_label(ps)}、发射频率+{pct_label(fr)}"
                f"{f'（间隔{interval}s→约{new_iv}s）' if interval and new_iv else ''}"
            )
        else:
            fr = effect_val(effects, "teamFireRatePct")
            parts.append(f"【{slot_cn}】全队发射频率+{pct_label(fr)}")

    return "。".join(parts) + "。"


def build_damage_examples(hero: dict, cat: str, slot: str, base_effects: list[dict]) -> dict:
    atk = hero_atk_l1(hero)
    hp = hero_hp_l1(hero)
    rows = []
    for lv in range(1, SPECIAL_SKILL_MAX + 1):
        scaled = []
        for e in base_effects:
            if e["type"] in (
                "extraTargets", "chainTargets", "wallTiles", "reviveAdjacentDead",
                "revealAdjacent", "healFull", "cleanse", "blockRush", "projectileArc",
                "executeThreshold",
            ):
                scaled.append({**e})
            else:
                scaled.append({**e, "value": skill_value_at_level(e["value"], lv)})
        row = {"skillLevel": lv, "effects": scaled}
        if cat == "attack" and atk:
            atk_b = effect_val(scaled, "atkPct")
            row["attackPerHit"] = round(atk * (1 + atk_b)) if atk_b else atk
            row["splashDamage"] = round(atk * effect_val(scaled, "splashPct"))
        if cat == "supply" and hp:
            row["healAmount"] = round(hp * effect_val(scaled, "healAllyPct", effect_val(scaled, "healAreaPct")))
        rows.append(row)
    return {"heroAttackL1": atk or None, "heroHpL1": hp or None, "levels": rows}


def build_normal_skill(hero: dict, prof: dict) -> dict:
    q = hero["quality"]
    cat = prof["category"]
    hid = hero["id"]
    p = QUALITY_POWER[q]

    if cat == "attack":
        name, desc = "平直点射", "单点平直弹道，对目标兵卡造成基础攻击伤害（无抛物线）"
        if hero_atk_l1(hero):
            desc += f"（100%攻击力，L1约{hero_atk_l1(hero)}点）"
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

    desc = enrich_special_description(hero, cat, slot, desc, base_effects, prof, name)

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
        "unlockLevel": SPECIAL_UNLOCK_HERO_LEVEL[slot],
        "upgradeable": True,
        "maxLevel": SPECIAL_SKILL_MAX,
        "scalingPerSkillLevel": SPECIAL_SCALING_PER_LEVEL,
        "effects": level_curve[0]["effects"],
        "levelCurve": level_curve,
        "damageExamples": build_damage_examples(hero, cat, slot, base_effects),
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


def load_hero_level() -> dict:
    return json.loads((ROOT / "heroLevel.json").read_text(encoding="utf-8"))


def skill_upgrade_table(hero_level: dict) -> dict:
    gold_by_q = hero_level["goldNeedByQuality"]
    diamond_rows = []
    for slot, unlock in SPECIAL_UNLOCK_HERO_LEVEL.items():
        q = slot
        for from_lv in range(1, SPECIAL_SKILL_MAX):
            gold_idx = min(max(0, unlock + from_lv - 2), 29)
            gold_ref = gold_by_q[q][gold_idx]
            premium = SKILL_DIAMOND_PREMIUM[q]
            diamond = max(30, round(gold_ref * GOLD_TO_DIAMOND_RATE * premium))
            diamond_rows.append({
                "slot": slot,
                "fromLevel": from_lv,
                "toLevel": from_lv + 1,
                "diamondCost": diamond,
                "heroGoldReference": gold_ref,
                "heroLevelContext": unlock + from_lv - 1,
            })
    return {
        "specialSkillMaxLevel": SPECIAL_SKILL_MAX,
        "normalSkillUpgradeable": False,
        "scalingPerLevel": SPECIAL_SCALING_PER_LEVEL,
        "formula": "effect(L) = base * (1 + 0.08*(L-1))",
        "currency": "diamond",
        "fragmentCost": None,
        "unlockByHeroLevel": SPECIAL_UNLOCK_HERO_LEVEL,
        "diamondCostFormula": (
            "diamond = round(heroGoldNeed[unlockBase + skillLv - 2] × 0.045 × premium)；"
            "premium: rare×2.0 epic×2.5 legendary×3.0；仅钻石，无碎片"
        ),
        "diamondCost": diamond_rows,
    }


def assign_faction(heroes: list[dict]) -> dict[str, str]:
    mapping = {}
    for h in heroes:
        hid = h["id"]
        if hid in HERO_FACTION:
            mapping[hid] = HERO_FACTION[hid]
        elif h["type"] == "resource":
            mapping[hid] = "mechanical"
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
            "factionLabel": FACTION_CN.get(factions.get(hid), "—"),
            "category": prof["category"],
            "categoryLabel": CATEGORY_CN[prof["category"]],
            "bondEligible": hid != "gold_mine",
            "unitType": h.get("type", "unit"),
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
            "skillUnlock": {
                "rare": SPECIAL_UNLOCK_HERO_LEVEL["rare"],
                "epic": SPECIAL_UNLOCK_HERO_LEVEL["epic"],
                "legendary": SPECIAL_UNLOCK_HERO_LEVEL["legendary"],
                "description": "英雄达到对应等级解锁品质特技；普通技 L1 即拥有",
            },
        }
    return {
        "version": "3.1.0",
        "description": "英雄战斗元数据 v3.1：种族阵营 + 等级解锁特技 + 钻石升级",
        "rules": {
            "noMeleeRangedLogic": True,
            "attackSpeedMeans": "弹道飞行速度（表现+命中时机）",
            "fireRateMeans": "发射频率（攻击间隔=2.2/fireRate）",
            "projectileStyle": "flat=平直射击 arc=高抛重击",
            "skillUnlockByHeroLevel": SPECIAL_UNLOCK_HERO_LEVEL,
            "specialSkillUpgradeCurrency": "diamond",
        },
        "heroes": entries,
    }


FACTION_BOND_TIERS = {
    "human": [
        {"count": 2, "effects": [{"type": "atkPct", "value": 0.06}]},
        {"count": 4, "effects": [{"type": "atkPct", "value": 0.10}, {"type": "unitHpPct", "value": 0.04}]},
        {"count": 6, "effects": [{"type": "atkPct", "value": 0.14}]},
    ],
    "beast": [
        {"count": 2, "effects": [{"type": "fireRatePct", "value": 0.06}]},
        {"count": 4, "effects": [{"type": "fireRatePct", "value": 0.10}, {"type": "atkPct", "value": 0.04}]},
        {"count": 6, "effects": [{"type": "fireRatePct", "value": 0.14}]},
    ],
    "undead": [
        {"count": 2, "effects": [{"type": "healPct", "value": 0.08}]},
        {"count": 4, "effects": [{"type": "healPct", "value": 0.12}, {"type": "damageReductionPct", "value": 0.04}]},
        {"count": 6, "effects": [{"type": "reviveChancePct", "value": 0.05}, {"type": "healPct", "value": 0.08}]},
    ],
    "mechanical": [
        {"count": 2, "effects": [{"type": "projectileSpeedPct", "value": 0.08}]},
        {"count": 4, "effects": [{"type": "damageReductionPct", "value": 0.06}, {"type": "projectileSpeedPct", "value": 0.04}]},
        {"count": 6, "effects": [{"type": "damageReductionPct", "value": 0.10}, {"type": "projectileSpeedPct", "value": 0.10}]},
    ],
}

CATEGORY_BOND_TIERS = {
    "attack": [
        {"count": 2, "effects": [{"type": "atkPct", "value": 0.05}]},
        {"count": 4, "effects": [{"type": "atkPct", "value": 0.08}]},
        {"count": 6, "effects": [{"type": "atkPct", "value": 0.12}]},
    ],
    "defense": [
        {"count": 2, "effects": [{"type": "damageReductionPct", "value": 0.04}]},
        {"count": 4, "effects": [{"type": "damageReductionPct", "value": 0.07}]},
        {"count": 6, "effects": [{"type": "damageReductionPct", "value": 0.10}]},
    ],
    "supply": [
        {"count": 2, "effects": [{"type": "healPct", "value": 0.10}]},
        {"count": 4, "effects": [{"type": "healPct", "value": 0.15}]},
        {"count": 6, "effects": [{"type": "healPct", "value": 0.20}]},
    ],
    "speed": [
        {"count": 2, "effects": [{"type": "fireRatePct", "value": 0.08}]},
        {"count": 4, "effects": [{"type": "fireRatePct", "value": 0.12}, {"type": "projectileSpeedPct", "value": 0.06}]},
        {"count": 6, "effects": [{"type": "fireRatePct", "value": 0.16}]},
    ],
}


def gen_bond(heroes: list[dict]) -> dict:
    factions = assign_faction(heroes)
    faction_heroes: dict[str, list[str]] = {f: [] for f in FACTIONS}
    for hid, fid in sorted(factions.items()):
        if fid in faction_heroes:
            faction_heroes[fid].append(hid)

    bonds = []
    for fid in FACTIONS:
        bonds.append({
            "bondId": f"faction_{fid}",
            "type": "faction",
            "name": FACTION_CN[fid],
            "faction": fid,
            "heroIds": faction_heroes[fid],
            "tiers": FACTION_BOND_TIERS[fid],
        })
    for cat, label in CATEGORY_CN.items():
        bonds.append({
            "bondId": f"category_{cat}",
            "type": "skillCategory",
            "name": f"{label}型",
            "category": cat,
            "effectTheme": {
                "attack": "攻击力",
                "defense": "减伤防御",
                "supply": "回血补给",
                "speed": "攻速/弹速",
            }[cat],
            "tiers": CATEGORY_BOND_TIERS[cat],
        })
    return {
        "version": "3.0.0",
        "description": "羁绊：人族/兽族/亡灵/机械 + 攻击/防御/补给/加速定位型",
        "rules": {
            "deckSize": 8,
            "excludeHeroIds": ["gold_mine"],
            "tierActivation": "atCount2And4And6",
            "maxActiveFactionBonds": 1,
            "maxActiveCategoryBonds": 1,
            "factions": FACTION_CN,
            "factionCounter": {
                "bonusPct": FACTION_COUNTER_BONUS,
                "cycle": [
                    {"attacker": atk, "strongVs": def_f, "label": FACTION_COUNTER_LABEL[atk]}
                    for atk, def_f in FACTION_COUNTER_CYCLE.items()
                ],
                "note": "普攻在基础伤害上额外叠加克制加成；人族对机械族（含建筑单位）+10%",
            },
        },
        "bonds": bonds,
    }


if __name__ == "__main__":
    heroes = load_heroes()
    hero_level = load_hero_level()
    skills = gen_skills(heroes)
    upgrade = skill_upgrade_table(hero_level)
    hero_battle = gen_hero_battle(heroes, skills)
    bond = gen_bond(heroes)

    (ROOT / "skill.json").write_text(
        json.dumps(
            {
                "version": "3.1.0",
                "description": "技能 v3.1：种族阵营羁绊 + 等级解锁特技 + 钻石升级",
                "categories": CATEGORY_CN,
                "combatRules": {
                    "trajectory": {
                        "flat": "平直弹道（普通攻击、双联/连锁特技）",
                        "arc": "高抛弹道（传奇攻击特技「高空重击」等）",
                        "defenseRule": "普通防御 blocksTrajectory 仅含 flat；史诗及以上特技防御含 flat+arc",
                    },
                    "factionCounter": {
                        "bonusPct": FACTION_COUNTER_BONUS,
                        "cycle": FACTION_COUNTER_CYCLE,
                        "labels": FACTION_COUNTER_LABEL,
                        "rule": "人族克机械 → 机械克兽族 → 兽族克亡灵 → 亡灵克人族；克制时普攻额外+10%伤害",
                    },
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
