 (function(){
 'use strict';
 class BootScene{
     constructor(game){
         this.game=game;
         this._images=[];
     }
     _generatePokerList(){
         const suits=['hearts','diamonds','spades','clubs'];
         const ranks=['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
         const list=[];
         suits.forEach(s=>{
             ranks.forEach(r=>{
                 const prefix=(s==='clubs'&&r==='3')?'P':'p';
                 list.push(`assets/images/poker/${prefix}-${s}-${r}.png`);
             });
         });
         return list;
     }
     _defaultAssets(){
         const ui=[
             'assets/images/ui/icon-money.png',
         ];
         const backgrounds=[
             'assets/images/backgrounds/bg-login.png',
             'assets/images/backgrounds/bg-gameselected.jpg'
         ];
         return [...ui,...backgrounds,...this._generatePokerList()];
     }
     load(assets,progressCb){
         const list=assets&&assets.length>0?assets:this._defaultAssets();
         const total=list.length;
         let loaded=0;
         return new Promise(resolve=>{
             if(total===0){resolve();return;}
             const bar=document.getElementById('splash-progress');
             const update=()=>{
                 loaded++;
                 const p=Math.min(100,Math.floor(loaded*100/total));
                 if(bar)bar.style.width=`${p}%`;
                 if(typeof progressCb==='function')progressCb(p,loaded,total);
                 if(loaded>=total)resolve();
             };
             list.forEach(src=>{
                 const img=new Image();
                 this._images.push(img);
                 img.onload=update;
                 img.onerror=update;
                 img.src=src;
             });
         });
     }
     destroy(){
         this._images.forEach(i=>{i.onload=null;i.onerror=null;});
         this._images=[];
     }
 }
 window.BootScene=BootScene;
 })();
 
