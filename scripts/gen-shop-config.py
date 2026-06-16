#!/usr/bin/env python3
"""Generate shop.json and docs/SHOP_AND_ECONOMY.md"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 品质单价（金币/钻石每卡）— 全店唯一基准
GOLD_PER = {"common": 100, "rare": 50, "epic": 150, "legendary": 400}
DIAMOND_PER = {"common": 1, "rare": 3, "epic": 8, "legendary": 20}

HERO_COUNT = 37
FRAG_PER_HERO = 4565
DECK_SIZE = 8

QUALITY_CN = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}

FACTION_PACK_ORDER = ["human", "beast", "undead", "mechanical"]
FACTION_PACK_PRODUCT_ID = {
    "human": "hero_pack_human",
    "beast": "hero_pack_beast",
    "undead": "hero_pack_undead",
    "mechanical": "hero_pack_mechanical",
}

# 礼包：每周期 3 天刷新，5 次购买；每次领取 3 张指定英雄卡（非兑换池）
GIFT_PACK_REFRESH_DAYS = 3
GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE = 5

GIFT_PACK_CARD_SLOTS = [
    {"slot": 1, "quality": "legendary", "count": 20, "label": "传奇卡牌"},
    {"slot": 2, "quality": "epic", "count": 50, "label": "史诗卡牌"},
    {"slot": 3, "quality": "rare", "count": 100, "label": "稀有卡牌"},
]

# 基础区 · 钻石转盘四档
DIAMOND_WHEEL_TIERS = [
    {
        "tierId": 1,
        "productId": "diamond_wheel_120",
        "name": "钻石×120",
        "label": "一小把",
        "reward": {"type": "diamond", "amount": 120},
        "wheel": {
            "slotCount": 3,
            "adSlotCount": 2,
            "winSlotCount": 1,
            "displayProbability": "1/3",
            "probabilityModel": "scripted",
            "scriptedWinOnSpin": {
                "dailyFirstSessionWinOnSpin": 2,
                "cycle": [2, 3, 4, 3],
                "note": "非真概率；按累计转动次数脚本命中；每日首次会话第2转必中",
            },
        },
        "sortWeight": 40,
    },
    {
        "tierId": 2,
        "productId": "diamond_wheel_280",
        "name": "钻石×280",
        "label": "一袋",
        "reward": {"type": "diamond", "amount": 280},
        "wheel": {
            "slotCount": 4,
            "adSlotCount": 3,
            "winSlotCount": 1,
            "displayProbability": "1/4",
            "probabilityModel": "scripted",
            "scriptedWinOnSpin": {
                "dailyFirstSessionWinOnSpin": 3,
                "cycle": [5, 4],
                "note": "非真概率；每日首次会话第3转必中；之后 5转/4转 循环",
            },
        },
        "sortWeight": 30,
    },
    {
        "tierId": 3,
        "productId": "diamond_wheel_720",
        "name": "钻石×720",
        "label": "一箱",
        "reward": {"type": "diamond", "amount": 720},
        "wheel": {
            "slotCount": 5,
            "adSlotCount": 4,
            "winSlotCount": 1,
            "displayProbability": "1/5",
            "probabilityModel": "pity_loss_streak",
            "pity": {
                "message": "触发连败保底，再转 {withinSpins} 次内必中",
                "useTrueRandomInPityWindow": True,
                "sessions": [
                    {
                        "sessionIndex": 1,
                        "triggerOnSpin": 3,
                        "guaranteedWithinSpins": 2,
                        "note": "首次购买：第3转仍失败则触发，2次内真随机必中",
                    },
                    {
                        "sessionIndex": 2,
                        "triggerOnSpin": 4,
                        "guaranteedWithinSpins": 3,
                        "note": "第二次：第4转触发，3次内真随机必中",
                    },
                ],
                "cycleAfterSession2": {
                    "triggerOnSpinCycle": [3, 4],
                    "guaranteedWithinSpinsCycle": [2, 3],
                    "note": "之后循环：第3转触发保底(2次内必中)、第4转触发保底(3次内必中)",
                },
            },
        },
        "sortWeight": 20,
    },
    {
        "tierId": 4,
        "productId": "diamond_wheel_1680",
        "name": "钻石×1680",
        "label": "巨藏",
        "reward": {"type": "diamond", "amount": 1680},
        "wheel": {
            "slotCount": 7,
            "adSlotCount": 6,
            "winSlotCount": 1,
            "displayProbability": "1/7",
            "probabilityModel": "crit_and_pity",
            "critMechanism": {
                "activateAfterConsecutiveAdFailures": 3,
                "bonusPerAdSlotHit": 100,
                "accumulatesUntilWin": True,
                "adSlotUILabel": "+100钻石",
                "note": "第3次连续看广告仍失败后，看广告格显示+100钻；再转到看广告则奖励累加直至中奖",
            },
            "pity": {
                "guaranteedWithinSpinsMin": 8,
                "guaranteedWithinSpinsMax": 10,
                "useTrueRandomInWindow": True,
                "note": "默认 8～10 转内必中（窗口内真随机）",
            },
        },
        "sortWeight": 10,
    },
]

BRICK_PACK_TIERS = [
    {
        "tierId": 1,
        "productId": "brick_pack_ad_50",
        "name": "砖头×50",
        "reward": {"type": "brick", "amount": 50},
        "purchaseModel": "watch_ad",
        "purchase": {"ad": True, "diamond": None},
        "note": "直接看广告领取",
        "sortWeight": 40,
    },
    {
        "tierId": 2,
        "productId": "brick_pack_100",
        "name": "砖头×100",
        "reward": {"type": "brick", "amount": 100},
        "purchaseModel": "diamond",
        "purchase": {"diamond": 99, "ad": False},
        "note": "99 钻石购买",
        "sortWeight": 30,
    },
    {
        "tierId": 3,
        "productId": "brick_pack_600",
        "name": "砖头×600",
        "reward": {"type": "brick", "amount": 600},
        "purchaseModel": "diamond",
        "purchase": {"diamond": 500, "ad": False},
        "note": "500 钻石购买",
        "sortWeight": 20,
    },
    {
        "tierId": 4,
        "productId": "brick_pack_3000",
        "name": "砖头×3000",
        "reward": {"type": "brick", "amount": 3000},
        "purchaseModel": "diamond",
        "purchase": {"diamond": 2000, "ad": False},
        "note": "2000 钻石购买",
        "sortWeight": 10,
    },
]

BASIC_AD_FLOW = {
    "completionNotGuaranteed": True,
    "onIncompleteReturn": "wheel_page",
    "preserveSpinResult": True,
    "preserveSpinCount": True,
    "preserveCritBonus": True,
    "onAdLoadFail": {
        "stayOnWheel": True,
        "doNotAdvanceSpinCount": True,
    },
    "buttons": {
        "spin": "抽奖",
        "watchAd": "看广告",
        "continueSpin": "继续抽奖",
        "claim": "领取",
    },
}

WHEEL_SLOTS = [
    {
        "slotId": "free",
        "label": "直接免费",
        "displayWeight": 0.25,
        "adsRequired": 0,
        "tierKey": "free",
    },
    {
        "slotId": "ad_1",
        "label": "看1个广告",
        "displayWeight": 0.25,
        "adsRequired": 1,
        "tierKey": "ad_1",
    },
    {
        "slotId": "ad_2",
        "label": "看2个广告",
        "displayWeight": 0.25,
        "adsRequired": 2,
        "tierKey": "ad_2",
    },
    {
        "slotId": "ad_3",
        "label": "看3个广告",
        "displayWeight": 0.25,
        "adsRequired": 3,
        "tierKey": "ad_3",
    },
]


def load_bond_factions() -> dict[str, dict]:
    bond = json.loads((ROOT / "bond.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for b in bond["bonds"]:
        if b.get("type") != "faction":
            continue
        fid = b["faction"]
        out[fid] = {
            "bondId": b["bondId"],
            "name": b["name"],
            "faction": fid,
            "heroIds": list(b["heroIds"]),
        }
    return out


def price_gold(quality: str, count: int) -> int:
    return GOLD_PER[quality] * count


def price_diamond(quality: str, count: int) -> int:
    return DIAMOND_PER[quality] * count


def card_reward(quality: str, count: int) -> dict:
    return {
        "quality": quality,
        "count": count,
        "goldPrice": price_gold(quality, count),
        "diamondPrice": price_diamond(quality, count),
    }


def card_purchase(
    quality: str,
    count: int,
    *,
    allow_gold: bool = True,
    allow_diamond: bool = True,
) -> dict:
    return {
        "gold": price_gold(quality, count) if allow_gold else None,
        "diamond": price_diamond(quality, count) if allow_diamond else None,
    }


def load_hero_qualities() -> dict[str, str]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    const m={};
    for (const h of HeroesConfig.HEROES) if (h.type!=='resource') m[h.id]=h.quality;
    console.log(JSON.stringify(m));
    """
    return json.loads(subprocess.check_output(
        ["node", "-e", script], cwd=ROOT, text=True
    ))


def pick_featured_hero_ids(pool: list[str], qualities: dict[str, str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for q in ("legendary", "epic", "rare"):
        candidates = sorted(h for h in pool if qualities.get(h) == q)
        out[q] = candidates[0] if candidates else None
    return out


def build_pack_contents(pool: list[str], qualities: dict[str, str]) -> dict:
    featured = pick_featured_hero_ids(pool, qualities)
    cards = []
    for slot_def in GIFT_PACK_CARD_SLOTS:
        q = slot_def["quality"]
        hid = featured.get(q)
        cards.append({
            "slot": slot_def["slot"],
            "type": "heroCard",
            "heroId": hid,
            "quality": q,
            "count": slot_def["count"],
            "grantMode": "direct_to_collection",
            "label": f"{slot_def['label']}×{slot_def['count']}",
            "note": "单一名英雄；直接入卡库，可立即升级使用（非兑换、非多角色拆分）",
        })
    return {
        "cardCount": 3,
        "grantMode": "direct_to_collection",
        "grantNote": "共3张卡：传奇×20 + 史诗×50 + 稀有×100，各绑定1名本阵营英雄",
        "cards": cards,
    }


def faction_pack_products(factions: dict[str, dict], qualities: dict[str, str]) -> list[dict]:
    products = []
    for idx, fid in enumerate(FACTION_PACK_ORDER):
        meta = factions[fid]
        pool = meta["heroIds"]
        contents = build_pack_contents(pool, qualities)
        products.append(
            {
                "productId": FACTION_PACK_PRODUCT_ID[fid],
                "name": f"{meta['name']}礼包",
                "faction": fid,
                "factionLabel": meta["name"],
                "bondId": meta["bondId"],
                "heroPool": pool,
                "heroPoolNote": "四礼包角色池互不重叠；每周期刷新3名展示/发放英雄",
                "sortWeight": 100 - idx,
                "refreshCycleDays": GIFT_PACK_REFRESH_DAYS,
                "refreshAt": "04:00",
                "purchaseLimitPerCycle": GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE,
                "purchaseModel": "ad_wheel",
                "contents": contents,
                "displayRefresh": {
                    "onCycleReset": True,
                    "cycleDays": GIFT_PACK_REFRESH_DAYS,
                    "pickFromHeroPool": True,
                    "note": "每3天按本阵营重新抽取1传奇+1史诗+1稀有展示；周期内5次购尽后售罄",
                },
                "soldOut": {
                    "buttonLabel": "售罄",
                    "dimmed": True,
                    "sortToBottom": True,
                    "toast": f"本周期购买已达上限（{GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE}/{GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE}），{GIFT_PACK_REFRESH_DAYS}天后刷新。",
                },
            }
        )
    return products


def basic_zone(daily_slots: list, daily_rotation: list) -> dict:
    return {
        "name": "基础区",
        "tabId": "basic",
        "note": "仅每日优惠、钻石转盘、砖头购买；无通用卡包；IAP 未接入",
        "removedModules": ["universalCardPacks", "iapDiamondRecharge"],
        "purchaseLimitPolicy": "none",
        "dailyDeals": {
            "slotCount": 6,
            "refresh": {
                "adCooldownHours": 2,
                "maxAdRefreshesPerDay": 12,
                "manualRefreshDiamond": 20,
                "manualRefreshLimitPerDay": 6,
            },
            "slots": daily_slots,
            "rotationPool": daily_rotation,
        },
        "diamondWheel": {
            "enabled": True,
            "purchaseModel": "ad_wheel",
            "purchaseLimit": None,
            "note": "四档均走转盘+看广告；非真概率档位见各 tier 配置",
            "sharedAdFlow": BASIC_AD_FLOW,
            "tiers": [
                {
                    **tier,
                    "purchaseLimit": None,
                    "wheel": {
                        **tier["wheel"],
                        "slots": _build_wheel_slots(
                            tier["wheel"]["adSlotCount"],
                            tier["wheel"]["winSlotCount"],
                        ),
                    },
                }
                for tier in DIAMOND_WHEEL_TIERS
            ],
        },
        "brickPacks": {
            "currency": "brick",
            "purchaseLimit": None,
            "note": "四档砖头礼包；无限购",
            "packs": [{**p, "purchaseLimit": None} for p in BRICK_PACK_TIERS],
        },
    }


def _build_wheel_slots(ad_count: int, win_count: int) -> list[dict]:
    total = ad_count + win_count
    slots = []
    for i in range(ad_count):
        slots.append({
            "slotId": f"ad_{i + 1}",
            "type": "watch_ad",
            "label": "看广告",
            "displayWeight": round(1 / total, 4),
        })
    for i in range(win_count):
        slots.append({
            "slotId": f"win_{i + 1}",
            "type": "win",
            "label": "获得钻石",
            "displayWeight": round(1 / total, 4),
        })
    return slots


def gift_pack_zone(factions: dict[str, dict]) -> dict:
    return {
        "name": "礼包",
        "tabId": "giftPacks",
        "enabled": True,
        "note": "仅卡牌礼包；暂不做月卡与神器；IAP 未接入时统一走看广告转盘",
        "removedProducts": ["monthly_card", "artifact_pack_starter", "hero_pack_premium"],
        "purchaseModel": "ad_wheel",
        "refreshCycleDays": GIFT_PACK_REFRESH_DAYS,
        "refreshAt": "04:00",
        "purchaseLimitPerCycle": GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE,
        "listSort": {
            "availableFirst": True,
            "soldOutBottom": True,
            "soldOutDimmed": True,
        },
        "wheelSpin": {
            "ui": {
                "layout": "four_way",
                "pointerStartsCenter": True,
            },
            "slots": WHEEL_SLOTS,
            "spinDisplay": {
                "equalWeightLabel": "四格各 25% 展示概率",
                "note": "展示等概率；实际档位由当日 tierDeck 保底分配",
            },
            "dailyTierDeck": {
                "description": f"每周期每礼包 {GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE} 次购买，预洗牌 5 档",
                "tierKeys": ["free", "ad_1", "ad_2", "ad_3"],
                "guaranteedDistribution": {
                    "free": 1,
                    "ad_1": 2,
                    "ad_2": 1,
                    "ad_3": 1,
                },
                "shuffleOnCycleReset": True,
                "drawFromRemainingOnly": True,
            },
            "adFlow": {
                "completionNotGuaranteed": True,
                "onIncompleteReturn": "wheel_page",
                "preserveSpinResult": True,
                "preserveAdsWatchedProgress": True,
                "onAdLoadFail": {
                    "stayOnWheel": True,
                    "doNotConsumeTier": True,
                    "doNotConsumePurchase": True,
                },
            },
            "buttons": {
                "purchase": "购买",
                "watchAd": "看广告",
                "continueSpin": "继续抽奖",
                "forfeit": "放弃机会",
                "claimFree": "领取",
            },
            "forfeit": {
                "consumesPurchase": True,
                "hintTemplate": "放弃后，本礼包只剩{remainingAfterForfeit}次购买机会",
            },
            "freeTier": {
                "primaryButton": "claimFree",
                "rewardFlow": "common_reward_page",
            },
            "adTier": {
                "primaryButtonBeforePartial": "watchAd",
                "primaryButtonAfterPartial": "continueSpin",
                "secondaryButton": "forfeit",
            },
        },
        "userStateSchema": {
            "scope": "perUserPerPackPerCycle",
            "fields": {
                "cycleKey": "周期标识（每3天刷新）",
                "cycleStartAt": "周期开始时间",
                "purchasesRemaining": f"0-{GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE}",
                "tierDeck": "剩余未抽中的 tierKey 列表",
                "currentSession": "null | { tierKey, spinSlotId, adsRequired, adsWatched }",
                "soldOut": "purchasesRemaining === 0",
                "featuredHeroIds": "本周期3张卡绑定的 heroId（传奇/史诗/稀有各1）",
            },
            "crossCyclePolicy": "进行中的 currentSession 作废，次数与 tierDeck 按新周期重置，featuredHeroIds 重新抽取",
        },
        "products": faction_pack_products(factions, load_hero_qualities()),
    }


def validate_shop(shop: dict) -> list[str]:
    """校验所有卡牌商品价格是否与 pricingReference 一致。"""
    errors: list[str] = []
    ref_g = shop["pricingReference"]["goldPerCard"]
    ref_d = shop["pricingReference"]["diamondPerCard"]

    def check(label: str, quality: str, count: int, purchase: dict, reward: dict) -> None:
        eg = ref_g[quality] * count
        ed = ref_d[quality] * count
        if reward.get("goldPrice") != eg:
            errors.append(f"{label} reward.goldPrice {reward.get('goldPrice')} != {eg}")
        if reward.get("diamondPrice") != ed:
            errors.append(f"{label} reward.diamondPrice {reward.get('diamondPrice')} != {ed}")
        if purchase.get("gold") is not None and purchase["gold"] != eg:
            errors.append(f"{label} purchase.gold {purchase['gold']} != {eg} ({QUALITY_CN[quality]}×{count})")
        if purchase.get("diamond") is not None and purchase["diamond"] != ed:
            errors.append(f"{label} purchase.diamond {purchase['diamond']} != {ed}")

    daily = shop["zones"]["basic"]["dailyDeals"]
    for s in daily["slots"]:
        r = s["reward"]
        if r.get("type") == "diamond":
            continue
        check(f"slot{s['slotId']}", r["quality"], r["count"], s["purchase"], r)

    for s in daily["rotationPool"]:
        r = s["reward"]
        check(s["slotId"], r["quality"], r["count"], s["purchase"], r)

    # 四阵营礼包英雄池互不重叠
    seen: set[str] = set()
    for p in shop["zones"]["giftPacks"]["products"]:
        pool = set(p["heroPool"])
        overlap = seen & pool
        if overlap:
            errors.append(f"{p['productId']} heroPool overlaps: {sorted(overlap)}")
        seen |= pool

    return errors


def gen_shop() -> dict:
    factions = load_bond_factions()

    daily_slots = [
        {
            "slotId": 1,
            "name": "钻石小包",
            "reward": {"type": "diamond", "amount": 29},
            "purchase": {"gold": None, "diamond": 29},
            "ad": {"enabled": True, "note": "看广告免费领取"},
        },
        {
            "slotId": 2,
            "name": "普通卡×30",
            "reward": card_reward("common", 30),
            "purchase": card_purchase("common", 30),
            "ad": {"enabled": False},
        },
        {
            "slotId": 3,
            "name": "普通卡×50",
            "reward": card_reward("common", 50),
            "purchase": card_purchase("common", 50),
            "ad": {"enabled": False},
            "note": "原稿「500金」应为笔误，按100金/张=5000",
        },
        {
            "slotId": 4,
            "name": "稀有卡×15",
            "reward": card_reward("rare", 15),
            "purchase": card_purchase("rare", 15),
            "ad": {"enabled": False},
        },
        {
            "slotId": 5,
            "name": "稀有卡×20",
            "reward": card_reward("rare", 20),
            "purchase": card_purchase("rare", 20),
            "ad": {"enabled": False},
        },
        {
            "slotId": 6,
            "name": "史诗卡×5",
            "reward": card_reward("epic", 5),
            "purchase": card_purchase("epic", 5),
            "ad": {"enabled": True, "note": "看广告领取；金币/钻石价=150×5=750金 / 8×5=40钻"},
        },
    ]

    daily_rotation = [
        {
            "slotId": "R1",
            "name": "传奇卡×2",
            "reward": card_reward("legendary", 2),
            "purchase": card_purchase("legendary", 2, allow_gold=False),
            "ad": {"enabled": True, "cooldownHours": 4, "note": "40钻=20×2；金币档400×2=800（仅钻石购买）"},
        },
        {
            "slotId": "R2",
            "name": "史诗卡×10",
            "reward": card_reward("epic", 10),
            "purchase": card_purchase("epic", 10),
            "ad": {"enabled": False},
        },
        {
            "slotId": "R3",
            "name": "传奇卡×5",
            "reward": card_reward("legendary", 5),
            "purchase": card_purchase("legendary", 5, allow_gold=False),
            "ad": {"enabled": True, "cooldownHours": 6, "note": "100钻=20×5；非750（750为史诗×5）"},
        },
    ]

    return {
        "version": "2.2.0",
        "description": "商店 v2.2：礼包(3天5次·3张指定英雄卡直入库) + 基础(每日优惠/钻石转盘/砖头)",
        "tabs": [
            {"tabId": "giftPacks", "name": "礼包", "enabled": True},
            {"tabId": "basic", "name": "基础", "enabled": True},
            {"tabId": "arena", "name": "竞技场", "enabled": False, "note": "一期不做"},
        ],
        "iapPolicy": {
            "directPurchaseEnabled": False,
            "note": "IAP 未接入；礼包与钻石均走看广告转盘；广告完成不保证 100%",
        },
        "zones": {
            "giftPacks": gift_pack_zone(factions),
            "basic": basic_zone(daily_slots, daily_rotation),
        },
        "pricingReference": {
            "goldPerCard": GOLD_PER,
            "diamondPerCard": DIAMOND_PER,
            "brickPackDiamondPerBrick": {
                "ad_tier": 0,
                "tier2": round(BRICK_PACK_TIERS[1]["purchase"]["diamond"] / BRICK_PACK_TIERS[1]["reward"]["amount"], 3),
                "tier4": round(BRICK_PACK_TIERS[3]["purchase"]["diamond"] / BRICK_PACK_TIERS[3]["reward"]["amount"], 3),
            },
            "formula": "总价 = 单价 × 张数；每日优惠卡牌价格由此推导",
            "examples": {
                "epic5": "史诗×5 = 150×5 = 750金 / 8×5 = 40钻",
                "legendary5": "传奇×5 = 400×5 = 2000金 / 20×5 = 100钻",
            },
            "note": "基础区无通用卡包；钻石四档走转盘；砖头四档无限购",
        },
    }


def estimate_economy(shop: dict) -> dict:
    battle_cards_day = 20 * 10
    battle_month = battle_cards_day * 30
    ad_month_cards = (5 + 20 + 35 * 0.3) * 30
    pack_contents = shop["zones"]["giftPacks"]["products"][0]["contents"]
    cards_per_claim = sum(c["count"] for c in pack_contents["cards"])
    cycles_per_month = 30 / GIFT_PACK_REFRESH_DAYS
    pack_month_max = cards_per_claim * GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE * 4 * cycles_per_month
    diamond_tiers = shop["zones"]["basic"]["diamondWheel"]["tiers"]
    diamond_day_scripted_min = sum(t["reward"]["amount"] for t in diamond_tiers[:2])  # rough low estimate
    deck_frag = FRAG_PER_HERO * DECK_SIZE
    all_heroes_frag = FRAG_PER_HERO * HERO_COUNT

    return {
        "targets": {
            "heroesTotal": HERO_COUNT,
            "fragPerHero": FRAG_PER_HERO,
            "deckSize": DECK_SIZE,
            "allHeroesFrag": all_heroes_frag,
            "coreDeckFrag": deck_frag,
        },
        "factionGiftPack": {
            "packCount": len(shop["zones"]["giftPacks"]["products"]),
            "refreshCycleDays": GIFT_PACK_REFRESH_DAYS,
            "purchasesPerPackPerCycle": GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE,
            "cardsPerClaim": cards_per_claim,
            "heroesPerClaim": pack_contents["cardCount"],
            "grantMode": pack_contents["grantMode"],
            "maxCardsPerCycleAllPacks": cards_per_claim * GIFT_PACK_PURCHASE_LIMIT_PER_CYCLE * 4,
        },
        "monthlyCardsEstimate": {
            "f2p_battleOnly": battle_month,
            "ad_player": battle_month + ad_month_cards,
            "gift_pack_max_grind": pack_month_max,
        },
        "gapAnalysis": {
            "monthsToCoreDeck8F2P": round(deck_frag / battle_month, 1),
            "monthsToCoreDeck8Ad": round(deck_frag / (battle_month + ad_month_cards), 1),
        },
        "diamondWheel": {
            "tierCount": len(diamond_tiers),
            "rewards": [t["reward"]["amount"] for t in diamond_tiers],
        },
    }


def _fmt_price_row(quality: str, count: int, purchase: dict) -> str:
    g = purchase.get("gold")
    d = purchase.get("diamond")
    g_s = str(g) if g is not None else "—"
    d_s = str(d) if d is not None else "—"
    unit_g = GOLD_PER[quality]
    unit_d = DIAMOND_PER[quality]
    return f"| {QUALITY_CN[quality]}×{count} | {unit_g} | {unit_d} | {g_s} | {d_s} |"


def _contents_summary(contents: dict) -> str:
    cards = contents.get("cards") or []
    parts = []
    for c in cards:
        if c["type"] == "heroCard":
            parts.append(f"{c.get('heroId','?')}·{QUALITY_CN[c['quality']]}{c['count']}")
    return " + ".join(parts)


def gen_shop_md(shop: dict, economy: dict) -> str:
    ex = shop["pricingReference"]["examples"]
    gp = shop["zones"]["giftPacks"]
    wheel = gp["wheelSpin"]
    efp = economy["factionGiftPack"]

    lines = [
        "# 商店配置与经济补足分析",
        "",
        "> 配表：`shop.json` v" + shop["version"] + " · 生成：`python3 scripts/gen-shop-config.py`",
        "> 阵营英雄池来源：`bond.json`",
        "",
        "---",
        "",
        "## 目录",
        "",
        "1. [商店页签](#一商店页签)",
        "2. [礼包页 · 四阵营卡牌礼包](#二礼包页--四阵营卡牌礼包)",
        "3. [转盘与广告交互流程](#三转盘与广告交互流程)",
        "4. [周期档位保底分配](#四周期档位保底分配)",
        "5. [用户状态字段](#五用户状态字段)",
        "6. [基础区 · 每日优惠](#六基础区--每日优惠)",
        "7. [基础区 · 钻石转盘四档](#七基础区--钻石转盘四档)",
        "8. [基础区 · 砖头四档](#八基础区--砖头四档)",
        "9. [品质单价基准](#九品质单价基准)",
        "10. [经济补足粗算](#十经济补足粗算)",
        "",
        "---",
        "",
        "## 一、商店页签",
        "",
        "| tabId | 名称 | 状态 | 说明 |",
        "|:---|:---|:---:|:---|",
    ]
    for t in shop["tabs"]:
        status = "✅" if t["enabled"] else "—"
        note = t.get("note", "")
        lines.append(f"| `{t['tabId']}` | {t['name']} | {status} | {note or '—'} |")

    lines += [
        "",
        f"> IAP 直购：**{'开启' if shop['iapPolicy']['directPurchaseEnabled'] else '关闭'}** — {shop['iapPolicy']['note']}",
        "",
        "---",
        "",
        "## 二、礼包页 · 四阵营卡牌礼包",
        "",
        "**范围**：仅卡牌礼包；**不做**月卡、神器。",
        "",
        f"**周期**：每 **{gp.get('refreshCycleDays', 3)}** 天刷新；每礼包 **{gp.get('purchaseLimitPerCycle', 5)}/{gp.get('purchaseLimitPerCycle', 5)}** 次购买机会（每次购买走转盘，逻辑不变）。",
        "",
        f"> {shop['iapPolicy']['note']}",
        "",
        "**单次领取内容**（共 **3 张卡**，各 **1 名英雄**，直接入卡库可升级，**非兑换**）：",
        "",
        "| 槽位 | 品质 | 数量 | 发放方式 |",
        "|:---:|:---|:---:|:---|",
    ]
    sample_cards = gp["products"][0]["contents"]["cards"]
    for c in sample_cards:
        lines.append(
            f"| {c['slot']} | {QUALITY_CN[c['quality']]} | {c['count']} | 指定英雄 `{c['heroId']}` · 直入库 |"
        )

    lines += [
        "",
        f"> {gp['products'][0]['contents']['grantNote']}",
        "",
        "**四礼包角色池互不重叠**（来源 `bond.json`）；每周期从池内各抽 1 名传奇/史诗/稀有展示：",
        "",
        "| 礼包 | productId | 阵营 | 本周期示例（传/史/稀） |",
        "|:---|:---|:---|:---|",
    ]
    for p in gp["products"]:
        ids = [c["heroId"] for c in p["contents"]["cards"]]
        lines.append(
            f"| {p['name']} | `{p['productId']}` | {p['factionLabel']} | {' / '.join(ids)} |"
        )

    lines += [
        "",
        "**列表排序**：有剩余次数在上；本周期 5/5 用尽后售罄置灰沉底。",
        "",
        "**售罄**：按钮「售罄」；点击 Toast「" + gp["products"][0]["soldOut"]["toast"] + "」",
        "",
        f"**周期刷新**：每 {gp.get('refreshCycleDays', 3)} 天（{gp.get('refreshAt', '04:00')}）重新抽取 3 名英雄并重置购买次数。",
        "",
        "---",
        "",
        "## 三、转盘与广告交互流程",
        "",
        "### 3.1 转盘四格（展示各 25%）",
        "",
        "| 格 | slotId | 文案 | 需广告数 |",
        "|:---|:---|:---|:---:|",
    ]
    for s in wheel["slots"]:
        lines.append(f"| — | `{s['slotId']}` | {s['label']} | {s['adsRequired']} |")

    lines += [
        "",
        "### 3.2 主流程",
        "",
        "```",
        "礼包列表 → 点击 [购买]",
        "    → 转盘动画（四格各 25% 展示）",
        "    → 停在某一档",
        "",
        "【直接免费】→ [领取] → 通用奖励页 → 扣 1 次 → 刷新阵营展示",
        "",
        "【看 N 个广告】",
        "    → 主按钮 [看广告]  次按钮 [放弃机会]",
        "    → 次按钮下：放弃后，本礼包只剩 M 次购买机会",
        "    → 点 [看广告] → 播广告（可能未看完返回）",
        "        → 未看完：回转盘页，指针不变，进度保留，仍 [看广告]/[放弃机会]",
        "        → 看完 1 个且 N>1：[继续抽奖] + [放弃机会]",
        "        → 看满 N 个：通用奖励页 → 扣 1 次 → 刷新阵营展示",
        "    → 点 [放弃机会]：扣 1 次，不发奖",
        "",
        "四次用完 → 售罄置灰沉底",
        "本周期 5/5 用尽 → 售罄至下周期刷新",
        "```",
        "",
        "### 3.3 按钮文案（配表）",
        "",
        "| 键 | 文案 |",
        "|:---|:---|",
    ]
    for k, v in wheel["buttons"].items():
        lines.append(f"| `{k}` | {v} |")

    lines += [
        "",
        "### 3.4 异常",
        "",
        "- 广告加载失败：停留转盘，不扣次数、不消耗档位",
        "- 跨日：进行中的 `currentSession` 作废，按新日重置",
        "- 广告完成不保证 100%",
        "",
        "---",
        "",
        "## 四、周期档位保底分配",
        "",
        wheel["dailyTierDeck"]["description"],
        "",
        f"> 每 **{gp.get('refreshCycleDays', 3)}** 天重置一次；非每日。",
        "",
        "| 档位 | 本周期次数 |",
        "|:---|:---:|",
    ]
    for tier, cnt in wheel["dailyTierDeck"]["guaranteedDistribution"].items():
        label = next(s["label"] for s in wheel["slots"] if s["tierKey"] == tier)
        lines.append(f"| {label} | {cnt} |")

    lines += [
        "",
        "> 每次购买从**本周期剩余档位池**抽取；5 次用完后恰好发完 5 档（免费×1 + 看1广告×2 + 看2×1 + 看3×1）。",
        "",
        "---",
        "",
        "## 五、用户状态字段",
        "",
        "| 字段 | 说明 |",
        "|:---|:---|",
    ]
    for k, v in gp["userStateSchema"]["fields"].items():
        lines.append(f"| `{k}` | {v} |")
    lines.append(f"| 跨周期 | {gp['userStateSchema']['crossCyclePolicy']} |")

    lines += [
        "",
        "---",
        "",
        "## 六、基础区 · 每日优惠",
        "",
        "> 基础区已移除**通用卡包**；钻石/砖头**无限购**。",
        "",
        f"广告刷新 CD **{shop['zones']['basic']['dailyDeals']['refresh']['adCooldownHours']}小时**；手动刷新 **20钻**（日限6次）。",
        "",
        "| 格 | 商品 | 金币价 | 钻石价 | 广告 | 验算 |",
        "|:---:|:---|:---:|:---:|:---:|:---|",
    ]
    for s in shop["zones"]["basic"]["dailyDeals"]["slots"]:
        r = s["reward"]
        if r.get("type") == "diamond":
            lines.append(f"| {s['slotId']} | 钻石×{r['amount']} | — | {r['amount']} | ✅ | — |")
        else:
            q, n = r["quality"], r["count"]
            g, d = s["purchase"].get("gold"), s["purchase"].get("diamond")
            ad = "✅" if s["ad"].get("enabled") else "—"
            calc = f"{GOLD_PER[q]}×{n}={GOLD_PER[q]*n}"
            lines.append(f"| {s['slotId']} | {s['name']} | {g} | {d} | {ad} | {calc} |")

    lines += [
        "",
        "### 轮换池",
        "",
        "| 商品 | 金币价 | 钻石价 | 广告 | 验算 |",
        "|:---|:---:|:---:|:---:|:---|",
    ]
    for s in shop["zones"]["basic"]["dailyDeals"]["rotationPool"]:
        r = s["reward"]
        q, n = r["quality"], r["count"]
        g = s["purchase"].get("gold")
        d = s["purchase"].get("diamond")
        ad = "✅" if s["ad"].get("enabled") else "—"
        g_s = str(g) if g is not None else "—"
        calc = f"{GOLD_PER[q]}×{n}={GOLD_PER[q]*n}"
        lines.append(f"| {s['name']} | {g_s} | {d} | {ad} | {calc} |")

    basic = shop["zones"]["basic"]
    dw = basic["diamondWheel"]
    lines += [
        "",
        "---",
        "",
        "## 七、基础区 · 钻石转盘四档",
        "",
        f"> {dw['note']} · **无限购**",
        "",
        "### 7.1 档位一览",
        "",
        "| 档 | productId | 奖励 | 格数 | 展示概率 | 概率模型 |",
        "|:---:|:---|:---:|:---:|:---:|:---|",
    ]
    for t in dw["tiers"]:
        w = t["wheel"]
        lines.append(
            f"| {t['tierId']} | `{t['productId']}` | {t['reward']['amount']}钻 | "
            f"{w['slotCount']} | {w['displayProbability']} | `{w['probabilityModel']}` |"
        )

    lines += [
        "",
        "### 7.2 交互流程（与礼包转盘共用广告回退规则）",
        "",
        "```",
        "点击档位 → 转盘页 → [抽奖]",
        "    → 停在「看广告」→ 播广告（可能未看完返回，指针与计数保留）",
        "    → 停在「获得钻石」→ 通用奖励页入账",
        "广告未看完：回转盘页，主按钮 [看广告] / [继续抽奖]",
        "```",
        "",
        "### 7.3 第一档 · 120 钻（3 格：2 看广告 + 1 获奖）",
        "",
        "- 展示概率：各 **1/3**",
        "- **非真概率**，按累计转动次数脚本命中",
        "- 每日**首次会话**：第 **2** 转必中",
        "- 之后循环：**2 → 3 → 4 → 3** 转命中",
        "",
        "### 7.4 第二档 · 280 钻（4 格：3 看广告 + 1 获奖）",
        "",
        "- 展示概率：各 **1/4**",
        "- **非真概率**",
        "- 每日首次会话：第 **3** 转必中",
        "- 之后循环：**5 → 4** 转命中",
        "",
        "### 7.5 第三档 · 720 钻（5 格：4 看广告 + 1 获奖）",
        "",
        "- 展示概率：各 **1/5**",
        "- **连败保底**（保底窗口内为**真随机**）：",
        "  - **第 1 次**购买：第 3 转仍失败 → 提示「触发连败保底，再转 2 次内必中」",
        "  - **第 2 次**购买：第 4 转触发 → **3 次内必中**",
        "  - **之后循环**：第 3 转触发(2次内必中) ↔ 第 4 转触发(3次内必中)",
        "",
        "### 7.6 第四档 · 1680 钻（7 格：6 看广告 + 1 获奖）",
        "",
        "- 展示概率：各 **1/7**",
        "- **暴击**：第 3 次连续看广告仍失败后，看广告格显示 **「+100钻石」**；",
        "  若再次转到看广告，奖励 **1680→1780→…** 累加直至中奖",
        "- **默认保底**：**8～10 转**内必中（窗口内真随机）",
        "",
        "### 7.7 按钮文案",
        "",
        "| 键 | 文案 |",
        "|:---|:---|",
    ]
    for k, v in dw["sharedAdFlow"]["buttons"].items():
        lines.append(f"| `{k}` | {v} |")

    bp = basic["brickPacks"]
    lines += [
        "",
        "---",
        "",
        "## 八、基础区 · 砖头四档",
        "",
        f"> {bp['note']} · **无限购**",
        "",
        "| 档 | productId | 砖头 | 获取方式 | 消耗 | 钻/砖 |",
        "|:---:|:---|:---:|:---|:---:|:---:|",
    ]
    for p in bp["packs"]:
        amt = p["reward"]["amount"]
        if p["purchaseModel"] == "watch_ad":
            cost = "看广告"
            unit = "—"
        else:
            dia = p["purchase"]["diamond"]
            cost = f"{dia} 钻石"
            unit = str(round(dia / amt, 3))
        lines.append(f"| {p['tierId']} | `{p['productId']}` | {amt} | {cost} | — | {unit} |")

    lines += [
        "",
        "**交互**：",
        "- 第 1 档：点购买 → 看广告 → 领取 50 砖",
        "- 第 2～4 档：点购买 → 扣钻石 → 通用奖励页",
        "",
        "---",
        "",
        "## 九、品质单价基准",
        "",
        "| 品质 | 金币/张 | 钻石/张 |",
        "|:---|:---:|:---:|:---:|",
    ]
    for q in ("common", "rare", "epic", "legendary"):
        lines.append(f"| {QUALITY_CN[q]} | {GOLD_PER[q]} | {DIAMOND_PER[q]} |")

    lines += [
        "",
        f"- {ex['epic5']}（每日优惠第6格）",
        f"- {ex['legendary5']}（轮换池传奇×5）",
        "",
        "---",
        "",
        "## 十、经济补足粗算",
        "",
        f"- 核心8卡满级需碎片：**{economy['targets']['coreDeckFrag']:,}**",
        f"- 单礼包单次领取：**{efp['cardsPerClaim']}** 张（{efp['heroesPerClaim']}英雄：传20+史50+稀100）· **直入库**",
        f"- 四礼包满勤每周期上限：**{efp['maxCardsPerCycleAllPacks']}** 张",
        f"- 钻石转盘四档奖励：**{' / '.join(str(x) for x in economy['diamondWheel']['rewards'])}** 钻",
        "",
        "| 玩家 | 月获卡(粗算) | 核心8卡满级 |",
        "|:---|:---:|:---:|:---:|",
        f"| F2P | ~{economy['monthlyCardsEstimate']['f2p_battleOnly']:,} | ~{economy['gapAnalysis']['monthsToCoreDeck8F2P']}月 |",
        f"| 广告党 | ~{int(economy['monthlyCardsEstimate']['ad_player']):,} | ~{economy['gapAnalysis']['monthsToCoreDeck8Ad']}月 |",
        f"| 礼包满勤(理论) | ~{economy['monthlyCardsEstimate']['gift_pack_max_grind']:,} | — |",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    shop = gen_shop()
    errors = validate_shop(shop)
    if errors:
        raise SystemExit("定价校验失败:\n" + "\n".join(errors))

    economy = estimate_economy(shop)
    shop_path = ROOT / "shop.json"
    shop_path.write_text(json.dumps(shop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {shop_path} (pricing OK)")

    md_path = ROOT / "docs" / "SHOP_AND_ECONOMY.md"
    md_path.write_text(gen_shop_md(shop, economy) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")
