 (function(){
 'use strict';
 class ResultScene{
     constructor(game){
         this.game=game;
     }
     show(){
         const ov=document.getElementById('overlay-screen');
         if(ov){ov.classList.add('visible');this.game&&this.game.setOverlayState&&this.game.setOverlayState(true);}
     }
     hide(){
         const ov=document.getElementById('overlay-screen');
         if(ov){ov.classList.remove('visible');this.game&&this.game.setOverlayState&&this.game.setOverlayState(false);}
     }
 }
 window.ResultScene=ResultScene;
 })();
 
