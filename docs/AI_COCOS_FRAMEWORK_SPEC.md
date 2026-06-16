# 《代号x》Cocos 客户端框架规格（AI 实施文档）

> **用途**：供 AI / 开发者在 Cocos Creator 中搭建项目骨架。  
> **来源**：基于 `260611《代号x》系统-战斗/卡牌/商店（一级页）.docx` V2.0 整理。  
> **当前阶段**：第一步「纯前端单机版」+ 第二步「可接后端」的代码结构；**局内战斗逻辑后续补充**。

---

## 0. 系统总框架

养成（37 张角色卡升级）与竞技（15 个竞技场 / 15 档段位 / 每月赛季）的关系见 **[`docs/SYSTEM_FRAMEWORK.md`](SYSTEM_FRAMEWORK.md)**。

---

## 0.1 开发路线（必须遵守）

### 第一步：纯前端单机版（当前目标）

| 能力 | 一期实现方式 |
|------|-------------|
| 进入游戏 | Launch → Loading → MainShell（**3 Tab** 壳） |
| 抽卡 | `GachaService` 本地权重随机 + 结果页 |
| 养成 | 英雄升级 / 神器升级 / 牌组替换（本地校验） |
| PVE | 「玩家对局」→ **BattleStub 场景**（占位，不接真实战斗） |
| 存档 | `SaveService` → 抖音 `tt.setStorage` / 浏览器 `localStorage` |

### 第二步：可接后端（接口先行，本地实现）

所有业务通过 Service 接口访问，一期用 `LocalXxxService`，后期换 `HttpXxxService`：

```
IUserService      → 登录、昵称、头像、UID
ISaveService      → 读写存档、缓存秒开
IGachaService     → 召唤（神器十连、广告十连 mock）
IBattleService    → 匹配、结算、奖杯/经验（一期 mock）
ILobbyService     → 大厅聚合包
ICardService      → 卡牌聚合包、升级、装备、替换
IShopService      → 商品列表、购买（mock 支付）
IRedDotService    → 红点聚合（一期本地计算，结构对齐服务端） 
IMailService      → 邮件（一期 mock 数据）
```

### 第三步：上线前补最小后端

仅：用户存档、排行榜、公告、活动配置。**不做**公会、聊天、拍卖、实时匹配。

### 一期明确不做 / 仅占位

- **局内战斗完整逻辑**（翻牌、火球冰球、占城等）→ `BattleStubScene`
- **领地 / 排名 Tab** → **已移除**（不在一期范围）
- **真实支付 / 广告 SDK** → mock 成功回调
- **注销账号**
- **多语言完整翻译** → 先中文 + i18n key 结构

---

## 1. 产品概览

| 项 | 说明 |
|----|------|
| 游戏类型 | 卡牌养成 + 对战（占城类局内，后续文档补充） |
| 卡牌规模 | **37 张**角色/道具卡 + **13 张**神器卡 |
| 平台目标 | **抖音小游戏**（Cocos Creator 3.x，竖屏） |
| 设计分辨率 | 750 × 1334（或 720 × 1280，统一竖屏） |
| 一级导航 | **3 Tab**，**左右滑切换**：商店 / 卡牌 / **战斗(默认)** |
| 二级导航 | **仅点击切换**，不参与一级滑动手势 |

---

## 2. Cocos 工程结构（建议）

```
assets/
├── scenes/
│   ├── Launch.scene          # 启动、读档、进 MainShell
│   ├── MainShell.scene       # 3 Tab 容器 + 顶部资源栏 + 底栏（合并在 Launch 场景）
│   ├── BattleStub.scene      # PVE/匹配占位（后续换 Battle.scene）
│   └── sub/                  # 可选：独立弹窗场景
├── scripts/
│   ├── app/                  # GameApp, EventBus, Constants
│   ├── framework/            # UIManager, SceneManager, Pool, Audio
│   ├── services/             # 接口 + Local 实现 + Http 占位
│   │   ├── interfaces/
│   │   ├── local/
│   │   └── http/             # 空壳，后期实现
│   ├── models/               # TS 类型 / 存档结构
│   ├── config/               # ConfigLoader, tables
│   ├── modules/
│   │   ├── lobby/            # 战斗一级页
│   │   ├── card/             # 卡牌一级页（4 子 Tab）
│   │   ├── shop/             # 商店一级页（3 子模块）
│   │   └── common/           # 弹窗、奖励、开箱、货币不足
│   └── battle/               # 仅占位，后续扩展
├── resources/
│   ├── config/               # JSON 配表
│   ├── prefabs/
│   └── i18n/
└── textures/                 # 占位图即可
```

### 核心单例

```typescript
// GameApp.ts — 启动时注册 Service，注入 Config
class GameApp {
  static user: IUserService;
  static save: ISaveService;
  static lobby: ILobbyService;
  static card: ICardService;
  static shop: IShopService;
  static gacha: IGachaService;
  static battle: IBattleService;
  static redDot: IRedDotService;
}
```

---

## 3. 场景与 UI 架构

### 3.1 MainShell（主壳）

```
MainShell
├── TopBar（全局常驻）
│   └── CurrencyBar（金币/木材/钻石）
├── ContentArea（PageView，3 页）
│   ├── ShopPage
│   ├── CardPage
│   └── LobbyPage      ← 默认 index=2
└── BottomNav（3 Tab 高亮）
```

**手势规则**：
- 一级页：左右滑 / 点 Tab 切换，**不重新登录、不销毁 Service**
- 切换 Tab 时：若该页未加载数据，触发对应 `enterPage()` 拉聚合包（一期读存档+本地 mock）

### 3.2 战斗一级页 — LobbyPage（主大厅）

**布局（自上而下）**：

| 区域 | 元素 | 交互 |
|------|------|------|
| 顶部 | 已在 TopBar | 货币「+」→ ShopPage 并 scrollTo 对应货币 |
| 左上 | 个人信息卡（头像、昵称、战力、段位、奖杯） | 打开 ProfilePopup |
| 右上 | 设置「≡」 | SettingsPopup |
| 左中 | 运营活动图标列表 | EventPopup（配置驱动） |
| 中央 | 竞技场岛屿、名称、奖杯进度、今日可得、「玩家对局」 | 对局入口；点击岛屿区 → ArenaDetailPopup |
| 右中 | 运营活动图标列表 | 同左 |
| 中下 | 4 宝箱槽 | ChestSlot × 4 |
| 底部 | BottomNav | 当前高亮「战斗」 |

**Lobby 聚合数据包 `LobbyAggregateData`（一期本地模拟）**：

```typescript
interface LobbyAggregateData {
  profile: PlayerProfile;
  currencies: Record<CurrencyType, number>;
  arena: ArenaState;           // 当前竞技场、奖杯、段位
  chestSlots: ChestSlotState[]; // 长度 4
  heroAccountLevel: number;    // 账号英雄等级（非单卡等级）
  heroAccountExp: number;
  redDots: RedDotMap;
  events: EventEntry[];        // 左右侧活动入口
  mailUnread: number;
  combatPower: number;         // 总战力
}
```

**子模块清单（按实现优先级）**：

| P | 模块 | 一期范围 |
|---|------|----------|
| P0 | 布局 + 聚合数据刷新 | 必须 |
| P0 | 玩家对局按钮 → BattleStub | 必须 |
| P0 | 货币栏 + 不足弹窗跳转商店 | 必须 |
| P1 | 4 宝箱槽状态机 | 简化计时，广告 mock |
| P1 | 个人中心（头像/昵称/战旗/统计） | 头像 36 角色；昵称本地校验 |
| P1 | 设置（音效/音乐/帧率本地存储） | 邮件/公告 mock 列表 |
| P2 | 英雄等级弹窗 + 升级奖励 | 自动领取 + 通用开箱 UI |
| P2 | 竞技场详情 + 奖杯奖励 | 15 竞技场配表 |
| P2 | 运营活动（新手礼包/月卡/通行证） | UI 骨架 + mock 购买 |
| P3 | 匹配动画（寻找对手→321） | 直接进 BattleStub |

**宝箱状态机（必须实现枚举）**：

```
Empty → PendingUnlock → Countdown → ReadyToOpen → Opening → Empty
```

- 胜利掉落 → 占 Empty 槽
- 广告 -30min、钻石 instant open（mock）
- 可开启 → 红点

**账号英雄等级**：
- 1–100 级，经验来自对战（BattleStub 结算 mock）
- 升级后**自动领取**奖励 → 通用 `RewardFlow` → 开箱动效
- 首次获得传奇英雄 → `NewLegendHeroPopup`

---

### 3.3 卡牌一级页 — CardPage

**4 个子 Tab（点击切换，不滑动）**：英雄 | 神器 | 背包 | 表情

**Card 聚合数据包 `CardAggregateData`**：

```typescript
interface CardAggregateData {
  heroes: HeroInstance[];       // 持有、等级、碎片、技能等级、new/viewed
  decks: DeckConfig[];          // 5 组，每组 8 heroId
  activeDeckId: number;         // 1-5，出战中
  bonds: BondActiveState[];     // 服务端/本地重算结果
  artifacts: ArtifactInstance[];
  equippedArtifactId: number;   // 一期仅 1 槽
  artifactSummon: SummonState;  // 召唤等级、经验、广告次数
  bag: BagItem[];
  emojis: EmojiState;
  redDots: RedDotMap;
  tutorialStepId?: number;
}
```

#### 3.3.1 英雄子页

**牌组**：
- 5 组 × 8 槽；默认 5 组相同（注册赠送 8 张初始卡）
- **约束**：至少 1 普通 + 1 稀有 + 1 史诗 + **铸币坊（金矿）必装**
- 传奇不强制；铸币坊不计入羁绊统计
- 切换出战组：点 Tab → 请求（一期本地）→ 「出战中」徽标移动

**卡牌状态（UI 角标优先级）**：`MAX > 锁 > 升级↑/红点 > NEW`

**详情弹窗**：阵营、近/远、5 技能槽、属性、升级、装备

**升级**：碎片 + 金币；动效：光效 + 单卡战力滚动 +（若在出战组）总战力滚动

**替换流程**：
1. 详情点「装备」→ 进入替换模式
2. 牌组槽晃动；底部卡栏收起
3. 违反约束 → tips（如「卡组必须包含至少1张史诗卡牌」）
4. 成功 → 重算羁绊

**羁绊（6 种）**：
- 阵营：魏 / 蜀 / 吴 / 群雄
- 位置：近战 / 远程
- 每羁绊 3 段：2 / 4 / 6 张激活；达到 4 同时激活 2+4

#### 3.3.2 神器子页

- **解锁**：竞技场 3 级（一期可配置为账号等级或奖杯阈值）
- **装备**：仅 **1 个**神器槽，必须佩戴，无卸下（只能替换）
- 默认赠送：龙焰战歌
- **召唤**：广告十连（mock 广告）+ 钻石十连；召唤等级影响权重
- **升级**：碎片 + 水晶；最高 50 级
- 重复 → 转碎片

#### 3.3.3 背包子页

- 4 列网格；按获取时间倒序
- 点击 → 详情气泡（无复杂使用逻辑一期可只展示）

#### 3.3.4 表情子页

- 4 装备槽；默认 6 个免费 emoji
- 文本表情仅局内，不可装备
- 替换流程：选中 → 点槽位 → 请求保存

---

### 3.4 商店一级页 — ShopPage

> 配表：`shop.json` v2.0.0 · 文档：`docs/SHOP_AND_ECONOMY.md` · 运行时：`shop-config.js`

**子模块（顶 Tab）**：

| 模块 | tabId | 内容 |
|------|-------|------|
| **礼包** | `giftPacks` | 四阵营卡牌礼包（人族/兽族/亡灵/机械）；广告转盘获取；**无月卡、无神器** |
| **基础** | `basic` | **每日优惠**、**钻石转盘四档**（广告转盘）、**砖头四档**（1 广告 + 3 钻石）；**无通用卡包** |
| 竞技场 | `arena` | 一期不做 |

**基础页（`basic`）**：
- **每日优惠**：保留原 6 格 + 轮换池
- **钻石转盘**（无限购）：120 / 280 / 720 / 1680 四档；均转盘+看广告；脚本概率/连败保底/暴击见 `docs/SHOP_AND_ECONOMY.md` §7
- **砖头四档**（无限购）：看广告 50 砖；99 钻→100 砖；500 钻→600 砖；2000 钻→3000 砖

**礼包页（`giftPacks`）**：
- 4 个礼包，角色池来自 `bond.json`，**互不重叠**
- 每礼包每日 **4 次**购买；IAP 未接入时统一 **转盘 + 看广告**
- 转盘四格各 25% 展示；当日保底：1 次免费、1 次看 1 广告、1 次看 2 广告、1 次看 3 广告
- 领取后通用奖励页；按阵营刷新传奇预览与其他卡牌
- 售罄置灰沉底；Toast「今日购买已达上限，请明日再来。」

**购买流程（一期）**：
```
点击购买 → 转盘 → (免费领取 | 看广告×N) → ShopService.claimGiftPack(productId)
→ RewardFlow → 刷新礼包展示 / 售罄态
```

**广告未完成**：回到转盘页，保留指针档位与已看广告进度；主按钮「看广告」/「继续抽奖」+ 次按钮「放弃机会」。

**货币不足**：`CurrencyLackPopup` → 跳转 ShopPage 并 `scrollToProduct(currencyType)`

**从大厅跳转**：TopBar「+」传入 `{ focus: 'diamond' | 'gold' | ... }`

---

## 4. 数据模型（核心 TypeScript）

### 4.1 枚举

```typescript
enum CurrencyType { Gold, Wood, Rune, Crystal, Diamond }
enum Quality { Common, Rare, Epic, Legend }  // 绿蓝紫黄
enum Faction { Wei, Shu, Wu, Qun }
enum RangeType { Melee, Ranged }
enum ChestSlotState { Empty, PendingUnlock, Countdown, ReadyToOpen, Opening }
enum TabId { Shop, Card, Battle, Territory, Rank }
enum CardSubTab { Hero, Artifact, Bag, Emoji }
```

### 4.2 英雄 / 神器

```typescript
interface HeroConf {
  heroId: number;
  nameKey: string;
  faction: Faction;
  range: RangeType;
  quality: Quality;
  levelMax: number;
  fragmentNeed: number[];
  goldNeed: number[];
  attrs: HeroAttrs[];          // 每级
  skillNormalId: number[];
  skillEpicId: number[];
  skillEpicUnlockLv: number[];
  skillLegendId: number;
  skillLegendUnlockLv: number;
  basePower: number;
  isMintBase: boolean;         // 铸币坊
}

interface HeroInstance {
  heroId: number;
  level: number;
  fragments: number;
  skillLevels: Record<number, number>;
  isNew: boolean;
  viewed: boolean;
}

interface ArtifactConf { /* artifactId, quality, levelMax, effect[], fragmentNeed[], crystalNeed[] */ }
interface ArtifactInstance { artifactId: number; level: number; fragments: number; isNew: boolean; }

interface DeckConfig {
  deckId: number;              // 1-5
  heroIds: number[];           // length 8
}
```

### 4.3 存档根结构 `SaveData`

```typescript
interface SaveData {
  version: number;
  uid: string;
  profile: PlayerProfile;
  currencies: Record<CurrencyType, number>;
  heroes: HeroInstance[];
  decks: DeckConfig[];
  activeDeckId: number;
  artifacts: ArtifactInstance[];
  equippedArtifactId: number;
  summon: SummonState;
  bag: BagItem[];
  emojis: EmojiSlotConfig[];
  arena: ArenaState;
  chestSlots: ChestSlotState[];
  heroAccountLevel: number;
  heroAccountExp: number;
  stats: BattleStats;
  mail: MailItem[];
  shop: ShopPurchaseState;      // 月卡剩余天数、已购礼包等
  redDotViewed: Record<string, boolean>;
  settings: AudioSettings;
  lastLoginTime: number;
}
```

---

## 5. Service 接口（Local 一期实现要点）

### 5.1 ISaveService

```typescript
interface ISaveService {
  load(): Promise<SaveData>;
  save(data: Partial<SaveData>): Promise<void>;
  getCache(): SaveData | null;  // 秒开
}
```

- 启动：`getCache()` 渲染 → `load()` 合并服务器/本地

### 5.2 ICardService

```typescript
interface ICardService {
  getAggregate(): Promise<CardAggregateData>;
  upgradeHero(heroId: number, reqId: string): Promise<HeroUpgradeResult>;
  upgradeSkill(heroId: number, skillId: number, reqId: string): Promise<...>;
  replaceDeckCard(deckId: number, slotIndex: number, heroId: number, reqId: string): Promise<DeckConfig>;
  setActiveDeck(deckId: number, reqId: string): Promise<void>;
  equipArtifact(artifactId: number, reqId: string): Promise<void>;
  upgradeArtifact(artifactId: number, reqId: string): Promise<...>;
  replaceEmoji(slotIndex: number, emojiId: number, reqId: string): Promise<void>;
}
```

**本地实现必须**：
- `reqId` 30s 去重
- 扣资源 + 改数据 **原子**（单事务写存档）
- 返回**差量**（仅变更字段 + redDots）

### 5.3 IGachaService

```typescript
interface IGachaService {
  summonArtifactTen(poolId: number, payType: 'ad' | 'diamond', reqId: string): Promise<SummonResult>;
}
```

### 5.4 IBattleService（一期 stub）

```typescript
interface IBattleService {
  startMatch(): Promise<{ battleId: string }>;
  finishBattle(result: 'win' | 'lose'): Promise<BattleSettlement>;
}

interface BattleSettlement {
  trophyDelta: number;
  expDelta: number;
  chestDropped?: ChestDrop;
  todayEarnings: number;
}
```

- `BattleStubScene` 点「结束」调用 `finishBattle` → 回 Lobby → 触发等级/竞技场奖励队列

### 5.5 ILobbyService

```typescript
interface ILobbyService {
  getAggregate(): Promise<LobbyAggregateData>;
  unlockChest(slotIndex: number, reqId: string): Promise<void>;
  openChest(slotIndex: number, reqId: string): Promise<RewardItem[]>;
  speedUpChestAd(slotIndex: number): Promise<void>;
  claimArenaReward(rewardId: string, reqId: string): Promise<RewardItem[]>;
}
```

---

## 6. 通用 UI 组件（common 模块）

| 组件 | 说明 |
|------|------|
| `SystemPopup` | 标题 + 正文 + 1~2 按钮 + 遮罩关闭 |
| `WeakTips` | 短提示 toast |
| `CurrencyLackPopup` | 动态货币类型 + 跳转商店 |
| `RewardFlow` | 请求→发奖→表现 四段式 |
| `ChestOpenFlow` | 晃动→开启动效→逐张展示→结果页 |
| `NewCardReveal` | 首次获得新卡/传奇 |
| `RedDot` | 普通点 / 数字点（最大 4） |
| `QualityFrame` | 绿蓝紫黄菱形(角色/神器) / 方形(道具) |
| `NetworkReconnectMask` | 重连遮罩（一期可简化） |
| `LoadingPlaceholder` | 数据 `--` 占位 |

### 数字显示规则

| 场景 | 规则 |
|------|------|
| 资源栏、商店卡片 | 缩写：10K, 999K, 1M, 999M, B |
| 个人中心、统计、牌组战力 | **不缩写**，超出缩字号 |
| 奖杯（个人中心/战旗） | 不缩略，如 `000/200` |

---

## 7. 配表 JSON（resources/config/）

一期至少准备（可先 mock 少量条目，结构完整）：

```
hero.json          # 37 英雄（含 1 铸币坊）
artifact.json      # 13 神器
skill.json
skillUpgrade.json
bond.json
deckDefault.json
arena.json         # 15 竞技场
rankTier.json      # 段位
chest.json
heroAccountLevel.json  # 1-100
currency.json
shop.json           # 礼包(四阵营) + 基础区商品；见 docs/SHOP_AND_ECONOMY.md
summonPool.json
summonLevel.json
emoji.json
avatar.json
banner.json          # 战旗
eventEntry.json      # 大厅左右活动入口
```

**加载**：`ConfigLoader.loadAll()` 在 Launch 完成；只读。

---

## 8. 红点系统（结构对齐服务端）

- **原则**：一期本地 `RedDotService.compute(save)`，字段结构与未来服务端一致
- **一级 Tab 红点**：Shop / Card / Battle 等有未处理项
- **Card 内**：Hero / Artifact / Bag / Emoji 子 Tab；数字红点 2–4 capped

关键触发（详见策划 doc）：
- 英雄：可升级、技能可升级、NEW 未查看
- 神器：可免费召唤、可升级、NEW
- 宝箱：ReadyToOpen
- 邮件：未读或未领附件 → 设置入口红点

消除：用户行为 + `viewed` 上报（一期写存档）

---

## 9. 请求 / 并发规范（全模块统一）

```typescript
// 所有写操作
interface WriteRequest {
  reqId: string;  // UUID
  // ...
}
```

- 客户端：请求前按钮禁用；500ms 内重复点击丢弃
- 服务端（后期）：reqId 30s 幂等；失败不本地扣资源
- 动效中断网：动效播完再展示结果；以存档/服务器为准

---

## 10. 抖音小游戏适配要点

```typescript
// platform/DouyinAdapter.ts
declare const tt: any;

class DouyinAdapter {
  static storage = {
    get(key: string) { return tt?.getStorageSync?.(key) ?? localStorage.getItem(key); },
    set(key: string, val: string) { tt?.setStorageSync?.(key, val) ?? localStorage.setItem(key, val); },
  };
  static share() { /* 未接入则隐藏分享按钮 */ }
  static showRewardedVideo(): Promise<boolean> { /* 一期 resolve(true) mock */ }
  static pay(productId: string): Promise<boolean> { /* 一期 mock 成功 */ }
}
```

- 竖屏：`cc.view.setOrientation(macro.ORIENTATION_PORTRAIT)`
- 安全区：TopBar / BottomNav 留刘海/ home indicator padding
- 包体：一期占位图 + 后续 AssetBundle 按模块拆分

---

## 11. AI 实施顺序（推荐 Sprint）

### Sprint 1 — 骨架
1. 创建 Cocos 3.x 工程，Douyin 构建模板
2. `GameApp` + `EventBus` + `ConfigLoader`
3. `SaveService` + 默认 `SaveData` 新档
4. `Launch` → `MainShell` + 5 Tab 滑动 + BottomNav

### Sprint 2 — 大厅
1. `TopBar` + `LobbyPage` 布局占位
2. `ILobbyService` local + 聚合刷新
3. 「玩家对局」→ `BattleStub` → mock 结算回大厅
4. `CurrencyLackPopup`

### Sprint 3 — 卡牌
1. `CardPage` 四 Tab 框架
2. 英雄列表 + 牌组 8 槽 + 5 Tab
3. 详情弹窗 + 升级 + 替换（含约束校验）
4. 羁绊条 + 详情弹窗（本地重算）

### Sprint 4 — 神器 & 抽卡
1. 神器列表 + 装备 + 升级
2. `GachaService` 十连 + 结果页 + 召唤等级
3. 背包 + 表情槽位

### Sprint 5 — 商店 & 养成闭环
1. Shop 三模块列表 + mock 购买
2. 宝箱四槽状态机 + 简化开箱
3. 英雄账号等级 + 奖励流
4. 设置 + 邮件/公告 mock
5. 红点全链路

### Sprint 6 —  polish
1. 竞技场详情 + 奖杯奖励 UI
2. 运营活动入口 mock
3. 存档版本迁移 `SaveData.version`
4. 性能：列表虚拟滚动、对象池

---

## 12. 与「局内战斗」的边界

| 模块 | 归属 | 说明 |
|------|------|------|
| 匹配入口、321 倒计时 | Lobby | 已有文档 |
| 结算：奖杯/经验/宝箱掉落 | IBattleService | 接口返回，BattleStub 模拟 |
| 出战牌组、羁绊、神器 | Card → Battle | 战斗开始时读取 `activeDeck` + `equippedArtifact` |
| 翻牌、占城、火球冰球 | **后续 Battle 文档** | 不在本 spec 实现 |
| 表情局内发送 | Battle | 读 emoji 槽配置 |

**BattleStubScene 最小 UI**：
- 显示当前出战牌组摘要
- 「胜利」「失败」按钮 → 调用 `finishBattle`
- 返回 Lobby 后依次弹：竞技场奖励 → 英雄等级升级 → 宝箱掉落（如有）

---

## 13. 商店文档补充（原文缺失部分的推断约定）

以下原文仅图片，AI 默认：

| 商品类型 | 字段 |
|----------|------|
| 货币包 | productId, currencyType, amount, priceDiamond/priceYuan, bonusFirst |
| 角色包/神器包 | productId, poolPreview[], price, limitCount |
| 竞技场礼包 | arenaId, unlockTrophy, items[], price, expireAt |
| 每日优惠 | dailyRefresh, discountPrice, originalPrice |

排序：礼包页按 `sortWeight` 降序（售罄沉底）；基础区按配置序。

---

## 14. 验收清单（第一步完成标准）

- [ ] 竖屏 MainShell，5 Tab 可滑可点，默认战斗页
- [ ] 新用户初始 8 卡牌组 + 默认神器 + 6 表情
- [ ] 卡牌页：换卡、升级、羁绊刷新、神器十连、装备
- [ ] 商店页：浏览 + mock 购买 + 货币跳转聚焦
- [ ] 大厅：对局 stub 结算 → 奖杯/经验/宝箱变化
- [ ] 存档重启后数据保留
- [ ] 所有写操作走 Service + reqId
- [ ] `HttpXxxService` 文件存在但空实现，便于替换

---

## 15. 参考原文档路径

```
/Users/sming/Desktop/testgame/260611《代号x》系统-战斗（一级页）.docx
/Users/sming/Desktop/testgame/260611《代号x》系统-卡牌（一级页）.docx
/Users/sming/Desktop/testgame/260611《代号x》系统-商店（一级页）.docx
```

提取纯文本备份：
```
260611《代号x》系统-战斗（一级页）.txt
260611《代号x》系统-卡牌（一级页）.txt
260611《代号x》系统-商店（一级页）.txt
```

---

*文档版本：V1.0 | 整理日期：2026-06-12 | 对应策划 V2.0（战斗/卡牌）、V1.0（商店）*
