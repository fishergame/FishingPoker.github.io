/**
 * 竞技场 / 账号等级 / 宝箱 — 轻量查询（完整数据见 arena.json、chest.json、accountLevel.json）
 */
const ProgressionConfig = {
  ARENA_COUNT: 10,
  ACCOUNT_LEVEL_MAX: 100,

  RULES: {
    trophyMin: 0,
    arenaNoDemotion: true,
    tierNoDemotion: true,
    seasonResetRatio: 0.2,
  },

  ARENAS: [
    { id: 1, name: '青铜', unlock: 0, next: 100, trophyWin: 30, trophyLoss: 0, expWin: 20, expLoss: 8, victoryGold: 50, dailyCap: 500, chest: 'wooden' },
    { id: 2, name: '白银', unlock: 100, next: 300, trophyWin: 28, trophyLoss: 5, expWin: 25, expLoss: 10, victoryGold: 80, dailyCap: 800, chest: 'silver' },
    { id: 3, name: '黄金', unlock: 300, next: 600, trophyWin: 26, trophyLoss: 8, expWin: 30, expLoss: 12, victoryGold: 120, dailyCap: 1200, chest: 'golden' },
    { id: 4, name: '铂金', unlock: 600, next: 1000, trophyWin: 25, trophyLoss: 10, expWin: 35, expLoss: 14, victoryGold: 160, dailyCap: 1600, chest: 'platinum' },
    { id: 5, name: '钻石', unlock: 1000, next: 1600, trophyWin: 24, trophyLoss: 12, expWin: 40, expLoss: 16, victoryGold: 200, dailyCap: 2000, chest: 'diamond' },
    { id: 6, name: '星耀', unlock: 1600, next: 2500, trophyWin: 23, trophyLoss: 15, expWin: 45, expLoss: 18, victoryGold: 250, dailyCap: 2500, chest: 'diamond' },
    { id: 7, name: '大师', unlock: 2500, next: 4000, trophyWin: 22, trophyLoss: 18, expWin: 50, expLoss: 20, victoryGold: 300, dailyCap: 3000, chest: 'epic' },
    { id: 8, name: '宗师', unlock: 4000, next: 6000, trophyWin: 21, trophyLoss: 20, expWin: 55, expLoss: 22, victoryGold: 350, dailyCap: 3500, chest: 'epic' },
    { id: 9, name: '王者', unlock: 6000, next: 9000, trophyWin: 20, trophyLoss: 22, expWin: 60, expLoss: 24, victoryGold: 400, dailyCap: 4000, chest: 'legendary' },
    { id: 10, name: '传奇', unlock: 9000, next: null, trophyWin: 19, trophyLoss: 25, expWin: 70, expLoss: 28, victoryGold: 500, dailyCap: 5000, chest: 'legendary' },
  ],

  getArenaByTrophy(trophy) {
    let current = this.ARENAS[0];
    for (const a of this.ARENAS) {
      if (trophy >= a.unlock) current = a;
      else break;
    }
    return current;
  },

  getMaxArenaUnlocked(trophy) {
    return this.getArenaByTrophy(trophy);
  },

  calcBattleResult(arenaId, won) {
    const a = this.ARENAS.find((x) => x.id === arenaId) || this.ARENAS[0];
    return {
      trophyDelta: won ? a.trophyWin : -a.trophyLoss,
      expDelta: won ? a.expWin : a.expLoss,
      goldDelta: won ? a.victoryGold : 0,
      chestId: won ? a.chest : null,
    };
  },

  applyTrophy(current, delta) {
    return Math.max(this.RULES.trophyMin, current + delta);
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProgressionConfig;
}
