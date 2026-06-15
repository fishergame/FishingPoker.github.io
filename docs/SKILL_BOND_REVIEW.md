# 技能 · 羁绊数值审查（接入前）

> 配表：`skill.json` · `bond.json` · `heroBattle.json`
> 生成：`python3 scripts/gen-skill-bond-config.py`

---

## 一、当前状态

| 模块 | 文件 | 状态 |
|:---|:---|:---|
| 主城 HP / 对局时长 | `battleBalance.json` | ✅ 已落地 |
| 英雄 L1 属性 | `heroes-config.js` | ✅ |
| 英雄升级 | `heroLevel.json` | ✅ |
| **羁绊** | `bond.json` | ✅ 初版 |
| **技能** | `skill.json` | ✅ 骨架（每英雄5槽） |
| 战斗接入 | `battle-rules.js` | ⚠️ 仍用品质被动模板 |

---

## 二、羁绊配置摘要

**规则：** 2 / 4 / 6 张激活；**4 张时同时激活 2 档+4 档**；采矿机不计入。

| 羁绊 | 2张 | 4张 | 6张 |
|:---|:---|:---|:---|
| 魏 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 蜀 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 吴 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 群雄 | atkPct5% | atkPct8%+unitHpPct5% | atkPct12%+unitHpPct8%+cityDamagePct5% |
| 近战 | unitHpPct6% | unitHpPct10%+damageReductionPct5% | unitHpPct15%+damageReductionPct8% |
| 远程 | atkPct6% | atkPct10%+atkSpeedPct5% | atkPct15%+atkSpeedPct8% |

---

## 三、技能效果类型与数值边界

| 效果 type | 推荐区间 | 说明 |
|:---|:---|:---|
| `atkPct` | 5%–25% | 单技能单条 |
| `atkSpeedPct` | 5%–20% | 单技能单条 |
| `splashPct` | 10%–35% | 单技能单条 |
| `cityDamagePct` | 5%–20% | 单技能单条 |
| `unitHpPct` | 5%–20% | 单技能单条 |
| `damageReductionPct` | 5%–20% | 单技能单条 |
| `dotPctPerSec` | 2%–8% | 单技能单条 |
| `lifestealPct` | 5%–15% | 单技能单条 |

**技能槽：** 普通×2（L1） + 史诗×2（L8/L15） + 传奇×1（L20）

---

## 四、与主城血量的关系（重点）

主城 HP 已按 **1.15^等级** 与攻击同步成长，默认编队清场后攻城约 **45% 对局时长**。

接入技能/羁绊后需额外乘算：

```
实际攻城DPS ≈ 基础DPS × (1 + 羁绊攻% + 技能攻%) × (1 + 对城伤害%)
建议合计上限：≤ 1.45×（见 battleBalance.json 建议）
```

| 风险 | 说明 | 建议 |
|:---|:---|:---|
| 羁绊6+远程6双满 | 攻击加成可达 ~27% | 加成用**加算**并 cap 35% |
| 多传奇「破城」叠加 | 对城伤害线性叠加 | 全队对城加成 cap 25% |
| 溅射/多段 | 清场更快 → 更早攻城管 | 溅射不对主城生效 |
| 两套战斗数值 | flip 模板 vs 37 英雄 | 统一读 `heroes-config` + `skill.json` |

---

## 五、接入清单（开发）

1. `battle-rules.js`：伤害结算读取 `heroBattle.json` + `skill.json`
2. 开战前根据卡组重算 `bond.json` 激活档
3. 对城伤害单独通道，应用 `cityDamagePct`
4. 主城 HP / 时长从 `BattleBalanceConfig` 按竞技场读取
5. 禁用：溅射、DOT 对主城直接生效（仅对单位）

