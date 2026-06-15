#!/usr/bin/env python3
"""Generate shop.json and docs/SHOP_AND_ECONOMY.md"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 品质单价（金币/钻石每卡）— 全店唯一基准
GOLD_PER = {"common": 100, "rare": 50, "epic": 150, "legendary": 400}
DIAMOND_PER = {"common": 1, "rare": 3, "epic": 8, "legendary": 20}

HERO_COUNT = 37
FRAG_PER_HERO = 4565
DECK_SIZE = 8

QUALITY_CN = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}


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

    return errors


def gen_shop() -> dict:
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

    universal_packs = [
        {
            "productId": "universal_rare_30",
            "name": "稀有通用卡×30",
            "quality": "rare",
            "count": 30,
            "priceCny": 18,
            "dailyLimit": 4,
            "exchangeRule": "兑换为指定英雄稀有卡/碎片",
        },
        {
            "productId": "universal_epic_30",
            "name": "史诗通用卡×30",
            "quality": "epic",
            "count": 30,
            "priceCny": 18,
            "dailyLimit": 4,
            "exchangeRule": "兑换为指定英雄史诗卡/碎片",
        },
        {
            "productId": "universal_legendary_30",
            "name": "传奇通用卡×30",
            "quality": "legendary",
            "count": 30,
            "priceCny": 18,
            "dailyLimit": 4,
            "exchangeRule": "兑换为指定英雄传奇卡/碎片",
        },
    ]

    diamond_tiers = [
        {"tierId": 1, "priceCny": 6, "diamond": 60, "bonus": 0, "label": "一小把"},
        {"tierId": 2, "priceCny": 12, "diamond": 130, "bonus": 10, "label": "一袋"},
        {"tierId": 3, "priceCny": 30, "diamond": 330, "bonus": 30, "label": "一箱"},
        {"tierId": 4, "priceCny": 68, "diamond": 750, "bonus": 90, "label": "一大箱"},
        {"tierId": 5, "priceCny": 128, "diamond": 1580, "bonus": 220, "label": "宝库"},
        {"tierId": 6, "priceCny": 328, "diamond": 4280, "bonus": 780, "label": "巨藏"},
    ]

    return {
        "version": "1.1.0",
        "description": "商店：角色区(直购) + 基础区(每日优惠/通用卡/钻石)；价格由品质单价推导",
        "zones": {
            "character": {
                "name": "角色区",
                "products": [
                    {
                        "productId": "monthly_card",
                        "name": "月卡",
                        "priceCny": 30,
                        "durationDays": 30,
                        "firstBuyBonus": {"diamond": 300},
                        "dailyClaim": {"diamond": 30},
                        "privileges": ["skipAdForDailyRewards", "monthlyCardBadge"],
                        "renewable": True,
                        "note": "30天累计约1200钻+首购300",
                    },
                    {
                        "productId": "artifact_pack_starter",
                        "name": "神器礼包·启程",
                        "priceCny": 30,
                        "contents": [
                            {"type": "artifactCard", "quality": "epic", "count": 1},
                            {"type": "diamond", "amount": 200},
                        ],
                        "weeklyLimit": 1,
                    },
                    {
                        "productId": "hero_pack_premium",
                        "name": "角色礼包",
                        "priceCny": 68,
                        "contents": [
                            {"type": "heroCard", "quality": "legendary", "count": 20},
                            {"type": "heroCard", "quality": "epic", "count": 50},
                            {"type": "heroCard", "quality": "rare", "count": 100},
                        ],
                        "weeklyLimit": 2,
                        "note": "可指定目标英雄兑换",
                    },
                ],
            },
            "basic": {
                "name": "基础区",
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
                "universalCardPacks": {
                    "dailyLimitPerSku": 4,
                    "dailyRefreshAt": "04:00",
                    "maxCardsPerQualityPerDay": 120,
                    "packs": universal_packs,
                },
                "diamondRecharge": diamond_tiers,
            },
        },
        "pricingReference": {
            "goldPerCard": GOLD_PER,
            "diamondPerCard": DIAMOND_PER,
            "formula": "总价 = 单价 × 张数；所有每日优惠由此推导",
            "examples": {
                "epic5": "史诗×5 = 150×5 = 750金 / 8×5 = 40钻",
                "legendary5": "传奇×5 = 400×5 = 2000金 / 20×5 = 100钻",
            },
            "note": "每日优惠可用金币或钻石；传奇轮换位默认仅钻石购买；通用卡仅人民币直购",
        },
    }


def estimate_economy(shop: dict) -> dict:
    battle_cards_day = 20 * 10
    battle_month = battle_cards_day * 30
    ad_month_cards = (5 + 20 + 35 * 0.3) * 30  # 史诗广告+稀有+传奇轮换期望
    small_rare_month = 30 * 30
    pack = shop["zones"]["character"]["products"][2]["contents"]
    pack_month = sum(c["count"] for c in pack) * 4
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
        "monthlyCardsEstimate": {
            "f2p_battleOnly": battle_month,
            "ad_player": battle_month + ad_month_cards,
            "small_payer_18daily": battle_month + small_rare_month,
            "mid_payer_packx4": battle_month + pack_month,
        },
        "gapAnalysis": {
            "monthsToCoreDeck8F2P": round(deck_frag / battle_month, 1),
            "monthsToCoreDeck8Ad": round(deck_frag / (battle_month + ad_month_cards), 1),
            "monthsToCoreDeck8SmallPayer": round(deck_frag / (battle_month + small_rare_month), 1),
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


def gen_shop_md(shop: dict, economy: dict) -> str:
    ex = shop["pricingReference"]["examples"]
    lines = [
        "# 商店配置与经济补足分析",
        "",
        "> 配表：`shop.json` v" + shop["version"] + " · 生成：`python3 scripts/gen-shop-config.py`",
        "",
        "---",
        "",
        "## 品质单价（全店唯一基准）",
        "",
        "| 品质 | 金币/张 | 钻石/张 |",
        "|:---|:---:|:---:|",
    ]
    for q in ("common", "rare", "epic", "legendary"):
        lines.append(f"| {QUALITY_CN[q]} | {GOLD_PER[q]} | {DIAMOND_PER[q]} |")

    lines += [
        "",
        "**换算示例：**",
        f"- {ex['epic5']}（每日优惠第6格）",
        f"- {ex['legendary5']}（轮换池传奇×5）",
        "",
        "> ⚠️ **750 金 = 史诗×5，不是传奇×5。** 传奇×5 应为 **2000 金 / 100 钻**。",
        "",
        "---",
        "",
        "## 一、角色区（直购）",
        "",
        "| 商品 | 价格 | 内容 | 限购 |",
        "|:---|:---:|:---|:---|",
    ]
    for p in shop["zones"]["character"]["products"]:
        if p["productId"] == "monthly_card":
            content = f"首购{p['firstBuyBonus']['diamond']}钻 + 每日{p['dailyClaim']['diamond']}钻×30天"
        elif "contents" in p:
            parts = []
            for c in p["contents"]:
                if c["type"] == "diamond":
                    parts.append(f"钻石{c['amount']}")
                else:
                    parts.append(f"{QUALITY_CN.get(c.get('quality',''), c.get('quality',''))}{c['count']}张")
            content = " + ".join(parts)
        else:
            content = "—"
        limit = p.get("weeklyLimit", p.get("durationDays", "—"))
        lines.append(f"| {p['name']} | ¥{p['priceCny']} | {content} | {limit} |")

    lines += [
        "",
        "---",
        "",
        "## 二、每日优惠（6格）",
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

    lines += [
        "",
        "### 全商品验算表",
        "",
        "| 商品 | 金/张 | 钻/张 | 总金币 | 总钻石 |",
        "|:---|:---:|:---:|:---:|:---:|",
    ]
    for s in shop["zones"]["basic"]["dailyDeals"]["slots"]:
        r = s["reward"]
        if r.get("type") == "diamond":
            continue
        lines.append(_fmt_price_row(r["quality"], r["count"], s["purchase"]))
    for s in shop["zones"]["basic"]["dailyDeals"]["rotationPool"]:
        r = s["reward"]
        lines.append(_fmt_price_row(r["quality"], r["count"], s["purchase"]))

    lines += [
        "",
        "---",
        "",
        "## 三、通用卡直购（¥18/30张，每品质日限4次）",
        "",
        "| SKU | 日满购 |",
        "|:---|:---:|",
    ]
    for p in shop["zones"]["basic"]["universalCardPacks"]["packs"]:
        lines.append(f"| {p['name']} | {p['count']*p['dailyLimit']}张 |")

    lines += [
        "",
        "---",
        "",
        "## 四、钻石充值（6档）",
        "",
        "| 档位 | 价格 | 合计钻石 |",
        "|:---:|:---:|:---:|",
    ]
    for t in shop["zones"]["basic"]["diamondRecharge"]:
        lines.append(f"| {t['tierId']} | ¥{t['priceCny']} | {t['diamond']+t['bonus']} |")

    e = economy
    lines += [
        "",
        "---",
        "",
        "## 五、经济补足（30天粗算）",
        "",
        f"- 核心8卡满级需碎片：**{e['targets']['coreDeckFrag']:,}**",
        "",
        "| 玩家 | 月获卡(粗算) | 核心8卡满级 |",
        "|:---|:---:|:---:|",
        f"| F2P | ~{e['monthlyCardsEstimate']['f2p_battleOnly']:,} | ~{e['gapAnalysis']['monthsToCoreDeck8F2P']}月 |",
        f"| 广告党 | ~{int(e['monthlyCardsEstimate']['ad_player']):,} | ~{e['gapAnalysis']['monthsToCoreDeck8Ad']}月 |",
        f"| 小氪 | ~{e['monthlyCardsEstimate']['small_payer_18daily']:,} | ~{e['gapAnalysis']['monthsToCoreDeck8SmallPayer']}月 |",
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
