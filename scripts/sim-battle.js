#!/usr/bin/env node
/**
 * 全英雄技能一览 + 翻卡对战模拟
 * 用法：node scripts/sim-battle.js [--battles=50] [--level=20]
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

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
  loadGlobal('BattleSkillRuntime', 'battle-skill-runtime.js');
  loadGlobal('SkillConfig', 'skill-config.js');
  loadGlobal('BattleRules', 'battle-rules.js');

  SkillConfig.hydrateFromJson(
    JSON.parse(fs.readFileSync(path.join(ROOT, 'skill.json'), 'utf8')),
    JSON.parse(fs.readFileSync(path.join(ROOT, 'heroBattle.json'), 'utf8')),
  );
}

function parseArgs() {
  const args = { battles: 40, level: 20, seed: 42 };
  for (const a of process.argv.slice(2)) {
    if (a.startsWith('--battles=')) args.battles = Number(a.split('=')[1]);
    if (a.startsWith('--level=')) args.level = Number(a.split('=')[1]);
    if (a.startsWith('--seed=')) args.seed = Number(a.split('=')[1]);
  }
  return args;
}

/** 简易可复现随机 */
function makeRng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0x100000000;
  };
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

function printHeroRoster() {
  const lines = [];
  lines.push('## 全英雄技能一览（37 张）\n');
  lines.push('| 英雄 | 品质 | 定位 | 近/远 | 普通(L1) | 史诗(L8) | 传奇(L20) |');
  lines.push('|:---|:---|:---|:---|:---|:---|:---|');

  const sorted = [...HeroesConfig.HEROES].sort((a, b) => {
    const qo = { legendary: 0, epic: 1, rare: 2, common: 3 };
    return (qo[a.quality] ?? 9) - (qo[b.quality] ?? 9) || a.name.localeCompare(b.name, 'zh');
  });

  for (const h of sorted) {
    const meta = SkillConfig.HERO_BATTLE[h.id] || {};
    const sk = (slot) => {
      const id = meta.skills?.[slot];
      const s = id ? SkillConfig.SKILLS[id] : null;
      return s ? s.name.replace(`${h.name}·`, '') + '：' + s.description : '—';
    };
    const range = meta.range === 'melee' ? '近战' : meta.range === 'ranged' ? '远程' : '—';
    const arch = meta.archetypeLabel || '—';
    const qLabel = HeroesConfig.QUALITY[h.quality]?.label || h.quality;
    lines.push(
      `| ${h.name} | ${qLabel} | ${arch} | ${range} | ${sk('normal')} | ${sk('epic')} | ${sk('legend')} |`,
    );
  }
  return lines.join('\n');
}

function spawnHeroInCell(state, side, row, col, heroId, level, flipCost = 20) {
  const key = BattleRules.cellKey(side, row, col);
  const cell = state.cells[key];
  if (!cell) return null;
  const hero = BattleSkillRuntime.buildCombatHero(heroId, {
    heroLevel: level,
    flipCost,
    side,
  });
  cell.revealed = true;
  cell.contentType = 'hero';
  cell.hero = hero;
  cell.flipPreview = null;
  return hero;
}

/** 单挑：攻击方 vs 标准守门靶子，测清场效率 */
function duelVsGuard(attackerId, level) {
  const state = BattleRules.createInitialState();
  spawnHeroInCell(state, 'player', 3, 3, attackerId, level);
  spawnHeroInCell(state, 'enemy', 2, 3, 'bear_warrior', level);

  const maxSec = 90;
  let t = 0;
  let killSec = null;
  while (t < maxSec) {
    BattleRules.tickCombat(state, 0.1);
    t += 0.1;
    const enemyCell = state.cells[BattleRules.cellKey('enemy', 2, 3)];
    if (!enemyCell?.hero || enemyCell.hero.hp <= 0) {
      killSec = Math.round(t * 10) / 10;
      break;
    }
  }

  const atk = state.cells[BattleRules.cellKey('player', 3, 3)]?.hero;
  return {
    killSec,
    attackerHpPct: atk ? Math.round((atk.hp / atk.maxHp) * 100) : 0,
    attackerAtk: atk?.atk ?? 0,
  };
}

/** 攻城：清场后 solo 拆主城 10 秒 DPS */
function siegeBurst(heroId, level, cityHp = 5000) {
  const state = BattleRules.createInitialState();
  state.enemyCityHp = cityHp;
  state.enemyCityMaxHp = cityHp;
  spawnHeroInCell(state, 'player', 3, 4, heroId, level);

  let dealt = 0;
  for (let i = 0; i < 100; i++) {
    const before = state.enemyCityHp;
    BattleRules.tickCombat(state, 0.1);
    dealt += before - state.enemyCityHp;
  }
  return {
    cityDmg10s: dealt,
    dps: Math.round(dealt / 10),
    hasCityMod: (state.cells[BattleRules.cellKey('player', 3, 4)]?.hero?.combatMods?.cityDamagePct || 0) > 0,
  };
}

function runFullBattle(level, rng, deck) {
  BattleRules.configure({
    playerDeck: deck,
    enemyDeck: deck,
    heroLevels: heroLevelsMap(level),
  });

  const realRandom = Math.random;
  Math.random = rng;

  const state = BattleRules.createInitialState();
  let goldAcc = 0;
  const dt = 0.1;
  const maxSec = BattleConfig.MATCH_DURATION_SEC + 5;
  let t = 0;

  const spawns = { player: {}, enemy: {} };

  while (t < maxSec && !state.gameOver) {
    BattleRules.tickTimer(state, dt);
    goldAcc = BattleRules.tickGold(state, dt, goldAcc);
    BattleRules.tickEnemyAi(state, dt);

    if (rng() < 0.35) {
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

  return {
    winner: state.result?.winner || 'draw',
    reason: state.result?.reason || 'timeout',
    timeLeft: Math.round(state.timeLeft),
    playerKills: state.playerKills,
    enemyKills: state.enemyKills,
    playerCityHp: state.playerCityHp,
    enemyCityHp: state.enemyCityHp,
    spawns,
  };
}

function archetypeDuelSummary(level) {
  const byArch = { clear: [], guard: [], siege: [], tempo: [] };
  for (const h of HeroesConfig.HEROES) {
    if (h.type === 'resource') continue;
    const arch = SkillConfig.HERO_BATTLE[h.id]?.archetype;
    if (!arch) continue;
    const duel = duelVsGuard(h.id, level);
    const siege = siegeBurst(h.id, level);
    byArch[arch].push({
      name: h.name,
      killSec: duel.killSec,
      atk: duel.attackerAtk,
      siegeDps: siege.dps,
    });
  }

  const lines = [];
  lines.push('## 定位单挑/攻城抽样（vs 重锤卫士 L' + level + '，主城5000HP清场后10s）\n');
  for (const [arch, label] of [
    ['clear', '清场'],
    ['guard', '守门'],
    ['siege', '破城'],
    ['tempo', '节奏'],
  ]) {
    const list = byArch[arch].sort((a, b) => (a.killSec ?? 99) - (b.killSec ?? 99));
    const avgKill =
      list.filter((x) => x.killSec != null).reduce((s, x) => s + x.killSec, 0) /
      Math.max(1, list.filter((x) => x.killSec != null).length);
    const avgSiege = list.reduce((s, x) => s + x.siegeDps, 0) / list.length;
    lines.push(`### ${label}（${list.length} 张）`);
    lines.push(`- 平均击杀用时：**${avgKill.toFixed(1)}s** · 平均攻城 DPS：**${Math.round(avgSiege)}**`);
    lines.push('');
    lines.push('| 英雄 | 击杀(s) | 攻击 | 攻城DPS/10s |');
    lines.push('|:---|:---|:---|:---|');
    for (const row of list) {
      lines.push(
        `| ${row.name} | ${row.killSec ?? '未击杀'} | ${row.atk} | ${row.siegeDps} |`,
      );
    }
    lines.push('');
  }
  return lines.join('\n');
}

function main() {
  const args = parseArgs();
  boot();

  const deck = allCombatHeroIds();
  const roster = printHeroRoster();
  const duel = archetypeDuelSummary(args.level);

  const results = [];
  let playerWins = 0;
  let enemyWins = 0;
  let draws = 0;
  const reasonCount = {};
  const archKills = { clear: 0, guard: 0, siege: 0, tempo: 0 };

  for (let i = 0; i < args.battles; i++) {
    const rng = makeRng(args.seed + i * 9973);
    const r = runFullBattle(args.level, rng, deck);
    results.push(r);
    if (r.winner === 'player') playerWins++;
    else if (r.winner === 'enemy') enemyWins++;
    else draws++;
    reasonCount[r.reason] = (reasonCount[r.reason] || 0) + 1;
  }

  // 用最后一场作为「示例战报」
  const sample = results[results.length - 1];

  const lines = [];
  lines.push('# 全英雄技能 + 模拟对战报告\n');
  lines.push(`> 生成时间：模拟脚本 · 英雄等级 L${args.level} · ${args.battles} 场自动对战\n`);
  lines.push(roster);
  lines.push('\n---\n');
  lines.push(duel);
  lines.push('---\n');
  lines.push(`## 自动对战汇总（${args.battles} 场，双方卡组=全部战斗英雄 ${deck.length} 张）\n`);
  lines.push('| 指标 | 结果 |');
  lines.push('|:---|:---|');
  lines.push(`| 玩家胜 | ${playerWins}（${((playerWins / args.battles) * 100).toFixed(0)}%） |`);
  lines.push(`| 敌方胜 | ${enemyWins}（${((enemyWins / args.battles) * 100).toFixed(0)}%） |`);
  lines.push(`| 平局 | ${draws} |`);
  lines.push(`| 胜因分布 | ${Object.entries(reasonCount).map(([k, v]) => `${k}:${v}`).join(' · ')} |`);
  lines.push('');
  lines.push('### 示例战报（最后一场）\n');
  lines.push('| 项目 | 数值 |');
  lines.push('|:---|:---|');
  lines.push(`| 胜负 | **${sample.winner}**（${sample.reason}） |`);
  lines.push(`| 剩余时间 | ${sample.timeLeft}s |`);
  lines.push(`| 击杀 | 玩家 ${sample.playerKills} : ${sample.enemyKills} 敌方 |`);
  lines.push(`| 主城HP | 玩家 ${sample.playerCityHp} / 敌方 ${sample.enemyCityHp} |`);
  lines.push('');
  lines.push('**玩家本局翻出英雄（次数）：**');
  const pSpawns = Object.entries(sample.spawns.player).sort((a, b) => b[1] - a[1]);
  lines.push(pSpawns.map(([id, n]) => {
    const h = HeroesConfig.getById(id);
    const arch = SkillConfig.HERO_BATTLE[id]?.archetypeLabel || '';
    return `${h?.name || id}（${arch}）×${n}`;
  }).join(' · ') || '无');
  lines.push('');
  lines.push('**定位局内出场（全场翻卡统计）：**');
  lines.push('');
  lines.push('| 定位 | 出场次数 | 占比 |');
  lines.push('|:---|:---|:---|');

  const archSpawn = { clear: 0, guard: 0, siege: 0, tempo: 0 };
  for (const r of results) {
    for (const side of ['player', 'enemy']) {
      for (const [hid, cnt] of Object.entries(r.spawns[side] || {})) {
        const a = SkillConfig.HERO_BATTLE[hid]?.archetype;
        if (a) archSpawn[a] = (archSpawn[a] || 0) + cnt;
      }
    }
  }
  const totalSpawn = Object.values(archSpawn).reduce((a, b) => a + b, 0);
  for (const [k, label] of [['clear', '清场'], ['guard', '守门'], ['siege', '破城'], ['tempo', '节奏']]) {
    lines.push(`| ${label} | ${archSpawn[k]} | ${((archSpawn[k] / totalSpawn) * 100).toFixed(1)}% |`);
  }

  const out = lines.join('\n');
  const outPath = path.join(ROOT, 'docs', 'SKILL_BATTLE_SIM_REPORT.md');
  fs.writeFileSync(outPath, out + '\n', 'utf8');

  console.log(out);
  console.log('\n---\nWrote', outPath);
}

main();
