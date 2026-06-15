#!/usr/bin/env python3
"""Generate skill.json, bond.json, heroBattle.json, docs/SKILL_BOND_REVIEW.md"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAT_GROWTH = 1.15
# 技能/羁绊对主城伤害的合计软上限（相对普攻 DPS）
MAX_CITY_DPS_MULTIPLIER = 1.45
MAX_BOND_ATK_BONUS = 0.15  # 单羁绊 tier6

FACTIONS = ["wei", "shu", "wu", "qun"]
FACTION_CN = {"wei": "魏", "shu": "蜀", "wu": "吴", "qun": "群雄"}

# 技能效果类型与推荐数值区间（接入战斗时校验）
EFFECT_BOUNDS = {
    "atkPct": (0.05, 0.25),
    "atkSpeedPct": (0.05, 0.20),
    "splashPct": (0.10, 0.35),
    "cityDamagePct": (0.05, 0.20),
    "unitHpPct": (0.05, 0.20),
    "damageReductionPct": (0.05, 0.20),
    "dotPctPerSec": (0.02, 0.08),
    "lifestealPct": (0.05, 0.15),
}

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


def assign_faction(heroes: list[dict]) -> dict[str, str]:
    """按 id 哈希均匀分阵营（铸币坊不参与羁绊）。"""
    mapping = {}
    factions_cycle = FACTIONS * 20
    idx = 0
    for h in sorted(heroes, key=lambda x: x["id"]):
        if h["id"] == "gold_mine":
            continue
        mapping[h["id"]] = factions_cycle[idx % len(FACTIONS)]
        idx += 1
    return mapping


def skill_template(hero: dict, slot: str, index: int) -> dict:
    """按品质/远近战生成技能骨架（数值待策划逐英雄微调）。"""
    hid = hero["id"]
    q = hero["quality"]
    rng = infer_range(hero)
    sid = f"skill_{hid}_{slot}{index}"

    if slot == "normal":
        if rng == "ranged":
            effect = {"type": "atkPct", "value": 0.06 if q == "common" else 0.08}
            desc = "精准：普攻伤害提升"
        else:
            effect = {"type": "unitHpPct", "value": 0.05}
            desc = "坚韧：生命提升"
    elif slot == "epic":
        if rng == "ranged":
            effect = {"type": "splashPct", "value": 0.15 if q in ("common", "rare") else 0.20}
            desc = "散射：溅射伤害"
        else:
            effect = {"type": "damageReductionPct", "value": 0.10}
            desc = "铁壁：减伤"
    else:  # legend
        if hero["type"] == "building":
            effect = {"type": "cityDamagePct", "value": 0.12}
            desc = "破城：对主城伤害提升"
        elif rng == "ranged":
            effect = {"type": "cityDamagePct", "value": 0.10}
            desc = "狙击：对主城伤害提升"
        else:
            effect = {"type": "atkPct", "value": 0.15}
            desc = "破军：普攻伤害大幅提升"

    return {
        "skillId": sid,
        "heroId": hid,
        "slot": slot,
        "slotIndex": index,
        "name": f"{hero['name']}·{desc.split('：')[0]}",
        "description": desc,
        "unlockLevel": 1 if slot == "normal" else (8 if slot == "epic" and index == 1 else 15 if slot == "epic" else 20),
        "maxLevel": 10,
        "effects": [effect],
        "scalingPerSkillLevel": 0.02,
        "target": "self",
        "tags": [q, rng, hero["type"]],
    }


def gen_skills(heroes: list[dict]) -> list[dict]:
    skills = []
    for h in heroes:
        if h["type"] == "resource":
            continue
        skills.append(skill_template(h, "normal", 1))
        skills.append(skill_template(h, "normal", 2))
        skills.append(skill_template(h, "epic", 1))
        skills.append(skill_template(h, "epic", 2))
        skills.append(skill_template(h, "legend", 1))
    return skills


def gen_hero_battle(heroes: list[dict], skills: list[dict]) -> dict:
    factions = assign_faction(heroes)
    by_hero: dict[str, list] = {}
    for s in skills:
        by_hero.setdefault(s["heroId"], []).append(s)

    entries = {}
    for h in heroes:
        if h["id"] == "gold_mine":
            entries[h["id"]] = {
                "heroId": h["id"],
                "name": h["name"],
                "bondEligible": False,
                "note": "铸币坊不计入羁绊",
            }
            continue
        hs = by_hero.get(h["id"], [])
        entries[h["id"]] = {
            "heroId": h["id"],
            "name": h["name"],
            "faction": factions[h["id"]],
            "range": infer_range(h),
            "bondEligible": True,
            "skills": {
                "normal": [s["skillId"] for s in hs if s["slot"] == "normal"],
                "epic": [s["skillId"] for s in hs if s["slot"] == "epic"],
                "legend": next((s["skillId"] for s in hs if s["slot"] == "legend"), None),
                "epicUnlockLevels": [8, 15],
                "legendUnlockLevel": 20,
            },
        }
    return {
        "version": "1.0.0",
        "description": "英雄战斗元数据：阵营、远近程、技能ID映射",
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
        "recommendedCityDpsCap": 1.45,
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
            if not (lo <= e["value"] <= hi):
                errors.append(f"{s['skillId']}: {et}={e['value']} outside [{lo},{hi}]")
    return errors


def estimate_city_dps_multiplier(bond: dict, skills: list[dict], deck_hero_ids: list[str], hero_battle: dict) -> float:
    """粗算羁绊+传奇技能对主城 DPS 的加成倍率。"""
    eligible = [hid for hid in deck_hero_ids if hid and hero_battle["heroes"].get(hid, {}).get("bondEligible")]
    factions = {}
    melee = ranged = 0
    for hid in eligible:
        meta = hero_battle["heroes"][hid]
        factions[meta["faction"]] = factions.get(meta["faction"], 0) + 1
        if meta["range"] == "melee":
            melee += 1
        else:
            ranged += 1

    atk_bonus = city_bonus = 0.0
    for b in bond["bonds"]:
        if b["type"] == "faction":
            cnt = max(factions.get(b["faction"], 0) for factions in [factions]) if False else factions.get(b["faction"], 0)
            # pick best faction count
        # simplify: use max faction count
    max_faction = max(factions.values()) if factions else 0
    range_cnt = melee if melee >= ranged else ranged
    range_key = "range_melee" if melee >= ranged else "range_ranged"

    def tier_bonus(bond_id: str, count: int) -> float:
        b = next(x for x in bond["bonds"] if x["bondId"] == bond_id)
        bonus = 0.0
        for tier in b["tiers"]:
            if count >= tier["count"]:
                for e in tier["effects"]:
                    if e["type"] == "atkPct":
                        bonus = max(bonus, e["value"])
                    if e["type"] == "cityDamagePct":
                        nonlocal_city = e["value"]
        return bonus

    nonlocal_city = 0
    atk_bonus = tier_bonus(f"faction_{max(factions, key=factions.get)}", max_faction) if factions else 0
    atk_bonus += tier_bonus(range_key, range_cnt)

    skill_city = 0.0
    skill_atk = 0.0
    skill_map = {s["skillId"]: s for s in skills}
    for hid in eligible:
        meta = hero_battle["heroes"][hid]
        leg_id = meta["skills"]["legend"]
        if leg_id and leg_id in skill_map:
            for e in skill_map[leg_id]["effects"]:
                if e["type"] == "cityDamagePct":
                    skill_city += e["value"]
                if e["type"] == "atkPct":
                    skill_atk += e["value"]

    return 1.0 + min(atk_bonus + skill_atk, 0.35) + min(skill_city, 0.25)


def gen_review_md(bond, skills, hero_battle, balance_path: Path) -> str:
    balance = json.loads(balance_path.read_text())
    issues = validate_skills(skills)

    lines = [
        "# 技能 · 羁绊数值审查（接入前）",
        "",
        "> 配表：`skill.json` · `bond.json` · `heroBattle.json`",
        "> 生成：`python3 scripts/gen-skill-bond-config.py`",
        "",
        "---",
        "",
        "## 一、当前状态",
        "",
        "| 模块 | 文件 | 状态 |",
        "|:---|:---|:---|",
        "| 主城 HP / 对局时长 | `battleBalance.json` | ✅ 已落地 |",
        "| 英雄 L1 属性 | `heroes-config.js` | ✅ |",
        "| 英雄升级 | `heroLevel.json` | ✅ |",
        "| **羁绊** | `bond.json` | ✅ 初版 |",
        "| **技能** | `skill.json` | ✅ 骨架（每英雄5槽） |",
        "| 战斗接入 | `battle-rules.js` | ⚠️ 仍用品质被动模板 |",
        "",
        "---",
        "",
        "## 二、羁绊配置摘要",
        "",
        "**规则：** 2 / 4 / 6 张激活；**4 张时同时激活 2 档+4 档**；采矿机不计入。",
        "",
        "| 羁绊 | 2张 | 4张 | 6张 |",
        "|:---|:---|:---|:---|",
    ]
    for b in bond["bonds"]:
        t2 = t4 = t6 = "—"
        for t in b["tiers"]:
            eff = "+".join(f"{e['type']}{int(e['value']*100)}%" for e in t["effects"])
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
        "## 三、技能效果类型与数值边界",
        "",
        "| 效果 type | 推荐区间 | 说明 |",
        "|:---|:---|:---|",
    ]
    for k, (lo, hi) in EFFECT_BOUNDS.items():
        lines.append(f"| `{k}` | {int(lo*100)}%–{int(hi*100)}% | 单技能单条 |")

    lines += [
        "",
        "**技能槽：** 普通×2（L1） + 史诗×2（L8/L15） + 传奇×1（L20）",
        "",
        "---",
        "",
        "## 四、与主城血量的关系（重点）",
        "",
        "主城 HP 已按 **1.15^等级** 与攻击同步成长，默认编队清场后攻城约 **45% 对局时长**。",
        "",
        "接入技能/羁绊后需额外乘算：",
        "",
        "```",
        "实际攻城DPS ≈ 基础DPS × (1 + 羁绊攻% + 技能攻%) × (1 + 对城伤害%)",
        "建议合计上限：≤ 1.45×（见 battleBalance.json 建议）",
        "```",
        "",
        "| 风险 | 说明 | 建议 |",
        "|:---|:---|:---|",
        "| 羁绊6+远程6双满 | 攻击加成可达 ~27% | 加成用**加算**并 cap 35% |",
        "| 多传奇「破城」叠加 | 对城伤害线性叠加 | 全队对城加成 cap 25% |",
        "| 溅射/多段 | 清场更快 → 更早攻城管 | 溅射不对主城生效 |",
        "| 两套战斗数值 | flip 模板 vs 37 英雄 | 统一读 `heroes-config` + `skill.json` |",
        "",
    ]

    if issues:
        lines += ["### 校验告警", ""]
        for i in issues[:20]:
            lines.append(f"- {i}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 五、接入清单（开发）",
        "",
        "1. `battle-rules.js`：伤害结算读取 `heroBattle.json` + `skill.json`",
        "2. 开战前根据卡组重算 `bond.json` 激活档",
        "3. 对城伤害单独通道，应用 `cityDamagePct`",
        "4. 主城 HP / 时长从 `BattleBalanceConfig` 按竞技场读取",
        "5. 禁用：溅射、DOT 对主城直接生效（仅对单位）",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    heroes = load_heroes()
    skills = gen_skills(heroes)
    errors = validate_skills(skills)
    if errors:
        print("WARN:", len(errors), "skill validation issues")

    bond = gen_bond()
    hero_battle = gen_hero_battle(heroes, skills)

    (ROOT / "skill.json").write_text(json.dumps({
        "version": "1.0.0",
        "description": "英雄技能：每英雄5槽；效果数值为接入骨架",
        "effectBounds": EFFECT_BOUNDS,
        "skillCount": len(skills),
        "skills": skills,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (ROOT / "bond.json").write_text(json.dumps(bond, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "heroBattle.json").write_text(json.dumps(hero_battle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review = gen_review_md(bond, skills, hero_battle, ROOT / "battleBalance.json")
    (ROOT / "docs" / "SKILL_BOND_REVIEW.md").write_text(review + "\n", encoding="utf-8")
    print("Wrote skill.json, bond.json, heroBattle.json, docs/SKILL_BOND_REVIEW.md")
