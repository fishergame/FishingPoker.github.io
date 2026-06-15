#!/usr/bin/env python3
"""Print progression sync calibration table (55% WR simulation)."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    arena = json.loads((ROOT / "arena.json").read_text())
    account = json.loads((ROOT / "account.json" if (ROOT / "account.json").exists() else ROOT / "accountLevel.json").read_text())
    exp_reqs = [lv["expRequired"] for lv in account["levels"]]

    def sim(win_rate=0.55, target=12000, seed=42):
        random.seed(seed)
        trophy = battles = ai = exp = idx = 0
        checkpoints = {}
        while trophy < target and battles < 150000:
            a = arena["arenas"][ai]
            br = a["battleReward"]
            tw, tl, ew, el = br["trophyWin"], br["trophyLoss"], br["expWin"], br["expLoss"]
            battles += 1
            if random.random() < win_rate:
                trophy += tw
                exp += ew
            else:
                trophy = max(0, trophy - tl)
                exp += el
            if ai < 9 and trophy >= arena["arenas"][ai]["nextArenaTrophy"]:
                ai += 1
            while idx < 99 and exp >= sum(exp_reqs[: idx + 1]):
                idx += 1
            for cup in [4000, 6000, 7500, 9000, 10000, 12000]:
                if cup not in checkpoints and trophy >= cup:
                    checkpoints[cup] = (idx + 1, battles)
        return checkpoints, battles, idx + 1

    print("=== 账号×竞技场同步校准 (55% WR) ===")
    cp, b12, lv = sim()
    for cup in [4000, 6000, 7500, 9000, 10000, 12000]:
        if cup in cp:
            l, b = cp[cup]
            arena_name = next(
                (a["name"] for a in arena["arenas"] if a["unlockTrophy"] <= cup),
                "?",
            )
            print(f"  {cup}杯 (~{arena_name}段): L{l} @ {b}场")
    print(f"  12k毕业: {b12}场, 终等级L{lv}")
    print(f"  L90累计经验: {sum(exp_reqs[:89]):,}")
    print(f"  L100累计经验: {sum(exp_reqs):,}")


if __name__ == "__main__":
    main()
