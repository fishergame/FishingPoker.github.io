/**
 * 英雄卡牌升级消耗配置表
 * JSON 同源：heroLevel.json
 *
 * fragmentNeed[level - 1]：从 level 升到 level+1 所需卡牌数
 * goldNeedByQuality[quality][level - 1]：从 level 升到 level+1 所需金币
 */
const HeroLevelConfig = {
  VERSION: '1.0.0',
  LEVEL_MAX: 30,
  UNLOCK_CARD: 1,
  STAT_GROWTH_RATE: 1.15,

  GOLD_MULTIPLIER: {
    common: 1,
    rare: 2.5,
    epic: 6,
    legendary: 15,
  },

  FRAGMENT_NEED: [
    10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
    60, 65, 70, 75, 80, 85, 95, 110, 120, 140,
    160, 190, 220, 250, 290, 330, 380, 440, 500, 580,
  ],

  GOLD_NEED_BY_QUALITY: {
    common: [
      5, 40, 130, 280, 480, 730, 1050, 1400, 1800, 2300,
      2850, 3400, 4050, 4750, 5500, 6300, 7150, 8100, 9050, 10100,
      11200, 12300, 13500, 14700, 16000, 17400, 18800, 20300, 21800, 23400,
    ],
    rare: [
      10, 100, 320, 690, 1200, 1800, 2600, 3500, 4550, 5750,
      7100, 8550, 10100, 11900, 13800, 15800, 17900, 20200, 22600, 25200,
      27900, 30700, 33700, 36800, 40100, 43400, 47000, 50600, 54400, 58400,
    ],
    epic: [
      30, 240, 780, 1650, 2850, 4400, 6250, 8450, 11000, 13800,
      17000, 20500, 24300, 28500, 33000, 37800, 43000, 48500, 54300, 60400,
      66900, 73700, 80900, 88400, 96200, 104500, 112500, 121500, 130500, 140000,
    ],
    legendary: [
      75, 600, 1950, 4100, 7100, 11000, 15600, 21100, 27400, 34500,
      42400, 51200, 60800, 71200, 82500, 94600, 107500, 121000, 136000, 151000,
      167500, 184500, 202000, 221000, 240500, 260500, 282000, 304000, 326500, 350000,
    ],
  },

  /** @param {number} level 当前等级 1..LEVEL_MAX */
  getFragmentNeed(level) {
    if (level < 1 || level > this.LEVEL_MAX) return null;
    return this.FRAGMENT_NEED[level - 1];
  },

  /** @param {'common'|'rare'|'epic'|'legendary'} quality */
  getGoldNeed(quality, level) {
    if (level < 1 || level > this.LEVEL_MAX) return null;
    const table = this.GOLD_NEED_BY_QUALITY[quality];
    return table ? table[level - 1] : null;
  },

  /** @param {'common'|'rare'|'epic'|'legendary'} quality */
  getUpgradeCost(quality, level) {
    return {
      fragment: this.getFragmentNeed(level),
      gold: this.getGoldNeed(quality, level),
    };
  },

  /** @param {'common'|'rare'|'epic'|'legendary'} quality */
  canUpgrade(quality, level, fragments, gold) {
    if (level >= this.LEVEL_MAX) return false;
    const cost = this.getUpgradeCost(quality, level);
    return fragments >= cost.fragment && gold >= cost.gold;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = HeroLevelConfig;
}
