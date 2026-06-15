/**
 * 战斗平衡配表（对局时长 / 主城血量）
 * JSON 同源：battleBalance.json
 */
const BattleBalanceConfig = {
  VERSION: '1.0.0',
  STAT_GROWTH_RATE: 1.15,

  /** @type {Record<number, { matchDurationSec: number, mainCityHpBase: number, mainCityHpByLevel: Record<string, number> }>} */
  ARENAS: {},

  /**
   * 由 battleBalance.json 注入；开发时可在页面加载 JSON 后调用 hydrateFromJson
   */
  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.STAT_GROWTH_RATE = data.statGrowthRate;
    this.DEFAULT_DECK = data.defaultDeck;
    this.SKILL_QUALITY_REFERENCE = data.skillQualityReference;
    this.ARENAS = {};
    for (const a of data.arenas) {
      this.ARENAS[a.arenaId] = a;
    }
  },

  matchDurationSec(arenaId) {
    const a = this.ARENAS[arenaId];
    return a ? a.matchDurationSec : 180;
  },

  mainCityHp(arenaId, avgDeckLevel) {
    const a = this.ARENAS[arenaId];
    if (!a) return 200;
    const lv = Math.max(1, Math.min(30, Math.round(avgDeckLevel)));
    return a.mainCityHpByLevel[String(lv)] ?? a.mainCityHpBase;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BattleBalanceConfig };
}
