// ===== View + loop（规则在 battle-rules.js，后续迁 Cocos 时只换本文件）=====

const C = BattleConfig;
const R = BattleRules;

let state = null;
let goldAcc = 0;
let lastTime = 0;
let projectiles = [];

const enemyBoardEl = document.getElementById('enemy-board');
const playerBoardEl = document.getElementById('player-board');
const canvas = document.getElementById('fx-canvas');
const ctx = canvas.getContext('2d');

const PREVIEW_ICONS = {
  hero: '⛑',
  resource: '◆',
  mystery: '?',
};

const QUALITY_ICONS = {
  common: '⚔',
  rare: '🏹',
  epic: '🛡',
  legendary: '🐉',
};

function init() {
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  document.getElementById('restart-btn').addEventListener('click', resetGame);
  resetGame();
  requestAnimationFrame(gameLoop);
}

function resizeCanvas() {
  const rect = document.getElementById('game-container').getBoundingClientRect();
  canvas.width = rect.width * devicePixelRatio;
  canvas.height = rect.height * devicePixelRatio;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
}

function resetGame() {
  state = R.createInitialState();
  goldAcc = 0;
  lastTime = 0;
  projectiles = [];
  document.getElementById('overlay').classList.add('hidden');
  renderBoards();
  updateUI();
}

function renderBoards() {
  renderSideBoard(enemyBoardEl, 'enemy');
  renderSideBoard(playerBoardEl, 'player');
}

function renderSideBoard(container, side) {
  container.innerHTML = '';
  const flippable = R.getFlippableCells(state, side);
  const isPlayerSide = side === 'player';

  for (let r = 0; r < C.GRID_ROWS; r++) {
    for (let c = 0; c < C.GRID_COLS; c++) {
      const key = R.cellKey(side, r, c);
      const cell = state.cells[key];
      const div = document.createElement('div');
      div.className = 'card';
      div.dataset.side = side;
      div.dataset.row = r;
      div.dataset.col = c;

      if (cell.isMainCity) {
        div.classList.add('main-city', `${side}-side`);
        div.dataset.mainCity = 'true';
        div.innerHTML = '<span class="city-icon">🏰</span>';
      } else if (!cell.revealed && cell.flipPreview) {
        const { previewType, cost } = cell.flipPreview;
        div.classList.add('preview-card', `${side}-side`);
        const affordable = getGold(side) >= cost;
        const canFlip = !state.gameOver && flippable.has(key);

        if (canFlip) {
          div.classList.add('flippable');
          if (!affordable) div.classList.add('disabled-flip');
          if (isPlayerSide && affordable) {
            div.addEventListener('click', () => onCardClick(r, c));
          }
        }

        div.innerHTML = `
          <span class="preview-icon">${PREVIEW_ICONS[previewType]}</span>
          <span class="preview-cost"><span>⬡</span>${cost}</span>`;
      } else if (!cell.revealed) {
        div.classList.add('hidden-card', `${side}-side`);
      } else if (cell.contentType === 'hero' && cell.hero) {
        div.classList.add('hero-card', `quality-${cell.hero.quality}`, `${side}-side`);
        const hpPct = (cell.hero.hp / cell.hero.maxHp) * 100;
        div.innerHTML = `
          <span class="hero-icon">${QUALITY_ICONS[cell.hero.quality]}</span>
          <div class="hero-hp-bar"><div class="hero-hp-fill" style="width:${hpPct}%"></div></div>
          <span class="hero-label">${cell.hero.name}</span>`;
      } else if (cell.contentType === 'resource' || cell.contentType === 'mystery_gold') {
        div.classList.add('resource-card', `${side}-side`);
        div.textContent = '◆';
      } else if (cell.contentType === 'grave') {
        div.classList.add('grave-card', `${side}-side`);
        div.textContent = '✕';
      } else {
        div.classList.add('hidden-card', `${side}-side`);
        div.style.opacity = '0.35';
      }

      container.appendChild(div);
    }
  }
}

function getGold(side) {
  return side === 'player' ? state.playerGold : state.enemyGold;
}

function onCardClick(row, col) {
  if (state.gameOver) return;
  if (!R.flipCard(state, 'player', row, col)) return;
  const flashes = handleEvents();
  renderBoards();
  applyHitFlashes(flashes);
  updateUI();
}

function handleEvents() {
  const events = R.drainEvents(state);
  const cityHits = [];
  const heroHits = [];

  for (const ev of events) {
    if (ev.type === 'damage' || ev.type === 'city_damage') {
      spawnProjectile(ev);
      if (ev.type === 'damage' && ev.target) {
        heroHits.push({ side: ev.target.side, row: ev.target.row, col: ev.target.col });
      }
      if (ev.type === 'city_damage') {
        cityHits.push(ev.targetSide);
      }
    }
    if (ev.type === 'game_over') showResult(ev);
  }

  return { cityHits, heroHits };
}

function applyHitFlashes({ cityHits, heroHits }) {
  for (const h of heroHits) flashCard(h.side, h.row, h.col);
  for (const side of cityHits) flashMainCity(side);
}

function flashCard(side, row, col) {
  const board = side === 'player' ? playerBoardEl : enemyBoardEl;
  const el = board.querySelector(`[data-row="${row}"][data-col="${col}"]`);
  if (!el) return;
  el.classList.remove('damage-flash');
  void el.offsetWidth;
  el.classList.add('damage-flash');
}

function flashMainCity(side) {
  const board = side === 'player' ? playerBoardEl : enemyBoardEl;
  const cityEl = board.querySelector('[data-main-city="true"]');
  if (!cityEl) return;
  cityEl.classList.remove('city-hit-flash');
  void cityEl.offsetWidth;
  cityEl.classList.add('city-hit-flash');
}

function getCardCenter(side, row, col) {
  const board = side === 'player' ? playerBoardEl : enemyBoardEl;
  const el = board.querySelector(`[data-row="${row}"][data-col="${col}"]`);
  const containerRect = document.getElementById('game-container').getBoundingClientRect();
  if (!el) return { x: containerRect.width / 2, y: containerRect.height / 2 };
  const rect = el.getBoundingClientRect();
  return {
    x: rect.left + rect.width / 2 - containerRect.left,
    y: rect.top + rect.height / 2 - containerRect.top,
  };
}

function spawnProjectile(ev) {
  const src = ev.source;
  const start = getCardCenter(src.side, src.row, src.col);
  let end;

  if (ev.type === 'city_damage') {
    const pos = R.getMainCityPos(ev.targetSide);
    end = getCardCenter(ev.targetSide, pos.row, pos.col);
  } else {
    end = getCardCenter(ev.target.side, ev.target.row, ev.target.col);
  }

  projectiles.push({
    type: src.side === 'player' ? 'fire' : 'ice',
    x: start.x,
    y: start.y,
    startX: start.x,
    startY: start.y,
    endX: end.x,
    endY: end.y,
    t: 0,
    duration: C.PROJECTILE_DURATION || 0.45,
    trail: [],
  });
}

function updateProjectiles(dt) {
  for (let i = projectiles.length - 1; i >= 0; i--) {
    const p = projectiles[i];
    p.t += dt / p.duration;
    if (p.t >= 1) {
      projectiles.splice(i, 1);
      continue;
    }
    const t = p.t;
    p.x = p.startX + (p.endX - p.startX) * t;
    const linearY = p.startY + (p.endY - p.startY) * t;
    const arcHeight = Math.abs(p.endY - p.startY) * 0.25 + 30;
    const arc = -4 * arcHeight * t * (1 - t);
    p.y = linearY + arc;

    p.trail.push({ x: p.x, y: p.y, life: 1 });
    if (p.trail.length > 14) p.trail.shift();
    for (const pt of p.trail) pt.life -= dt * 2.5;
    p.trail = p.trail.filter(pt => pt.life > 0);
  }
}

function drawProjectiles() {
  const w = canvas.width / devicePixelRatio;
  const h = canvas.height / devicePixelRatio;
  ctx.clearRect(0, 0, w, h);

  for (const p of projectiles) {
    const isFire = p.type === 'fire';
    for (let i = 0; i < p.trail.length; i++) {
      const pt = p.trail[i];
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 2 + i * 0.2, 0, Math.PI * 2);
      ctx.fillStyle = isFire
        ? `rgba(255, ${120 + i * 6}, 40, ${pt.life * 0.5})`
        : `rgba(100, 200, 255, ${pt.life * 0.5})`;
      ctx.fill();
    }
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = isFire ? '#ffe066' : '#a8e6ff';
    ctx.fill();
  }
}

function updateUI() {
  document.getElementById('player-gold').textContent = Math.floor(state.playerGold);
  document.getElementById('player-kills').textContent = state.playerKills;
  document.getElementById('enemy-kills').textContent = state.enemyKills;
  document.getElementById('timer').textContent = R.formatTime(state.timeLeft);

  document.getElementById('enemy-hp-fill').style.width =
    `${(state.enemyCityHp / state.enemyCityMaxHp) * 100}%`;
  document.getElementById('player-hp-fill').style.width =
    `${(state.playerCityHp / state.playerCityMaxHp) * 100}%`;
  document.getElementById('enemy-hp-text').textContent = Math.ceil(state.enemyCityHp);
  document.getElementById('player-hp-text').textContent = Math.ceil(state.playerCityHp);

  const statusEl = document.getElementById('battle-status');
  statusEl.textContent = state.gameOver ? '战斗结束' : '战斗中';
  statusEl.className = 'status-badge';

  const hint = document.getElementById('hint');
  if (state.gameOver) {
    hint.textContent = '';
    return;
  }

  const flippable = R.getFlippableCells(state, 'player');
  const affordable = [...flippable].some((key) => {
    const cell = state.cells[key];
    return state.playerGold >= cell.flipPreview.cost;
  });

  if (flippable.size === 0) {
    hint.textContent = '无回合限制：随时翻牌；暂无可翻卡，等待金币恢复';
  } else if (!affordable) {
    hint.textContent = `金币不足（每秒 +${C.GOLD_PER_SEC}），战斗仍在继续`;
  } else {
    hint.textContent = '点击亮起卡牌翻牌；先清对方攻击卡，才能打主城';
  }
}

function showResult(ev) {
  const { winner, reason } = ev;
  const title = document.getElementById('result-title');
  const desc = document.getElementById('result-desc');

  if (winner === 'player') {
    title.textContent = '胜利！';
    title.style.color = '#ffd700';
  } else if (winner === 'enemy') {
    title.textContent = '失败…';
    title.style.color = '#ff7b72';
  } else {
    title.textContent = '平局';
    title.style.color = '#ccc';
  }

  const reasonText = {
    destroy_city: '摧毁了对方主城',
    more_kills: `时间到！击杀 ${state.playerKills}:${state.enemyKills} 获胜`,
    tie_kills: `时间到！击杀 ${state.playerKills}:${state.enemyKills} 平局`,
  };

  const side = winner === 'player' ? '你' : winner === 'enemy' ? '敌方' : '';
  desc.textContent = winner === 'draw'
    ? reasonText[reason]
    : `${side}${reasonText[reason]}`;
  document.getElementById('overlay').classList.remove('hidden');
}

function gameLoop(timestamp) {
  const dt = lastTime ? Math.min((timestamp - lastTime) / 1000, 0.05) : 0;
  lastTime = timestamp;

  if (!state.gameOver) {
    goldAcc = R.tickGold(state, dt, goldAcc);
    R.tickTimer(state, dt);
    R.tickCombat(state, dt);
    const aiFlipped = R.tickEnemyAi(state, dt);
    const hadEvents = state.events.length > 0;
    const flashes = handleEvents();
    if (hadEvents || aiFlipped) renderBoards();
    if (flashes.cityHits.length || flashes.heroHits.length) applyHitFlashes(flashes);
    updateUI();
  }

  updateProjectiles(dt);
  drawProjectiles();
  requestAnimationFrame(gameLoop);
}

init();
