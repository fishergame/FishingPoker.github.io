 (function(){
 'use strict';
 class GameplayScene{
     constructor(game){
         this.game=game;
         this.el=document.getElementById('main-stage');
     }
     show(){
        if(this.game&&this.game.setGameplayMode)this.game.setGameplayMode(true);
         const map=document.getElementById('map-screen');
         if(map)map.style.display='none';
         const lobby=document.getElementById('lobby-screen');
         if(lobby)lobby.style.display='none';
        const gfc=document.getElementById('game-func-controls'); if(gfc) gfc.style.display='flex';
         document.getElementById('header-left-col')?.classList.remove('lobby-hide');
         document.getElementById('header-right-col')?.classList.remove('lobby-hide');
        document.getElementById('gp-opp-hand-top')?.classList.remove('lobby-hide');
        document.getElementById('gp-boss')?.classList.remove('lobby-hide');
        document.getElementById('gp-skill-float')?.classList.remove('lobby-hide');
         document.getElementById('info-screen')?.classList.remove('visible');
     }
     hide(){
         const ov=document.getElementById('overlay-screen');
         if(ov)ov.classList.remove('visible');
     }
 }
 window.GameplayScene=GameplayScene;
 })();
 
