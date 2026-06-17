#!/usr/bin/env python3
"""Generate combatTiming.json + docs/COMBAT_TIMING.md

弹道速度 = A→B 飞行用时（秒），UI 名称保持「弹道速度」，数值越小越快。
攻击间隔 = 两次出手间隔（秒）。

替代 v3 旧口径：heroBattle.combatStats.attackSpeedL1（无单位指数）与 fireRate 推导间隔。
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROJECTILE = {
    "dragon_knight": "arc",
    "demon_lord": "arc",
    "archmage": "arc",
    "ranger": "flat",
    "royal_knight": "flat",
    "druid": "flat",
    "lich_queen": "arc",
    "blademaster": "flat",
    "frost_dragon": "arc",
    "crusher": "arc",
    "helicopter": "flat",
    "dread_knight": "flat",
    "warlord": "flat",
    "panda_monk": "arc",
    "shaman": "flat",
    "gargoyle": "flat",
    "skeleton_giant": "flat",
    "sniper": "flat",
    "catapult_tower": "arc",
    "catapult": "arc",
    "cavalry": "flat",
    "wyrmling": "arc",
    "ballista": "arc",
    "necromancer": "arc",
    "spear_orc": "flat",
    "wolf_rider": "flat",
    "skeleton_knight": "flat",
    "archer": "flat",
    "infantry": "flat",
    "arrow_tower": "arc",
    "bear_warrior": "flat",
    "skeleton_warrior": "flat",
    "goblin": "flat",
    "blacksmith": "flat",
    "militia": "flat",
    "bone_archer": "flat",
    "gold_mine": "flat",
    "heavy_shield": "flat",
}

# 攻击间隔：L1 特例 + 其余沿用 2.2/legacyFireRate
INTERVAL_OVERRIDE_L1 = {"dread_knight": 2.0}

# 升级曲线（校验后采用）
INTERVAL_GROWTH = 0.992  # 每级约 -0.8%，L30 约为 L1 的 79%
FLIGHT_GROWTH = 0.976  # 每级约 -2.4%，L30 约为 L1 的 50%，升级感知更明显
INTERVAL_MIN = 1.15  # 慢速卡参考下限（仅 L1≥此值时作兜底，不强制卡死每级）
INTERVAL_DISPLAY_STEP = 0.01  # UI 两位小数：每级攻击间隔至少缩短 0.01s
MAX_HERO_LEVEL = 30

# 弹道速度 L1 分档（秒，整体较 v0.9 草案 +1s 左右，重武器更慢）
FLIGHT_FLAT_TIERS = [
    (1.2, 1.20),  # 贴身
    (2.0, 1.45),  # 近战
    (3.0, 1.65),  # 短中
    (5.0, 1.95),  # 中程
    (7.0, 2.25),  # 远程
    (99.0, 2.55),  # 超远程
]
FLIGHT_ARC_BUILDING = 2.85
FLIGHT_ARC_BASE = 2.05
FLIGHT_ARC_RANGE_STEP = 0.12  # 每格 attackRange +0.12s，封顶 +0.75


def load_heroes() -> list[dict]:
    script = r"""
    const fs=require('fs');
    const code=fs.readFileSync('heroes-config.js','utf8').replace('const HeroesConfig','var HeroesConfig');
    eval(code);
    console.log(JSON.stringify(HeroesConfig.HEROES));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


def interval_l1(hero: dict) -> float | None:
    if hero["type"] == "resource":
        return None
    hid = hero["id"]
    if hid in INTERVAL_OVERRIDE_L1:
        return INTERVAL_OVERRIDE_L1[hid]
    legacy = hero.get("attackSpeed") or 1.0
    return round(2.2 / legacy, 2)


def flight_l1(hero: dict) -> float | None:
    if hero["type"] == "resource":
        return None
    style = PROJECTILE.get(hero["id"], "flat")
    rng = hero.get("attackRange")
    if hero["type"] == "building" and style == "arc":
        return FLIGHT_ARC_BUILDING
    if style == "arc":
        r = min(float(rng) if rng is not None else 5.0, 8.0)
        extra = min(0.75, max(0, (r - 3) * FLIGHT_ARC_RANGE_STEP))
        return round(min(2.85, FLIGHT_ARC_BASE + extra), 2)
    r = float(rng) if rng is not None else 2.0
    for cap, sec in FLIGHT_FLAT_TIERS:
        if r <= cap:
            return sec
    return FLIGHT_FLAT_TIERS[-1][1]


def at_level(l1: float | None, level: int, growth: float, min_val: float | None = None) -> float | None:
    if l1 is None:
        return None
    v = round(l1 * (growth ** (level - 1)), 2)
    if min_val is not None and l1 >= min_val:
        v = max(min_val, v)
    return v


def interval_series(l1: float, max_level: int = MAX_HERO_LEVEL) -> list[float]:
    """攻击间隔逐级曲线：指数目标与「每级至少 -0.01s」取更快者，避免两位小数并列。"""
    series = [round(l1, 2)]
    for level in range(2, max_level + 1):
        v_exp = round(l1 * (INTERVAL_GROWTH ** (level - 1)), 2)
        v_step = round(series[-1] - INTERVAL_DISPLAY_STEP, 2)
        v = min(v_exp, v_step)
        if v >= series[-1]:
            v = v_step
        series.append(v)
    return series


def interval_at_level(l1: float | None, level: int) -> float | None:
    if l1 is None:
        return None
    return interval_series(l1)[level - 1]


def old_v3_flight_index(hero: dict) -> float | None:
    """旧 heroBattle v3 无单位弹速指数（仅供参考对比）。"""
    if hero["type"] == "resource":
        return None
    legacy = hero.get("attackSpeed") or 1.0
    style = PROJECTILE.get(hero["id"], "flat")
    if style == "arc":
        return round(min(10, max(4.0, legacy + 2.5)), 2)
    return round(min(10, max(5.0, legacy + 3.0)), 2)


def old_v3_interval(hero: dict) -> float | None:
    if hero["type"] == "resource":
        return None
    legacy = hero.get("attackSpeed") or 1.0
    return round(2.2 / legacy, 2)


def build_rows(heroes: list[dict]) -> list[dict]:
    rows = []
    for h in heroes:
        il1 = interval_l1(h)
        fl1 = flight_l1(h)
        rows.append(
            {
                "heroId": h["id"],
                "name": h["name"],
                "quality": h["quality"],
                "unitType": h["type"],
                "projectileStyle": PROJECTILE.get(h["id"], "flat"),
                "attackRange": h.get("attackRange"),
                "legacyFireRate": h.get("attackSpeed"),
                "legacyV3": {
                    "attackIntervalL1": old_v3_interval(h),
                    "projectileSpeedIndexL1": old_v3_flight_index(h),
                    "source": "heroBattle.json combatStats (skill-system v3 分支)",
                },
                "attackIntervalL1": il1,
                "attackIntervalL2": interval_at_level(il1, 2),
                "attackIntervalL15": interval_at_level(il1, 15),
                "attackIntervalL30": interval_at_level(il1, 30),
                "attackIntervalLevels": interval_series(il1) if il1 is not None else None,
                "projectileFlightSecL1": fl1,
                "projectileFlightSecL2": at_level(fl1, 2, FLIGHT_GROWTH),
                "projectileFlightSecL15": at_level(fl1, 15, FLIGHT_GROWTH),
                "projectileFlightSecL30": at_level(fl1, 30, FLIGHT_GROWTH),
            }
        )
    return rows


def gen_markdown(data: dict) -> str:
    rows = data["heroes"]
    lines = [
        "# 战斗节奏：攻击间隔 · 弹道速度（秒）",
        "",
        "> 配表：`combatTiming.json` · 生成：`python3 scripts/gen-combat-timing-config.py`",
        "> **独立文档**：本表不并入 `MAIN_CITY_PROGRESSION.md` / `BATTLE_BALANCE.md`",
        "",
        "---",
        "",
        "## 一、字段定义（UI）",
        "",
        "| UI 名称 | 配表字段 | 单位 | 含义 |",
        "|:---|:---|:---:|:---|",
        "| 攻击间隔 | `attackIntervalL1` + 成长 | **秒** | 两次攻击之间等待时间 |",
        "| 弹道速度 | `projectileFlightSecL1` + 成长 | **秒** | 从 A 点到命中点 B 的**飞行用时**（越小越快） |",
        "| 弹道 | `projectileStyle` | — | `flat` 平直 / `arc` 高抛（只影响轨迹，不另设高度参数） |",
        "",
        "**升级展示建议**：绿字显示相对上一级的秒数差（负值表示更快/更短）。",
        "",
        "---",
        "",
        "## 二、升级曲线（校验结论）",
        "",
        f"| 属性 | 成长公式 | 参数 | L1→L30 体感 |",
        "|:---|:---|:---|:---|",
        f"| 攻击间隔 | 逐级 `min(round(L1×{INTERVAL_GROWTH}^(L-1),2), 上级-{INTERVAL_DISPLAY_STEP})` | 指数约 **-0.8%**，且**每级至少 -0.01s** | L30 约 **L1-0.29s** 或更快 |",
        f"| 弹道速度 | `round(L1 × {FLIGHT_GROWTH}^(L-1), 2)` | 每级约 **-2.4%** | 约为 L1 的 **50%**，飞行明显变快 |",
        "",
        "**设计取舍**：",
        "",
        "- 攻击间隔纯指数 + 两位小数时，常出现 **连两级同为 0.78s**；现强制每级至少缩短 0.01s，升级绿字始终有数",
        "- 弹道速度成长快于攻击间隔：升级后更容易看出「弹到了」",
        f"- 全量 30 级间隔见 `combatTiming.json` → `attackIntervalLevels`（或按上式逐级递推）",
        "- 弹道 L1 整体比旧 v3 指数口径 **+约 1s** 量级；重炮/高抛可更慢（2.0～2.85s）",
        "",
        "---",
        "",
        "## 三、旧配置在哪里（已废弃口径）",
        "",
        "| 位置 | 旧字段 | 问题 |",
        "|:---|:---|:---|",
        "| `heroBattle.json` → `combatStats`（`cursor/skill-system-v3-d188` 分支） | `attackSpeedL1` | 名为弹速实为**无单位指数**（约 5～8），易被当成秒 |",
        "| 同上 | `fireRateL1` + `attackInterval = 2.2/fireRate` | 间隔间接推导，与 UI 不直观 |",
        "| `heroes-config.js` → `attackSpeed` | 遗留 **发射频率**，不是 UI 弹速 |",
        "| `docs/SKILL_SYSTEM.md`（v3 分支） | `attackSpeedMeans: 弹道飞行速度` | 与上表指数混用 |",
        "| `scripts/gen-skill-bond-config.py` → `derive_combat_stats()` | 生成旧 `combatStats` | 需改读 `combatTiming.json` |",
        "",
        "**本版替代**：以 `combatTiming.json` 为单一数据源；`projectileFlightSec` 直接存**秒**。",
        "",
        "---",
        "",
        "## 四、全卡 L1 配表（新）",
        "",
        "| id | 名称 | 品质 | 弹道 | 攻击间隔 L1 | 弹道速度 L1 | 旧间隔 L1 | 旧弹速指数 |",
        "|:---|:---|:---|:---|:---:|:---:|:---:|:---:|",
    ]
    for r in rows:
        if r["unitType"] == "resource":
            lines.append(f"| `{r['heroId']}` | {r['name']} | {r['quality']} | — | — | — | — | — |")
            continue
        leg = r["legacyV3"]
        lines.append(
            f"| `{r['heroId']}` | {r['name']} | {r['quality']} | {r['projectileStyle']} | "
            f"**{r['attackIntervalL1']}s** | **{r['projectileFlightSecL1']}s** | "
            f"{leg['attackIntervalL1']}s | {leg['projectileSpeedIndexL1']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 五、关键等级对照（攻击间隔 · 弹道速度）",
        "",
        "| id | 名称 | L1 间隔/弹速 | L15 | L30 |",
        "|:---|:---|:---:|:---:|:---:|",
    ]
    key_ids = [
        "dread_knight",
        "dragon_knight",
        "crusher",
        "archer",
        "sniper",
        "arrow_tower",
        "infantry",
        "catapult",
    ]
    by_id = {r["heroId"]: r for r in rows}
    for hid in key_ids:
        r = by_id[hid]
        lines.append(
            f"| `{hid}` | {r['name']} | {r['attackIntervalL1']}s / {r['projectileFlightSecL1']}s | "
            f"{r['attackIntervalL15']}s / {r['projectileFlightSecL15']}s | "
            f"{r['attackIntervalL30']}s / {r['projectileFlightSecL30']}s |"
        )

    lines += [
        "",
        "### 巨斧酋长逐级（示例 UI）",
        "",
        "| 等级 | 攻击间隔 | 较 L1 | 弹道速度 | 较 L1 |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ]
    dk = by_id["dread_knight"]
    dk_intervals = dk["attackIntervalLevels"]
    for lv in [1, 2, 5, 10, 15, 20, 30]:
        iv = dk_intervals[lv - 1]
        fv = at_level(dk["projectileFlightSecL1"], lv, FLIGHT_GROWTH)
        lines.append(
            f"| L{lv} | {iv}s | {iv - dk['attackIntervalL1']:+.2f}s | {fv}s | {fv - dk['projectileFlightSecL1']:+.2f}s |"
        )

    lines += [
        "",
        "---",
        "",
        "## 六、完整 30 级采样（L1 / L15 / L30）",
        "",
        "| id | 名称 | 间隔 L1 | L15 | L30 | 弹速 L1 | L15 | L30 |",
        "|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in rows:
        if r["unitType"] == "resource":
            continue
        lines.append(
            f"| `{r['heroId']}` | {r['name']} | {r['attackIntervalL1']} | {r['attackIntervalL15']} | "
            f"{r['attackIntervalL30']} | {r['projectileFlightSecL1']} | {r['projectileFlightSecL15']} | "
            f"{r['projectileFlightSecL30']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 七、程序接入",
        "",
        "```json",
        '"formulas": {',
        f'  "attackInterval": "逐级 min(round(L1×{INTERVAL_GROWTH}^(L-1),2), prev-{INTERVAL_DISPLAY_STEP})；或读 attackIntervalLevels[L-1]",',
        f'  "projectileFlightSec": "round(projectileFlightSecL1 * {FLIGHT_GROWTH}^(heroLevel-1), 2)"',
        "}",
        "```",
        "",
        "`heroBattle.json` 每英雄读取 `combatTiming.json` 对应项写入 `combatStats`；UI 标签仍为「弹道速度」，单位显示 `s`。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    heroes = load_heroes()
    rows = build_rows(heroes)
    data = {
        "version": "1.1.0",
        "description": "攻击间隔与弹道飞行用时（秒）；替代 heroBattle v3 无单位弹速指数",
        "replaces": {
            "heroBattleCombatStats": "attackSpeedL1 / fireRateL1（见 cursor/skill-system-v3-d188）",
            "doc": "docs/SKILL_SYSTEM.md §属性成长（v3 分支）",
            "generator": "scripts/gen-skill-bond-config.py → derive_combat_stats()",
        },
        "ui": {
            "attackIntervalLabel": "攻击间隔",
            "projectileFlightLabel": "弹道速度",
            "unit": "s",
            "projectileFlightNote": "数值为飞行用时，越小越快",
        },
        "formulas": {
            "attackInterval": (
                f"perLevel: v = min(round(attackIntervalL1 * {INTERVAL_GROWTH}^(heroLevel-1), 2), "
                f"prevAttackInterval - {INTERVAL_DISPLAY_STEP}); "
                f"or lookup attackIntervalLevels[heroLevel-1]"
            ),
            "projectileFlightSec": f"round(projectileFlightSecL1 * {FLIGHT_GROWTH}^(heroLevel-1), 2)",
            "intervalGrowthPerLevel": round((INTERVAL_GROWTH - 1) * 100, 2),
            "flightGrowthPerLevel": round((FLIGHT_GROWTH - 1) * 100, 2),
            "intervalDisplayStepMin": INTERVAL_DISPLAY_STEP,
            "attackIntervalMinReference": INTERVAL_MIN,
        },
        "flightL1Tiers": {
            "flat": FLIGHT_FLAT_TIERS,
            "arcBuilding": FLIGHT_ARC_BUILDING,
            "arcBase": FLIGHT_ARC_BASE,
            "arcRangeStep": FLIGHT_ARC_RANGE_STEP,
        },
        "intervalOverridesL1": INTERVAL_OVERRIDE_L1,
        "heroes": rows,
    }

    out_json = ROOT / "combatTiming.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")

    out_md = ROOT / "docs" / "COMBAT_TIMING.md"
    out_md.write_text(gen_markdown(data) + "\n", encoding="utf-8")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
