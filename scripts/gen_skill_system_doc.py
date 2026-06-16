"""Generate unified docs/SKILL_SYSTEM.md from skill v3 config data."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUALITY_CN = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}
FACTION_CN = {"human": "人族", "beast": "兽族", "undead": "亡灵", "mechanical": "机械"}
SLOT_CN = {
    "normal_1": "普通技能1",
    "normal_2": "普通技能2",
    "normal_3": "普通技能3",
    "basic_attack": "普通技能1",
    "normal": "普通技能2",
    "rare": "稀有特技",
    "epic": "史诗特技",
    "legendary": "传奇特技",
}
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
    if sk.get("blockFeedback"):
        bf = sk["blockFeedback"]
        lines.append(f"- 抵挡反馈：成功时飘字 **{bf.get('text', 'MISS')}**")
    if sk.get("activation"):
        act = sk["activation"]
        act_parts = []
        if act.get("trigger") == "autoAttack" or act.get("trigger") == "onBasicAttack":
            act_parts.append("随角色普攻自动发射")
            if act.get("useHeroAttackSpeed"):
                act_parts.append("攻击间隔=角色属性（2.2/发射频率）")
        elif act.get("trigger") == "onKill":
            act_parts.append("击杀敌方兵卡时触发")
        elif act.get("trigger") == "passive":
            act_parts.append("常驻被动")
            if act.get("cooldownSec"):
                act_parts.append(f"每{act['cooldownSec']}秒自动触发")
        elif act.get("trigger") == "active" and act.get("cooldownSec"):
            act_parts.append(f"每{act['cooldownSec']}秒主动释放1次")
        if act.get("useHeroAttackSpeed") is False:
            iv = act.get("attackIntervalSec") or act.get("cooldownSec")
            if iv:
                act_parts.append(f"技能独立间隔{iv}秒（不跟随普攻）")
        if act.get("durationSec"):
            act_parts.append(f"持续{act['durationSec']}秒")
        if act.get("lockTarget"):
            act_parts.append(f"锁定={act['lockTarget']}")
        if act.get("target"):
            act_parts.append(f"目标={act['target']}")
        if act_parts:
            lines.append(f"- 触发：{'；'.join(act_parts)}")
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

    combat_count = sum(1 for h in heroes.values() if h.get("heroId") != "gold_mine")
    faction_count: dict[str, int] = {}
    for h in heroes.values():
        f = h.get("faction")
        if f and h.get("heroId") != "gold_mine":
            faction_count[f] = faction_count.get(f, 0) + 1

    lines: list[str] = [
        "# 技能体系 v3 · 完整文档",
        "",
        "> **唯一合流文档** — 设计规则、配表、英雄详表、羁绊",
        "> 配表：`skill.json` v3.6.0 · `heroBattle.json` v3.6.0 · `bond.json` v3.6.0",
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
        "",
        "---",
        "",
        "## 一、设计总览",
        "",
        "技能体系 v3 以**卡牌品质**决定特技槽位。每位战斗英雄拥有 **普通技能1 + 普通技能2 + 普通技能3**，外加 **0~1 个品质特技**：",
        "",
        "- **普通技能1**（`normal_1`）：主动攻击，**攻击间隔跟随角色属性**（公式 `2.2/发射频率`），不可升级",
        "- **普通技能2**（`normal_2`）：被动/自动效果，按定位每 N 秒触发，不可升级",
        "- **普通技能3**（`normal_3`）：**种族克制被动**，对克制阵营伤害 +10%，不可升级",
        "- **特技**：主动技能使用**技能独立间隔**（不跟随普攻）；被动特技无需间隔定义",
        "- **取消近战/远程战斗逻辑**：`attackRange` 仅表现；`attackSpeed` = 弹道速度；`fireRate` = 发射频率",
        "",
        f"当前共 **{skill_count}** 个技能，覆盖 **{len(heroes)}** 位英雄。",
        f"**定位分布（战斗英雄 {combat_count}）**："
        + " · ".join(f"{CATEGORY_CN[k]} {cat_count.get(k, 0)}" for k in CATEGORY_CN),
        f"**种族分布**："
        + " · ".join(f"{FACTION_CN[k]} {faction_count.get(k, 0)}" for k in FACTION_CN),
        "",
        "---",
        "",
        "## 二、品质与技能槽",
        "",
        "| 卡牌品质 | 技能组成 | 普通技能1 | 普通技能2 | 普通技能3 | 特技 |",
        "|:---|:---|:---:|:---:|:---:|:---:|",
        "| **普通** | 技能1 + 技能2 + 技能3 | ✅ | ✅ | ✅ | — |",
        "| **稀有** | 技能1~3 + 稀有特技 | ✅ | ✅ | ✅ | 稀有特技 ×1 |",
        "| **史诗** | 技能1~3 + 史诗特技 | ✅ | ✅ | ✅ | 史诗特技 ×1 |",
        "| **传奇** | 技能1~3 + 传奇特技 | ✅ | ✅ | ✅ | 传奇特技 ×1 |",
        "",
        "---",
        "",
        "## 三、四类技能与特技递进",
        "",
        "| 类型 | 战术目标 | 普通技能1 | 普通技能2（被动） | 稀有特技 | 史诗特技 | 传奇特技 |",
        "|:---|:---|:---|:---|:---|:---|:---|",
        "| **攻击** | 输出/击杀 | 平直/高抛点射 | 战意凝集（12s/4s） | 双联点射（随普攻） | 连锁穿透（锁定最低血敌） | 高空重击（10s独立间隔） |",
        "| **防御** | 护墙/减伤 | 平直/高抛点射 | 铁壁（10s/5s，MISS飘字） | 单格护墙 / 重盾护壁 | 三格盾带 | 全局圣域 / 天穹护盾（10s） |",
        "| **补给** | 回血 | 平直/高抛点射 | 应急包扎（10s，20%自疗） | 战地包扎 | 群体复苏 | 满血圣疗 / 幽魂还魂（20s） |",
        "| **加速** | 攻速/弹速 | 平直/高抛点射 | 迅捷装填（10s/5s） | 速射补给 | 弹速增压 | 狂热号令 / 巨型炸弹（15s） |",
        "",
        "### 3.1 普通技能2 被动触发（L1）",
        "",
        "| 定位 | 技能名 | 触发间隔 | 持续时间 | 效果概要 |",
        "|:---|:---|:---:|:---:|:---|",
        "| 攻击 | 战意凝集 | 12秒 | 4秒 | 自身攻击力 +8%（品质缩放） |",
        "| 防御 | 铁壁 | 10秒 | 5秒 | 抵挡平直弹道；成功显示 **MISS** 飘字 |",
        "| 补给 | 应急包扎 | 10秒 | 即时 | 自身恢复20%最大生命 |",
        "| 加速 | 迅捷装填 | 10秒 | 5秒 | 发射频率 +8% |",
        "",
        "### 3.2 传奇主动特技间隔（独立于普攻）",
        "",
        "| 技能 | 代表英雄 | 间隔 | 说明 |",
        "|:---|:---|:---:|:---|",
        "| 高空重击 | 龙焰女王、永冬之王、幻影刺客等 | **10秒** | 高抛重击，不跟随角色普攻间隔 |",
        "| 幽魂还魂 | 幽灵船长 | **20秒** | 复苏1张我方阵亡兵卡，50%血量 |",
        "| 巨型炸弹 | 爆破鬼才 | **15秒** | 周围4格伤害，邻格溅射40% |",
        "| 天穹护盾 | 天穹 | **10秒** | 激活5秒，抵御高抛炮击 |",
        "",
        "### 3.3 锁定目标定义",
        "",
        "| 锁定键 | 含义 | 适用示例 |",
        "|:---|:---|:---|",
        "| `lowestHpEnemyOnField` | 锁定场上血量最低的敌方兵卡 | 史诗「连锁穿透」 |",
        "| `lowestHpAllyOnField` | 锁定场上血量最低的友军兵卡 | 传奇「满血圣疗」 |",
        "| `allyDeadCard` | 我方阵亡兵卡 | 传奇「幽魂还魂」 |",
        "",
        "### 3.4 普通技能3 · 种族克制（被动）",
        "",
        "每位战斗英雄 L1 拥有 **普通技能3·种族克制**，按自身种族对克制目标 **+10% 伤害**（与 `bond.json` / `battle-rules.js` 一致）：",
        "",
        "| 自身种族 | 克制目标 | 技能描述 |",
        "|:---|:---|:---|",
        "| **人族** | 机械（含建筑） | 对机械单位伤害 +10% |",
        "| **机械** | 兽族 | 对兽族单位伤害 +10% |",
        "| **兽族** | 亡灵 | 对亡灵单位伤害 +10% |",
        "| **亡灵** | 人族 | 对人族单位伤害 +10% |",
        "",
        "> 采矿机等资源卡无普通技能1/3，仅有矿脉（普通技能2）。",
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
        "| **重型盾·重盾护壁** | 仅 `flat` | 自身1格挡平直；后方建筑免伤；**MISS** 飘字 |",
        "| **天穹·天穹护盾** | `flat`（被动）+ `arc`（激活） | 周围4格挡平直；每**10秒**激活5秒挡高抛；**MISS** 飘字 |",
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
        "### 6.2 升级消耗",
        "",
        "| 特技档 | 货币 | 说明 |",
        "|:---|:---:|:---|",
        "| **稀有** | **金币** | `gold ≈ heroGoldNeed × 0.85`（参考同级英雄升级） |",
        "| **史诗** | **钻石** | 固定阶梯 200→380→620→**980** |",
        "| **传奇** | **钻石** | 固定阶梯 280→520→880→**1480** |",
        "",
        f"效果曲线：`effect(L) = base × (1 + {SPECIAL_SCALING_PER_LEVEL} × (L-1))`",
        "",
        f"充值参考：{upgrade.get('diamondCnyReference', '')}。",
        "旧公式（英雄金币×0.045×溢价）在传奇末档会破万钻（约¥2700+），已废弃。",
        "",
        "#### 稀有 · 金币",
        "",
        "| 升级 | 金币 | 参考英雄金币 |",
        "|:---|:---:|:---:|",
    ]

    for row in upgrade.get("goldCost", []):
        slot_cn = {"rare": "稀有", "epic": "史诗", "legendary": "传奇"}.get(row["slot"], row["slot"])
        lines.append(
            f"| {slot_cn} L{row['fromLevel']}→L{row['toLevel']} | **{row['goldCost']}** | {row.get('heroGoldReference', '—')} |"
        )

    lines += [
        "",
        "#### 史诗 / 传奇 · 钻石",
        "",
        "| 特技档 | 升级 | 钻石 | 约合 | 折后(看满3次广告) |",
        "|:---|:---:|:---:|:---:|:---:|",
    ]

    for row in upgrade.get("diamondCost", []):
        slot_cn = {"rare": "稀有", "epic": "史诗", "legendary": "传奇"}.get(row["slot"], row["slot"])
        base = row["diamondCost"]
        disc = round(base * 0.7)
        cny = row.get("priceCnyReference", round(base * 0.1, 1))
        lines.append(
            f"| {slot_cn} | L{row['fromLevel']}→L{row['toLevel']} | **{base}** | ¥{cny} | **{disc}** |"
        )

    ad = upgrade.get("adDiscount", {})
    lines += [
        "",
        "### 6.3 广告抵扣（史诗/传奇钻石升级）",
        "",
        "| 规则 | 值 |",
        "|:---|:---|",
        f"| 每次抵扣 | **{int(ad.get('percentPerAd', 0.1) * 100)}%** |",
        f"| 每日次数 | **{ad.get('maxAdsPerDay', 3)}** 次 |",
        f"| 冷却 | **{ad.get('cooldownSec', 3600) // 3600}** 小时/次 |",
        f"| 上限 | **{int(ad.get('maxDiscountPct', 0.3) * 100)}%** |",
        f"| 生效 | 仅当日（每日零点重置） |",
        "",
        "**客户端交互**",
        "",
        "1. 用户点击「看广告抵扣10%」→ 播放广告成功后，按钮下方展示：**抵扣仅今日生效**",
        f"2. 每看完 1 次：当日累计抵扣 +10%；冷却 {ad.get('cooldownSec', 3600) // 3600} 小时后可再看",
        f"3. 看完 {ad.get('maxAdsPerDay', 3)} 次后：广告按钮文案变为 **{ad.get('buttonExhaustedLabel', '已抵扣30%')}**",
        "4. 升级按钮上的钻石数显示为折后价：`ceil(原价 × (1 - 当日抵扣%))`",
        "",
        "示例（传奇 L4→5）：原价 **1480** 钻 → 看满 3 次后 **1036** 钻",
        "",
        "### 6.4 特技等级曲线示例（传奇高空重击 atkPct，base=0.25）",
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
        "| `factionCounterDamagePct` | 克制 | 对克制种族伤害 +10%（普通技能3） |",
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
        "| 英雄 | 品质 | 种族 | 定位 | 攻击L1 | 生命L1 | 发射L1 | 弹道速L1 | 间隔 | 弹道 | 技能1 | 技能2 | 技能3 | 特技 |",
        "|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|:---|:---|",
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
            f"| {sk.get('normal_1', '—')} | {sk.get('normal_2', '—')} | {sk.get('normal_3', '—')} | {sp} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 十、技能一览速查表",
        "",
        "| 英雄 | 品质 | 种族 | 定位 | 弹道 | 普通技能1 | 普通技能2 | 普通技能3 | 特技 | 解锁 | 高抛 |",
        "|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---:|",
    ]

    for hid in sorted(heroes.keys()):
        h = heroes[hid]
        sk = h["skills"]
        normal2 = skill_by_id.get(sk.get("normal_2"), {})
        normal3 = skill_by_id.get(sk.get("normal_3"), {})
        basic = skill_by_id.get(sk.get("normal_1"), {})
        special_id = sk.get("rare") or sk.get("epic") or sk.get("legendary")
        special = skill_by_id.get(special_id, {}) if special_id else {}
        arc = "✅" if special.get("attackTrajectory") == "arc" else "—"
        unlock_lv = special.get("unlockLevel", "—") if special else "—"
        lines.append(
            f"| {h['name']} | {QUALITY_CN[h['quality']]} | {h.get('factionLabel', '—')} | {h['categoryLabel']} "
            f"| {h['combatStats'].get('projectileStyle', '—')} "
            f"| {(basic.get('name') or '—').split('·')[-1] if basic else '—'} "
            f"| {(normal2.get('name') or '—').split('·')[-1]} "
            f"| {(normal3.get('name') or '—').split('·')[-1] if normal3 else '—'} "
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
        lines.append("#### 普通技能1（主动攻击）")
        lines.append("")
        lines.append(skill_block(skill_by_id.get(sk.get("normal_1"))))
        lines.append("")
        lines.append("#### 普通技能2（被动）")
        lines.append("")
        lines.append(skill_block(skill_by_id.get(sk.get("normal_2"))))
        lines.append("")
        lines.append("#### 普通技能3（种族克制）")
        lines.append("")
        lines.append(skill_block(skill_by_id.get(sk.get("normal_3"))))
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
        "",
        "**维护流程**",
        "",
        "改配表逻辑后：`python3 scripts/gen-skill-bond-config.py`（生 JSON + 本文档）",
        "",
    ]

    return "\n".join(lines)
