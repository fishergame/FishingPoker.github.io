 (function(){
 'use strict';
 class LevelSelectScene{
     constructor(game){
         this.game=game;
         this.el=document.getElementById('map-screen');
     }
     show(){
         if(this.el)this.el.style.display='flex';
         const lobby=document.getElementById('lobby-screen');
         if(lobby)lobby.style.display='none';
         document.getElementById('header-left-col')?.classList.add('lobby-hide');
         document.getElementById('header-right-col')?.classList.add('lobby-hide');
         document.body.classList.remove('lobby-mode');
     }
     hide(){
         if(this.el)this.el.style.display='none';
     }
 }
 window.LevelSelectScene=LevelSelectScene;
 })();
 
