# 战斗平衡：对局时长 · 主城血量 · 攻城模拟

> 配表：`battleBalance.json` · 生成：`python3 scripts/gen-battle-balance.py`
> 角色 L1 属性：`heroes-config.js` · 升级成长：`heroLevel.json`（statGrowthRate=1.15）

---

## 零、开局赠送卡组

> 单一数据源：`heroes-config.js → DEFAULT_DECK`（`getStarterGrantIds()`）
> 新号赠送 **8** 张，卡组容量 **8** 槽。

| # | id | 名称 | 品质 | 类型 | 阵营 |
|:---:|:---|:---|:---:|:---|:---|
| 1 | `dragon_knight` | 龙焰女王 | legendary | unit | — |
| 2 | `archer` | 见习女巫 | rare | unit | — |
| 3 | `infantry` | 重步兵 | rare | unit | — |
| 4 | `arrow_tower` | 高射塔 | rare | building | — |
| 5 | `bear_warrior` | 重锤卫士 | common | unit | — |
| 6 | `skeleton_warrior` | 骷髅刀盾兵 | common | unit | — |
| 7 | `gold_mine` | 采矿机 | common | resource | 无阵营 |
| 8 | `heavy_shield` | 重型盾 | rare | building | — |

阵营对照见 `bond.json`；`gold_mine` 不参与羁绊。

---

## 一、技能表在哪里？

### 1. 翻牌对战 · 按品质被动（已实现在 `battle-config.js`）

| 品质 | 模板 | 被动 | 描述 |
|:---|:---|:---|:---|
| 普通 | 步兵 | none | 无被动 |
| 稀有 | 弓手 | swift | 迅捷：攻速+10%（攻击间隔×0.9） |
| 史诗 | 重甲 | ironwall | 铁壁：受到伤害-15% |
| 传奇 | 龙骑 | splash | 破军：25% 伤害溅射相邻目标 |

### 2. 37 张命名英雄 · 独立技能（**尚未有独立 JSON 表**）

- 37 张命名英雄的独立技能表（skillNormalId / skillEpicId / skillLegendId）尚未落地为 JSON，设计见 docs/AI_COCOS_FRAMEWORK_SPEC.md；养成属性见 heroes-config.js + heroLevel.json statGrowthRate。
- 策划原文：`260611《代号x》系统-卡牌（一级页）.txt`（提及技能等级字段）
- 计划配表：`skill.json` / `skillUpgrade.json`（见 `docs/AI_COCOS_FRAMEWORK_SPEC.md`）

> 当前攻城模拟使用 **`heroes-config.js` 的 attack / attackSpeed**，不用翻牌模板数值。

---

## 二、对局时长（按竞技场）

| 场次 | 名称 | 时长 | 说明 |
|:---:|:---|:---:|:---|
| 1 | 青铜 | **1:30** | 90秒 |
| 2 | 白银 | **1:40** | 100秒 |
| 3 | 黄金 | **1:50** | 110秒 |
| 4 | 铂金 | **2:00** | 120秒 |
| 5 | 钻石 | **2:10** | 130秒 |
| 6 | 星耀 | **2:20** | 140秒 |
| 7 | 大师 | **2:30** | 150秒 |
| 8 | 宗师 | **2:40** | 160秒 |
| 9 | 王者 | **2:50** | 170秒 |
| 10 | 传奇 | **3:00** | 180秒 |

公式：`90 + (arenaId-1)*10, max 180`

---

## 三、主城血量 · 产金（独立养成）

- 主城 HP：`mainCity.json → round(1500 * 1.15^(mainCityLevel-1))`
- 产金/秒：`mainCity.json → round(2 * 1.10^(mainCityLevel-1))`
- 完整 1–30 级表：**[`docs/MAIN_CITY_PROGRESSION.md`](MAIN_CITY_PROGRESSION.md)** · 配表 `mainCity.json`

---

## 四、攻城模拟（清场后集火 · 主城等级=卡组等级）

**开局赠送**（8 张，`heroes-config.js → DEFAULT_DECK`）：`dragon_knight, archer, infantry, arrow_tower, bear_warrior, skeleton_warrior, gold_mine, heavy_shield`
**L1 编队攻城 DPS**：208.8

| 主城/卡组等级 | 主城 HP | 编队 DPS | 理论拆城(s) |
|:---:|:---:|:---:|:---:|
| L1 | 1,500 | 209 | 7.2s |
| L5 | 2,624 | 365 | 7.2s |
| L10 | 5,277 | 735 | 7.2s |
| L15 | 10,614 | 1478 | 7.2s |
| L20 | 21,348 | 2972 | 7.2s |
| L25 | 42,938 | 5977 | 7.2s |
| L30 | 86,363 | 12023 | 7.2s |

### 满配编队（8 张 L30 最高攻城 DPS）

卡牌：`blademaster, dragon_knight, dread_knight, panda_monk, helicopter, crusher, warlord, demon_lord` · DPS **44160**
· 拆 L30 主城（86,363 HP）约 **2.0s**

### 解读

- 主城 HP 与编队 DPS **同用 1.15 成长**时，理论拆城时间全等级约 **7.7s**（仅清场后集火段）。
- 实际对局含翻牌、清场、击杀判定；对局总时长由 **竞技场时长** 决定。
- 产金随主城等级（1.10/级），详见 `mainCity.json`。

