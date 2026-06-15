/**
 * 羁绊配表（bond.json）
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
   * 计算卡组激活的羁绊档位
   * @param {Array<{heroId:string,faction:string,range:string,bondEligible:boolean}>} deckMeta
   */
  computeActive(deckMeta) {
    const eligible = deckMeta.filter((h) => h.bondEligible);
    const factionCount = {};
    let melee = 0;
    let ranged = 0;
    for (const h of eligible) {
      factionCount[h.faction] = (factionCount[h.faction] || 0) + 1;
      if (h.range === 'melee') melee++;
      else ranged++;
    }
    const bestFaction = Object.entries(factionCount).sort((a, b) => b[1] - a[1])[0];
    const active = [];
    if (bestFaction && bestFaction[1] >= 2) {
      const bond = this._byId[`faction_${bestFaction[0]}`];
      if (bond) active.push({ bondId: bond.bondId, count: bestFaction[1], tiers: this._activeTiers(bond, bestFaction[1]) });
    }
    const rangeBond = melee >= ranged ? this._byId.range_melee : this._byId.range_ranged;
    const rangeCount = Math.max(melee, ranged);
    if (rangeBond && rangeCount >= 2) {
      active.push({ bondId: rangeBond.bondId, count: rangeCount, tiers: this._activeTiers(rangeBond, rangeCount) });
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
