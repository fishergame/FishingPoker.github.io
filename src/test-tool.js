/**
 * 测试工具 - 独立文件，可随时注释掉 index.html 中的引入来隐藏入口
 * 引入方式: <script src="src/test-tool.js"></script>（放在主脚本之后）
 */
(function () {
    'use strict';

    // 等待 game 实例就绪
    function waitForGame(cb) {
        if (window.game) { cb(window.game); return; }
        const t = setInterval(function () {
            if (window.game) { clearInterval(t); cb(window.game); }
        }, 100);
    }

    // 挑战场配置（同 3-3 关卡）
    const TEST_CHALLENGE_CFG = {
        id: 'test-challenge',
        floor: 3, step: 3,
        target: 'best_of_3',
        gold: 0, rounds: 3,
        openHand: false,   // 明牌由 startRound hook 实现
        name: '3-3 挑战场',
        challenge: true,
        bossName: '金瞳徒',
        bossText: '金币闪光时，便是你失明之刻。',
        rewardGold: 2000,
        skipGold: 300
    };

    function initTestTool(game) {
        var isTestMode = false;

        // ─── 1. 大厅按钮 ─────────────────────────────────────────────
        function addLobbyBtn() {
            if (document.getElementById('test-mode-btn')) return;
            var lobby = document.getElementById('lobby-screen');
            if (!lobby) return;
            var btn = document.createElement('button');
            btn.id = 'test-mode-btn';
            btn.style.cssText = [
                'position:absolute',
                'right:30px',
                'bottom:30px',
                'padding:6px 10px',
                'font-size:13px',
                'z-index:9999',
                'cursor:pointer',
                'border:none',
                'background:none',
                'color:rgba(255,255,255,0.55)',
                'font-weight:bold',
                'letter-spacing:2px',
                'font-family:"SimHei",sans-serif'
            ].join(';');
            btn.textContent = '测试';
            btn.onclick = enterTestShop;
            lobby.appendChild(btn);
        }

        // ─── 2. 进入测试商店 ─────────────────────────────────────────
        // fromBattle=true 表示从关卡结算/失败后回商店，不重置装备
        function enterTestShop(fromBattle) {
            isTestMode = true;
            game.isTestMode = true;

            if (!fromBattle) {
                // 首次进入：重置全局状态，设置测试槽位
                game.resetGlobal();
            }
            // 无论首次还是回来，都保持测试槽位和金币
            game.maxPassiveSlots = 8;
            game.maxSkillSlots = 5;
            game.playerGold = 99999;
            game.inGame = false;
            // config 设一个安全默认值（避免 renderShopHome 里读 this.config.floor 报错）
            game.config = { floor: 1, step: 1, id: 'test', target: 'best_of_3', rounds: 3, openHand: true, name: '测试' };

            // 关闭 lobby-screen（从大厅首次进入时它是显示的）
            document.getElementById('lobby-screen').style.display = 'none';

            // 展示全部道具，价格全 0
            var allItems = REWARD_POOL.map(function (item) {
                return Object.assign({}, item, {
                    price: 0,
                    _purchased: false,
                    _uid: 'test_' + item.id + '_' + Math.random().toString(36).slice(2)
                });
            });
            
            // 如果刚从挑战场胜利归来，把奖励提到最前面
            if (game.config && game.config.challenge && game._challengeWon && game._challengeRewardId) {
                var rItem = REWARD_POOL.find(function(x) { return x.id === game._challengeRewardId; });
                if (rItem && !game.ownedPassives.includes(rItem.id)) {
                    var freeRare = Object.assign({}, rItem, {
                        price: 0,
                        _purchased: false,
                        _uid: 'challenge_' + Date.now()
                    });
                    allItems.unshift(freeRare);
                }
                game._challengeRewardId = null;
                game._challengeWon = false;
            }
            
            game.shopDirectItems = allItems;
            // 不展示道具包
            game.availablePacks = [];

            // 打开商店 UI
            var ov = document.getElementById('overlay-screen');
            ov.innerHTML = '';
            ov.classList.add('visible');
            var modal = document.getElementById('shop-screen');
            modal.style.display = 'flex';
            setTimeout(function () { modal.classList.add('shop-visible'); }, 50);
            game.audio && game.audio.playShopOpenSound && game.audio.playShopOpenSound();
            game.setOverlayState(true);

            game.switchShopTab('shop');
            game.renderEquipCircle();

            // 替换底部按钮
            injectShopButtons();
        }

        function injectShopButtons() {
            setTimeout(function () {
                var shopNextBtn = document.getElementById('shop-next-btn');
                if (!shopNextBtn) return;

                // 克隆节点去掉原有事件
                var newNext = shopNextBtn.cloneNode(false);
                newNext.id = 'shop-next-btn';
                newNext.className = shopNextBtn.className;
                newNext.style.cssText = shopNextBtn.style.cssText;
                newNext.textContent = '进入测试';
                newNext.onclick = showTestLevelPicker;
                shopNextBtn.parentNode.replaceChild(newNext, shopNextBtn);

                // 返回大厅按钮
                var existReturn = document.getElementById('test-return-lobby-btn');
                if (!existReturn) {
                    var retBtn = document.createElement('button');
                    retBtn.id = 'test-return-lobby-btn';
                    retBtn.className = 'btn';
                    retBtn.style.cssText = 'width:240px;padding:10px;margin-top:8px;border:1px solid #555;color:#aaa;';
                    retBtn.textContent = '返回大厅';
                    retBtn.onclick = backToLobby;
                    newNext.parentNode.insertBefore(retBtn, newNext.nextSibling);
                }
            }, 80);
        }

        function backToLobby() {
            isTestMode = false;
            game.isTestMode = false;
            // 关闭商店 UI（不走 leaveShop 避免 levelIndex++ / showMap 副作用）
            var shopModal = document.getElementById('shop-screen');
            shopModal.classList.remove('shop-visible');
            setTimeout(function () {
                shopModal.style.display = 'none';
                document.getElementById('overlay-screen').classList.remove('visible');
                game.setOverlayState(false);
                if (game.setGameplayMode) game.setGameplayMode(false);
                else document.body.classList.remove('gameplay-mode');
                // 回大厅
                game.resetGlobal();
                document.getElementById('lobby-screen').style.display = 'flex';
                document.getElementById('map-screen').style.display = 'none';
                document.getElementById('header-left-col').classList.add('lobby-hide');
                document.getElementById('header-right-col').classList.add('lobby-hide');
                var continueBtn = document.getElementById('btn-continue');
                if (continueBtn) continueBtn.style.display = (localStorage.getItem('fishingPokerSave_v3_8_2') || localStorage.getItem('fishingPokerSave_v3_7_5')) ? 'block' : 'none';
                game.inGame = false;
            }, 300);
        }

        // ─── 3. 关卡选择面板 ─────────────────────────────────────────
        function showTestLevelPicker() {
            // 先关商店
            var shopModal = document.getElementById('shop-screen');
            shopModal.classList.remove('shop-visible');
            setTimeout(function () { shopModal.style.display = 'none'; }, 300);

            var ov = document.getElementById('overlay-screen');
            ov.innerHTML = '';
            ov.classList.add('visible');

            var wrap = document.createElement('div');
            wrap.style.cssText = [
                'background:linear-gradient(180deg,#1e293b 0%,#0f172a 100%)',
                'border:2px solid var(--highlight)',
                'border-radius:16px',
                'padding:36px 32px',
                'max-width:380px',
                'width:90%',
                'display:flex',
                'flex-direction:column',
                'gap:16px',
                'text-align:center',
                'box-shadow:0 0 40px rgba(0,242,255,0.25)'
            ].join(';');

            var title = document.createElement('div');
            title.style.cssText = 'font-size:20px;font-weight:900;color:var(--highlight);letter-spacing:2px;margin-bottom:4px;';
            title.textContent = '选择测试关卡';
            wrap.appendChild(title);

            var sub = document.createElement('div');
            sub.style.cssText = 'font-size:12px;color:#64748b;margin-bottom:8px;';
            sub.textContent = '对局中玄机次数无限，对手手牌全部明牌';
            wrap.appendChild(sub);

            // 胜负场：用 accumulate + gold:0，任何积分即通关（1回合结束就判定）
            wrap.appendChild(makePickerBtn('胜负场（1 局定胜负）', '#00f2ff', function () {
                startTestLevel({
                    id: 'test-best1', floor: 1, step: 1,
                    target: 'accumulate', gold: 0, rounds: 1,
                    openHand: true, name: '测试胜负场'
                });
            }));

            // 积分场
            wrap.appendChild(makePickerBtn('积分场（目标 100 分）', '#10b981', function () {
                startTestLevel({
                    id: 'test-score', floor: 1, step: 2,
                    target: 'accumulate', gold: 100, rounds: 3,
                    openHand: true, name: '测试积分场'
                });
            }));

            // 挑战场
            var challengeBtn = makePickerBtn('挑战场（同 3-3 关卡）', '#f97316', function () {
                showTestChallengeConfirm(ov);
            });
            wrap.appendChild(challengeBtn);

            // 返回商城
            var backBtn = document.createElement('button');
            backBtn.style.cssText = 'padding:12px;border:1px solid #334155;border-radius:10px;background:transparent;color:#94a3b8;font-size:14px;cursor:pointer;margin-top:4px;font-family:"SimHei",sans-serif;';
            backBtn.textContent = '← 返回商城';
            backBtn.onclick = enterTestShop;
            wrap.appendChild(backBtn);

            ov.appendChild(wrap);
        }

        function makePickerBtn(label, color, onClick) {
            var btn = document.createElement('button');
            btn.style.cssText = [
                'padding:14px 0',
                'border:2px solid ' + color,
                'border-radius:10px',
                'background:rgba(0,0,0,0.3)',
                'color:' + color,
                'font-size:15px',
                'font-weight:bold',
                'cursor:pointer',
                'font-family:"SimHei",sans-serif',
                'letter-spacing:1px',
                'transition:background 0.15s'
            ].join(';');
            btn.textContent = label;
            btn.onmouseenter = function () { btn.style.background = 'rgba(255,255,255,0.07)'; };
            btn.onmouseleave = function () { btn.style.background = 'rgba(0,0,0,0.3)'; };
            btn.onclick = onClick;
            return btn;
        }

        // ─── 4. 挑战场确认弹窗（复用 showChallengeConfirm 逻辑）────────
        function showTestChallengeConfirm(ov) {
            ov.innerHTML = '';
            var cfg = TEST_CHALLENGE_CFG;
            // 复用游戏原有的挑战确认弹窗渲染
            game.config = cfg;
            // 让 showChallengeConfirm 调用原逻辑，但我们需要替换它的两个按钮回调
            // 所以先把 startChallenge / skipChallenge 临时替换
            var origStart = game.startChallenge;
            var origSkip = game.skipChallenge;

            game.startChallenge = function () {
                // 恢复
                game.startChallenge = origStart;
                game.skipChallenge = origSkip;
                document.getElementById('overlay-screen').classList.remove('visible');
                game.setOverlayState(false);
                startTestLevel(cfg);
            };
            game.skipChallenge = function (skipGold) {
                game.startChallenge = origStart;
                game.skipChallenge = origSkip;
                document.getElementById('overlay-screen').classList.remove('visible');
                game.setOverlayState(false);
                // 跳过挑战：直接回商店
                enterTestShop();
            };

            game.showChallengeConfirm(cfg);
        }

        // ─── 5. 开始测试关卡 ─────────────────────────────────────────
        function startTestLevel(cfg) {
            // 清理 overlay
            var ov = document.getElementById('overlay-screen');
            ov.innerHTML = '';
            ov.classList.remove('visible');
            game.setOverlayState(false);

            // 将测试 config 注入到 LEVEL_CONFIG（若已存在则替换，否则 push）
            var existIdx = LEVEL_CONFIG.findIndex(function (l) { return l.id === cfg.id; });
            if (existIdx >= 0) {
                LEVEL_CONFIG[existIdx] = cfg;
                game.levelIndex = existIdx;
            } else {
                LEVEL_CONFIG.push(cfg);
                game.levelIndex = LEVEL_CONFIG.length - 1;
            }

            // 必须隐藏 lobby-screen，否则它的 z-index:200 会遮住游戏界面
            document.getElementById('lobby-screen').style.display = 'none';
            // 隐藏地图
            var mapScreen = document.getElementById('map-screen');
            if (mapScreen) mapScreen.style.display = 'none';

            // 直接走 startLevel()，它会读 LEVEL_CONFIG[levelIndex]
            game.startLevel();
        }

        // ─── 6. 对局内覆盖：玄机无限 + 明牌 ──────────────────────────
        function applyInGameOverrides() {
            if (!game.isTestMode) return;
            // 玄机使用次数设为 999
            if (game.skillUsage['xuanji'] !== undefined) {
                game.skillUsage['xuanji'] = 999;
            }
            game.skillMaxModifiers['xuanji'] = 996; // 确保下回合重置后也够用

            // 对手明牌：强制 config.openHand = true，renderScene 里会用这个标志
            game.config.openHand = true;
        }

        // ─── 7. hook startRound，每回合都重新应用覆盖 ────────────────
        var origStartRound = game.startRound.bind(game);
        game.startRound = function () {
            origStartRound();
            if (game.isTestMode) {
                applyInGameOverrides();
            }
        };

        // ─── 8. hook showSettlePanel：最终结算后替换按钮 ─────────────
        var origShowSettle = game.showSettlePanel.bind(game);
        game.showSettlePanel = function (win, myRes, aiRes, gold, myCards, aiCards, mySrc, aiSrc, fish, isEnd, failMsg, levelVal) {
            if (game.isTestMode && isEnd && win) {
                // 临时插入一个假关卡在末尾，让 levelIndex 不等于 LEVEL_CONFIG.length-1
                // 防止触发"无尽塔楼挑战成功"彩蛋结局
                var fakeIdx = LEVEL_CONFIG.length;
                LEVEL_CONFIG.push({ id: '_test_fake_end_', floor: 99, step: 1 });
                origShowSettle(win, myRes, aiRes, gold, myCards, aiCards, mySrc, aiSrc, fish, isEnd, failMsg, levelVal);
                // 还原：移除假关卡
                LEVEL_CONFIG.splice(fakeIdx, 1);
            } else {
                origShowSettle(win, myRes, aiRes, gold, myCards, aiCards, mySrc, aiSrc, fish, isEnd, failMsg, levelVal);
            }
            if (game.isTestMode && isEnd) {
                // 延迟后替换"前往道具商店"按钮为"返回测试商店"
                setTimeout(function () {
                    var ov = document.getElementById('overlay-screen');
                    if (!ov) return;
                    var allBtns = ov.querySelectorAll('button');
                    allBtns.forEach(function (btn) {
                        var oc = btn.getAttribute('onclick') || '';
                        if (oc.indexOf('openShopInventory') >= 0 || oc.indexOf('nextRound') >= 0 || btn.textContent.indexOf('道具') >= 0 || btn.textContent.indexOf('奖励') >= 0) {
                            btn.textContent = '返回测试商店';
                            btn.removeAttribute('onclick');
                            btn.onclick = function () { enterTestShop(true); };
                        }
                    });
                }, 200);
            }
        };

        // ─── 9. hook showFailPanel：失败时替换按钮 ───────────────────
        var origShowFail = game.showFailPanel.bind(game);
        game.showFailPanel = function (myRes, aiRes, myCards, aiCards, reason, levelVal, roundWin) {
            origShowFail(myRes, aiRes, myCards, aiCards, reason, levelVal, roundWin);
            if (game.isTestMode) {
                setTimeout(function () {
                    var ov = document.getElementById('overlay-screen');
                    if (!ov) return;
                    var allBtns = ov.querySelectorAll('button');
                    allBtns.forEach(function (btn) {
                        var oc = btn.getAttribute('onclick') || '';
                        if (oc.indexOf('challengeFailNext') >= 0 || oc.indexOf('returnToLobby') >= 0 || btn.textContent.indexOf('下一关') >= 0 || btn.textContent.indexOf('大厅') >= 0) {
                            btn.textContent = '返回测试商店';
                            btn.removeAttribute('onclick');
                            btn.onclick = function () { enterTestShop(true); };
                        }
                    });
                }, 200);
            }
        };

        // ─── 10. hook challengeFailNext ──────────────────────────────
        var origChallengeFailNext = game.challengeFailNext.bind(game);
        game.challengeFailNext = function () {
            if (game.isTestMode) {
                document.getElementById('overlay-screen').classList.remove('visible');
                game.setOverlayState(false);
                game.inGame = false;
                enterTestShop(true);
            } else {
                origChallengeFailNext();
            }
        };

        // ─── 11. hook skipChallenge（挑战确认弹窗跳过）──────────────
        var origSkipChallenge = game.skipChallenge.bind(game);
        game.skipChallenge = function (skipGold) {
            if (game.isTestMode) {
                document.getElementById('overlay-screen').classList.remove('visible');
                game.setOverlayState(false);
                enterTestShop(true);
            } else {
                origSkipChallenge(skipGold);
            }
        };

        // ─── 12. hook leaveShop（普通结束商店跳关逻辑不走，回商店）──
        //  不 hook leaveShop，让"返回大厅"按钮自己调 backToLobby 即可

        // ─── 初始化 ─────────────────────────────────────────────────
        addLobbyBtn();
        console.log('[TestTool] 初始化完成，大厅左下角已添加「测试」按钮');
    }

    // 等待 DOM + game 就绪
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { waitForGame(initTestTool); });
    } else {
        waitForGame(initTestTool);
    }

})();
