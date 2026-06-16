"""Generate unified docs/SKILL_SYSTEM.md from skill v3 config data."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM_APPENDIX_PATH = ROOT / "docs" / "_SKILL_SIM_APPENDIX.md"

QUALITY_CN = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}
FACTION_CN = {"human": "人族", "beast": "兽族", "undead": "亡灵", "mechanical": "机械"}
SLOT_CN = {"normal": "普通技", "rare": "稀有特技", "epic": "史诗特技", "legendary": "传奇特技"}
CATEGORY_CN = {
    "attack": "攻击",
    "defense": "防御",
    "supply": "补给",
    "speed": "加速",
}
STAT_GROWTH = 1.15
FIRE_RATE_GROWTH = 1.02
PROJECTILE_SPEED_GROWTH = 1.03
SPECIAL_SCALING_PER_LEVEL = 0.08


def skill_value_at_level(base: float, skill_level: int) -> float:
    return round(base * (1 + SPECIAL_SCALING_PER_LEVEL * (skill_level - 1)), 3)


def fmt_effects(effects: list[dict]) -> str:
    parts = []
    for e in effects:
        p = f"{e['type']}={e.get('value')}"
        if e.get("blocksTrajectory"):
            p += f" [挡{'/'.join(e['blocksTrajectory'])}]"
        parts.append(p)
    return "; ".join(parts)


def skill_block(sk: dict | None) -> str:
    if not sk:
        return "—"
    lines = [
        f"**{sk['name']}** (`{sk['skillId']}`)",
        f"- 描述：{sk['description']}",
        f"- 表现：{sk['visualDescription']}",
        f"- 效果：{fmt_effects(sk['effects'])}",
    ]
    if sk.get("attackTrajectory"):
        lines.append(f"- 攻击弹道：**{sk['attackTrajectory']}**（穿透普通铁壁）")
    if sk.get("upgradeable"):
        lines.append(f"- 可升级：1→{sk['maxLevel']} 级")
    ex = sk.get("damageExamples")
    if ex and ex.get("levels"):
        lv1 = ex["levels"][0]
        if lv1.get("attackPerHit"):
            lines.append(f"- L1伤害示例：约 **{lv1['attackPerHit']}** 点/击（基础攻{ex.get('heroAttackL1')}）")
        if lv1.get("splashDamage"):
            lines.append(f"- L1溅射示例：约 **{lv1['splashDamage']}** 点")
        if lv1.get("healAmount"):
            lines.append(f"- L1治疗示例：约 **{lv1['healAmount']}** 点")
    return "\n".join(lines)


def migrate_legacy_sim_appendix() -> str:
    """One-time merge of v2 sim reports into appendix source file."""
    chunks: list[str] = []
    legacy = [
        ("SKILL_BATTLE_SIM_REPORT.md", "A.1 定位单挑与自动对战（v2 原型）"),
        ("SKILL_BATTLE_SIM_REPORT_REAL_HP.md", "A.2 真实主城 HP 多阶段对战（v2 原型）"),
    ]
    for fname, heading in legacy:
        path = ROOT / "docs" / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"^#\s+.+\n+", "", text, count=1)
        chunks.append(f"### {heading}\n\n> 历史模拟数据，基于 v2 技能原型；请运行 `node scripts/sim-battle.js` 后执行 `python3 scripts/gen-skill-bond-config.py` 刷新。\n\n{text.strip()}")
    if not chunks:
        return (
            "> 暂无模拟数据。运行：\n"
            "> - `node scripts/sim-battle.js --battles=50 --level=20`\n"
            "> - `node scripts/sim-battle.js --real --multi --battles=25`\n"
            "> 然后 `python3 scripts/gen-skill-bond-config.py` 合入本文档。"
        )
    return "\n\n---\n\n".join(chunks)


def load_sim_appendix() -> str:
    if not SIM_APPENDIX_PATH.exists():
        body = migrate_legacy_sim_appendix()
        SIM_APPENDIX_PATH.parent.mkdir(parents=True, exist_ok=True)
        SIM_APPENDIX_PATH.write_text(body + "\n", encoding="utf-8")
        return body
    return SIM_APPENDIX_PATH.read_text(encoding="utf-8").strip()


def gen_unified_skill_md(
    skills: list[dict],
    hero_battle: dict,
    upgrade: dict,
    bond: dict,
    skill_count: int,
) -> str:
    heroes = hero_battle["heroes"]
    skill_by_id = {s["skillId"]: s for s in skills}

    cat_count: dict[str, int] = {}
    for h in heroes.values():
        c = h.get("category")
        if c:
            cat_count[c] = cat_count.get(c, 0) + 1

    lines: list[str] = [
        "# 技能体系 v3 · 完整文档",
        "",
        "> **唯一合流文档** — 设计规则、配表、英雄详表、羁绊、对战模拟附录",
        "> 配表：`skill.json` v3.0.0 · `heroBattle.json` v3.0.0 · `bond.json` v2.0.0",
        "> 生成：`python3 scripts/gen-skill-bond-config.py`",
        "",
        "---",
        "",
        "## 目录",
        "",
        "1. [设计总览](#一设计总览)",
        "2. [品质与技能槽](#二品质与技能槽)",
        "3. [四类技能与特技递进](#三四类技能与特技递进)",
        "4. [弹道与防御规则](#四弹道与防御规则)",
        "5. [英雄属性公式](#五英雄属性公式)",
        "6. [特技升级消耗](#六特技升级消耗)",
        "7. [效果类型说明](#七效果类型说明)",
        "8. [羁绊系统](#八羁绊系统)",
        "9. [英雄属性速查表](#九英雄属性速查表)",
        "10. [技能一览速查表](#十技能一览速查表)",
        "11. [全英雄技能详表](#十一全英雄技能详表)",
        "12. [战斗接入与文件索引](#十二战斗接入与文件索引)",
        "13. [附录：对战模拟](#附录对战模拟)",
        "",
        "---",
        "",
        "## 一、设计总览",
        "",
        "技能体系 v3 以**卡牌品质**决定特技槽位，每位英雄拥有 **1 个普通技能** + **0~1 个品质特技**：",
        "",
        "- **普通技**：开局即拥有，**不可升级**",
        "- **特技**：按品质解锁（稀有/史诗/传奇），**可升至 5 级**",
        "- **取消近战/远程战斗逻辑**：`attackRange` 仅表现；`attackSpeed` = 弹道速度；`fireRate` = 发射频率",
        "",
        f"当前共 **{skill_count}** 个技能，覆盖 **{len(heroes)}** 位英雄。",
        f"**定位分布（战斗英雄 36）**：攻击 14 · 防御 10 · 补给 6 · 加速 6",
        f"**种族分布**：人族 10 · 兽族 9 · 亡灵 9 · 机械 9",
        "",
        "---",
        "",
        "## 二、品质与技能槽",
        "",
        "| 卡牌品质 | 技能组成 | 普通技 | 特技 |",
        "|:---|:---|:---:|:---:|",
        "| **普通** | 仅普通技能 | ✅ | — |",
        "| **稀有** | 普通 + 稀有特技 | ✅ | 稀有特技 ×1 |",
        "| **史诗** | 普通 + 史诗特技 | ✅ | 史诗特技 ×1 |",
        "| **传奇** | 普通 + 传奇特技 | ✅ | 传奇特技 ×1 |",
        "",
        "---",
        "",
        "## 三、四类技能与特技递进",
        "",
        "| 类型 | 战术目标 | 普通技 | 稀有特技 | 史诗特技 | 传奇特技 |",
        "|:---|:---|:---|:---|:---|:---|",
        "| **攻击** | 输出/击杀/亡灵 | 平直点射 | 双联点射（溅射） | 连锁穿透 | 高空重击 / 亡灵收割 |",
        "| **防御** | 护墙/减伤 | 铁壁（仅挡平直） | 单格护墙 | 三格盾带（挡弧） | 全局圣域（挡弧） |",
        "| **补给** | 回血 | 应急包扎 20% | 战地包扎 30% | 群体复苏 50% | 满血圣疗 |",
        "| **加速** | 攻速/弹速 | 迅捷装填 | 速射补给 | 弹速增压 | 狂热号令 |",
        "",
        "---",
        "",
        "## 四、弹道与防御规则",
        "",
        "### 4.1 两种弹道",
        "",
        "| 弹道 | 代号 | 典型来源 |",
        "|:---|:---:|:---|",
        "| **平直** | `flat` | 普通攻击技、双联/连锁特技 |",
        "| **高抛** | `arc` | 传奇攻击特技「高空重击」、亡灵收割 |",
        "",
        "### 4.2 防御分层",
        "",
        "| 防御类型 | 可挡弹道 | 说明 |",
        "|:---|:---:|:---|",
        "| **普通铁壁** | 仅 `flat` | 无法抵挡特技高抛 |",
        "| **稀有单格护墙**附加减伤 | 仅 `flat` | 护墙 + 平直减伤 |",
        "| **史诗三格盾带** | `flat` + `arc` | 范围内友军可挡高抛 |",
        "| **传奇全局圣域** | `flat` + `arc` | 全队减伤，可挡高抛 |",
        "",
        "### 4.3 对抗示例",
        "",
        "- 重步兵：平直约 **16%** 减伤，高抛 **0%** 减伤",
        "- 龙焰女王（高空重击）：攻击 `arc`，穿透普通铁壁",
        "- 圣盾领主（铁壁+全局圣域）：平直最高约 **40%**，高抛约 **33%**",
        "",
        "### 4.4 配表字段",
        "",
        "| 字段 | 含义 |",
        "|:---|:---|",
        "| `effects[].blocksTrajectory` | 防御可挡弹道 `[\"flat\"]` 或 `[\"flat\",\"arc\"]` |",
        "| `attackTrajectory` | 攻击特技弹道（`arc`） |",
        "| `bypassesNormalDefense` | 穿透普通铁壁 |",
        "| `combatRules.trajectory` | skill.json 全局规则 |",
        "",
        "### 4.4 种族克制（普攻额外伤害）",
        "",
        "在**普通攻击基础伤害**上，额外叠加 **+10%** 克制加成：",
        "",
        "| 攻击方 | 克制目标 |",
        "|:---|:---|",
        "| **人族** | 机械（含建筑单位） |",
        "| **机械** | 兽族 |",
        "| **兽族** | 亡灵 |",
        "| **亡灵** | 人族 |",
        "",
        "循环：**人族 → 机械 → 兽族 → 亡灵 → 人族**。",
        "",
        "---",
        "",
        "## 五、英雄属性公式",
        "",
        "```",
        f"attack(L)      = round(attackL1 × {STAT_GROWTH}^(L-1))",
        f"unitHp(L)      = round(unitHpL1 × {STAT_GROWTH}^(L-1))",
        f"buildingHp(L)  = round(buildingHpL1 × {STAT_GROWTH}^(L-1))",
        f"fireRate(L)    = round(fireRateL1 × {FIRE_RATE_GROWTH}^(L-1), 2)",
        f"attackSpeed(L) = round(attackSpeedL1 × {PROJECTILE_SPEED_GROWTH}^(L-1), 2)",
        "attackInterval = 2.2 / fireRate",
        "```",
        "",
        "---",
        "",
        "## 六、特技解锁与升级",
        "",
        "### 6.1 解锁条件（英雄等级）",
        "",
        "| 特技品质 | 解锁英雄等级 | 说明 |",
        "|:---|:---:|:---|",
        "| **稀有特技** | **L5** | 稀有品质卡牌 |",
        "| **史诗特技** | **L10** | 史诗品质卡牌 |",
        "| **传奇特技** | **L20** | 传奇品质卡牌 |",
        "| **普通技能** | L1 | 始终拥有，不可升级 |",
        "",
        "### 6.2 升级消耗（仅钻石）",
        "",
        "特技升级**不使用碎片**，仅消耗**钻石**；同档参考英雄升级金币折算后 × 溢价系数（稀有×2.0 / 史诗×2.5 / 传奇×3.0），高于普通英雄升级。",
        "",
        f"效果曲线：`effect(L) = base × (1 + {SPECIAL_SCALING_PER_LEVEL} × (L-1))`",
        "",
        "| 特技档 | 升级 | 钻石消耗 | 参考英雄金币 |",
        "|:---|:---:|:---:|:---:|",
    ]

    unlock = upgrade.get("unlockByHeroLevel", {"rare": 5, "epic": 10, "legendary": 20})
    for row in upgrade.get("diamondCost", []):
        slot_cn = {"rare": "稀有", "epic": "史诗", "legendary": "传奇"}.get(row["slot"], row["slot"])
        lines.append(
            f"| {slot_cn} | L{row['fromLevel']}→L{row['toLevel']} | **{row['diamondCost']}** | {row.get('heroGoldReference', '—')} |"
        )

    lines += [
        "",
        f"公式：`{upgrade.get('diamondCostFormula', '')}`",
        "",
        "### 6.3 特技等级曲线示例（传奇高空重击 atkPct，base=0.25）",
        "",
        "| 特技等级 | 效果系数 |",
        "|:---:|:---:|",
    ]
    for lv in range(1, 6):
        lines.append(f"| L{lv} | {skill_value_at_level(0.25, lv)} |")

    lines += [
        "",
        "---",
        "",
        "## 七、效果类型说明",
        "",
        "| 效果类型 | 适用 | 说明 |",
        "|:---|:---|:---|",
        "| `atkPct` | 攻击 | 攻击力百分比加成 |",
        "| `damageReductionPct` | 防御 | 自身减伤；配合 `blocksTrajectory` |",
        "| `allyDamageReductionPct` | 防御 | 友军范围减伤（史诗三格盾带） |",
        "| `globalDamageReductionPct` | 防御 | 全队减伤（传奇全局圣域） |",
        "| `splashPct` | 攻击 | 邻格溅射伤害比例 |",
        "| `extraTargets` | 攻击 | 额外命中目标数 |",
        "| `chainTargets` | 攻击 | 连锁命中格数 |",
        "| `projectileArc` | 攻击 | 标记高抛弹道 |",
        "| `executeThreshold` | 攻击 | 低血斩杀阈值 |",
        "| `wallTiles` | 防御 | 护墙覆盖格数 |",
        "| `healPct` / `healAllyPct` / `healAreaPct` | 补给 | 回血比例 |",
        "| `healFull` | 补给 | 满血恢复 |",
        "| `fireRatePct` / `projectileSpeedPct` | 加速 | 攻速/弹速提升 |",
        "| `teamFireRatePct` | 加速 | 全队攻速 |",
        "| `revealAdjacent` | 加速 | 翻开相邻格 |",
        "| `reviveChancePct` | 亡灵羁绊 | 复活/复燃概率加成 |",
        "| `deployGold` | 补给 | 翻开获得金币（采矿机） |",
        "",
        "---",
        "",
        "## 八、羁绊系统（仅阵营）",
        "",
        f"版本：bond.json v{bond['version']}",
        "",
        "卡组 8 张（不含采矿机）；最多激活 **1 条阵营羁绊**。技能定位羁绊已取消。",
        "",
        "### 8.1 种族阵营羁绊（人族 / 兽族 / 亡灵 / 机械）",
        "",
    ]

    for b in bond["bonds"]:
        if b["type"] != "faction":
            continue
        fname = b["name"]
        lines.append(f"#### {fname}")
        lines.append("")
        hero_names = []
        for hid in b.get("heroIds", []):
            h = heroes.get(hid)
            if h:
                hero_names.append(h["name"])
        lines.append(f"**成员（{len(hero_names)}）**：{' · '.join(hero_names)}")
        lines.append("")
        lines.append("| 数量 | 效果 |")
        lines.append("|:---:|:---|")
        for t in b["tiers"]:
            eff = "；".join(
                f"{e['type']} +{int(e['value']*100)}%"
                if "Pct" in e["type"]
                else f"{e['type']} {e['value']}"
                for e in t["effects"]
            )
            lines.append(f"| {t['count']} | {eff} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## 九、英雄属性速查表",
        "",
        "| 英雄 | 品质 | 种族 | 定位 | 攻击L1 | 生命L1 | 发射L1 | 弹道速L1 | 间隔 | 弹道 | 普通技 ID | 特技 ID |",
        "|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|:---|",
    ]

    for hid in sorted(heroes.keys()):
        h = heroes[hid]
        cs = h["combatStats"]
        sk = h["skills"]
        sp = sk.get("rare") or sk.get("epic") or sk.get("legendary") or "—"
        lines.append(
            f"| {h['name']} | {h['qualityLabel']} | {h.get('factionLabel', '—')} | {h['categoryLabel']} "
            f"| {cs.get('attackL1', '—')} | {cs.get('unitHpL1', '—')} "
            f"| {cs.get('fireRateL1', '—')} | {cs.get('attackSpeedL1', '—')} "
            f"| {cs.get('attackIntervalL1', '—')} | {cs.get('projectileStyle', '—')} "
            f"| {sk.get('normal', '—')} | {sp} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 十、技能一览速查表",
        "",
        "| 英雄 | 品质 | 种族 | 定位 | 弹道 | 普通技能 | 特技 | 解锁等级 | 高抛穿透 |",
        "|:---|:---|:---|:---|:---|:---|:---|:---:|:---:|",
    ]

    for hid in sorted(heroes.keys()):
        h = heroes[hid]
        sk = h["skills"]
        normal = skill_by_id.get(sk.get("normal"), {})
        special_id = sk.get("rare") or sk.get("epic") or sk.get("legendary")
        special = skill_by_id.get(special_id, {}) if special_id else {}
        arc = "✅" if special.get("attackTrajectory") == "arc" else "—"
        unlock_lv = special.get("unlockLevel", "—") if special else "—"
        lines.append(
            f"| {h['name']} | {QUALITY_CN[h['quality']]} | {h.get('factionLabel', '—')} | {h['categoryLabel']} "
            f"| {h['combatStats'].get('projectileStyle', '—')} "
            f"| {(normal.get('name') or '—').split('·')[-1]} "
            f"| {(special.get('name') or '—').split('·')[-1] if special else '—'} | L{unlock_lv} | {arc} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 十一、全英雄技能详表",
        "",
    ]

    for hid in sorted(heroes.keys()):
        h = heroes[hid]
        cs = h["combatStats"]
        sk = h["skills"]
        lines.append(f"### {h['name']}（{QUALITY_CN[h['quality']]} · {h.get('factionLabel', '—')} · {h['categoryLabel']}）")
        lines.append("")
        lines.append(
            "| 攻击L1 | 生命L1 | 发射L1 | 弹道速L1 | 间隔 | 弹道 | 阵营 |"
        )
        lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        lines.append(
            f"| {cs.get('attackL1', '—')} | {cs.get('unitHpL1', '—')} | "
            f"{cs.get('fireRateL1', '—')} | {cs.get('attackSpeedL1', '—')} | "
            f"{cs.get('attackIntervalL1', '—')} | {cs.get('projectileStyle', '—')} | {h.get('factionLabel', h.get('faction', '—'))} |"
        )
        lines.append("")
        lines.append("#### 普通技能")
        lines.append("")
        lines.append(skill_block(skill_by_id.get(sk.get("normal"))))
        lines.append("")
        special_id = sk.get("rare") or sk.get("epic") or sk.get("legendary")
        if special_id:
            special = skill_by_id[special_id]
            lines.append(f"#### {SLOT_CN.get(special['slot'], '特技')}")
            lines.append("")
            lines.append(skill_block(special))
        else:
            lines.append("#### 特技")
            lines.append("")
            lines.append("—（普通品质，无特技槽）")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines += [
        "## 十二、战斗接入与文件索引",
        "",
        "| 模块 | 职责 |",
        "|:---|:---|",
        "| `skill.json` | 技能定义、弹道规则、`levelCurve` |",
        "| `heroBattle.json` | `combatStats`、技能槽映射 |",
        "| `bond.json` | 种族阵营羁绊 |",
        "| `battle-skill-runtime.js` | `trajectoryDefense`、`primaryAttackTrajectory` |",
        "| `battle-rules.js` | 按 `attackTrajectory` 结算减伤 |",
        "| `skill-config.js` | 配表加载 |",
        "| `scripts/sim-battle.js` | 对战模拟 → `docs/_SKILL_SIM_APPENDIX.md` |",
        "",
        "**维护流程**",
        "",
        "1. 改配表逻辑后：`python3 scripts/gen-skill-bond-config.py`（生 JSON + 本文档）",
        "2. 重跑模拟后：`node scripts/sim-battle.js …`，再执行步骤 1 合入附录",
        "",
        "---",
        "",
        "## 附录：对战模拟",
        "",
        load_sim_appendix(),
        "",
    ]

    return "\n".join(lines)
