/**
 * 纯规则层 — 不依赖 DOM，后续可直接迁到 Cocos TypeScript。
 */
const BattleRules = (() => {
  const C = BattleConfig;
  const DIRS = [[-1, 0], [1, 0], [0, -1], [0, 1]];

  let battleContext = {
    loaded: false,
    playerDeck: [],
    enemyDeck: [],
    heroLevels: {},
    skillLevels: {},
    playerMatchNumber: 1,
  };

  async function loadConfig() {
    const [skillRes, heroBattleRes] = await Promise.all([
      fetch('skill.json'),
      fetch('heroBattle.json'),
    ]);
    if (!skillRes.ok || !heroBattleRes.ok) {
      throw new Error('Failed to load skill.json or heroBattle.json');
    }
    SkillConfig.hydrateFromJson(await skillRes.json(), await heroBattleRes.json());
    const deck = BattleSkillRuntime.defaultDeck();
    battleContext.playerDeck = deck.slice();
    battleContext.enemyDeck = deck.slice();
    battleContext.loaded = true;
  }

  function configure(options = {}) {
    if (options.playerDeck) battleContext.playerDeck = options.playerDeck.filter(Boolean);
    if (options.enemyDeck) battleContext.enemyDeck = options.enemyDeck.filter(Boolean);
    if (options.heroLevels) battleContext.heroLevels = { ...options.heroLevels };
    if (options.skillLevels) battleContext.skillLevels = { ...options.skillLevels };
    if (options.playerMatchNumber != null) {
      battleContext.playerMatchNumber = options.playerMatchNumber;
    }
    if (Object.keys(SkillConfig.SKILLS || {}).length > 0) {
      battleContext.loaded = true;
      if (battleContext.playerDeck.length === 0) {
        const deck = BattleSkillRuntime.defaultDeck();
        battleContext.playerDeck = deck.slice();
        battleContext.enemyDeck = deck.slice();
      }
    }
  }

  function getDeck(side) {
    return side === 'player' ? battleContext.playerDeck : battleContext.enemyDeck;
  }

  function cellKey(side, row, col) {
    return `${side}_${row}_${col}`;
  }

  function inBounds(row, col) {
    return row >= 0 && row < C.GRID_ROWS && col >= 0 && col < C.GRID_COLS;
  }

  function getMainCityPos(side) {
    return {
      row: side === 'player' ? C.PLAYER_MAIN_ROW : C.ENEMY_MAIN_ROW,
      col: C.MAIN_COL,
    };
  }

  function isMainCity(side, row, col) {
    const pos = getMainCityPos(side);
    return row === pos.row && col === pos.col;
  }

  function readPlayerMatchNumber() {
    const cfg = C.NEWBIE_MATCHES;
    if (!cfg?.storageKey) return 1;
    try {
      const storage = typeof localStorage !== 'undefined' ? localStorage : null;
      if (!storage) return 1;
      const completed = parseInt(storage.getItem(cfg.storageKey) || '0', 10);
      return Number.isFinite(completed) ? completed + 1 : 1;
    } catch {
      return 1;
    }
  }

  function recordMatchCompleted() {
    const cfg = C.NEWBIE_MATCHES;
    if (!cfg?.storageKey) return;
    try {
      const storage = typeof localStorage !== 'undefined' ? localStorage : null;
      if (!storage) return;
      const completed = parseInt(storage.getItem(cfg.storageKey) || '0', 10);
      storage.setItem(cfg.storageKey, String(completed + 1));
    } catch {
      /* noop */
    }
  }

  function isNewbieMatch(matchNumber = battleContext.playerMatchNumber) {
    const cfg = C.NEWBIE_MATCHES;
    if (!cfg?.enabled) return false;
    return matchNumber <= (cfg.maxMatchIndex || 0);
  }

  function getQualityTable(cost, matchNumber = battleContext.playerMatchNumber) {
    const cfg = C.NEWBIE_MATCHES;
    if (
      cfg?.enabled
      && cost === cfg.heroLowCost
      && isNewbieMatch(matchNumber)
      && C.QUALITY_BY_COST['50_newbie']
    ) {
      return C.QUALITY_BY_COST['50_newbie'];
    }
    return C.QUALITY_BY_COST[cost] || C.QUALITY_BY_COST[50] || C.QUALITY_BY_COST[20];
  }

  function rollQuality(cost, matchNumber = battleContext.playerMatchNumber) {
    const table = getQualityTable(cost, matchNumber);
    const r = Math.random();
    let acc = 0;
    for (const q of ['common', 'rare', 'epic', 'legendary']) {
      acc += table[q];
      if (r < acc) return q;
    }
    return 'common';
  }

  function randomFlipPreview() {
    const roll = Math.random();
    if (roll < 0.55) {
      const costs = C.FLIP_COSTS;
      const cost = costs[Math.floor(Math.random() * costs.length)];
      return { previewType: 'hero', cost };
    }
    if (roll < 0.82) return { previewType: 'resource', cost: C.FLIP_GRID_TYPES?.gold_mine?.cost || 50 };
    return { previewType: 'mystery', cost: C.MYSTERY_COST || 25 };
  }

  function matchNumberForSide(side) {
    if (side === 'player') return battleContext.playerMatchNumber;
    return (C.NEWBIE_MATCHES?.maxMatchIndex || 0) + 1;
  }

  function spawnHeroFromDeck(side, cost) {
    const quality = rollQuality(cost, matchNumberForSide(side));
    const heroId = BattleSkillRuntime.pickDeckHero(getDeck(side), quality);
    if (!heroId) return null;
    return BattleSkillRuntime.buildCombatHero(heroId, {
      heroLevel: battleContext.heroLevels[heroId] || 1,
      skillLevels: battleContext.skillLevels,
      flipCost: cost,
      side,
    });
  }

  function createCell(side, row, col) {
    const main = isMainCity(side, row, col);
    return {
      side,
      row,
      col,
      revealed: main,
      isMainCity: main,
      flipPreview: null,
      contentType: main ? 'main_city' : null,
      hero: null,
    };
  }

  function createBoard(side) {
    const cells = {};
    for (let r = 0; r < C.GRID_ROWS; r++) {
      for (let c = 0; c < C.GRID_COLS; c++) {
        const cell = createCell(side, r, c);
        cells[cellKey(side, r, c)] = cell;
      }
    }

    const mainPos = getMainCityPos(side);
    for (const p of C.INITIAL_PREVIEWS) {
      const r = mainPos.row + p.dr;
      const c = mainPos.col + p.dc;
      const key = cellKey(side, r, c);
      cells[key].flipPreview = { previewType: p.previewType, cost: p.cost };
    }

    return cells;
  }

  function createInitialState(options = {}) {
    const playerMatchNumber = options.playerMatchNumber ?? readPlayerMatchNumber();
    battleContext.playerMatchNumber = playerMatchNumber;
    return {
      playerGold: C.START_GOLD,
      enemyGold: C.START_GOLD,
      playerCityHp: C.MAIN_CITY_HP,
      enemyCityHp: C.MAIN_CITY_HP,
      playerCityMaxHp: C.MAIN_CITY_HP,
      enemyCityMaxHp: C.MAIN_CITY_HP,
      playerKills: 0,
      enemyKills: 0,
      gameOver: false,
      result: null,
      timeLeft: C.MATCH_DURATION_SEC,
      enemyFlipCd: C.ENEMY_FLIP_INTERVAL * 0.5,
      playerMatchNumber,
      isNewbieMatch: isNewbieMatch(playerMatchNumber),
      matchRecorded: false,
      cells: {
        ...createBoard('player'),
        ...createBoard('enemy'),
      },
      events: [],
    };
  }

  function getGold(state, side) {
    return side === 'player' ? state.playerGold : state.enemyGold;
  }

  function setGold(state, side, value) {
    if (side === 'player') state.playerGold = value;
    else state.enemyGold = value;
  }

  function getFlippableCells(state, side) {
    const set = new Set();
    for (const key of Object.keys(state.cells)) {
      const cell = state.cells[key];
      if (cell.side !== side || cell.revealed || cell.isMainCity) continue;
      if (!cell.flipPreview) continue;
      set.add(key);
    }
    return set;
  }

  function openAdjacentPreviews(state, side, row, col, count = 1) {
    let opened = 0;
    for (const [dr, dc] of DIRS) {
      if (opened >= count) break;
      const nr = row + dr;
      const nc = col + dc;
      if (!inBounds(nr, nc)) continue;
      const key = cellKey(side, nr, nc);
      const cell = state.cells[key];
      if (!cell || cell.revealed || cell.isMainCity) continue;
      if (!cell.flipPreview) {
        cell.flipPreview = randomFlipPreview();
        opened += 1;
      }
    }
  }

  function resolveFlipContent(side, previewType, cost) {
    if (previewType === 'hero') {
      const hero = battleContext.loaded
        ? spawnHeroFromDeck(side, cost)
        : null;
      if (hero) return { contentType: 'hero', hero };
      const quality = rollQuality(cost, matchNumberForSide(side));
      return {
        contentType: 'hero',
        hero: {
          quality,
          name: C.HERO_TEMPLATES[quality].name,
          hp: Math.round(C.HERO_TEMPLATES[quality].hp * (C.COMBAT_HP_SCALE || 1)),
          maxHp: Math.round(C.HERO_TEMPLATES[quality].hp * (C.COMBAT_HP_SCALE || 1)),
          atk: C.HERO_TEMPLATES[quality].atk,
          atkInterval: C.HERO_TEMPLATES[quality].atkInterval * (C.COMBAT_PACE || 1),
          attackTimer: 0,
          combatMods: {},
        },
      };
    }
    if (previewType === 'resource') {
      return { contentType: 'resource', hero: null, goldBonus: C.RESOURCE_GOLD };
    }
    const roll = Math.random();
    if (roll < 0.5) {
      const hero = battleContext.loaded ? spawnHeroFromDeck(side, cost) : null;
      if (hero) return { contentType: 'hero', hero };
    }
    if (roll < 0.8) {
      return { contentType: 'resource', hero: null, goldBonus: C.RESOURCE_GOLD };
    }
    return { contentType: 'mystery_gold', hero: null, goldBonus: C.MYSTERY_GOLD };
  }

  function findNearestEnemyUnit(state, attackerCell) {
    const enemies = findEnemyAttackUnits(state, attackerCell.side);
    let best = null;
    let bestDist = Infinity;
    for (const e of enemies) {
      const d = gridDistance(attackerCell, e.row, e.col);
      if (d < bestDist) {
        bestDist = d;
        best = e;
      }
    }
    return best;
  }

  function applyDeploySkills(state, side, row, col, hero) {
    const mods = hero.combatMods || {};
    const attackerCell = state.cells[cellKey(side, row, col)];

    if (mods.flipRefundPct > 0 && hero.flipCost > 0) {
      const refund = Math.round(hero.flipCost * mods.flipRefundPct);
      if (refund > 0) {
        setGold(state, side, getGold(state, side) + refund);
        state.events.push({ type: 'skill_flip_refund', side, row, col, amount: refund });
      }
    }

    if (mods.revealAdjacent > 0) {
      openAdjacentPreviews(state, side, row, col, mods.revealAdjacent);
      state.events.push({
        type: 'skill_reveal',
        side,
        row,
        col,
        count: mods.revealAdjacent,
      });
    }

    if (mods.deployBurstPct > 0) {
      const target = findNearestEnemyUnit(state, attackerCell);
      if (target?.hero) {
        const burst = Math.round(hero.atk * mods.deployBurstPct);
        const dealt = applyDamageToHero(target.hero, burst, { isFieldCombat: true });
        state.events.push({
          type: 'skill_deploy_burst',
          source: attackerCell,
          target,
          amount: dealt,
        });
        if (target.hero.hp <= 0) onHeroKilled(state, target, side, attackerCell);
      }
    }
  }

  function canFlip(state, side, row, col) {
    if (state.gameOver) return false;

    const key = cellKey(side, row, col);
    const cell = state.cells[key];
    if (!cell || cell.revealed || cell.isMainCity || !cell.flipPreview) return false;

    const gold = getGold(state, side);
    return gold >= cell.flipPreview.cost;
  }

  function flipCard(state, side, row, col) {
    if (!canFlip(state, side, row, col)) return false;

    const key = cellKey(side, row, col);
    const cell = state.cells[key];
    const { previewType, cost } = cell.flipPreview;

    setGold(state, side, getGold(state, side) - cost);
    cell.revealed = true;
    cell.flipPreview = null;

    const resolved = resolveFlipContent(side, previewType, cost);
    cell.contentType = resolved.contentType;
    cell.hero = resolved.hero || null;

    if (resolved.goldBonus) {
      setGold(state, side, getGold(state, side) + resolved.goldBonus);
      state.events.push({
        type: 'gold_bonus',
        side,
        row,
        col,
        amount: resolved.goldBonus,
      });
    }

    if (resolved.hero) {
      state.events.push({
        type: 'hero_spawn',
        side,
        row,
        col,
        heroId: resolved.hero.heroId || null,
        quality: resolved.hero.quality,
        name: resolved.hero.name,
        archetype: resolved.hero.archetypeLabel || null,
      });
      applyDeploySkills(state, side, row, col, resolved.hero);
    }

    openAdjacentPreviews(state, side, row, col);
    state.events.push({ type: 'card_flipped', side, row, col, previewType, cost });

    checkWin(state);
    return true;
  }

  function gridDistance(attacker, targetRow, targetCol) {
    const vert = attacker.row + (C.GRID_ROWS - 1 - targetRow);
    return vert + Math.abs(attacker.col - targetCol);
  }

  function isAttackUnit(cell) {
    return !!(cell.hero && cell.hero.hp > 0);
  }

  function findEnemyAttackUnits(state, attackerSide) {
    const enemySide = attackerSide === 'player' ? 'enemy' : 'player';
    const list = [];
    for (const key of Object.keys(state.cells)) {
      const cell = state.cells[key];
      if (cell.side !== enemySide || !isAttackUnit(cell)) continue;
      list.push(cell);
    }
    return list;
  }

  function canAttackEnemyMainCity(state, attackerSide) {
    if (!C.CITY_ATTACK_REQUIRES_CLEAR_FIELD) return true;
    return findEnemyAttackUnits(state, attackerSide).length === 0;
  }

  function findAttackTarget(state, attackerCell) {
    const attackerSide = attackerCell.side;
    const enemySide = attackerSide === 'player' ? 'enemy' : 'player';
    let enemies = findEnemyAttackUnits(state, attackerSide);

    if (enemies.length > 0) {
      const taunts = enemies.filter((e) => e.hero?.combatMods?.taunt);
      if (taunts.length > 0) enemies = taunts;

      let best = null;
      let bestDist = Infinity;
      for (const e of enemies) {
        const d = gridDistance(attackerCell, e.row, e.col);
        if (d < bestDist) {
          bestDist = d;
          best = e;
        }
      }
      return { kind: 'hero', cell: best };
    }

    if (canAttackEnemyMainCity(state, attackerSide)) {
      const cityPos = getMainCityPos(enemySide);
      return {
        kind: 'main_city',
        side: enemySide,
        row: cityPos.row,
        col: cityPos.col,
      };
    }

    return { kind: 'none' };
  }

  function calcUnitDamage(attacker, rawDamage, targetHero, isFieldCombat) {
    let dmg = rawDamage;
    const mods = attacker.combatMods || {};

    if (isFieldCombat && mods.executeThreshold != null && targetHero.maxHp > 0) {
      const ratio = targetHero.hp / targetHero.maxHp;
      if (ratio <= mods.executeThreshold) {
        dmg = Math.round(dmg * (1 + mods.executeBonusPct));
      }
    }

    return dmg;
  }

  function applyDamageToHero(hero, rawDamage, options = {}) {
    const { isFieldCombat = true } = options;
    let dmg = rawDamage;
    const red = hero.combatMods?.damageReductionPct || 0;
    if (isFieldCombat && red > 0) {
      dmg = Math.round(dmg * (1 - red));
    }
    hero.hp = Math.max(0, hero.hp - dmg);
    return dmg;
  }

  function applySplash(state, attackerCell, primaryTarget, rawDamage) {
    const splashPct = attackerCell.hero?.combatMods?.splashPct || 0;
    if (!attackerCell.hero || splashPct <= 0) return;
    if (primaryTarget.kind !== 'hero') return;

    const splashDmg = Math.round(rawDamage * splashPct);
    const enemySide = attackerCell.side === 'player' ? 'enemy' : 'player';

    for (const [dr, dc] of DIRS) {
      const nr = primaryTarget.cell.row + dr;
      const nc = primaryTarget.cell.col + dc;
      if (!inBounds(nr, nc)) continue;
      const key = cellKey(enemySide, nr, nc);
      const cell = state.cells[key];
      if (!cell?.hero || cell.hero.hp <= 0) continue;
      if (cell === primaryTarget.cell) continue;
      const dealt = applyDamageToHero(cell.hero, splashDmg, { isFieldCombat: true });
      state.events.push({
        type: 'damage',
        source: attackerCell,
        target: cell,
        amount: dealt,
        splash: true,
      });
      if (cell.hero.hp <= 0) onHeroKilled(state, cell, attackerCell.side, attackerCell);
    }
  }

  function applyDotOnHit(targetHero, dotPctPerSec, durationSec = 3) {
    if (!targetHero || dotPctPerSec <= 0) return;
    targetHero.activeDots = targetHero.activeDots || [];
    targetHero.activeDots.push({ pctPerSec: dotPctPerSec, ttl: durationSec });
  }

  function applyDotTick(state, dt) {
    for (const key of Object.keys(state.cells)) {
      const cell = state.cells[key];
      if (!cell.hero || cell.hero.hp <= 0 || !cell.hero.activeDots?.length) continue;

      const hero = cell.hero;
      hero._dotAcc = (hero._dotAcc || 0) + dt;
      if (hero._dotAcc < 1) continue;
      hero._dotAcc -= 1;

      let tickDmg = 0;
      hero.activeDots = hero.activeDots.filter((dot) => {
        tickDmg += Math.max(1, Math.round(hero.maxHp * dot.pctPerSec));
        dot.ttl -= 1;
        return dot.ttl > 0;
      });

      if (tickDmg > 0) {
        const dealt = applyDamageToHero(hero, tickDmg, { isFieldCombat: true });
        state.events.push({ type: 'dot_damage', target: cell, amount: dealt });
        if (hero.hp <= 0) onHeroKilled(state, cell, null, null);
      }
    }
  }

  function onHeroKilled(state, deadCell, killerSide, killerCell) {
    deadCell.contentType = 'grave';
    const deadHero = deadCell.hero;
    deadCell.hero = null;

    if (killerSide === 'player') state.playerKills += 1;
    else if (killerSide === 'enemy') state.enemyKills += 1;

    state.events.push({
      type: 'hero_killed',
      side: deadCell.side,
      row: deadCell.row,
      col: deadCell.col,
      killerSide,
    });

    const killGold = killerCell?.hero?.combatMods?.killGold || 0;
    if (killGold > 0 && killerSide) {
      setGold(state, killerSide, getGold(state, killerSide) + killGold);
      state.events.push({
        type: 'skill_kill_gold',
        side: killerSide,
        amount: killGold,
        victim: { row: deadCell.row, col: deadCell.col },
      });
    }
  }

  function tickCombat(state, dt) {
    if (state.gameOver) return;

    applyDotTick(state, dt);

    for (const key of Object.keys(state.cells)) {
      const cell = state.cells[key];
      if (!cell.hero || cell.hero.hp <= 0) continue;

      const hero = cell.hero;
      hero.attackTimer -= dt;
      if (hero.attackTimer > 0) continue;

      const target = findAttackTarget(state, cell);
      if (target.kind === 'none') {
        hero.attackTimer = hero.atkInterval;
        continue;
      }

      if (target.kind === 'hero') {
        const raw = calcUnitDamage(hero, hero.atk, target.cell.hero, true);
        const dealt = applyDamageToHero(target.cell.hero, raw, { isFieldCombat: true });
        state.events.push({
          type: 'damage',
          source: cell,
          target: target.cell,
          amount: dealt,
          splash: false,
        });
        applySplash(state, cell, target, hero.atk);
        const dotPct = hero.combatMods?.dotPctPerSec || 0;
        if (dotPct > 0) applyDotOnHit(target.cell.hero, dotPct);
        if (target.cell.hero.hp <= 0) onHeroKilled(state, target.cell, cell.side, cell);
      } else {
        const cityBonus = hero.combatMods?.cityDamagePct || 0;
        const cityDmg = Math.round(hero.atk * (1 + cityBonus));
        if (target.side === 'enemy') {
          state.enemyCityHp = Math.max(0, state.enemyCityHp - cityDmg);
        } else {
          state.playerCityHp = Math.max(0, state.playerCityHp - cityDmg);
        }
        state.events.push({
          type: 'city_damage',
          source: cell,
          targetSide: target.side,
          amount: cityDmg,
        });
      }

      hero.attackTimer = hero.atkInterval;
    }

    checkWin(state);
  }

  function tickGold(state, dt, accumulator) {
    if (state.gameOver) return accumulator;
    accumulator += dt;
    while (accumulator >= 1) {
      accumulator -= 1;
      state.playerGold += C.GOLD_PER_SEC;
      state.enemyGold += C.GOLD_PER_SEC;
    }
    return accumulator;
  }

  function tickTimer(state, dt) {
    if (state.gameOver) return;
    state.timeLeft = Math.max(0, state.timeLeft - dt);
    if (state.timeLeft <= 0) checkWin(state, true);
  }

  function checkWin(state, forceTimeUp = false) {
    if (state.gameOver) return true;

    if (state.enemyCityHp <= 0) {
      endGame(state, 'player', 'destroy_city');
      return true;
    }
    if (state.playerCityHp <= 0) {
      endGame(state, 'enemy', 'destroy_city');
      return true;
    }

    if (forceTimeUp || state.timeLeft <= 0) {
      if (state.playerKills > state.enemyKills) {
        endGame(state, 'player', 'more_kills');
      } else if (state.enemyKills > state.playerKills) {
        endGame(state, 'enemy', 'more_kills');
      } else {
        endGame(state, 'draw', 'tie_kills');
      }
      return true;
    }

    return false;
  }

  function endGame(state, winner, reason) {
    state.gameOver = true;
    if (!state.matchRecorded) {
      state.matchRecorded = true;
      recordMatchCompleted();
    }
    state.result = { winner, reason };
    state.events.push({ type: 'game_over', winner, reason });
  }

  function getAffordableFlips(state, side) {
    const gold = getGold(state, side);
    const list = [];
    for (const key of getFlippableCells(state, side)) {
      const cell = state.cells[key];
      if (gold >= cell.flipPreview.cost) {
        list.push({ key, row: cell.row, col: cell.col, cell });
      }
    }
    return list;
  }

  function pickAiFlip(state) {
    const affordable = getAffordableFlips(state, 'enemy');
    if (affordable.length === 0) return null;

    const scored = affordable.map(({ key, row, col, cell }) => {
      const { previewType, cost } = cell.flipPreview;
      let score = 0;
      if (previewType === 'hero') score += 60 + cost;
      if (previewType === 'resource') score += 20;
      if (previewType === 'mystery') score += 30;
      score -= cost * 0.2;
      score += Math.random() * 6;
      return { key, row, col, score };
    });

    scored.sort((a, b) => b.score - a.score);
    return scored[0];
  }

  function hasEnemyFlippable(state) {
    return getFlippableCells(state, 'enemy').size > 0;
  }

  function canEnemyAffordAnyFlip(state) {
    return getAffordableFlips(state, 'enemy').length > 0;
  }

  function runAiFlip(state) {
    const pick = pickAiFlip(state);
    if (!pick) return false;
    return flipCard(state, 'enemy', pick.row, pick.col);
  }

  function tickEnemyAi(state, dt) {
    if (state.gameOver) return false;

    state.enemyFlipCd -= dt;
    if (state.enemyFlipCd > 0) return false;

    if (canEnemyAffordAnyFlip(state)) {
      const flipped = runAiFlip(state);
      state.enemyFlipCd = C.ENEMY_FLIP_INTERVAL;
      return flipped;
    }

    state.enemyFlipCd = hasEnemyFlippable(state) ? C.ENEMY_FLIP_RETRY : C.ENEMY_FLIP_INTERVAL;
    return false;
  }

  function drainEvents(state) {
    const events = state.events.slice();
    state.events.length = 0;
    return events;
  }

  function formatTime(sec) {
    const s = Math.ceil(sec);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`;
  }

  return {
    cellKey,
    getMainCityPos,
    loadConfig,
    configure,
    createInitialState,
    getFlippableCells,
    canFlip,
    flipCard,
    tickCombat,
    tickGold,
    tickTimer,
    checkWin,
    runAiFlip,
    tickEnemyAi,
    pickAiFlip,
    getAffordableFlips,
    hasEnemyFlippable,
    canEnemyAffordAnyFlip,
    drainEvents,
    formatTime,
    canAttackEnemyMainCity,
    findAttackTarget,
    getQualityTable,
    isNewbieMatch,
    readPlayerMatchNumber,
    recordMatchCompleted,
    rollQuality,
  };
})();
