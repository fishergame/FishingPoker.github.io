#!/usr/bin/env python3
"""Generate skill.json, bond.json, heroBattle.json, docs/SKILL_BOND_REVIEW.md"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
MAX_CITY_DPS_MULTIPLIER = 1.45

FACTIONS = ["wei", "shu", "wu", "qun"]
FACTION_CN = {"wei": "魏", "shu": "蜀", "wu": "吴", "qun": "群雄"}

ARCHETYPE_CN = {
    "clear": "清场",
    "guard": "守门",
    "siege": "破城",
    "tempo": "节奏",
}

# 翻卡玩法：每英雄定位（清场 / 守门 / 破城 / 节奏）
HERO_ARCHETYPE: dict[str, str] = {
    "dragon_knight": "clear",
    "demon_lord": "clear",
    "archmage": "clear",
    "ranger": "siege",
    "royal_knight": "guard",
    "druid": "guard",
    "lich_queen": "clear",
    "blademaster": "clear",
    "frost_dragon": "siege",
    "crusher": "siege",
    "helicopter": "siege",
    "dread_knight": "clear",
    "warlord": "guard",
    "panda_monk": "clear",
    "shaman": "clear",
    "gargoyle": "guard",
    "skeleton_giant": "guard",
    "sniper": "siege",
    "catapult_tower": "siege",
    "catapult": "clear",
    "cavalry": "clear",
    "wyrmling": "clear",
    "ballista": "siege",
    "necromancer": "tempo",
    "spear_orc": "clear",
    "wolf_rider": "clear",
    "skeleton_knight": "clear",
    "archer": "siege",
    "infantry": "guard",
    "arrow_tower": "siege",
    "bear_warrior": "guard",
    "skeleton_warrior": "guard",
    "goblin": "tempo",
    "blacksmith": "guard",
    "militia": "tempo",
    "bone_archer": "siege",
    "gold_mine": "tempo",
}

QUALITY_SCALE = {
    "common": 0.88,
    "rare": 1.0,
    "epic": 1.08,
    "legendary": 1.15,
}

EFFECT_BOUNDS = {
    "atkPct": (0.05, 0.25),
    "atkSpeedPct": (0.05, 0.20),
    "splashPct": (0.10, 0.35),
    "cityDamagePct": (0.05, 0.20),
    "unitHpPct": (0.05, 0.20),
    "damageReductionPct": (0.05, 0.20),
    "dotPctPerSec": (0.02, 0.08),
    "lifestealPct": (0.05, 0.15),
    "deployBurstPct": (0.30, 0.70),
    "killGold": (5, 25),
    "flipRefundPct": (0.10, 0.35),
    "revealAdjacent": (1, 2),
    "deployGold": (8, 30),
    "taunt": (1, 1),
    "executeBonusPct": (0.20, 0.50),
}

EXECUTE_THRESHOLD = 0.25

BOND_TIER_EFFECTS = {
    "faction": [
        {"count": 2, "effects": [{"type": "atkPct", "value": 0.05}]},
        {
            "count": 4,
            "effects": [
                {"type": "atkPct", "value": 0.08},
                {"type": "unitHpPct", "value": 0.05},
            ],
        },
        {
            "count": 6,
            "effects": [
                {"type": "atkPct", "value": 0.12},
                {"type": "unitHpPct", "value": 0.08},
                {"type": "cityDamagePct", "value": 0.05},
            ],
        },
    ],
    "range_melee": [
        {"count": 2, "effects": [{"type": "unitHpPct", "value": 0.06}]},
        {
            "count": 4,
            "effects": [
                {"type": "unitHpPct", "value": 0.10},
                {"type": "damageReductionPct", "value": 0.05},
            ],
        },
        {
            "count": 6,
            "effects": [
                {"type": "unitHpPct", "value": 0.15},
                {"type": "damageReductionPct", "value": 0.08},
            ],
        },
    ],
    "range_ranged": [
        {"count": 2, "effects": [{"type": "atkPct", "value": 0.06}]},
        {
            "count": 4,
            "effects": [
                {"type": "atkPct", "value": 0.10},
                {"type": "atkSpeedPct", "value": 0.05},
            ],
        },
        {
            "count": 6,
            "effects": [
                {"type": "atkPct", "value": 0.15},
                {"type": "atkSpeedPct", "value": 0.08},
            ],
        },
    ],
}

# 清场传奇：部分英雄用处决/剧毒替代部署突袭
CLEAR_LEGEND_VARIANT = {
    "blademaster": "execute",
    "archmage": "dot",
    "lich_queen": "dot",
    "panda_monk": "deploy_burst",
    "catapult": "deploy_burst",
}


def load_heroes() -> list[dict]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


def infer_range(hero: dict) -> str:
    if hero["type"] == "building":
        return "ranged"
    if hero.get("attackRange") is None:
        return "melee"
    return "ranged" if hero["attackRange"] > 2.5 else "melee"


def infer_archetype(hero: dict) -> str:
    hid = hero["id"]
    if hid in HERO_ARCHETYPE:
        return HERO_ARCHETYPE[hid]
    rng = infer_range(hero)
    if hero["type"] == "resource":
        return "tempo"
    if hero["type"] == "building":
        return "siege"
    atk = hero.get("attack") or 0
    hp = hero.get("unitHp") or 0
    if hp >= 400 or (hp >= 250 and rng == "melee"):
        return "guard"
    if (hero.get("attackRange") or 0) >= 5 or atk >= 90:
        return "siege"
    return "clear"


def scale_value(base: float, quality: str) -> float:
    return round(base * QUALITY_SCALE.get(quality, 1.0), 3)


def build_skill(hero: dict, slot: str, archetype: str) -> dict:
    hid = hero["id"]
    q = hero["quality"]
    rng = infer_range(hero)
    sid = f"skill_{hid}_{slot}"
    unlock = {"normal": 1, "epic": 8, "legend": 20}[slot]

    if archetype == "clear":
        if slot == "normal":
            name, desc = "猎杀", "翻卡出击后普攻伤害提升，擅长快速清理敌方兵卡"
            effects = [{"type": "atkPct", "value": scale_value(0.07, q)}]
            phase, target = "always", "self"
        elif slot == "epic":
            name, desc = "横扫", "对敌方兵卡造成伤害时，溅射相邻敌方单位（不对主城生效）"
            effects = [{"type": "splashPct", "value": scale_value(0.20, q)}]
            phase, target = "field_only", "enemy_unit_adjacent"
        else:
            variant = CLEAR_LEGEND_VARIANT.get(hid, "deploy_burst")
            if variant == "execute":
                name, desc = "处决", f"攻击血量低于{int(EXECUTE_THRESHOLD * 100)}%的敌方兵卡时，伤害大幅提升"
                effects = [
                    {"type": "executeBonusPct", "value": scale_value(0.35, q), "threshold": EXECUTE_THRESHOLD},
                ]
                phase, target = "field_only", "enemy_unit"
            elif variant == "dot":
                name, desc = "剧毒", "普攻命中敌方兵卡后施加持续伤害（仅对单位，不对主城）"
                effects = [{"type": "dotPctPerSec", "value": scale_value(0.05, q)}]
                phase, target = "field_only", "enemy_unit"
            else:
                name, desc = "部署突袭", "翻卡落地时对最近敌方兵卡造成一次爆发伤害"
                effects = [{"type": "deployBurstPct", "value": scale_value(0.50, q)}]
                phase, target = "on_deploy", "enemy_unit_nearest"

    elif archetype == "guard":
        if slot == "normal":
            name, desc = "坚盾", "提升自身生命，在前线阻挡更久"
            effects = [{"type": "unitHpPct", "value": scale_value(0.08, q)}]
            phase, target = "always", "self"
        elif slot == "epic":
            name, desc = "铁壁", "受到敌方兵卡攻击时减伤"
            effects = [{"type": "damageReductionPct", "value": scale_value(0.12, q)}]
            phase, target = "field_only", "self"
        else:
            name, desc = "嘲讽", "敌方兵卡优先攻击本单位，为队友争取攻城窗口"
            effects = [{"type": "taunt", "value": 1}]
            phase, target = "always", "self"

    elif archetype == "siege":
        if slot == "normal":
            name, desc = "瞄准", "提升攻速，清场后更快转火主城"
            effects = [{"type": "atkSpeedPct", "value": scale_value(0.08, q)}]
            phase, target = "always", "self"
        elif slot == "epic":
            name, desc = "蓄力", "对敌方兵卡伤害提升，便于打开攻城通道"
            effects = [{"type": "atkPct", "value": scale_value(0.10, q)}]
            phase, target = "field_only", "self"
        else:
            name, desc = "破城", "场上无敌方兵卡时，对主城伤害大幅提升"
            effects = [{"type": "cityDamagePct", "value": scale_value(0.12, q)}]
            phase, target = "siege_only", "enemy_city"

    else:  # tempo
        if slot == "normal":
            if hero["type"] == "resource":
                name, desc = "矿脉", "翻开后获得额外金币"
                effects = [{"type": "deployGold", "value": int(scale_value(12, q))}]
                phase, target = "on_deploy", "self"
            else:
                name, desc = "轻装", "翻卡费用部分返还，加快铺场节奏"
                effects = [{"type": "flipRefundPct", "value": scale_value(0.15, q)}]
                phase, target = "on_deploy", "self"
        elif slot == "epic":
            name, desc = "战利", "击杀敌方兵卡后获得金币"
            effects = [{"type": "killGold", "value": int(scale_value(10, q))}]
            phase, target = "on_kill", "self"
        else:
            name, desc = "扩张", "翻卡落地时额外翻开相邻未翻格预览"
            effects = [{"type": "revealAdjacent", "value": 1}]
            phase, target = "on_deploy", "adjacent_cells"

    return {
        "skillId": sid,
        "heroId": hid,
        "slot": slot,
        "archetype": archetype,
        "archetypeLabel": ARCHETYPE_CN[archetype],
        "name": f"{hero['name']}·{name}",
        "description": desc,
        "unlockLevel": unlock,
        "maxLevel": 10,
        "effects": effects,
        "scalingPerSkillLevel": 0.02,
        "phase": phase,
        "target": target,
        "tags": [q, rng, hero["type"], archetype],
    }


def gen_skills(heroes: list[dict]) -> list[dict]:
    skills = []
    for h in heroes:
        if h["type"] == "resource" and h["id"] != "gold_mine":
            continue
        archetype = infer_archetype(h)
        for slot in ("normal", "epic", "legend"):
            skills.append(build_skill(h, slot, archetype))
    return skills


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
        if h["id"] == "gold_mine":
            hs = by_hero.get(h["id"], [])
            by_slot = {s["slot"]: s["skillId"] for s in hs}
            entries[h["id"]] = {
                "heroId": h["id"],
                "name": h["name"],
                "archetype": "tempo",
                "archetypeLabel": "节奏",
                "bondEligible": False,
                "note": "铸币坊不计入羁绊",
                "skills": {
                    "normal": by_slot.get("normal"),
                    "epic": by_slot.get("epic"),
                    "legend": by_slot.get("legend"),
                    "epicUnlockLevel": 8,
                    "legendUnlockLevel": 20,
                },
            }
            continue
        hs = by_hero.get(h["id"], [])
        by_slot = {s["slot"]: s["skillId"] for s in hs}
        archetype = infer_archetype(h)
        entries[h["id"]] = {
            "heroId": h["id"],
            "name": h["name"],
            "faction": factions[h["id"]],
            "range": infer_range(h),
            "archetype": archetype,
            "archetypeLabel": ARCHETYPE_CN[archetype],
            "bondEligible": True,
            "skills": {
                "normal": by_slot.get("normal"),
                "epic": by_slot.get("epic"),
                "legend": by_slot.get("legend"),
                "epicUnlockLevel": 8,
                "legendUnlockLevel": 20,
            },
        }
    return {
        "version": "2.0.0",
        "description": "英雄战斗元数据：阵营、定位、技能ID（普通/史诗/传奇各一）",
        "heroes": entries,
    }


def gen_bond() -> dict:
    bonds = []
    for fid in FACTIONS:
        bonds.append({
            "bondId": f"faction_{fid}",
            "type": "faction",
            "name": FACTION_CN[fid],
            "faction": fid,
            "tiers": BOND_TIER_EFFECTS["faction"],
        })
    bonds.append({
        "bondId": "range_melee",
        "type": "range",
        "name": "近战",
        "range": "melee",
        "tiers": BOND_TIER_EFFECTS["range_melee"],
    })
    bonds.append({
        "bondId": "range_ranged",
        "type": "range",
        "name": "远程",
        "range": "ranged",
        "tiers": BOND_TIER_EFFECTS["range_ranged"],
    })
    return {
        "version": "1.0.0",
        "description": "羁绊：4阵营+近战/远程；2/4/6 档激活，4张时同时激活2+4档",
        "rules": {
            "deckSize": 8,
            "excludeHeroIds": ["gold_mine"],
            "tierActivation": "atCount4ActivateTier2And4",
            "maxActiveFactionBonds": 1,
            "maxActiveRangeBonds": 1,
            "stacking": "additiveBeforeCap",
            "cityDamageCapFromBonds": 0.05,
            "recommendedCityDpsCap": MAX_CITY_DPS_MULTIPLIER,
        },
        "bonds": bonds,
    }


def validate_skills(skills: list[dict]) -> list[str]:
    errors = []
    for s in skills:
        for e in s["effects"]:
            et = e["type"]
            if et not in EFFECT_BOUNDS:
                errors.append(f"{s['skillId']}: unknown effect {et}")
                continue
            lo, hi = EFFECT_BOUNDS[et]
            val = e["value"]
            if not (lo <= val <= hi):
                errors.append(f"{s['skillId']}: {et}={val} outside [{lo},{hi}]")
    return errors


def gen_review_md(bond, skills, hero_battle) -> str:
    issues = validate_skills(skills)
    archetype_counts: dict[str, int] = {}
    for h in hero_battle["heroes"].values():
        arch = h.get("archetype")
        if arch:
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    lines = [
        "# 技能 · 羁绊数值审查",
        "",
        "> 配表：`skill.json` · `bond.json` · `heroBattle.json`",
        "> 生成：`python3 scripts/gen-skill-bond-config.py`",
        "",
        "---",
        "",
        "## 一、翻卡技能体系（v2）",
        "",
        "**每英雄 3 技能槽：** 普通（L1）· 史诗（L8）· 传奇（L20）；升级逻辑不变（技能最高 10 级，`scalingPerSkillLevel` 2%）。",
        "",
        "**四类定位：**",
        "",
        "| 定位 | 战术目标 | 普通 | 史诗 | 传奇 |",
        "|:---|:---|:---|:---|:---|",
        "| 清场 | 消灭敌方兵卡、打开攻城窗口 | 攻击% | 溅射 | 部署突袭/处决/剧毒 |",
        "| 守门 | 拖延、保护后排翻卡 | 生命% | 减伤 | 嘲讽 |",
        "| 破城 | 清场后拆主城 | 攻速% | 对单位攻击% | 对城伤害% |",
        "| 节奏 | 多翻、多铺 | 返费/部署金 | 击杀返金 | 翻开相邻 |",
        "",
        "**定位分布：** "
        + " · ".join(f"{ARCHETYPE_CN[k]} {v}" for k, v in sorted(archetype_counts.items())),
        "",
        "---",
        "",
        "## 二、效果类型与 phase",
        "",
        "| 效果 type | 区间 | phase 建议 |",
        "|:---|:---|:---|",
    ]
    phase_hints = {
        "atkPct": "always / field_only",
        "atkSpeedPct": "always",
        "splashPct": "field_only",
        "cityDamagePct": "siege_only",
        "unitHpPct": "always",
        "damageReductionPct": "field_only",
        "dotPctPerSec": "field_only",
        "deployBurstPct": "on_deploy",
        "killGold": "on_kill",
        "flipRefundPct": "on_deploy",
        "revealAdjacent": "on_deploy",
        "deployGold": "on_deploy",
        "taunt": "always",
        "executeBonusPct": "field_only",
    }
    for k, (lo, hi) in EFFECT_BOUNDS.items():
        hint = phase_hints.get(k, "—")
        if k in ("killGold", "deployGold", "revealAdjacent", "taunt"):
            lines.append(f"| `{k}` | {lo}–{hi} | {hint} |")
        else:
            lines.append(f"| `{k}` | {int(lo * 100)}%–{int(hi * 100)}% | {hint} |")

    lines += [
        "",
        "---",
        "",
        "## 三、羁绊摘要",
        "",
        "| 羁绊 | 2张 | 4张 | 6张 |",
        "|:---|:---|:---|:---|",
    ]
    for b in bond["bonds"]:
        t2 = t4 = t6 = "—"
        for t in b["tiers"]:
            eff = "+".join(f"{e['type']}{int(e['value'] * 100)}%" for e in t["effects"])
            if t["count"] == 2:
                t2 = eff
            elif t["count"] == 4:
                t4 = eff
            elif t["count"] == 6:
                t6 = eff
        lines.append(f"| {b['name']} | {t2} | {t4} | {t6} |")

    lines += [
        "",
        "---",
        "",
        "## 四、数值红线",
        "",
        "- 对城 DPS 合计建议 ≤ **1.45×**",
        "- 全队 `cityDamagePct` cap **25%**",
        "- 攻击类加成 cap **35%**",
        "- 溅射 / DOT / 部署突袭 **不对主城**",
        "",
    ]

    if issues:
        lines += ["### 校验告警", ""]
        for i in issues[:30]:
            lines.append(f"- {i}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 五、战斗接入",
        "",
        "1. `battle-skill-runtime.js` 汇总技能加成",
        "2. `battle-rules.js` 按 `phase` 分支结算",
        "3. 翻卡即从卡组抽英雄，不再用品质随机模板",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    heroes = load_heroes()
    skills = gen_skills(heroes)
    errors = validate_skills(skills)
    if errors:
        print("WARN:", len(errors), "skill validation issues")
        for e in errors[:10]:
            print(" ", e)

    bond = gen_bond()
    hero_battle = gen_hero_battle(heroes, skills)

    (ROOT / "skill.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "description": "翻卡技能：每英雄普通/史诗/传奇各一；清场/守门/破城/节奏",
                "archetypes": ARCHETYPE_CN,
                "effectBounds": EFFECT_BOUNDS,
                "skillCount": len(skills),
                "skills": skills,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (ROOT / "bond.json").write_text(json.dumps(bond, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "heroBattle.json").write_text(
        json.dumps(hero_battle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    review = gen_review_md(bond, skills, hero_battle)
    (ROOT / "docs" / "SKILL_BOND_REVIEW.md").write_text(review + "\n", encoding="utf-8")
    print(f"Wrote {len(skills)} skills for {len(hero_battle['heroes'])} heroes")
