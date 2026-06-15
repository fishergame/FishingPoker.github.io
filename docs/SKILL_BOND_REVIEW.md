# 技能 · 羁绊数值审查

> 配表：`skill.json` · `bond.json` · `heroBattle.json`
> 生成：`python3 scripts/gen-skill-bond-config.py`

---

## 一、翻卡技能体系（v2）

**每英雄 3 技能槽：** 普通（L1）· 史诗（L8）· 传奇（L20）；升级逻辑不变（技能最高 10 级，`scalingPerSkillLevel` 2%）。

**四类定位：**

| 定位 | 战术目标 | 普通 | 史诗 | 传奇 |
|:---|:---|:---|:---|:---|
| 清场 | 消灭敌方兵卡、打开攻城窗口 | 攻击% | 溅射 | 部署突袭/处决/剧毒 |
| 守门 | 拖延、保护后排翻卡 | 生命% | 减伤 | 嘲讽 |
| 破城 | 清场后拆主城 | 攻速% | 对单位攻击% | 对城伤害% |
| 节奏 | 多翻、多铺 | 返费/部署金 | 击杀返金 | 翻开相邻 |

**定位分布：** 清场 14 · 守门 9 · 破城 10 · 节奏 4

---

## 二、效果类型与 phase

| 效果 type | 区间 | phase 建议 |
|:---|:---|:---|
| `atkPct` | 5%–25% | always / field_only |
| `atkSpeedPct` | 5%–20% | always |
| `splashPct` | 10%–35% | field_only |
| `cityDamagePct` | 5%–20% | siege_only |
| `unitHpPct` | 5%–20% | always |
| `damageReductionPct` | 5%–20% | field_only |
| `dotPctPerSec` | 2%–8% | field_only |
| `lifestealPct` | 5%–15% | — |
| `deployBurstPct` | 30%–70% | on_deploy |
| `killGold` | 5–25 | on_kill |
| `flipRefundPct` | 10%–35% | on_deploy |
| `revealAdjacent` | 1–2 | on_deploy |
| `deployGold` | 8–30 | on_deploy |
| `taunt` | 1–1 | always |
| `executeBonusPct` | 20%–50% | field_only |

---

## 三、羁绊摘要

| 羁绊 | 2张 | 4张 | 6张 |
|:---|:---|:---|:---|
| 魏 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 蜀 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 吴 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 群雄 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 近战 | unitHpPct6% | unitHpPct10%+damageReductionPct5% | unitHpPct15%+damageReductionPct8% |
| 远程 | atkPct6% | atkPct10%+atkSpeedPct5% | atkPct15%+atkSpeedPct8% |

---

## 四、数值红线

- 对城 DPS 合计建议 ≤ **1.45×**
- 全队 `cityDamagePct` cap **25%**
- 攻击类加成 cap **35%**
- 溅射 / DOT / 部署突袭 **不对主城**

---

## 五、战斗接入

1. `battle-skill-runtime.js` 汇总技能加成
2. `battle-rules.js` 按 `phase` 分支结算
3. 翻卡即从卡组抽英雄，不再用品质随机模板

