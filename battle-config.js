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

  /** 翻牌费用档位：越贵越容易出高品质英雄 */
  FLIP_COSTS: [10, 20, 50],

  QUALITY_BY_COST: {
    10: { common: 0.7, rare: 0.25, epic: 0.05, legendary: 0 },
    20: { common: 0.4, rare: 0.4, epic: 0.18, legendary: 0.02 },
    50: { common: 0.1, rare: 0.3, epic: 0.45, legendary: 0.15 },
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
