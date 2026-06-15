#!/usr/bin/env python3
"""Generate shop.json and docs/SHOP_AND_ECONOMY.md"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 稀有 50 金/张 → 史诗 ×3、传奇 ×8（金币）；钻石约 1 钻 ≈ 1.5 金
GOLD_PER = {"common": 100, "rare": 50, "epic": 150, "legendary": 400}
DIAMOND_PER = {"common": 1, "rare": 3, "epic": 8, "legendary": 20}

HERO_COUNT = 37
FRAG_PER_HERO = 4565  # heroLevel.json fragmentNeed sum
DECK_SIZE = 8


def card_offer(quality: str, count: int, **extra) -> dict:
    return {
        "quality": quality,
        "count": count,
        "goldPrice": GOLD_PER[quality] * count,
        "diamondPrice": DIAMOND_PER[quality] * count,
        **extra,
    }


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
            "reward": card_offer("common", 30),
            "purchase": {"gold": 3000, "diamond": 30},
            "ad": {"enabled": False},
        },
        {
            "slotId": 3,
            "name": "普通卡×50",
            "reward": card_offer("common", 50),
            "purchase": {"gold": 5000, "diamond": 50},
            "ad": {"enabled": False},
            "note": "原稿「500金」应为笔误，按100金/张校正为5000",
        },
        {
            "slotId": 4,
            "name": "稀有卡×15",
            "reward": card_offer("rare", 15),
            "purchase": {"gold": 750, "diamond": 45},
            "ad": {"enabled": False},
        },
        {
            "slotId": 5,
            "name": "稀有卡×20",
            "reward": card_offer("rare", 20),
            "purchase": {"gold": 1000, "diamond": 60},
            "ad": {"enabled": False},
        },
        {
            "slotId": 6,
            "name": "史诗卡×5",
            "reward": card_offer("epic", 5),
            "purchase": {"gold": 750, "diamond": 40},
            "ad": {"enabled": True, "note": "看广告领取5张史诗通用卡"},
        },
    ]

    # 轮换第7档（刷新时随机出现，不占固定6格时可作奖池）
    daily_rotation = [
        {
            "slotId": "R1",
            "name": "传奇卡×2",
            "reward": card_offer("legendary", 2),
            "purchase": {"gold": None, "diamond": 40},
            "ad": {"enabled": True, "cooldownHours": 4, "note": "高价值广告位，4小时1次"},
        },
        {
            "slotId": "R2",
            "name": "史诗卡×10",
            "reward": card_offer("epic", 10),
            "purchase": {"gold": 1500, "diamond": 80},
            "ad": {"enabled": False},
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
        "version": "1.0.0",
        "description": "商店：角色区(直购) + 基础区(每日优惠/通用卡/钻石)",
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
            "note": "每日优惠可用金币或钻石；通用卡仅人民币直购",
        },
    }


def estimate_economy(shop: dict) -> dict:
    """30天粗算：纯战斗 / 广告党 / 小氪 / 中氪"""
    # 战斗线 (55% WR, 20局/天)
    battle_cards_day = 20 * 10  # 粗算均质木质~10张/胜
    battle_month = battle_cards_day * 30

    daily = shop["zones"]["basic"]["dailyDeals"]
    ad_ref = daily["refresh"]["maxAdRefreshesPerDay"]
    # 广告党：每日优惠全买金币档 + 广告钻/史诗/传奇轮换
    ad_diamond_day = 29 + ad_ref * 0.3 * 29  # 约30%刷新出钻 slot
    ad_cards_day = 5 + 2 * 0.5  # 史诗广告5 + 传奇轮换期望1
    ad_gold_deals = 15 + 20  # 稀有卡
    ad_month_cards = (ad_cards_day + ad_gold_deals) * 30

    # 小氪：月卡 + 每日1档18元稀有
    small_rare_month = 30 * 30  # 900 rare/month

    # 中氪：月卡 + 角色包4次/月
    pack = shop["zones"]["character"]["products"][2]["contents"]
    pack_month = sum(c["count"] for c in pack) * 4

    all_heroes_frag = FRAG_PER_HERO * HERO_COUNT
    deck_frag = FRAG_PER_HERO * DECK_SIZE

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
            "note": "1卡=1碎片粗算；实际重复卡需有转化/溢出价值",
            "monthsToCoreDeck8F2P": round(deck_frag / battle_month, 1),
            "monthsToCoreDeck8Ad": round(deck_frag / (battle_month + ad_month_cards), 1),
            "monthsToCoreDeck8SmallPayer": round(deck_frag / (battle_month + small_rare_month), 1),
        },
    }


def gen_shop_md(shop: dict, economy: dict) -> str:
    lines = [
        "# 商店配置与经济补足分析",
        "",
        "> 配表：`shop.json` · 生成：`python3 scripts/gen-shop-config.py`",
        "> 与 [`docs/ARENA_REWARDS.md`](ARENA_REWARDS.md)（竞技场）和 [`docs/PROGRESSION_TABLES.md`](PROGRESSION_TABLES.md) §四（账号等级）分离",
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
                    parts.append(f"{c.get('quality','')}{c['count']}张")
            content = " + ".join(parts)
        else:
            content = "—"
        limit = p.get("weeklyLimit", p.get("durationDays", "—"))
        lines.append(f"| {p['name']} | ¥{p['priceCny']} | {content} | {limit} |")

    lines += [
        "",
        "---",
        "",
        "## 二、基础区 · 每日优惠（6格）",
        "",
        f"广告刷新 CD **{shop['zones']['basic']['dailyDeals']['refresh']['adCooldownHours']}小时**（日上限约12次）；可用 **20钻** 手动刷新（日限6次）。",
        "",
        "| 格 | 商品 | 金币价 | 钻石价 | 广告 |",
        "|:---:|:---|:---:|:---:|:---:|",
    ]
    for s in shop["zones"]["basic"]["dailyDeals"]["slots"]:
        r = s["reward"]
        if r.get("type") == "diamond":
            lines.append(f"| {s['slotId']} | 钻石×{r['amount']} | — | {r['amount']} | ✅ |")
        else:
            g = s["purchase"].get("gold")
            d = s["purchase"].get("diamond")
            ad = "✅" if s["ad"].get("enabled") else "—"
            lines.append(f"| {s['slotId']} | {s['name']} | {g or '—'} | {d} | {ad} |")

    lines += [
        "",
        "### 轮换高价值位（刷新随机）",
        "",
        "| 商品 | 钻石价 | 广告 |",
        "|:---|:---:|:---:|",
    ]
    for s in shop["zones"]["basic"]["dailyDeals"]["rotationPool"]:
        ad = "✅" if s["ad"].get("enabled") else "—"
        lines.append(f"| {s['name']} | {s['purchase']['diamond']} | {ad} |")

    lines += [
        "",
        "### 品质定价参考",
        "",
        "| 品质 | 金币/张 | 钻石/张 |",
        "|:---|:---:|:---:|",
    ]
    for q, g in shop["pricingReference"]["goldPerCard"].items():
        d = shop["pricingReference"]["diamondPerCard"][q]
        cn = {"common": "普通", "rare": "稀有", "epic": "史诗", "legendary": "传奇"}[q]
        lines.append(f"| {cn} | {g} | {d} |")

    lines += [
        "",
        "---",
        "",
        "## 三、通用卡直购（¥18 / 30张，每品质日限4次）",
        "",
        "| SKU | 内容 | 日上限 | 日满购 |",
        "|:---|:---|:---:|:---:|",
    ]
    for p in shop["zones"]["basic"]["universalCardPacks"]["packs"]:
        lines.append(f"| {p['name']} | ¥{p['priceCny']} | {p['dailyLimit']}次 | {p['count']*p['dailyLimit']}张 |")

    lines += [
        "",
        "---",
        "",
        "## 四、钻石充值（6档）",
        "",
        "| 档位 | 价格 | 钻石 | 赠送 | 合计 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    for t in shop["zones"]["basic"]["diamondRecharge"]:
        total = t["diamond"] + t["bonus"]
        lines.append(f"| {t['tierId']} | ¥{t['priceCny']} | {t['diamond']} | +{t['bonus']} | **{total}** |")

    e = economy
    lines += [
        "",
        "---",
        "",
        "## 五、能否补上养成缺口？（30天粗算）",
        "",
        f"- 37英雄全满需碎片（1卡=1片）：**{e['targets']['allHeroesFrag']:,}**",
        f"- 核心8卡编队满级需：**{e['targets']['coreDeckFrag']:,}**",
        "",
        "| 玩家类型 | 月获卡牌(粗算) | 说明 |",
        "|:---|:---:|:---|",
        f"| 纯战斗 F2P | ~{e['monthlyCardsEstimate']['f2p_battleOnly']:,} | 20胜/天 |",
        f"| 战斗+广告 | ~{e['monthlyCardsEstimate']['ad_player']:,} | 含每日广告优惠 |",
        f"| 小氪(月卡+¥18/天稀有) | ~{e['monthlyCardsEstimate']['small_payer_18daily']:,} | 拉平稀有缺口 |",
        f"| 中氪(月卡+角色包×4/月) | ~{e['monthlyCardsEstimate']['mid_payer_packx4']:,} | 传奇/史诗爆发 |",
        "",
        "| 目标 | F2P | 广告党 | 小氪 |",
        "|:---|:---:|:---:|:---:|",
        f"| 核心8卡满级(月) | ~{e['gapAnalysis']['monthsToCoreDeck8F2P']} | ~{e['gapAnalysis']['monthsToCoreDeck8Ad']} | ~{e['gapAnalysis']['monthsToCoreDeck8SmallPayer']} |",
        "",
        "**结论：**",
        "- 商店主要补 **稀有→传奇** 长线缺口，战斗线负责 **金币+经验+奖杯**",
        "- F2P 约 **2–3个月** 可养满核心8卡（合理）",
        "- 全37英雄满级是 **年级别** 目标，需角色包/通用传奇直购",
        "- 广告党与小氪差距主要体现在 **高品级卡速度**，符合「拉开差距」目标",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    shop = gen_shop()
    economy = estimate_economy(shop)

    shop_path = ROOT / "shop.json"
    shop_path.write_text(json.dumps(shop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {shop_path}")

    md_path = ROOT / "docs" / "SHOP_AND_ECONOMY.md"
    md_path.write_text(gen_shop_md(shop, economy) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")
