#!/usr/bin/env python3
"""Generate dailyQuest.json + docs/MAIN_CITY_DAILY_QUEST.md（主城每日任务 · 独立文档）"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVEL_MAX = 30

# 单格翻砖（与 mainCity.json 一致）
BRICK_BASE_PER_TILE = 12
BRICK_PER_TILE_STEP = 3

LOGIN_CFG = {
    "base": 5,
    "flipCostMult": 0.52,
    "min": 11,
    "max": 58,
    "cycleDays": 7,
    "dayMultipliers": [1.00, 1.00, 1.06, 1.10, 1.14, 1.18, 1.75],
    "breakResetsToDay": 1,
}

BATTLE_CFG = {
    "base": 3,
    "flipCostMult": 0.26,
    "min": 6,
    "max": 28,
    "countLosses": True,
    "tiers": [
        {"tierId": "warmup", "label": "热身", "battlesRequired": 3, "rewardMult": 0.55},
        {"tierId": "daily", "label": "日常", "battlesRequired": 6, "rewardMult": 0.90, "cumulative": True},
        {"tierId": "bonus", "label": "加赏", "battlesRequired": 10, "rewardMult": 0.55, "cumulative": True},
    ],
}

RESET = {"at": "00:00", "timezone": "Asia/Shanghai"}


def flip_brick_cost(level: int) -> int:
    return BRICK_BASE_PER_TILE + (level - 1) * BRICK_PER_TILE_STEP


def login_base(level: int) -> int:
    raw = round(LOGIN_CFG["base"] + flip_brick_cost(level) * LOGIN_CFG["flipCostMult"])
    return max(LOGIN_CFG["min"], min(LOGIN_CFG["max"], raw))


def battle_base(level: int) -> int:
    raw = round(BATTLE_CFG["base"] + flip_brick_cost(level) * BATTLE_CFG["flipCostMult"])
    return max(BATTLE_CFG["min"], min(BATTLE_CFG["max"], raw))


def login_reward(level: int, streak_day: int) -> int:
    mult = LOGIN_CFG["dayMultipliers"][streak_day - 1]
    return round(login_base(level) * mult)


def battle_tier_reward(level: int, tier: dict) -> int:
    return round(battle_base(level) * tier["rewardMult"])


def battle_day_max(level: int) -> int:
    base = battle_base(level)
    total = 0
    for t in BATTLE_CFG["tiers"]:
        total += round(base * t["rewardMult"])
    return total


def weekly_login_total(level: int) -> int:
    return sum(login_reward(level, d) for d in range(1, LOGIN_CFG["cycleDays"] + 1))


def build_level_rows() -> list[dict]:
    rows = []
    for lv in range(1, LEVEL_MAX + 1):
        flip = flip_brick_cost(lv)
        lb = login_base(lv)
        bb = battle_base(lv)
        login_by_day = [login_reward(lv, d) for d in range(1, 8)]
        battle_tiers = [
            {
                **t,
                "rewardBricks": battle_tier_reward(lv, t),
            }
            for t in BATTLE_CFG["tiers"]
        ]
        rows.append({
            "mainCityLevel": lv,
            "flipBrickCost": flip,
            "loginBase": lb,
            "battleBase": bb,
            "loginByStreakDay": login_by_day,
            "loginDay7": login_by_day[6],
            "loginWeekTotal": weekly_login_total(lv),
            "battleTiers": battle_tiers,
            "battleDayMax": battle_day_max(lv),
            "dayMaxCombined": login_by_day[6] + battle_day_max(lv),
        })
    return rows


def build_config(rows: list[dict]) -> dict:
    return {
        "version": "1.0.0",
        "description": "主城每日任务：登录连签（7日周期）+ 对战档位；数值随主城等级缩放",
        "scaleBy": "mainCityLevel",
        "flipBrickCostFormula": "12 + (mainCityLevel - 1) * 3",
        "reset": RESET,
        "loginStreak": {
            **LOGIN_CFG,
            "loginBaseFormula": "clamp(round(5 + flipBrickCost * 0.52), 11, 58)",
            "todayFormula": "round(loginBase * dayMultipliers[streakDay - 1])",
            "tomorrowPreview": "今日领取后 streakDay+1；第7天领完次日为第1天；断签重置为第1天",
        },
        "battleTasks": {
            **BATTLE_CFG,
            "battleBaseFormula": "clamp(round(3 + flipBrickCost * 0.26), 6, 28)",
            "tierRewardFormula": "round(battleBase * rewardMult)",
            "dayMaxFormula": "sum(all tier rewards)",
        },
        "ui": {
            "entry": "主城页 · 每日任务弹窗",
            "sections": ["loginStreak", "battleTasks"],
            "loginShowsTomorrowPreview": True,
            "battleCta": "前往对战",
        },
        "levels": rows,
    }


def gen_markdown(data: dict) -> str:
    rows = data["levels"]
    mults = data["loginStreak"]["dayMultipliers"]
    tiers = data["battleTasks"]["tiers"]

    lines = [
        "# 主城每日任务：登录连签 · 对战档位",
        "",
        "> 配表：`dailyQuest.json` · 生成：`python3 scripts/gen-daily-quest-config.py`",
        "> 主城翻格/砖头总经济见 [`MAIN_CITY_PROGRESSION.md`](MAIN_CITY_PROGRESSION.md)（**本文不合并进该总表**）",
        "",
        "---",
        "",
        "## 一、模块定位",
        "",
        "| 项 | 说明 |",
        "|:---|:---|",
        "| **入口** | 主城页 → 每日任务弹窗 |",
        "| **登录** | 每日领取；**7 日连签周期**，第 7 天大奖；**断签重置为第 1 天** |",
        "| **对战** | 与连签独立；每日 0 点重置；胜/负均计场次 |",
        "| **缩放** | 仅随 **主城等级** `mainCityLevel`，不随账号等级 |",
        "| **经济占比** | 满级全程约 **9%～11%** 砖头（登录 ~6%，对战 ~3%～5%） |",
        "",
        "### 弹窗结构",
        "",
        "```",
        "┌─────────────────────────────────────┐",
        "│  每日任务                    [×]    │",
        "├─────────────────────────────────────┤",
        "│  📅 登录奖励（7日周期 第N天）        │",
        "│  今日可领：XX 砖头        [领取]    │",
        "│  明日可领：XX 砖头（连续第N+1天）    │",
        "│  ●●●○○○○  进度点                   │",
        "├─────────────────────────────────────┤",
        "│  ⚔ 对战任务（今日 X/Y 场）           │",
        "│  □ 完成 3 场   +A 砖头              │",
        "│  □ 完成 6 场   +B 砖头（累计）       │",
        "│  □ 完成 10 场  +C 砖头（加赏）       │",
        "│              [前往对战]              │",
        "└─────────────────────────────────────┘",
        "```",
        "",
        "---",
        "",
        "## 二、规则",
        "",
        "### 2.1 登录连签（7 日周期）",
        "",
        f"- 周期 **{data['loginStreak']['cycleDays']}** 天：连签日 1→7，第 7 天领取后次日回到第 1 天",
        "- **断签**：跨日 0 点仍未领取昨日登录奖 → 连签重置为第 1 天（不补签）",
        "- **明日预览**：展示「若今日已领取」情况下明日的登录砖数",
        "- 领取只推进连签，不要求当日对战",
        "",
        "**连签倍率**",
        "",
        "| 连签日 | 倍率 |",
        "|:---:|:---:|",
    ]
    for i, m in enumerate(mults, 1):
        lines.append(f"| {i} | {m} |")

    lines += [
        "",
        "**公式**",
        "",
        "```",
        f"flipBrickCost(L) = {data['flipBrickCostFormula']}",
        f"loginBase(L)     = {data['loginStreak']['loginBaseFormula']}",
        "todayLogin(L, d) = round(loginBase(L) * dayMultipliers[d - 1])  // d ∈ 1..7",
        "```",
        "",
        "### 2.2 对战档位",
        "",
        "- 与登录连签 **互不影响**",
        "- 场次：完成一场对战即 +1（**胜负都算**）",
        "- 三档 **累计可领**（达 10 场可领满三档总和）",
        "",
        "| 档位 | 场次 | 奖励倍率 | 说明 |",
        "|:---|:---:|:---:|:---|",
    ]
    for t in tiers:
        lines.append(
            f"| {t['label']} | ≥{t['battlesRequired']} | ×{t['rewardMult']} | "
            f"`round(battleBase × {t['rewardMult']})` |"
        )

    lines += [
        "",
        "**公式**",
        "",
        "```",
        f"battleBase(L) = {data['battleTasks']['battleBaseFormula']}",
        "tierReward    = round(battleBase(L) * rewardMult)",
        "dayMax        = sum(all tier rewards)  // 约 battleBase × 2.0",
        "```",
        "",
        f"- 每日重置：`{RESET['at']}` `{RESET['timezone']}`",
        "",
        "---",
        "",
        "## 三、登录奖励曲线（按连签日）",
        "",
        "下表为各主城等级 **loginBase** 与第 1 / 4 / 7 天示例（完整 30 级见 `dailyQuest.json → levels`）。",
        "",
        "| 主城 L | 单格砖 | loginBase | 第1天 | 第4天 | 第7天 | 满7日合计 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    key_levels = [1, 5, 10, 15, 20, 25, 30]
    for lv in key_levels:
        r = rows[lv - 1]
        ld = r["loginByStreakDay"]
        lines.append(
            f"| **L{lv}** | {r['flipBrickCost']} | {r['loginBase']} | "
            f"{ld[0]} | {ld[3]} | {ld[6]} | {r['loginWeekTotal']} |"
        )

    lines += [
        "",
        "### L10 逐日明细（示例）",
        "",
        "| 连签日 | 倍率 | 今日登录砖 | 明日预览（今日已领后） |",
        "|:---:|:---:|:---:|:---:|",
    ]
    r10 = rows[9]
    for d in range(1, 8):
        mult = mults[d - 1]
        today = r10["loginByStreakDay"][d - 1]
        tomorrow_day = 1 if d == 7 else d + 1
        tomorrow = r10["loginByStreakDay"][tomorrow_day - 1]
        lines.append(f"| {d} | {mult} | {today} | {tomorrow} |")

    lines += [
        "",
        "---",
        "",
        "## 四、对战任务曲线",
        "",
        "| 主城 L | battleBase | 3场 | 6场累计 | 10场日上限 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    for lv in key_levels:
        r = rows[lv - 1]
        t = r["battleTiers"]
        cum6 = t[0]["rewardBricks"] + t[1]["rewardBricks"]
        lines.append(
            f"| **L{lv}** | {r['battleBase']} | {t[0]['rewardBricks']} | "
            f"{cum6} | {r['battleDayMax']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 五、玩家画像（日收入粗算）",
        "",
        "以 **L10** 为例，对比任务砖与战斗主产出（战斗砖见 `MAIN_CITY_PROGRESSION.md`，此处不展开）。",
        "",
        "| 行为 | 登录砖 | 对战砖 | 合计 | 适合画像 |",
        "|:---|:---:|:---:|:---:|:---|",
        f"| 只领登录（连签第1天） | {rows[9]['loginByStreakDay'][0]} | 0 | {rows[9]['loginByStreakDay'][0]} | 纯签到 |",
    ]
    l10 = rows[9]
    login_d4 = l10["loginByStreakDay"][3]
    b3 = l10["battleTiers"][0]["rewardBricks"]
    b6 = l10["battleTiers"][0]["rewardBricks"] + l10["battleTiers"][1]["rewardBricks"]
    day7 = l10["loginByStreakDay"][6]
    bmax = l10["battleDayMax"]
    lines += [
        f"| 登录 + 3 场 | {login_d4} | {b3} | {login_d4 + b3} | 轻度（5场/日） |",
        f"| 登录 + 6 场 | {login_d4} | {b6} | {login_d4 + b6} | 常规（10场/日） |",
        f"| 第7天 + 10 场满档 | {day7} | {bmax} | {day7 + bmax} | 活跃周 |",
        "",
        "---",
        "",
        "## 六、设计理由",
        "",
        "1. **随主城等级缩放**：`loginBase` / `battleBase` 锚定 `flipBrickCost`，全等级维持「约 0.5 格」体感。",
        "2. **7 日周期 + 第 7 天 ×1.75**：满周比全用第 1 天多约 **60%～65%**，提高连签动力。",
        "3. **断签重置**：规则简单；明日预览让玩家看见「今天领 vs 明天领」差异。",
        "4. **对战 3 / 6 / 10 场**：覆盖轻度（5 场）、常规（10 场）；10 场为加赏非硬性。",
        "5. **独立文档**：本模块为第五砖头渠道，数值自检不与 `MAIN_CITY_PROGRESSION` 总表混排。",
        "",
        "### 满级节奏影响（粗算）",
        "",
        "| 画像 | 原参考满级 | 加入本模块后 |",
        "|:---|:---:|:---:|",
        "| 常规 10 场/日 | ~27 天 | ~24～25 天 |",
        "| 轻度 5 场/日 | ~56 天 | ~46～50 天 |",
        "| 重度 25 场/日 | ~10 天 | ~10 天 |",
        "",
        "---",
        "",
        "## 七、完整 30 级配表",
        "",
        "| L | 单格砖 | loginBase | 连签1..7 | battleBase | 3场 | 6场计 | 10场上限 |",
        "|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|",
    ]
    for r in rows:
        ld = r["loginByStreakDay"]
        streak_str = "/".join(str(x) for x in ld)
        t = r["battleTiers"]
        cum6 = t[0]["rewardBricks"] + t[1]["rewardBricks"]
        lines.append(
            f"| {r['mainCityLevel']} | {r['flipBrickCost']} | {r['loginBase']} | {streak_str} | "
            f"{r['battleBase']} | {t[0]['rewardBricks']} | {cum6} | {r['battleDayMax']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = build_level_rows()
    data = build_config(rows)

    out_json = ROOT / "dailyQuest.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")

    out_md = ROOT / "docs" / "MAIN_CITY_DAILY_QUEST.md"
    out_md.write_text(gen_markdown(data) + "\n", encoding="utf-8")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
