/**
 * 商店配表运行时（shop.json）
 */
const ShopConfig = {
  VERSION: '2.0.0',
  TABS: [],
  IAP_POLICY: {},
  GIFT_PACKS: {},
  BASIC: {},
  GIFT_PRODUCTS_BY_ID: {},
  DIAMOND_WHEEL_BY_ID: {},
  BRICK_PACKS_BY_ID: {},

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.TABS = data.tabs || [];
    this.IAP_POLICY = data.iapPolicy || {};
    this.GIFT_PACKS = data.zones?.giftPacks || {};
    this.BASIC = data.zones?.basic || {};
    this.GIFT_PRODUCTS_BY_ID = Object.fromEntries(
      (this.GIFT_PACKS.products || []).map((p) => [p.productId, p]),
    );
    this.DIAMOND_WHEEL_BY_ID = Object.fromEntries(
      (this.BASIC.diamondWheel?.tiers || []).map((t) => [t.productId, t]),
    );
    this.BRICK_PACKS_BY_ID = Object.fromEntries(
      (this.BASIC.brickPacks?.packs || []).map((p) => [p.productId, p]),
    );
  },

  getGiftPack(productId) {
    return this.GIFT_PRODUCTS_BY_ID[productId] || null;
  },

  getDiamondWheelTier(productId) {
    return this.DIAMOND_WHEEL_BY_ID[productId] || null;
  },

  getBrickPack(productId) {
    return this.BRICK_PACKS_BY_ID[productId] || null;
  },

  getGiftWheelConfig() {
    return this.GIFT_PACKS.wheelSpin || null;
  },

  getBasicDiamondWheel() {
    return this.BASIC.diamondWheel || null;
  },

  getBasicAdFlow() {
    return this.BASIC.diamondWheel?.sharedAdFlow || null;
  },

  /** 礼包：每日重置时洗牌档位池（free/ad_1/ad_2/ad_3 各 1） */
  createDailyTierDeck() {
    const keys = this.GIFT_PACKS.wheelSpin?.dailyTierDeck?.tierKeys || [
      'free', 'ad_1', 'ad_2', 'ad_3',
    ];
    const deck = [...keys];
    for (let i = deck.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [deck[i], deck[j]] = [deck[j], deck[i]];
    }
    return deck;
  },

  drawGiftTier(tierDeck) {
    if (!tierDeck?.length) return { tierKey: null, remaining: [] };
    const idx = Math.floor(Math.random() * tierDeck.length);
    const tierKey = tierDeck[idx];
    const remaining = tierDeck.filter((_, i) => i !== idx);
    return { tierKey, remaining };
  },

  getGiftSlotByTierKey(tierKey) {
    return (this.GIFT_PACKS.wheelSpin?.slots || []).find((s) => s.tierKey === tierKey) || null;
  },

  forfeitHint(purchasesRemaining) {
    const tpl = this.GIFT_PACKS.wheelSpin?.forfeit?.hintTemplate
      || '放弃后，本礼包只剩{remainingAfterForfeit}次购买机会';
    const remainingAfterForfeit = Math.max(0, (purchasesRemaining || 0) - 1);
    return tpl.replace('{remainingAfterForfeit}', String(remainingAfterForfeit));
  },

  /**
   * 钻石转盘 · 脚本档位：返回本次会话第 spinIndex 转是否应命中
   * @param {object} tier diamondWheel tier config
   * @param {object} state { spinIndex, sessionIndex, isDailyFirstSession }
   */
  shouldScriptedDiamondWin(tier, state) {
    const wheel = tier?.wheel;
    if (!wheel || wheel.probabilityModel !== 'scripted') return false;
    const scripted = wheel.scriptedWinOnSpin;
    const spin = state.spinIndex || 0;
    if (state.isDailyFirstSession && spin === scripted.dailyFirstSessionWinOnSpin) {
      return true;
    }
    const cycle = scripted.cycle || [];
    if (!cycle.length) return false;
    const cycleIdx = ((state.sessionIndex || 1) - 1) % cycle.length;
    return spin === cycle[cycleIdx];
  },

  /**
   * 钻石转盘 · 第三档连败保底：是否进入保底窗口
   */
  getDiamondPityState(tier, state) {
    const pity = tier?.wheel?.pity;
    if (!pity || tier.wheel.probabilityModel !== 'pity_loss_streak') return null;
    const session = state.sessionIndex || 1;
    if (session === 1) {
      return pity.sessions?.[0] || null;
    }
    if (session === 2) {
      return pity.sessions?.[1] || null;
    }
    const cycle = pity.cycleAfterSession2;
    if (!cycle) return null;
    const idx = (session - 3) % 2;
    return {
      triggerOnSpin: cycle.triggerOnSpinCycle[idx],
      guaranteedWithinSpins: cycle.guaranteedWithinSpinsCycle[idx],
      message: pity.message,
      useTrueRandomInPityWindow: pity.useTrueRandomInPityWindow,
    };
  },

  /**
   * 钻石转盘 · 第四档暴击：当前奖励钻石（含累加）
   */
  getDiamondCritReward(tier, critStacks = 0) {
    const base = tier?.reward?.amount || 0;
    const bonus = tier?.wheel?.critMechanism?.bonusPerAdSlotHit || 0;
    return base + critStacks * bonus;
  },

  createPackDailyState(productId) {
    const pack = this.getGiftPack(productId);
    const limit = pack?.dailyPurchaseLimit || 4;
    return {
      productId,
      dateKey: null,
      purchasesRemaining: limit,
      tierDeck: this.createDailyTierDeck(),
      currentSession: null,
      soldOut: false,
      displayLegendaryHeroId: null,
      displayHeroIds: [],
    };
  },

  createDiamondWheelSession(productId) {
    return {
      productId,
      spinIndex: 0,
      sessionIndex: 1,
      isDailyFirstSession: true,
      pityActive: false,
      pitySpinsRemaining: 0,
      critStacks: 0,
      currentReward: this.getDiamondWheelTier(productId)?.reward?.amount || 0,
    };
  },
};

if (typeof module !== 'undefined') module.exports = { ShopConfig };
