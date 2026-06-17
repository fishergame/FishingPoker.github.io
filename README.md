# 代号x / testgame

## Cocos 工程（主项目）

**路径**：[`codename-x/`](codename-x/)  
**引擎**：Cocos Creator **3.8.7**，**2D 空项目**（非 3D）  
**打开方式**：Cocos Dashboard → 打开项目 → 选择 `codename-x` 目录

详见 [`codename-x/README.md`](codename-x/README.md)、[`docs/SYSTEM_FRAMEWORK.md`](docs/SYSTEM_FRAMEWORK.md)（**养成 + 竞技总框架**）与 [`docs/AI_COCOS_FRAMEWORK_SPEC.md`](docs/AI_COCOS_FRAMEWORK_SPEC.md)

---

## 页面流程

1. **卡组配置** [`index.html`](index.html) — 37 张卡，上方 8 槽出战，点击装备/卸下
2. **局内对战** [`battle.html`](battle.html) — 翻牌 + 自动战斗 Demo

配置表见 [`heroes-config.js`](heroes-config.js)

## HTML 局内对战 Demo（核心玩法验证）

竖屏双棋盘翻牌 + 自动战斗原型。规则层在 `battle-config.js` / `battle-rules.js`，可直接迁到 Cocos。

## 运行

```bash
cd /Users/sming/Desktop/testgame
python3 -m http.server 8080
```

浏览器访问 http://localhost:8080 （卡组页）→ 点击进入战斗

或直接双击 `index.html` 打开。

## 玩法（当前 Demo）

- **上下各 9×6（54 格）**，中间主城卡 HP **200**
- 开局双方 **20 金币**，主城四周 **4 张**可翻（类型与费用可见）
- **开局即战斗**：无回合概念，倒计时开始后双方同时翻牌，英雄实时自动互攻
- **⛑ 英雄**：低/中/高档（50/100/250 金）翻出不同品质；**前 3 局** 50 金低档可出传奇（5%）
- **◆ 资源**：立即获得金币
- **? 神秘**：随机英雄 / 资源 / 小量金币
- 英雄**自动攻击**（双方规则相同）：先消灭对方场上全部攻击卡牌，之后才可攻击主城
- **胜利**：主城 HP 归零，或 **3 分钟**倒计时结束且己方击杀数更多
