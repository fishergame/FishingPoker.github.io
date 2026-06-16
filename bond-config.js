/**
 * 羁绊配表（bond.json）— 仅种族阵营羁绊
 */
const BondConfig = {
  VERSION: '1.0.0',

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.RULES = data.rules;
    this.BONDS = data.bonds;
    this._byId = Object.fromEntries(data.bonds.map((b) => [b.bondId, b]));
  },

  /**
   * 计算卡组激活的阵营羁绊档位
   * @param {Array<{heroId:string,faction:string,bondEligible:boolean}>} deckMeta
   */
  computeActive(deckMeta) {
    const eligible = deckMeta.filter((h) => h.bondEligible);
    const factionCount = {};
    for (const h of eligible) {
      if (h.faction) factionCount[h.faction] = (factionCount[h.faction] || 0) + 1;
    }

    const active = [];
    const bestFaction = Object.entries(factionCount).sort((a, b) => b[1] - a[1])[0];
    if (bestFaction && bestFaction[1] >= 2) {
      const bond = this._byId[`faction_${bestFaction[0]}`];
      if (bond) {
        active.push({
          bondId: bond.bondId,
          count: bestFaction[1],
          tiers: this._activeTiers(bond, bestFaction[1]),
        });
      }
    }

    return active;
  },

  _activeTiers(bond, count) {
    const tiers = [];
    for (const t of bond.tiers) {
      if (count >= t.count) tiers.push(t);
    }
    return tiers;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BondConfig };
}
