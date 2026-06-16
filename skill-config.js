/**
 * 技能配表（skill.json + heroBattle.json）
 */
const SkillConfig = {
  VERSION: '2.0.0',
  EFFECT_BOUNDS: {},
  SKILLS: {},
  HERO_BATTLE: {},
  ARCHETYPES: {},

  hydrateFromJson(skillData, heroBattleData) {
    this.VERSION = skillData.version;
    this.EFFECT_BOUNDS = skillData.effectBounds || {};
    this.ARCHETYPES = skillData.archetypes || {};
    this.SKILL_UPGRADE = skillData.skillUpgrade || {};
    this.SKILLS = Object.fromEntries(skillData.skills.map((s) => [s.skillId, s]));
    this.HERO_BATTLE = heroBattleData.heroes;
  },

  getSkill(skillId) {
    return this.SKILLS[skillId] || null;
  },

  getHeroMeta(heroId) {
    return this.HERO_BATTLE[heroId] || null;
  },

  /** 特技升级行（fromLevel→toLevel） */
  getUpgradeCostRow(slot, fromLevel) {
    const rows = this.SKILL_UPGRADE.upgradeCost || this.SKILL_UPGRADE.diamondCost || [];
    return rows.find((r) => r.slot === slot && r.fromLevel === fromLevel) || null;
  },

  /**
   * 广告抵扣后钻石价（仅 epic/legendary）
   * @param {number} baseDiamond
   * @param {number} adsWatchedToday 0~3
   */
  applyAdDiscount(baseDiamond, adsWatchedToday = 0) {
    const ad = this.SKILL_UPGRADE.adDiscount || {};
    const pct = Math.min(
      (ad.maxDiscountPct ?? 0.3),
      (adsWatchedToday || 0) * (ad.percentPerAd ?? 0.1),
    );
    return Math.max(1, Math.ceil(baseDiamond * (1 - pct)));
  },

  /** 当日广告 UI 状态（供升级面板） */
  getAdDiscountUiState(adsWatchedToday = 0, cooldownRemainingSec = 0) {
    const ad = this.SKILL_UPGRADE.adDiscount || {};
    const max = ad.maxAdsPerDay ?? 3;
    const watched = Math.min(max, adsWatchedToday || 0);
    const exhausted = watched >= max;
    return {
      watchAdButtonLabel: exhausted ? (ad.buttonExhaustedLabel || '已抵扣30%') : (ad.ui?.watchAdButton || '看广告抵扣10%'),
      hintBelowButton: watched > 0 && !exhausted ? (ad.hintAfterWatch || '抵扣仅今日生效') : (exhausted ? (ad.hintAfterWatch || '抵扣仅今日生效') : ''),
      discountPct: Math.min(ad.maxDiscountPct ?? 0.3, watched * (ad.percentPerAd ?? 0.1)),
      canWatchAd: !exhausted && cooldownRemainingSec <= 0,
      adsWatchedToday: watched,
      maxAdsPerDay: max,
    };
  },

  /** 按英雄等级返回已解锁技能（普通 L1 / 史诗 L8 / 传奇 L20） */
  getHeroSkills(heroId, heroLevel = 30, skillLevels = {}) {
    const ids = BattleSkillRuntime.getUnlockedSkillIds(heroId, heroLevel);
    return ids
      .map((id) => {
        const sk = this.SKILLS[id];
        if (!sk) return null;
        const lv = skillLevels[id] || 1;
        return { ...sk, level: lv };
      })
      .filter(Boolean);
  },

  sumCityDamagePct(skillIds, skillLevels = {}) {
    let sum = 0;
    for (const id of skillIds) {
      const sk = this.SKILLS[id];
      if (!sk || sk.phase !== 'siege_only') continue;
      const lv = skillLevels[id] || 1;
      for (const e of sk.effects) {
        if (e.type === 'cityDamagePct') {
          sum += e.value + (lv - 1) * (sk.scalingPerSkillLevel || 0);
        }
      }
    }
    return Math.min(sum, BattleSkillRuntime.CAPS.cityDamagePct);
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SkillConfig };
}
