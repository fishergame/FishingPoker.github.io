/**
 * 主城养成配表（mainCity.json）
 * 血量 / 产金随主城等级；对局时长见 battleBalance.json
 */
const MainCityConfig = {
  VERSION: '1.0.0',
  LEVEL_MAX: 30,
  HP_GROWTH: 1.15,
  GOLD_GROWTH: 1.10,

  /** @type {Record<string, number>} */
  HP_BY_LEVEL: {},
  /** @type {Record<string, number>} */
  GOLD_PER_SEC_BY_LEVEL: {},
  /** @type {Array<object>} */
  LEVELS: [],

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.LEVEL_MAX = data.levelMax;
    this.HP_BY_LEVEL = data.hpByLevel || {};
    this.GOLD_PER_SEC_BY_LEVEL = data.goldPerSecByLevel || {};
    this.LEVELS = data.levels || [];
    this.FORMULAS = data.formulas || {};
  },

  /** @param {number} mainCityLevel 1..30 */
  hp(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.HP_BY_LEVEL[String(lv)] ?? 1500;
  },

  /** @param {number} mainCityLevel 1..30 */
  goldPerSec(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.GOLD_PER_SEC_BY_LEVEL[String(lv)] ?? 2;
  },

  getLevelRow(mainCityLevel) {
    const lv = Math.max(1, Math.min(this.LEVEL_MAX, Math.round(mainCityLevel)));
    return this.LEVELS.find((r) => r.level === lv) || null;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MainCityConfig };
}
