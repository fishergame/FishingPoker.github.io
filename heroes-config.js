/**
 * 英雄卡牌配置表（39 张）
 * 字段：id, name, avatar, quality, starter, level, power, buildingHp,
 *       attack, unitHp, attackSpeed, attackRange, income, type
 *
 * 战斗属性 v3（详见 heroBattle.json → combatStats）：
 * - attackSpeed（本表遗留字段）≈ 发射频率 fireRate；弹道速度见 heroBattle.json
 * - attackRange：仅表现距离，不参与远近战判定
 * - 英雄 30 级：attack/unitHp ×1.15/级；fireRate ×1.02/级；弹道速度 ×1.03/级
 */
const HeroesConfig = {
  DECK_SIZE: 8,
  MAX_ATTACK_SPEED: 10,
  DEFAULT_LEVEL: 1,

  QUALITY: {
    common: { label: '普通', color: '#4caf50', border: '#66bb6a' },
    rare: { label: '稀有', color: '#42a5f5', border: '#64b5f6' },
    epic: { label: '史诗', color: '#ab47bc', border: '#ba68c8' },
    legendary: { label: '传奇', color: '#ffb300', border: '#ffc107' },
  },

  DEFAULT_DECK: [
    'dragon_knight',
    'archer',
    'infantry',
    'arrow_tower',
    'bear_warrior',
    'skeleton_warrior',
    'gold_mine',
    null,
  ],

  HEROES: [
    // ===== 传奇 =====
    { id: 'dragon_knight', name: '龙焰女王', avatar: '🐉', quality: 'legendary', starter: true, level: 1, type: 'unit', power: 1983, buildingHp: 560, attack: 88, unitHp: 950, attackSpeed: 2.8, attackRange: 2 },
    { id: 'demon_lord', name: '永冬之王', avatar: '👹', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 793, buildingHp: 300, attack: 70, unitHp: 700, attackSpeed: 2.0, attackRange: 4 },
    { id: 'archmage', name: '风暴女巫', avatar: '🧙', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1081, buildingHp: 500, attack: 100, unitHp: 800, attackSpeed: 1.0, attackRange: 4 },
    { id: 'ranger', name: '荆棘女王', avatar: '🏹', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 349, buildingHp: 200, attack: 50, unitHp: 160, attackSpeed: 2.6, attackRange: 8 },
    { id: 'royal_knight', name: '圣盾领主', avatar: '🛡', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 853, buildingHp: 300, attack: 70, unitHp: 800, attackSpeed: 1.8, attackRange: 2 },
    { id: 'druid', name: '北境守护者', avatar: '🌿', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 889, buildingHp: 400, attack: 70, unitHp: 700, attackSpeed: 1.5, attackRange: 3 },
    { id: 'lich_queen', name: '幽灵船长', avatar: '👻', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 985, buildingHp: 400, attack: 70, unitHp: 860, attackSpeed: 1.4, attackRange: 5 },
    { id: 'blademaster', name: '幻影刺客', avatar: '⚔', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1237, buildingHp: 500, attack: 150, unitHp: 960, attackSpeed: 2.4, attackRange: 1.3 },
    { id: 'frost_dragon', name: '寒冰巨魔', avatar: '❄', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1387, buildingHp: 500, attack: 70, unitHp: 1040, attackSpeed: 1.2, attackRange: 5 },
    { id: 'crusher', name: '重装破城者', avatar: '🔨', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1525, buildingHp: 400, attack: 200, unitHp: 1500, attackSpeed: 0.8, attackRange: 1.3 },
    { id: 'helicopter', name: '机械飞鹰', avatar: '🚁', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 937, buildingHp: 400, attack: 110, unitHp: 700, attackSpeed: 1.6, attackRange: 5 },
    { id: 'dread_knight', name: '巨斧酋长', avatar: '💀', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1129, buildingHp: 500, attack: 90, unitHp: 900, attackSpeed: 2.5, attackRange: 2 },
    { id: 'warlord', name: '双头奇美拉', avatar: '🦁', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1249, buildingHp: 500, attack: 120, unitHp: 1040, attackSpeed: 1.3, attackRange: 1.5 },
    { id: 'panda_monk', name: '爆破鬼才', avatar: '🐼', quality: 'legendary', starter: false, level: 1, type: 'unit', power: 1153, buildingHp: 400, attack: 160, unitHp: 960, attackSpeed: 1.4, attackRange: 1.3 },
    { id: 'sky_dome', name: '天穹', avatar: '🔮', quality: 'legendary', starter: false, level: 1, type: 'building', power: 680, buildingHp: 480, attack: 65, unitHp: null, attackSpeed: 0.6, attackRange: null },

    // ===== 史诗 =====
    { id: 'shaman', name: '藤蔓萨满', avatar: '🪬', quality: 'epic', starter: false, level: 1, type: 'unit', power: 158, buildingHp: 360, attack: 58, unitHp: 96, attackSpeed: 1.2, attackRange: 3.5 },
    { id: 'gargoyle', name: '鹰女', avatar: '🦅', quality: 'epic', starter: false, level: 1, type: 'unit', power: 181, buildingHp: 300, attack: 60, unitHp: 300, attackSpeed: 1.5, attackRange: 1.3 },
    { id: 'skeleton_giant', name: '巨石魔像', avatar: '🗿', quality: 'epic', starter: false, level: 1, type: 'unit', power: 201, buildingHp: 300, attack: 60, unitHp: 400, attackSpeed: 0.6, attackRange: 2 },
    { id: 'sniper', name: '雇佣兵', avatar: '🎯', quality: 'epic', starter: false, level: 1, type: 'unit', power: 145, buildingHp: 300, attack: 60, unitHp: 120, attackSpeed: 1.0, attackRange: 9 },
    { id: 'catapult_tower', name: '炮楼', avatar: '🏯', quality: 'epic', starter: false, level: 1, type: 'building', power: 156, buildingHp: 200, attack: 100, unitHp: null, attackSpeed: 0.7, attackRange: null },
    { id: 'catapult', name: '自爆蜘蛛', avatar: '🕷', quality: 'epic', starter: false, level: 1, type: 'unit', power: 353, buildingHp: 550, attack: 200, unitHp: 480, attackSpeed: 0.5, attackRange: 8 },
    { id: 'cavalry', name: '龙骑士', avatar: '🐎', quality: 'epic', starter: false, level: 1, type: 'unit', power: 177, buildingHp: 300, attack: 50, unitHp: 300, attackSpeed: 1.9, attackRange: 2 },
    { id: 'wyrmling', name: '火龙', avatar: '🔥', quality: 'epic', starter: false, level: 1, type: 'unit', power: 548, buildingHp: 460, attack: 68, unitHp: 430, attackSpeed: 1.8, attackRange: 5 },
    { id: 'ballista', name: '弩车', avatar: '🏹', quality: 'epic', starter: false, level: 1, type: 'unit', power: 253, buildingHp: 550, attack: 90, unitHp: 200, attackSpeed: 0.5, attackRange: 6 },

    // ===== 稀有 =====
    { id: 'necromancer', name: '骷髅魔导师', avatar: '💜', quality: 'rare', starter: false, level: 1, type: 'unit', power: 93, buildingHp: 200, attack: 30, unitHp: 80, attackSpeed: 1.1, attackRange: 4.5 },
    { id: 'spear_orc', name: '鱼叉捕猎者', avatar: '🗡', quality: 'rare', starter: false, level: 1, type: 'unit', power: 101, buildingHp: 200, attack: 30, unitHp: 120, attackSpeed: 1.2, attackRange: 5 },
    { id: 'wolf_rider', name: '利爪猎犬', avatar: '🐺', quality: 'rare', starter: false, level: 1, type: 'unit', power: 161, buildingHp: 300, attack: 40, unitHp: 240, attackSpeed: 1.9, attackRange: 1 },
    { id: 'skeleton_knight', name: '蝙蝠突袭者', avatar: '🦇', quality: 'rare', starter: false, level: 1, type: 'unit', power: 125, buildingHp: 260, attack: 38, unitHp: 130, attackSpeed: 1.4, attackRange: 1 },
    { id: 'archer', name: '见习女巫', avatar: '🏹', quality: 'rare', starter: true, level: 1, type: 'unit', power: 166, buildingHp: 260, attack: 33, unitHp: 110, attackSpeed: 1.0, attackRange: 5 },
    { id: 'infantry', name: '重步兵', avatar: '⚔', quality: 'rare', starter: true, level: 1, type: 'unit', power: 256, buildingHp: 360, attack: 3, unitHp: 250, attackSpeed: 0.9, attackRange: 1 },
    { id: 'arrow_tower', name: '高射塔', avatar: '🗼', quality: 'rare', starter: true, level: 1, type: 'building', power: 277, buildingHp: 380, attack: 80, unitHp: null, attackSpeed: 0.8, attackRange: null },
    { id: 'heavy_shield', name: '重型盾', avatar: '🛡️', quality: 'rare', starter: false, level: 1, type: 'building', power: 220, buildingHp: 420, attack: 45, unitHp: null, attackSpeed: 0.7, attackRange: null },

    // ===== 普通 =====
    { id: 'bear_warrior', name: '重锤卫士', avatar: '🐻', quality: 'common', starter: true, level: 1, type: 'unit', power: 206, buildingHp: 260, attack: 53, unitHp: 210, attackSpeed: 1.0, attackRange: 1 },
    { id: 'skeleton_warrior', name: '骷髅刀盾兵', avatar: '💀', quality: 'common', starter: true, level: 1, type: 'unit', power: 119, buildingHp: 220, attack: 24, unitHp: 92, attackSpeed: 1.2, attackRange: 1 },
    { id: 'goblin', name: '小野猪人', avatar: '👺', quality: 'common', starter: false, level: 1, type: 'unit', power: 57, buildingHp: 100, attack: 20, unitHp: 80, attackSpeed: 1.3, attackRange: 1 },
    { id: 'blacksmith', name: '长枪教头', avatar: '🔧', quality: 'common', starter: false, level: 1, type: 'unit', power: 83, buildingHp: 100, attack: 25, unitHp: 200, attackSpeed: 0.9, attackRange: 1 },
    { id: 'militia', name: '短剑士', avatar: '🗡', quality: 'common', starter: false, level: 1, type: 'unit', power: 65, buildingHp: 100, attack: 30, unitHp: 100, attackSpeed: 1.1, attackRange: 1.2 },
    { id: 'bone_archer', name: '火枪手', avatar: '🔫', quality: 'common', starter: false, level: 1, type: 'unit', power: 57, buildingHp: 100, attack: 20, unitHp: 80, attackSpeed: 1.0, attackRange: 5 },
    { id: 'gold_mine', name: '采矿机', avatar: '⛏', quality: 'common', starter: true, level: 1, type: 'resource', power: null, buildingHp: 200, attack: null, unitHp: null, attackSpeed: null, attackRange: null, income: 10 },
  ],

  getById(id) {
    return this.HEROES.find((h) => h.id === id) || null;
  },

  getMap() {
    const map = {};
    for (const h of this.HEROES) map[h.id] = h;
    return map;
  },

  /** 攻速 → 攻击间隔（秒），攻速越高出手越快 */
  attackInterval(attackSpeed) {
    if (attackSpeed == null || attackSpeed <= 0) return null;
    const clamped = Math.min(attackSpeed, this.MAX_ATTACK_SPEED);
    return 2.2 / clamped;
  },
};
