/**
 * 战斗平衡配表（对局时长 → battleBalance.json；主城 HP/产金 → mainCity.json）
 */
const BattleBalanceConfig = {
  VERSION: '2.0.0',

  /** @type {Record<number, { matchDurationSec: number }>} */
  ARENAS: {},

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.MAIN_CITY_CONFIG = data.mainCityConfig || 'mainCity.json';
    this.ARENAS = {};
    for (const a of data.arenas) {
      this.ARENAS[a.arenaId] = a;
    }
  },

  matchDurationSec(arenaId) {
    const a = this.ARENAS[arenaId];
    return a ? a.matchDurationSec : 180;
  },

  /**
   * @deprecated 使用 MainCityConfig.hp(mainCityLevel)
   * 兼容旧调用：仅按主城等级读取（忽略 arenaId）
   */
  mainCityHp(_arenaId, mainCityLevel) {
    if (typeof MainCityConfig !== 'undefined' && MainCityConfig.HP_BY_LEVEL) {
      return MainCityConfig.hp(mainCityLevel);
    }
    const lv = Math.max(1, Math.min(30, Math.round(mainCityLevel)));
    return Math.round(1500 * 1.15 ** (lv - 1));
  },

  /**
   * @deprecated 使用 MainCityConfig.goldPerSec(mainCityLevel)
   */
  mainCityGoldPerSec(mainCityLevel) {
    if (typeof MainCityConfig !== 'undefined' && MainCityConfig.GOLD_PER_SEC_BY_LEVEL) {
      return MainCityConfig.goldPerSec(mainCityLevel);
    }
    const lv = Math.max(1, Math.min(30, Math.round(mainCityLevel)));
    return 2 + (lv - 1) * 0.5;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BattleBalanceConfig };
}
