#!/usr/bin/env node
/**
 * 全英雄技能一览 + 翻卡对战模拟（支持 battleBalance 真实主城 HP）
 *
 * 用法：
 *   node scripts/sim-battle.js --real --battles=30 --arena=1 --level=20
 *   node scripts/sim-battle.js --real --multi --battles=20
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

const ARENA_NAMES = {
  1: '青铜',
  2: '白银',
  3: '黄金',
  4: '铂金',
  5: '钻石',
  6: '星耀',
  7: '大师',
  8: '宗师',
  9: '王者',
  10: '传奇',
};

/** 多阶段模拟场景 */
const MULTI_SCENARIOS = [
  { arenaId: 1, level: 1, label: '青铜 · L1 新手' },
  { arenaId: 1, level: 10, label: '青铜 · L10' },
  { arenaId: 1, level: 20, label: '青铜 · L20' },
  { arenaId: 1, level: 30, label: '青铜 · L30' },
  { arenaId: 5, level: 20, label: '钻石 · L20' },
  { arenaId: 10, level: 20, label: '传奇 · L20' },
  { arenaId: 10, level: 30, label: '传奇 · L30 满级' },
];

const KEY_LEVELS = [1, 5, 10, 15, 20, 25, 30];

function loadGlobal(name, file) {
  const code = fs.readFileSync(path.join(ROOT, file), 'utf8').replace(
    new RegExp(`const ${name}`),
    `globalThis.${name}`,
  );
  eval(code);
}

function boot() {
  loadGlobal('BattleConfig', 'battle-config.js');
  loadGlobal('HeroesConfig', 'heroes-config.js');
  loadGlobal('HeroLevelConfig', 'hero-level-config.js');
  loadGlobal('BattleBalanceConfig', 'battle-balance-config.js');
  loadGlobal('BattleSkillRuntime', 'battle-skill-runtime.js');
  loadGlobal('SkillConfig', 'skill-config.js');
  loadGlobal('BattleRules', 'battle-rules.js');

  SkillConfig.hydrateFromJson(
    JSON.parse(fs.readFileSync(path.join(ROOT, 'skill.json'), 'utf8')),
    JSON.parse(fs.readFileSync(path.join(ROOT, 'heroBattle.json'), 'utf8')),
  );
  BattleBalanceConfig.hydrateFromJson(
    JSON.parse(fs.readFileSync(path.join(ROOT, 'battleBalance.json'), 'utf8')),
  );
}

function parseArgs() {
  const args = {
    battles: 30,
    level: 20,
    arena: 1,
    seed: 42,
    real: false,
    multi: false,
    out: 'docs/_SKILL_SIM_APPENDIX.md',
  };
  for (const a of process.argv.slice(2)) {
    if (a === '--real') args.real = true;
    if (a === '--multi') args.multi = true;
    if (a.startsWith('--battles=')) args.battles = Number(a.split('=')[1]);
    if (a.startsWith('--level=')) args.level = Number(a.split('=')[1]);
    if (a.startsWith('--arena=')) args.arena = Number(a.split('=')[1]);
    if (a.startsWith('--seed=')) args.seed = Number(a.split('=')[1]);
    if (a.startsWith('--out=')) args.out = a.split('=')[1];
  }
  if (args.real && !args.multi) {
    args.out = 'docs/_SKILL_SIM_APPENDIX.md';
  }
  if (args.multi) {
    args.real = true;
    args.out = 'docs/_SKILL_SIM_APPENDIX.md';
  }
  return args;
}

function makeRng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

function fmtNum(n) {
  return n.toLocaleString('en-US');
}

function fmtTime(sec) {
  const s = Math.max(0, Math.ceil(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}

function allCombatHeroIds() {
  return HeroesConfig.HEROES.filter((h) => h.type !== 'resource').map((h) => h.id);
}

function heroLevelsMap(level) {
  const map = {};
  for (const id of allCombatHeroIds()) map[id] = level;
  map.gold_mine = level;
  return map;
}

function applyArenaBalance(state, arenaId, level) {
  const hp = BattleBalanceConfig.mainCityHp(arenaId, level);
  const dur = BattleBalanceConfig.matchDurationSec(arenaId);
  state.playerCityHp = hp;
  state.playerCityMaxHp = hp;
  state.enemyCityHp = hp;
  state.enemyCityMaxHp = hp;
  state.timeLeft = dur;
  return { hp, dur };
}

function printMainCityHpTables() {
  const lines = [];
  lines.push('## 主城 HP 配表（battleBalance.json）\n');
  lines.push('公式：`mainCityHp = mainCityHpBase[场次] × 1.15^(avgDeckLevel - 1)`\n');

  lines.push('### 对局时长\n');
  lines.push('| 场次 | 名称 | 秒 | 显示 |');
  lines.push('|:---:|:---|:---:|:---:|');
  for (let aid = 1; aid <= 10; aid++) {
    const dur = BattleBalanceConfig.matchDurationSec(aid);
    lines.push(`| ${aid} | ${ARENA_NAMES[aid]} | ${dur} | **${fmtTime(dur)}** |`);
  }
  lines.push('');

  lines.push('### 关键等级横向对照（常用阶段）\n');
  lines.push('| 等级 | ' + Object.values(ARENA_NAMES).join(' | ') + ' |');
  lines.push('|:---|' + Object.keys(ARENA_NAMES).map(() => '---:').join('|') + '|');
  for (const lv of KEY_LEVELS) {
    const cols = [];
    for (let aid = 1; aid <= 10; aid++) {
      cols.push(fmtNum(BattleBalanceConfig.mainCityHp(aid, lv)));
    }
    lines.push(`| **L${lv}** | ${cols.join(' | ')} |`);
  }
  lines.push('');

  lines.push('### 全表：场次 × 等级（L1–L30）\n');
  lines.push('| 场次 | ' + Array.from({ length: 30 }, (_, i) => `L${i + 1}`).join(' | ') + ' |');
  lines.push('|:---|' + Array(30).fill('---:').join('|') + '|');
  for (let aid = 1; aid <= 10; aid++) {
    const cols = [];
    for (let lv = 1; lv <= 30; lv++) {
      cols.push(fmtNum(BattleBalanceConfig.mainCityHp(aid, lv)));
    }
    lines.push(`| **${aid} ${ARENA_NAMES[aid]}** | ${cols.join(' | ')} |`);
  }
  return lines.join('\n');
}

function runFullBattle(level, rng, deck, arenaId = null) {
  BattleRules.configure({
    playerDeck: deck,
    enemyDeck: deck,
    heroLevels: heroLevelsMap(level),
  });

  const realRandom = Math.random;
  Math.random = rng;

  const state = BattleRules.createInitialState();
  let balance = null;
  if (arenaId != null) {
    balance = applyArenaBalance(state, arenaId, level);
  }

  let goldAcc = 0;
  const dt = 0.1;
  const maxSec = (balance?.dur ?? BattleConfig.MATCH_DURATION_SEC) + 10;
  let t = 0;
  const spawns = { player: {}, enemy: {} };
  const startCityHp = balance?.hp ?? state.playerCityHp;

  while (t < maxSec && !state.gameOver) {
    BattleRules.tickTimer(state, dt);
    goldAcc = BattleRules.tickGold(state, dt, goldAcc);
    BattleRules.tickEnemyAi(state, dt);

    if (rng() < 0.32) {
      const flips = BattleRules.getAffordableFlips(state, 'player');
      if (flips.length > 0) {
        const pick = flips[Math.floor(rng() * flips.length)];
        BattleRules.flipCard(state, 'player', pick.row, pick.col);
        const cell = state.cells[pick.key];
        if (cell?.hero?.heroId) {
          spawns.player[cell.hero.heroId] = (spawns.player[cell.hero.heroId] || 0) + 1;
        }
      }
    }

    BattleRules.tickCombat(state, dt);
    t += dt;
  }

  Math.random = realRandom;

  for (const key of Object.keys(state.cells)) {
    const cell = state.cells[key];
    if (cell.side === 'enemy' && cell.hero?.heroId) {
      spawns.enemy[cell.hero.heroId] = (spawns.enemy[cell.hero.heroId] || 0) + 1;
    }
  }

  const cityDamageDealt = startCityHp - state.enemyCityHp;
  const cityDamageTaken = startCityHp - state.playerCityHp;

  return {
    winner: state.result?.winner || 'draw',
    reason: state.result?.reason || 'timeout',
    timeLeft: Math.round(state.timeLeft * 10) / 10,
    elapsed: Math.round(t * 10) / 10,
    playerKills: state.playerKills,
    enemyKills: state.enemyKills,
    playerCityHp: state.playerCityHp,
    enemyCityHp: state.enemyCityHp,
    startCityHp,
    cityDamageDealt,
    cityDamageTaken,
    spawns,
    balance,
  };
}

function summarizeBattles(results) {
  const n = results.length;
  let playerWins = 0;
  let enemyWins = 0;
  let draws = 0;
  const reasonCount = {};
  let avgTimeLeft = 0;
  let avgElapsed = 0;
  let avgCityDmg = 0;

  for (const r of results) {
    if (r.winner === 'player') playerWins++;
    else if (r.winner === 'enemy') enemyWins++;
    else draws++;
    reasonCount[r.reason] = (reasonCount[r.reason] || 0) + 1;
    avgTimeLeft += r.timeLeft;
    avgElapsed += r.elapsed;
    avgCityDmg += r.cityDamageDealt;
  }

  return {
    n,
    playerWins,
    enemyWins,
    draws,
    reasonCount,
    avgTimeLeft: avgTimeLeft / n,
    avgElapsed: avgElapsed / n,
    avgCityDmg: Math.round(avgCityDmg / n),
  };
}

function runScenario(scenario, battles, seed, deck) {
  const results = [];
  for (let i = 0; i < battles; i++) {
    const rng = makeRng(seed + scenario.arenaId * 1000 + scenario.level * 17 + i * 9973);
    results.push(runFullBattle(scenario.level, rng, deck, scenario.arenaId));
  }
  const summary = summarizeBattles(results);
  const hp = BattleBalanceConfig.mainCityHp(scenario.arenaId, scenario.level);
  const dur = BattleBalanceConfig.matchDurationSec(scenario.arenaId);
  return { scenario, hp, dur, results, summary, sample: results[results.length - 1] };
}

function formatScenarioBlock(run) {
  const { scenario, hp, dur, summary, sample } = run;
  const lines = [];
  lines.push(`### ${scenario.label}`);
  lines.push('');
  lines.push('| 配置 | 数值 |');
  lines.push('|:---|:---|');
  lines.push(`| 场次 | ${scenario.arenaId} ${ARENA_NAMES[scenario.arenaId]} |`);
  lines.push(`| 卡组平均等级 | L${scenario.level} |`);
  lines.push(`| 主城 HP（双方） | **${fmtNum(hp)}** |`);
  lines.push(`| 对局时长上限 | ${dur}s（${fmtTime(dur)}） |`);
  lines.push(`| 模拟场次 | ${summary.n} |`);
  lines.push('');
  lines.push('| 结果 | 数值 |');
  lines.push('|:---|:---|');
  lines.push(`| 玩家胜 | ${summary.playerWins}（${((summary.playerWins / summary.n) * 100).toFixed(0)}%） |`);
  lines.push(`| 敌方胜 | ${summary.enemyWins}（${((summary.enemyWins / summary.n) * 100).toFixed(0)}%） |`);
  lines.push(`| 平局 | ${summary.draws} |`);
  lines.push(`| 胜因 | ${Object.entries(summary.reasonCount).map(([k, v]) => `${k}:${v}`).join(' · ')} |`);
  lines.push(`| 平均剩余时间 | ${summary.avgTimeLeft.toFixed(1)}s |`);
  lines.push(`| 平均对敌方主城伤害 | ${fmtNum(summary.avgCityDmg)} / ${fmtNum(hp)}（${((summary.avgCityDmg / hp) * 100).toFixed(1)}%） |`);
  lines.push('');
  lines.push('**示例战报（末场）：**');
  lines.push(`- 胜负：**${sample.winner}**（${sample.reason}）· 剩余 ${sample.timeLeft}s`);
  lines.push(`- 击杀 ${sample.playerKills}:${sample.enemyKills} · 主城 ${fmtNum(sample.playerCityHp)} / ${fmtNum(sample.enemyCityHp)}`);
  const pSpawns = Object.entries(sample.spawns.player)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([id, n]) => {
      const h = HeroesConfig.getById(id);
      const arch = SkillConfig.HERO_BATTLE[id]?.archetypeLabel || '';
      return `${h?.name || id}（${arch}）×${n}`;
    });
  lines.push(`- 玩家翻出：${pSpawns.join(' · ') || '无'}`);
  lines.push('');
  return lines.join('\n');
}

function main() {
  const args = parseArgs();
  boot();

  const deck = allCombatHeroIds();
  const lines = [];

  if (args.real || args.multi) {
    lines.push('# 翻卡对战模拟（真实主城 HP）\n');
    lines.push('> 合入 `docs/SKILL_SYSTEM.md` 附录 · 技能 v3 · 运行后请执行 `python3 scripts/gen-skill-bond-config.py`\n');
    lines.push(printMainCityHpTables());
    lines.push('\n---\n');
    lines.push(`## 多阶段对战模拟（每场景 ${args.battles} 场）\n`);
    lines.push('说明：双方卡组均为全部战斗英雄；英雄等级=场景等级；AI 并行翻牌+自动战斗。\n');

    const scenarios = args.multi
      ? MULTI_SCENARIOS
      : [{ arenaId: args.arena, level: args.level, label: `${ARENA_NAMES[args.arena]} · L${args.level}` }];

    for (const sc of scenarios) {
      const run = runScenario(sc, args.battles, args.seed, deck);
      lines.push(formatScenarioBlock(run));
    }

    lines.push('---\n');
    lines.push('## 解读要点\n');
    lines.push('- 主城 HP 随场次基准（+5.5%/场）与等级（×1.15^等级）成长，与英雄攻击同步缩放。');
    lines.push('- 真实 HP 下胜因以 **more_kills（击杀多）** 与 **destroy_city（拆城）** 混合；高等级全场翻卡后总伤害可达主城 HP 的 40–65%。');
    lines.push('- 青铜场次时限仅 90s，高等级时易出现「时间耗尽前差一丝拆城」；传奇场次 180s 拆城率更高。');
    lines.push('- 技能 `cityDamagePct` 与羁绊加成会进一步提高拆城比例；建议对城 DPS cap 1.45×。');
  } else {
    lines.push('# 对战模拟附录\n');
    lines.push('> 合入 `docs/SKILL_SYSTEM.md` · 演示 HP=200 · 运行后请执行 `python3 scripts/gen-skill-bond-config.py`\n');
    const results = [];
    for (let i = 0; i < args.battles; i++) {
      results.push(runFullBattle(args.level, makeRng(args.seed + i * 9973), deck));
    }
    const summary = summarizeBattles(results);
    const sample = results[results.length - 1];
    lines.push('| 指标 | 结果 |');
    lines.push('|:---|:---|');
    lines.push(`| 玩家胜 | ${summary.playerWins} |`);
    lines.push(`| 胜因 | ${Object.entries(summary.reasonCount).map(([k, v]) => `${k}:${v}`).join(' · ')} |`);
    lines.push(`| 示例 | ${sample.winner} / 剩余${sample.timeLeft}s / 主城${sample.enemyCityHp} |`);
  }

  const outPath = path.join(ROOT, args.out);
  fs.writeFileSync(outPath, lines.join('\n') + '\n', 'utf8');
  console.log(lines.join('\n'));
  console.log('\n---\nWrote', outPath);
}

main();
