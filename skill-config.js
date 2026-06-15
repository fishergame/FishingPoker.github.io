/**
 * 技能配表（skill.json + heroBattle.json）
 */
const SkillConfig = {
  VERSION: '1.0.0',
  EFFECT_BOUNDS: {},

  hydrateFromJson(skillData, heroBattleData) {
    this.VERSION = skillData.version;
    this.EFFECT_BOUNDS = skillData.effectBounds || {};
    this.SKILLS = Object.fromEntries(skillData.skills.map((s) => [s.skillId, s]));
    this.HERO_BATTLE = heroBattleData.heroes;
  },

  getHeroSkills(heroId) {
    const meta = this.HERO_BATTLE[heroId];
    if (!meta || !meta.skills) return [];
    const ids = [
      ...(meta.skills.normal || []),
      ...(meta.skills.epic || []),
      meta.skills.legend,
    ].filter(Boolean);
    return ids.map((id) => this.SKILLS[id]).filter(Boolean);
  },

  /** 汇总对城伤害加成（建议战斗层再 cap） */
  sumCityDamagePct(skillIds, skillLevels = {}) {
    let sum = 0;
    for (const id of skillIds) {
      const sk = this.SKILLS[id];
      if (!sk) continue;
      const lv = skillLevels[id] || 1;
      for (const e of sk.effects) {
        if (e.type === 'cityDamagePct') {
          sum += e.value + (lv - 1) * (sk.scalingPerSkillLevel || 0);
        }
      }
    }
    return sum;
  },
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SkillConfig };
}
