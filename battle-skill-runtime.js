/**
 * 技能运行时：汇总加成、解锁判定、战斗修饰符
 * 依赖 SkillConfig（skill.json + heroBattle.json）、HeroesConfig、HeroLevelConfig
 */
const BattleSkillRuntime = (() => {
  const CAPS = {
    atkPct: 0.35,
    atkSpeedPct: 0.35,
    cityDamagePct: 0.25,
    unitHpPct: 0.40,
    damageReductionPct: 0.40,
  };

  function effectAtLevel(effect, skillLevel, scaling) {
    if (effect.type === 'taunt' || effect.type === 'revealAdjacent') {
      return effect.value;
    }
    return effect.value + (skillLevel - 1) * (scaling || 0);
  }

  const SPECIAL_UNLOCK_LEVEL = { rare: 5, epic: 10, legendary: 20 };

  function getUnlockedSkillIds(heroId, heroLevel = 1) {
    const meta = SkillConfig.HERO_BATTLE?.[heroId];
    if (!meta?.skills) return [];
    const { skills } = meta;
    const ids = [];
    if (skills.normal_1) ids.push(skills.normal_1);
    if (skills.normal_3) ids.push(skills.normal_3);
    // v3.3 兼容
    if (skills.basic_attack) ids.push(skills.basic_attack);
    if (skills.normal) ids.push(skills.normal);
    const cfg = typeof HeroesConfig !== 'undefined' ? HeroesConfig.getById(heroId) : null;
    const q = cfg?.quality;
    const unlockRules = meta.skillUnlock || SkillConfig.SKILL_UPGRADE?.unlockByHeroLevel || SPECIAL_UNLOCK_LEVEL;
    const specialSlot = { rare: 'rare', epic: 'epic', legendary: 'legendary' }[q];
    if (specialSlot && skills[specialSlot]) {
      const need = unlockRules[specialSlot] ?? SPECIAL_UNLOCK_LEVEL[specialSlot] ?? 1;
      const sk = SkillConfig.SKILLS[skills[specialSlot]];
      const unlockLv = sk?.unlockLevel ?? need;
      if (heroLevel >= unlockLv) ids.push(skills[specialSlot]);
    }
    // v2 兼容
    if (!specialSlot) {
      if (heroLevel >= (skills.epicUnlockLevel || 8) && skills.epic) ids.push(skills.epic);
      if (heroLevel >= (skills.legendUnlockLevel || 20) && skills.legend) ids.push(skills.legend);
    }
    return ids;
  }

  function isCombatPhase(sk) {
    const phase = sk.phase;
    return !phase || phase === 'always' || phase === 'field_only';
  }

  const TRAJECTORY_DR_TYPES = new Set(['damageReductionPct', 'globalDamageReductionPct']);

  function buildTrajectoryDefense(skills) {
    const result = { flat: 0, arc: 0 };
    for (const sk of skills) {
      if (!isCombatPhase(sk)) continue;
      for (const e of sk.resolvedEffects) {
        if (!TRAJECTORY_DR_TYPES.has(e.type)) continue;
        const blocks = e.blocksTrajectory || ['flat'];
        const val = e.resolvedValue ?? e.value ?? 0;
        for (const traj of blocks) {
          if (traj === 'flat' || traj === 'arc') {
            result[traj] = (result[traj] || 0) + val;
          }
        }
      }
    }
    result.flat = cap(result.flat, 'damageReductionPct');
    result.arc = cap(result.arc, 'damageReductionPct');
    return result;
  }

  function resolveAttackTrajectory(skills) {
    for (const sk of skills) {
      if (sk.attackTrajectory === 'arc') return 'arc';
      if (sk.resolvedEffects?.some((e) => e.type === 'projectileArc')) return 'arc';
    }
    return 'flat';
  }

  function getActiveSkills(heroId, heroLevel = 1, skillLevels = {}) {
    return getUnlockedSkillIds(heroId, heroLevel)
      .map((id) => {
        const sk = SkillConfig.SKILLS[id];
        if (!sk) return null;
        const lv = skillLevels[id] || 1;
        return {
          ...sk,
          level: lv,
          resolvedEffects: sk.effects.map((e) => ({
            ...e,
            resolvedValue: effectAtLevel(e, lv, sk.scalingPerSkillLevel),
          })),
        };
      })
      .filter(Boolean);
  }

  function sumEffects(skills, type, phaseFilter = null) {
    let sum = 0;
    for (const sk of skills) {
      const phase = sk.phase || 'field_only';
      if (phaseFilter && phase !== phaseFilter && phase !== 'always') continue;
      for (const e of sk.resolvedEffects) {
        if (e.type === type) sum += e.resolvedValue;
      }
    }
    return sum;
  }

  function hasEffect(skills, type) {
    return skills.some((sk) => sk.resolvedEffects.some((e) => e.type === type));
  }

  function getEffect(skills, type) {
    for (const sk of skills) {
      for (const e of sk.resolvedEffects) {
        if (e.type === type) return e;
      }
    }
    return null;
  }

  function cap(value, key) {
    const max = CAPS[key];
    return max != null ? Math.min(value, max) : value;
  }

  function statAtLevel(base, level, growth = 1.15) {
    if (base == null) return null;
    return Math.max(1, Math.round(base * growth ** (level - 1)));
  }

  function attackIntervalFromSpeed(attackSpeed, pace = 1) {
    const spd = Math.max(0.3, attackSpeed || 1);
    return (2.2 / spd) * pace;
  }

  /**
   * 从英雄配表 + 技能生成战斗单位
   */
  function buildCombatHero(heroId, options = {}) {
    const {
      heroLevel = 1,
      skillLevels = {},
      flipCost = 0,
      side = 'player',
    } = options;

    const cfg = HeroesConfig.getById(heroId);
    if (!cfg || cfg.type === 'resource') return null;

    const growth = HeroLevelConfig?.STAT_GROWTH_RATE || 1.15;
    const pace = BattleConfig.COMBAT_PACE || 1;
    const hpScale = BattleConfig.COMBAT_HP_SCALE || 1;
    const atkScale = BattleConfig.COMBAT_ATK_SCALE || 1;

    const skills = getActiveSkills(heroId, heroLevel, skillLevels);
    const isField = (phase) => phase === 'always' || phase === 'field_only';

    const combatSkills = skills.filter(isCombatPhase);
    const atkPct = cap(
      sumEffects(combatSkills, 'atkPct', 'always') + sumEffects(combatSkills, 'atkPct', 'field_only'),
      'atkPct',
    );
    const atkSpeedPct = cap(sumEffects(combatSkills, 'atkSpeedPct'), 'atkSpeedPct');
    const unitHpPct = cap(sumEffects(combatSkills, 'unitHpPct'), 'unitHpPct');
    const trajectoryDefense = buildTrajectoryDefense(skills);
    const dmgRed = Math.max(trajectoryDefense.flat, trajectoryDefense.arc);
    const cityDmgPct = cap(sumEffects(skills, 'cityDamagePct'), 'cityDamagePct');
    const splashPct = sumEffects(
      skills.filter((sk) => isCombatPhase(sk)),
      'splashPct',
    );
    const dotPct = sumEffects(
      skills.filter((sk) => isCombatPhase(sk)),
      'dotPctPerSec',
    );
    const executeEff = getEffect(
      skills.filter((sk) => isCombatPhase(sk)),
      'executeBonusPct',
    );
    const deployBurst = getEffect(
      skills.filter((sk) => sk.phase === 'on_deploy'),
      'deployBurstPct',
    );
    const killGoldEff = getEffect(
      skills.filter((sk) => sk.phase === 'on_kill'),
      'killGold',
    );
    const flipRefundEff = getEffect(
      skills.filter((sk) => sk.phase === 'on_deploy'),
      'flipRefundPct',
    );
    const revealEff = getEffect(
      skills.filter((sk) => sk.phase === 'on_deploy'),
      'revealAdjacent',
    );
    const taunt = hasEffect(skills, 'taunt');

    const baseHp = cfg.unitHp ?? cfg.buildingHp ?? 50;
    const hp = Math.round(statAtLevel(baseHp, heroLevel, growth) * hpScale * (1 + unitHpPct));
    const atk = Math.max(
      1,
      Math.round(statAtLevel(cfg.attack, heroLevel, growth) * atkScale * (1 + atkPct)),
    );
    let atkInterval = attackIntervalFromSpeed(cfg.attackSpeed, pace);
    atkInterval *= 1 / (1 + atkSpeedPct);

    const battleMeta = SkillConfig.HERO_BATTLE[heroId] || {};
    const primaryAttackTrajectory = resolveAttackTrajectory(skills);

    return {
      heroId,
      quality: cfg.quality,
      name: cfg.name,
      unitType: cfg.type || 'unit',
      faction: battleMeta.faction || null,
      factionLabel: battleMeta.factionLabel || null,
      archetype: battleMeta.archetype || null,
      archetypeLabel: battleMeta.archetypeLabel || null,
      hp,
      maxHp: hp,
      atk,
      atkInterval,
      attackTimer: Math.random() * atkInterval * 0.5,
      flipCost,
      side,
      heroLevel,
      skillIds: skills.map((s) => s.skillId),
      combatMods: {
        damageReductionPct: dmgRed,
        trajectoryDefense,
        primaryAttackTrajectory,
        cityDamagePct: cityDmgPct,
        splashPct,
        dotPctPerSec: dotPct,
        executeThreshold: executeEff?.threshold ?? null,
        executeBonusPct: executeEff?.resolvedValue ?? 0,
        deployBurstPct: deployBurst?.resolvedValue ?? 0,
        killGold: killGoldEff ? Math.round(killGoldEff.resolvedValue) : 0,
        flipRefundPct: flipRefundEff?.resolvedValue ?? 0,
        revealAdjacent: revealEff ? Math.round(revealEff.resolvedValue) : 0,
        taunt,
      },
      dots: [],
    };
  }

  function pickDeckHero(deckIds, qualityHint = null) {
    const pool = deckIds
      .filter((id) => id && id !== 'gold_mine')
      .map((id) => HeroesConfig.getById(id))
      .filter((h) => h && h.type !== 'resource');

    if (pool.length === 0) return null;

    if (qualityHint) {
      const same = pool.filter((h) => h.quality === qualityHint);
      if (same.length > 0) {
        return same[Math.floor(Math.random() * same.length)].id;
      }
    }
    return pool[Math.floor(Math.random() * pool.length)].id;
  }

  function defaultDeck() {
    const deck = HeroesConfig.DEFAULT_DECK.filter(Boolean);
    return deck.length > 0 ? deck : HeroesConfig.HEROES.filter((h) => h.starter).map((h) => h.id);
  }

  return {
    CAPS,
    effectAtLevel,
    getUnlockedSkillIds,
    getActiveSkills,
    buildCombatHero,
    pickDeckHero,
    defaultDeck,
    statAtLevel,
  };
})();

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BattleSkillRuntime };
}
