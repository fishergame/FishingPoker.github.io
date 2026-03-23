 (function(){
 'use strict';
 class LobbyScene{
     constructor(game){
         this.game=game;
         this.el=document.getElementById('lobby-screen');
     }
     show(){
        if(this.game&&this.game.setGameplayMode)this.game.setGameplayMode(false);
         if(this.el)this.el.style.display='flex';
         const map=document.getElementById('map-screen');
         if(map)map.style.display='none';
         document.getElementById('header-left-col')?.classList.add('lobby-hide');
         document.getElementById('header-right-col')?.classList.add('lobby-hide');
        document.getElementById('gp-opp-hand-top')?.classList.add('lobby-hide');
        document.getElementById('gp-boss')?.classList.add('lobby-hide');
        document.getElementById('gp-skill-float')?.classList.add('lobby-hide');
         document.body.classList.add('lobby-mode');
     }
     hide(){
         if(this.el)this.el.style.display='none';
         document.body.classList.remove('lobby-mode');
     }
 }
 window.LobbyScene=LobbyScene;
 })();
 
