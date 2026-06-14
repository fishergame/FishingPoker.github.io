/**
 * 纯规则层 — 不依赖 DOM，后续可直接迁到 Cocos TypeScript。
 */
const BattleRules = (() => {
  const C = BattleConfig;
  const DIRS = [[-1, 0], [1, 0], [0, -1], [0, 1]];

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

  function rollQuality(cost) {
    const table = C.QUALITY_BY_COST[cost] || C.QUALITY_BY_COST[20];
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
    if (roll < 0.82) return { previewType: 'resource', cost: 20 };
    return { previewType: 'mystery', cost: 10 };
  }

  function createHero(quality) {
    const tpl = C.HERO_TEMPLATES[quality];
    const pace = C.COMBAT_PACE || 1;
    const hpScale = C.COMBAT_HP_SCALE || 1;
    const atkScale = C.COMBAT_ATK_SCALE || 1;

    let atkInterval = tpl.atkInterval * pace;
    if (tpl.passiveId === 'swift') atkInterval *= C.PASSIVE.swiftAtkMul;

    const hp = Math.round(tpl.hp * hpScale);
    const atk = Math.max(1, Math.round(tpl.atk * atkScale));

    return {
      quality,
      name: tpl.name,
      hp,
      maxHp: hp,
      atk,
      atkInterval,
      attackTimer: Math.random() * atkInterval * 0.5,
      passive: tpl.passive,
      passiveId: tpl.passiveId,
    };
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

  function createInitialState() {
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

  function openAdjacentPreviews(state, side, row, col) {
    for (const [dr, dc] of DIRS) {
      const nr = row + dr;
      const nc = col + dc;
      if (!inBounds(nr, nc)) continue;
      const key = cellKey(side, nr, nc);
      const cell = state.cells[key];
      if (!cell || cell.revealed || cell.isMainCity) continue;
      if (!cell.flipPreview) cell.flipPreview = randomFlipPreview();
    }
  }

  function resolveFlipContent(previewType, cost) {
    if (previewType === 'hero') {
      const quality = rollQuality(cost);
      return { contentType: 'hero', hero: createHero(quality) };
    }
    if (previewType === 'resource') {
      return { contentType: 'resource', hero: null, goldBonus: C.RESOURCE_GOLD };
    }
    const roll = Math.random();
    if (roll < 0.5) {
      const quality = rollQuality(cost);
      return { contentType: 'hero', hero: createHero(quality) };
    }
    if (roll < 0.8) {
      return { contentType: 'resource', hero: null, goldBonus: C.RESOURCE_GOLD };
    }
    return { contentType: 'mystery_gold', hero: null, goldBonus: C.MYSTERY_GOLD };
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

    const resolved = resolveFlipContent(previewType, cost);
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
        quality: resolved.hero.quality,
        name: resolved.hero.name,
      });
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

  /** 攻击型单位（当前仅英雄；后续可扩展其他卡牌类型） */
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

  /** 双方共用：对方场上无攻击单位时，才允许打主城 */
  function canAttackEnemyMainCity(state, attackerSide) {
    if (!C.CITY_ATTACK_REQUIRES_CLEAR_FIELD) return true;
    return findEnemyAttackUnits(state, attackerSide).length === 0;
  }

  function findAttackTarget(state, attackerCell) {
    const attackerSide = attackerCell.side;
    const enemySide = attackerSide === 'player' ? 'enemy' : 'player';
    const enemies = findEnemyAttackUnits(state, attackerSide);

    if (enemies.length > 0) {
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

  function applyDamageToHero(hero, rawDamage) {
    let dmg = rawDamage;
    if (hero.passiveId === 'ironwall') {
      dmg = Math.round(dmg * (1 - C.PASSIVE.ironwallReduction));
    }
    hero.hp = Math.max(0, hero.hp - dmg);
    return dmg;
  }

  function applySplash(state, attackerCell, primaryTarget, rawDamage) {
    if (!attackerCell.hero || attackerCell.hero.passiveId !== 'splash') return;
    if (primaryTarget.kind !== 'hero') return;

    const splashDmg = Math.round(rawDamage * C.PASSIVE.splashRatio);
    const enemySide = attackerCell.side === 'player' ? 'enemy' : 'player';

    for (const [dr, dc] of DIRS) {
      const nr = primaryTarget.cell.row + dr;
      const nc = primaryTarget.cell.col + dc;
      if (!inBounds(nr, nc)) continue;
      const key = cellKey(enemySide, nr, nc);
      const cell = state.cells[key];
      if (!cell?.hero || cell.hero.hp <= 0) continue;
      if (cell === primaryTarget.cell) continue;
      const dealt = applyDamageToHero(cell.hero, splashDmg);
      state.events.push({
        type: 'damage',
        source: attackerCell,
        target: cell,
        amount: dealt,
        splash: true,
      });
      if (cell.hero.hp <= 0) onHeroKilled(state, cell, attackerCell.side);
    }
  }

  function onHeroKilled(state, deadCell, killerSide) {
    deadCell.contentType = 'grave';
    deadCell.hero = null;
    if (killerSide === 'player') state.playerKills += 1;
    else state.enemyKills += 1;
    state.events.push({
      type: 'hero_killed',
      side: deadCell.side,
      row: deadCell.row,
      col: deadCell.col,
      killerSide,
    });
  }

  function tickCombat(state, dt) {
    if (state.gameOver) return;

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

      const rawDamage = hero.atk;
      let dealt = rawDamage;

      if (target.kind === 'hero') {
        dealt = applyDamageToHero(target.cell.hero, rawDamage);
        state.events.push({
          type: 'damage',
          source: cell,
          target: target.cell,
          amount: dealt,
          splash: false,
        });
        applySplash(state, cell, target, rawDamage);
        if (target.cell.hero.hp <= 0) onHeroKilled(state, target.cell, cell.side);
      } else {
        if (target.side === 'enemy') {
          state.enemyCityHp = Math.max(0, state.enemyCityHp - rawDamage);
        } else {
          state.playerCityHp = Math.max(0, state.playerCityHp - rawDamage);
        }
        state.events.push({
          type: 'city_damage',
          source: cell,
          targetSide: target.side,
          amount: rawDamage,
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

  /** 敌方独立行动：开局即与玩家并行翻牌 */
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
  };
})();
