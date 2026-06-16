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

  getGiftPackCards(productId) {
    return this.getGiftPack(productId)?.contents?.cards || [];
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

  giftPackRefreshDays() {
    return this.GIFT_PACKS.refreshCycleDays
      || this.GIFT_PACKS.products?.[0]?.refreshCycleDays
      || 3;
  },

  giftPackPurchaseLimit() {
    return this.GIFT_PACKS.purchaseLimitPerCycle
      || this.GIFT_PACKS.products?.[0]?.purchaseLimitPerCycle
      || 5;
  },

  /** 礼包：周期重置时洗牌档位池（5 档：免费×1 + ad1×2 + ad2×1 + ad3×1） */
  createCycleTierDeck() {
    const dist = this.GIFT_PACKS.wheelSpin?.dailyTierDeck?.guaranteedDistribution || {
      free: 1, ad_1: 2, ad_2: 1, ad_3: 1,
    };
    const deck = [];
    Object.entries(dist).forEach(([key, count]) => {
      for (let i = 0; i < count; i += 1) deck.push(key);
    });
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

  /** 领取礼包：直接入卡库的 3 张英雄卡 */
  buildDirectGrantRewards(productId) {
    return this.getGiftPackCards(productId).map((c) => ({
      heroId: c.heroId,
      quality: c.quality,
      count: c.count,
      grantMode: c.grantMode || 'direct_to_collection',
    }));
  },

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

  getDiamondPityState(tier, state) {
    const pity = tier?.wheel?.pity;
    if (!pity || tier.wheel.probabilityModel !== 'pity_loss_streak') return null;
    const session = state.sessionIndex || 1;
    if (session === 1) return pity.sessions?.[0] || null;
    if (session === 2) return pity.sessions?.[1] || null;
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

  getDiamondCritReward(tier, critStacks = 0) {
    const base = tier?.reward?.amount || 0;
    const bonus = tier?.wheel?.critMechanism?.bonusPerAdSlotHit || 0;
    return base + critStacks * bonus;
  },

  createPackCycleState(productId) {
    const pack = this.getGiftPack(productId);
    const limit = pack?.purchaseLimitPerCycle || this.giftPackPurchaseLimit();
    const cards = pack?.contents?.cards || [];
    return {
      productId,
      cycleKey: null,
      cycleStartAt: null,
      purchasesRemaining: limit,
      tierDeck: this.createCycleTierDeck(),
      currentSession: null,
      soldOut: false,
      featuredHeroIds: cards.map((c) => c.heroId),
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
