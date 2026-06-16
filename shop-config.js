/**
 * 商店配表运行时（shop.json）
 */
const ShopConfig = {
  VERSION: '2.0.0',
  TABS: [],
  IAP_POLICY: {},
  GIFT_PACKS: {},
  BASIC: {},
  PRODUCTS_BY_ID: {},

  hydrateFromJson(data) {
    this.VERSION = data.version;
    this.TABS = data.tabs || [];
    this.IAP_POLICY = data.iapPolicy || {};
    this.GIFT_PACKS = data.zones?.giftPacks || {};
    this.BASIC = data.zones?.basic || {};
    this.PRODUCTS_BY_ID = Object.fromEntries(
      (this.GIFT_PACKS.products || []).map((p) => [p.productId, p]),
    );
  },

  getGiftPack(productId) {
    return this.PRODUCTS_BY_ID[productId] || null;
  },

  getWheelConfig() {
    return this.GIFT_PACKS.wheelSpin || null;
  },

  /** 每日重置时洗牌档位池（free/ad_1/ad_2/ad_3 各 1） */
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

  /** 从剩余档位池抽一档并移除 */
  drawTier(tierDeck) {
    if (!tierDeck?.length) return { tierKey: null, remaining: [] };
    const idx = Math.floor(Math.random() * tierDeck.length);
    const tierKey = tierDeck[idx];
    const remaining = tierDeck.filter((_, i) => i !== idx);
    return { tierKey, remaining };
  },

  getSlotByTierKey(tierKey) {
    return (this.GIFT_PACKS.wheelSpin?.slots || []).find((s) => s.tierKey === tierKey) || null;
  },

  forfeitHint(purchasesRemaining) {
    const tpl = this.GIFT_PACKS.wheelSpin?.forfeit?.hintTemplate
      || '放弃后，本礼包只剩{remainingAfterForfeit}次购买机会';
    const remainingAfterForfeit = Math.max(0, (purchasesRemaining || 0) - 1);
    return tpl.replace('{remainingAfterForfeit}', String(remainingAfterForfeit));
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
};

if (typeof module !== 'undefined') module.exports = { ShopConfig };
