const LEVEL_CONFIG=[];
for(let floor=1;floor<=8;floor++){
    LEVEL_CONFIG.push({id:`${floor}-1`,floor:floor,step:1,target:'best_of_3',gold:0,rounds:3,openHand:false,name:'暗牌-3局2胜',desc:'3局2胜，回合牌型赢过对方即胜'});
    let bossGold=400*floor;if(floor===4)bossGold=4000;if(floor===5)bossGold=9000;if(floor===6)bossGold=22000;if(floor===7)bossGold=55000;if(floor===8)bossGold=108000;
    LEVEL_CONFIG.push({id:`${floor}-2`,floor:floor,step:2,target:'accumulate',gold:bossGold,rounds:3,openHand:false,name:'暗牌-积分挑战',desc:`3 回合内积分 ≥ x/${bossGold}`,boss:true});
}

const OPPONENT_PERSONAS={1:[{name:"雾隐客",text:"雾锁牌路，你连自己都看不清。"},{name:"影弈者",text:"你的手，早被我的影子握住了。"},{name:"无相司命",text:"命无定形，汝亦无胜机。"}],2:[{name:"荧惑使",text:"火星照命，此局血光已现。"},{name:"岁破徒",text:"破你布局，如折枯枝。"},{name:"北斗刑官",text:"七星落子，罪罚已定。"}],3:[{name:"梦缚师",text:"沉溺旧梦者，不配醒着赢。"},{name:"灵犀盗",text:"你的心意，我已偷来看透。"},{name:"忘川守痴",text:"执念太重？那就永留此岸。"}],4:[{name:"焰骰客",text:"赌得越大，烧得越干净。"},{name:"金瞳徒",text:"金币闪光时，便是你失明之刻。"},{name:"饕弈尊",text:"贪心不足？正好喂我棋腹。"}],5:[{name:"虚言使",text:"我说真话，但你信吗？"},{name:"回声客",text:"你上一步，已是我的伏笔。"},{name:"千面狐君",text:"猜猜这副面具下，是笑还是杀？"}],6:[{name:"幻潮师",text:"牌如潮涌，理智将沉。"},{name:"妄念徒",text:"你以为的胜算，只是幻觉。"},{name:"大妄天狐",text:"天地皆妄，唯我弈真。"}],7:[{name:"寂默客",text:"沉默，是你最后的声音。"},{name:"空痕使",text:"痕迹不留，胜败成空。"},{name:"归寂白狐",text:"放下胜负，或永陷虚无。"}],8:[{name:"心镜师",text:"照见你心底的破绽了。"},{name:"尾迹客",text:"九尾留痕，步步皆我预设。"},{name:"九尾弈心君",text:"八重试炼尽，可敢与我弈心？"}]};
const SKILLS_DB={xuanji:{name:'玄机',icon:'🌀',desc:'选择 1～5 张牌弃掉重抽',type:'round_limit',maxUses:3},yundu:{name:'云渡',icon:'☁️',desc:'选择 1 张牌与对方手牌随机交换',type:'consumable'},huanzhu:{name:'幻注',icon:'💸',desc:'选择比例下注（仅-2关卡可用）',extDesc:'选择比例下注（仅-2关卡可用）\n下注说明：\n（1）回合胜利：已下注金额返还，并获得等额积分奖励\n（2）回合失败：已下注金额将全部扣除',type:'once_per_round'},xinjing:{name:'心镜',icon:'🔮',desc:'提前查看对方诱饵牌',type:'consumable'},abyss:{name:'深渊之眼',icon:'👁️',desc:'查看对方手牌',type:'consumable'},mirror:{name:'镜界',icon:'🪞',desc:'复制对方手牌',type:'consumable'},blast:{name:'爆破',icon:'💥',desc:'选择 1 张牌与对方指定牌交换',type:'consumable'}};

const UPGRADE_MAP = {
    '单牌':{id:'fumo',mult:1.8},
    '对子':{id:'shuangli',mult:1.8},
    '两对':{id:'jinwei',mult:1.8},
    '三条':{id:'yuezhu',mult:2.0},
    '顺子':{id:'yousuo',mult:2.0},
    '同花':{id:'yixi',mult:1.8},
    '葫芦':{id:'cangjiao',mult:1.8},
    '四炸':{id:'baochao',mult:2.0},
    '同花顺':{id:'longyuan',mult:2.0}
};

const REWARD_POOL=[
{id:'guchen',weight:60,name:'孤辰',desc:'结算时牌型为单牌，获得牌型积分x2',type:'passive',icon:'🃏',trigger:'单牌',mult:1,price:30,unique:true},
{id:'shuangying',weight:60,name:'双影',desc:'结算时牌型为对子，获得牌型积分x2',type:'passive',icon:'♊',trigger:'对子',mult:1,price:30,unique:true},
{id:'sixiang',weight:60,name:'四象',desc:'结算时牌型为两对，获得牌型积分x2',type:'passive',icon:'🐘',trigger:'两对',mult:1,price:30,unique:true},
{id:'sanyuan',weight:60,name:'三垣',desc:'结算时牌型为三条，获得牌型积分x3',type:'passive',icon:'⭐',trigger:'三条',mult:2,price:30,unique:true},
{id:'lianchao',weight:60,name:'连潮',desc:'结算时牌型为顺子，获得牌型积分x3',type:'passive',icon:'🌊',trigger:'顺子',mult:2,price:30,unique:true},
{id:'yise',weight:60,name:'一色',desc:'结算时牌型为同花，获得牌型积分x3',type:'passive',icon:'🎨',trigger:'同花',mult:2,price:30,unique:true},
{id:'fulu',weight:60,name:'福禄',desc:'结算时牌型为葫芦，获得牌型积分x4',type:'passive',icon:'🏺',trigger:'葫芦',mult:3,price:30,unique:true},
{id:'siji',weight:60,name:'四极',desc:'结算时牌型为四炸，获得牌型积分x4',type:'passive',icon:'⚡',trigger:'四炸',mult:3,price:30,unique:true},
{id:'tianlv',weight:60,name:'天律',desc:'结算时牌型为同花顺，获得牌型积分x5',type:'passive',icon:'📜',trigger:'同花顺',mult:4,price:30,unique:true},
{id:'yundu',weight:20,name:'云渡',desc:'选择 1 张牌与对方手牌随机交换',type:'item_active',ref:'yundu',unique:false,icon:'☁️',price:50},
{id:'huanzhu',weight:20,name:'幻注',desc:'选择比例下注（仅-2关卡可用）',type:'item_active',ref:'huanzhu',unique:true,icon:'💸',price:200},
{id:'xinjing',weight:20,name:'心镜',desc:'提前查看对方诱饵牌',type:'item_active',ref:'xinjing',unique:false,icon:'🔮',price:50},
{id:'abyss',weight:20,name:'深渊之眼',desc:'查看对方手牌',type:'item_active',ref:'abyss',unique:false,icon:'👁️',price:50},
{id:'mirror',weight:20,name:'镜界',desc:'复制对方手牌',type:'item_active',ref:'mirror',unique:false,icon:'🪞',price:50},
{id:'blast',weight:20,name:'爆破',desc:'选择 1 张牌与对方指定牌交换',type:'item_active',ref:'blast',unique:false,icon:'💥',price:50},
{id:'xuanshu',weight:10,name:'玄枢',desc:'【玄机】使用次数+1',type:'secret',icon:'🆙',effect:'add_xuanji',getPrice:(g)=>g.upgradeCounts.xuanshu?100:50},
{id:'huance',weight:10,name:'幻策',desc:'【幻注】下注比例+10%',type:'secret',icon:'💹',effect:'boost_bet',getPrice:(g)=>g.upgradeCounts.huance?100:50},
{id:'xinyu',weight:5,name:'心屿',desc:'技能槽位数+1',type:'secret',icon:'🧩',effect:'add_slot',getPrice:(g)=>g.upgradeCounts.xinyu?100:50},
{id:'xunang',weight:5,name:'虚囊',desc:'普通道具槽位数+1',type:'secret',icon:'👝',effect:'add_passive_slot',getPrice:(g)=>((g.upgradeCounts.xunang||0)+1)*200},
{id:'yunyan',weight:10,name:'云衍',desc:'【云渡】使用次数+1',type:'secret',icon:'☁️',effect:'add_yundu',getPrice:(g)=>g.upgradeCounts.yunyan?100:50},
{id:'heishi',weight:10,name:'黑石',desc:'选择1～2张牌，将花色变为黑桃',type:'secret',icon:'🪨',price:100,unique:false},
{id:'hongguo',weight:10,name:'红果',desc:'选择1～2张牌，将花色变为红心',type:'secret',icon:'🍎',price:100,unique:false},
{id:'mianju',weight:10,name:'面具',desc:'选择1～2张牌，变为人头牌',type:'secret',icon:'🎭',price:100,unique:false},
{id:'xiangpini',weight:10,name:'橡皮泥',desc:'选择1张牌，变为万能牌',type:'secret',icon:'🧱',price:100,unique:false},
{id:'xuyuanxing',weight:10,name:'许愿星',desc:'选择1张牌，变为特殊奖励牌',type:'secret',icon:'🌟',price:100,unique:false},
{id:'shuangshenglian',weight:10,name:'双生莲',desc:'选择2张牌，复制出同样的牌加入牌组',type:'secret',icon:'🪷',price:100,unique:false},
{id:'paomo',weight:20,name:'泡沫商城',desc:'商城所有物品 5 折出售',type:'secret',icon:'🫧',price:200,unique:true},
{id:'huojia',weight:10,name:'货架',desc:'商城道具+1',type:'secret',icon:'🗄️',price:200,unique:true},
{id:'dalibao',weight:10,name:'大礼包',desc:'商城道具包+1',type:'secret',icon:'🎁',price:200,unique:true},
{id:'jihaobi',weight:10,name:'记号笔',desc:'选择1张牌，将其变为积分牌，积分+500',type:'secret',icon:'🖍️',price:100,unique:false},
{id:'dayinji',weight:10,name:'打印机',desc:'选择1张背包中的普通道具牌，复制并获得该牌',type:'secret',icon:'🖨️',price:200,unique:false},
{id:'fumo',weight:10,name:'浮沫',desc:'升级单牌，牌型积分x1.8',type:'upgrade',icon:'🫧',price:200,unique:false},
{id:'shuangli',weight:10,name:'双鲤',desc:'升级对子，牌型积分x1.8',type:'upgrade',icon:'🎏',price:200,unique:false},
{id:'jinwei',weight:10,name:'锦尾',desc:'升级两对，牌型积分x1.8',type:'upgrade',icon:'🐠',price:200,unique:false},
{id:'yuezhu',weight:10,name:'跃珠',desc:'升级三条，牌型积分x2.0',type:'upgrade',icon:'🔮',price:200,unique:false},
{id:'yousuo',weight:10,name:'游梭',desc:'升级顺子，牌型积分x2.0',type:'upgrade',icon:'🛶',price:200,unique:false},
{id:'yixi',weight:10,name:'一汐',desc:'升级同花，牌型积分x1.8',type:'upgrade',icon:'🌊',price:200,unique:false},
{id:'cangjiao',weight:10,name:'藏鲛',desc:'升级葫芦，牌型积分x1.8',type:'upgrade',icon:'🧜',price:200,unique:false},
{id:'baochao',weight:10,name:'爆潮',desc:'升级四炸，牌型积分x2.0',type:'upgrade',icon:'💥',price:200,unique:false},
{id:'longyuan',weight:10,name:'龙渊',desc:'升级同花顺，牌型积分x2.0',type:'upgrade',icon:'🐉',price:200,unique:false},
{id:'yangyao',weight:20,name:'阳爻',desc:'结算时牌型包含奇数 （1、3、5、7、9），获得牌型积分 x每1张牌数',type:'passive',icon:'🔆',trigger:'odd',unique:true,price:100},
{id:'yinyao',weight:20,name:'阴爻',desc:'结算时牌型包含偶数（2、4、6、8、10），获得牌型积分 x每1张牌数',type:'passive',icon:'🌑',trigger:'even',unique:true,price:100},
{id:'qishi',weight:20,name:'骑士',desc:'结算时牌型包含人头牌（J、Q、K)，每 1 张可获得牌型积分 x5',type:'passive',icon:'🛡️',trigger:'face',unique:true,price:50},
{id:'fishhook',weight:20,name:'黄金鱼钩',desc:'钓鱼成功，倍数+1',type:'passive',icon:'🪝',trigger:'fishhook',unique:true,price:50},
{id:'haixing',weight:20,name:'海星',desc:'结算时牌型包含"红桃 A"，额外获得 200 金币',type:'passive',icon:'⭐',trigger:'haixing',unique:true,price:50},
{id:'hailuo',weight:20,name:'海螺',desc:'结算时牌型包含"梅花"花色，有 1/2概率获得 1000 积分',type:'passive',icon:'🐚',trigger:'hailuo',unique:true,price:100},
{id:'shanhu',weight:20,name:'珊瑚',desc:'结算时牌型包含“黑桃”花色，有 1/3概率获得 200 金币',type:'passive',icon:'🪸',trigger:'shanhu',unique:true,price:100},
{id:'jiangliu',weight:20,name:'江流',desc:'结算时获得 50 金币，此后每次多加 50金币',type:'passive',icon:'🌊',trigger:'jiangliu',unique:true,price:100},
{id:'langhua',weight:20,name:'浪花',desc:'结算时牌型包含"红桃 6、红桃 8"，额外获得 500 金币',type:'passive',icon:'💦',trigger:'langhua',unique:true,price:100},
{id:'chaoxi',weight:20,name:'潮汐',desc:'每回合结束有 1/2 概率获得 1000 积分',type:'passive',icon:'🌙',trigger:'chaoxi',unique:true,price:100},
{id:'fuping',weight:20,name:'浮萍',desc:'每回合结束获得 100 金币',type:'passive',icon:'🍃',trigger:'fuping',unique:true,price:100},
{id:'xuanwo',weight:20,name:'漩涡',desc:'【幻注】下注比例各提升 10%',type:'passive',icon:'🌪️',trigger:'xuanwo',unique:true,price:100},
{id:'jiaoshi',weight:20,name:'礁石',desc:'结算时获得 200 积分，此后每次多加 100积分',type:'passive',icon:'🪨',trigger:'jiaoshi',unique:true,price:100},
{id:'haikui',weight:20,name:'海葵',desc:'手牌+1张，玄机使用次数-1',type:'passive',icon:'🪼',trigger:'haikui',unique:true,price:100},
{id:'zhenzhu',weight:20,name:'珍珠',desc:'打出的诱饵牌为对子，胜利结算时+100 金币',type:'passive',icon:'⚪',trigger:'zhenzhu',unique:true,price:100},
{id:'shali',weight:20,name:'免费券',desc:'每次通关在商城中获得 1 张随机免费的升级牌',type:'passive',icon:'🎟️',trigger:'shali',unique:true,price:100},
{id:'yuqun',weight:20,name:'鱼群',desc:'结算时额外获得牌型数字总和 x50 积分',type:'passive',icon:'🐟',trigger:'yuqun',unique:true,price:100},
{id:'riyao',weight:20,name:'日爻',desc:'结算时牌型包含奇数 （1、3、5、7、9），获得牌型积分 x3',type:'passive',icon:'🌞',trigger:'odd_5x',unique:true,price:50},
{id:'yueyao',weight:20,name:'月爻',desc:'结算时牌型包含偶数（2、4、6、8、10），获得牌型积分 x2.5',type:'passive',icon:'🌜',trigger:'even_5x',unique:true,price:50},
{id:'hongsewangzuo',weight:20,name:'红色王座',desc:'结算时牌型为同花，且包含人头牌（J、Q、K)，获得牌型积分 x3.5',type:'passive',icon:'🪑',trigger:'flush_face_3.5x',unique:true,price:50},
{id:'yinsewangzuo',weight:20,name:'银色王座',desc:'结算时牌型为顺子，且包含人头牌（J、Q、K)，获得牌型积分 x4',type:'passive',icon:'💺',trigger:'straight_face_4x',unique:true,price:50}
];

const HAND_TYPES_BASE=[{name:'同花顺',en:'Straight Flush',base:300,level:9},{name:'四炸',en:'Four of a Kind',base:200,level:8},{name:'葫芦',en:'Full House',base:160,level:7},{name:'同花',en:'Flush',base:120,level:6},{name:'顺子',en:'Straight',base:90,level:5},{name:'三条',en:'Three of a Kind',base:60,level:4},{name:'两对',en:'Two Pair',base:40,level:3},{name:'对子',en:'Pair',base:20,level:2},{name:'单牌',en:'High Card',base:10,level:1}];
const SUITS=['♠','♥','♣','♦'];
const RANKS=['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
const RANK_VALUES={'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14};
const SUIT_VALS={'♠':4,'♥':3,'♦':2,'♣':1};