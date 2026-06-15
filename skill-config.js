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
    this.SKILLS = Object.fromEntries(skillData.skills.map((s) => [s.skillId, s]));
    this.HERO_BATTLE = heroBattleData.heroes;
  },

  getSkill(skillId) {
    return this.SKILLS[skillId] || null;
  },

  getHeroMeta(heroId) {
    return this.HERO_BATTLE[heroId] || null;
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
