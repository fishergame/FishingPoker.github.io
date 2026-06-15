/**
 * 主城养成配表（mainCity.json）
 */
const MainCityConfig = {
  VERSION: '2.0.0',
  LEVEL_MAX: 30,

  HP_BY_LEVEL: {},
  GOLD_PER_SEC_BY_LEVEL: {},
  LEVELS: [],
  GAMEPLAY: {},
  SHOP_BRICK_PACKS: [],

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.LEVEL_MAX = data.levelMax;
    this.HP_BY_LEVEL = data.hpByLevel || {};
    this.GOLD_PER_SEC_BY_LEVEL = data.goldPerSecByLevel || {};
    this.LEVELS = data.levels || [];
    this.GAMEPLAY = data.gameplay || {};
    this.SHOP_BRICK_PACKS = data.shopBrickPacks || [];
    this.FORMULAS = data.formulas || {};
    this.CUMULATIVE_BRICKS_TO_MAX = data.cumulativeBricksToMax;
  },

  getLevelRow(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.LEVELS.find((r) => r.level === lv) || null;
  },

  hp(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.HP_BY_LEVEL[String(lv)] ?? 1500;
  },

  goldPerSec(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.GOLD_PER_SEC_BY_LEVEL[String(lv)] ?? 2;
  },

  flipBrickCost(mainCityLevel) {
    const row = this.getLevelRow(mainCityLevel);
    return row?.flip?.brickCostPerTile ?? 2 + (mainCityLevel - 1);
  },

  bricksToLevelUp(mainCityLevel) {
    const row = this.getLevelRow(mainCityLevel);
    return row?.flip?.totalBricksToNext ?? 20 * this.flipBrickCost(mainCityLevel);
  },

  battleRewards(mainCityLevel, arenaId, won = true) {
    const row = this.getLevelRow(mainCityLevel);
    if (!row) return null;
    const key = won ? 'win' : 'lose';
    return row.battleRewards[key];
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MainCityConfig };
}
