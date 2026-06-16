/** @typedef {'common'|'rare'|'epic'|'legendary'} HeroQuality */
/** @typedef {'hero'|'resource'|'mystery'} FlipPreviewType */
/** @typedef {'player'|'enemy'} Side */

const BattleConfig = {
  GRID_COLS: 9,
  GRID_ROWS: 6,
  MAIN_COL: 4,
  /** 敌方主城行（靠近中线一侧） */
  ENEMY_MAIN_ROW: 2,
  /** 我方主城行（下移一格，与敌方关于中线对称） */
  PLAYER_MAIN_ROW: 3,

  START_GOLD: 20,
  GOLD_PER_SEC: 2,
  /** 演示默认值；按场次/等级请读 battleBalance.json + BattleBalanceConfig */
  MAIN_CITY_HP: 200,
  MATCH_DURATION_SEC: 180,

  /**
   * 战斗节奏调节（改这几个就能整体变慢/变快）：
   * - COMBAT_PACE：攻击间隔倍率，越大出手越慢（1 = 模板原速）
   * - COMBAT_HP_SCALE：英雄血量倍率，越大越耐打
   * - COMBAT_ATK_SCALE：攻击力倍率，越小每下越轻
   * - PROJECTILE_DURATION：弹道飞行秒数，只影响视觉节奏
   */
  COMBAT_PACE: 1.55,
  COMBAT_HP_SCALE: 1.35,
  COMBAT_ATK_SCALE: 0.9,
  PROJECTILE_DURATION: 0.72,

  /** 敌方 AI 翻牌间隔（秒）；开局即战斗，与玩家并行 */
  ENEMY_FLIP_INTERVAL: 1.1,
  ENEMY_FLIP_RETRY: 0.35,

  /**
   * 双方共用战斗规则：
   * 仅当对方场上攻击卡牌（当前为英雄）全部消灭后，才可攻击对方主城。
   */
  CITY_ATTACK_REQUIRES_CLEAR_FIELD: true,

  /** 翻牌费用档位（角色格：低/中/高） */
  FLIP_COSTS: [50, 100, 250],

  /**
   * 新手前 N 局：低级角色格（50 金）额外开放传奇掉落。
   * playerMatchNumber = 已完成局数 + 1（本局序号，1 起算）。
   */
  NEWBIE_MATCHES: {
    enabled: true,
    maxMatchIndex: 3,
    storageKey: 'codename_x_battle_matches_played',
    /** 仅对 hero_low 费用生效 */
    heroLowCost: 50,
  },

  /**
   * 翻开费用 → 英雄品质概率（常规局，第 4 局起低级格不出传奇）。
   * 键 50_newbie：前 3 局低级格专用。
   */
  QUALITY_BY_COST: {
    50: { common: 0.55, rare: 0.45, epic: 0, legendary: 0 },
    '50_newbie': { common: 0.50, rare: 0.40, epic: 0.05, legendary: 0.05 },
    100: { common: 0.20, rare: 0.25, epic: 0.50, legendary: 0.05 },
    250: { common: 0, rare: 0.20, epic: 0.20, legendary: 0.60 },
    /** 兼容旧预览费用（10/20 金） */
    10: { common: 0.70, rare: 0.25, epic: 0.05, legendary: 0 },
    20: { common: 0.40, rare: 0.40, epic: 0.18, legendary: 0.02 },
  },

  /** 格子类型一览（策划表；费用单位：局内金币） */
  FLIP_GRID_TYPES: {
    gold_mine: {
      label: '金矿格子',
      cost: 50,
      previewType: 'resource',
      note: '必开',
    },
    mystery: {
      label: '随机问好格子',
      cost: 25,
      previewType: 'mystery',
      outcomes: { empty: 0.60, gold_mine: 0.20, building: 0.20 },
    },
    hero_low: {
      label: '低级角色',
      cost: 50,
      previewType: 'hero',
      qualityKey: 50,
      newbieQualityKey: '50_newbie',
    },
    hero_mid: {
      label: '中级角色',
      cost: 100,
      previewType: 'hero',
      qualityKey: 100,
    },
    hero_high: {
      label: '高级角色',
      cost: 250,
      previewType: 'hero',
      qualityKey: 250,
    },
  },

  HERO_TEMPLATES: {
    common: {
      name: '步兵',
      hp: 42,
      atk: 9,
      atkInterval: 1.35,
      passive: '无',
      passiveId: 'none',
    },
    rare: {
      name: '弓手',
      hp: 58,
      atk: 13,
      atkInterval: 1.15,
      passive: '迅捷：攻速+10%',
      passiveId: 'swift',
    },
    epic: {
      name: '重甲',
      hp: 95,
      atk: 16,
      atkInterval: 1.05,
      passive: '铁壁：受伤-15%',
      passiveId: 'ironwall',
    },
    legendary: {
      name: '龙骑',
      hp: 125,
      atk: 24,
      atkInterval: 0.9,
      passive: '破军：25%溅射相邻敌',
      passiveId: 'splash',
    },
  },

  RESOURCE_GOLD: 28,
  MYSTERY_GOLD: 15,
  MYSTERY_COST: 25,

  /** 开局主城四周固定预览（与场景图一致） */
  INITIAL_PREVIEWS: [
    { dr: -1, dc: 0, previewType: 'hero', cost: 50 },
    { dr: 1, dc: 0, previewType: 'mystery', cost: 10 },
    { dr: 0, dc: -1, previewType: 'resource', cost: 20 },
    { dr: 0, dc: 1, previewType: 'hero', cost: 20 },
  ],

  PASSIVE: {
    swiftAtkMul: 0.9,
    ironwallReduction: 0.15,
    splashRatio: 0.25,
  },
};
