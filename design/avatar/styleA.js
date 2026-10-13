/* Style A v2 : « Héros » — stylisé, volumes par dégradés, peu de traits, silhouette en V (6,8 têtes) */
(function(){
var C=AVC, cr=C.cr, both=C.both, tube=C.tube, ell=C.ell, circ=C.circ, path=C.path, line=C.line, hsl=C.hsl;
var CX=120;
var SEX={
 m:{sh:64,chest:48,waist:33,hip:40,nW:13.5,arm:17,fa:12.5,wr:7.5,thigh:25,calf:16.5,jaw:1,bust:0},
 f:{sh:50,chest:39,waist:28,hip:47,nW:10.5,arm:13,fa:10,wr:6.2,thigh:26.5,calf:14.5,jaw:0,bust:1}
};
function pts(arr){return arr.map(function(p){return [CX+p[0],p[1]]})}
function render(o){
  var s=SEX[o.sex||'m'], m=o.muscle==null?.5:o.muscle, sk=C.skinPal(o.skin||[24,50,64]), isF=o.sex==='f', u=o.uid||'a', out='';
  var sh=s.sh+m*(isF?2:6), ch=s.chest+m*(isF?1:4.5), wa=s.waist, hp=s.hip, bu=s.bust;
  function lg(id,c,a,b){ // volume : clair à gauche -> sombre à droite (par forme)
    return '<linearGradient id="'+id+u+'" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="'+hsl(c[0],c[1],c[2]+(a||10))+'"/><stop offset=".42" stop-color="'+hsl(c[0],c[1],c[2])+'"/><stop offset="1" stop-color="'+hsl(c[0]-3,c[1]+5,c[2]-(b||15))+'"/></linearGradient>';
  }
  var defs='<defs>'+lg('sk',o.skin,9,13)+lg('cl',o.cl,9,16)+lg('sh',o.sh2,7,12)+lg('sn',o.sn,10,10)+lg('ac',o.ac,10,12)
   +'<radialGradient id="fl'+u+'" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="rgba(0,0,0,.30)"/><stop offset="1" stop-color="rgba(0,0,0,0)"/></radialGradient></defs>';
  var G='url(#sk'+u+')', CL='url(#cl'+u+')', SH='url(#sh'+u+')', SN='url(#sn'+u+')', AC='url(#ac'+u+')';
  var hc=o.hairCol||[24,40,20], H0=hsl(hc[0],hc[1],hc[2]), H1=hsl(hc[0],hc[1]+2,hc[2]+16), H2=hsl(hc[0],hc[1]+4,hc[2]-9), hy=40, hair=o.hair;
  var A=.28+m*.5, dl=sk.deep;
  function ln(d,op,w){out+=line(d,dl,w||1.6,' opacity="'+(op==null?A:op)+'"')}
  function hi(d,op){out+=path(d,sk.hi,' opacity="'+op+'"')}
  out+=ell(CX,392,74,9,'url(#fl'+u+')');
  // cheveux arrière
  if(hair==='long') out+=path(cr(pts([[0,hy-26],[26,hy-18],[34,hy+14],[37,hy+60],[40,hy+98],[28,hy+108],[0,hy+102],[-28,hy+108],[-40,hy+98],[-37,hy+60],[-34,hy+14],[-26,hy-18]]),true),H2);
  if(hair==='ponytail') out+=path(cr(pts([[16,hy-22],[36,hy-14],[50,hy+14],[50,hy+54],[42,hy+92],[32,hy+66],[34,hy+30],[24,hy-2]]),true),H2);
  if(hair==='curly') out+=circ(CX,hy-12,36,H2)+circ(CX-28,hy+2,18,H2)+circ(CX+28,hy+2,18,H2);
  // bras
  var arm=s.arm+m*(isF?1.2:3.6), fa=s.fa+m*(isF?.4:1.2), wr=s.wr;
  var HIP=o.pose==='hips';
  function armJ(sg){ if(HIP) return [[CX+sg*(sh-10),101],[CX+sg*(sh+1),122],[CX+sg*(sh+14),148],[CX+sg*(sh+8),172],[CX+sg*(wa+13),196],[CX+sg*(wa+9),203]];
    return [[CX+sg*(sh-10),101],[CX+sg*(sh-6),133],[CX+sg*(sh-3),160],[CX+sg*(sh),194],[CX+sg*(sh+2),224],[CX+sg*(sh+3),240]];}
  var armR=HIP?[arm+2,arm+1+m*1.5,arm-1,fa+1.2,wr+1.8,wr+.6]:[arm+2,arm+1+m*1.5,arm-2.2,fa+1.2,wr+1.4,wr-.4];
  [-1,1].forEach(function(sg){
    var j=armJ(sg); out+=path(cr(tube(j,armR,.6),true),G);
    var e=j[5]; if(!HIP) {out+=ell(e[0],e[1]+9,wr+2.6,12.5,G);
    out+=path(cr([[e[0]+sg*(-3),e[1]+5],[e[0]-sg*(wr+4),e[1]+13],[e[0]-sg*(wr+2.4),e[1]+20],[e[0]-sg*(wr-2),e[1]+16]],true),G);}
  });
  // jambes
  var th=s.thigh+m*(isF?1.4:3.2);
  function legJ(sg){return [[CX+sg*17,238],[CX+sg*24,274],[CX+sg*25,308],[CX+sg*26,338],[CX+sg*22,374]];}
  var legR=[th+1,th-1+m*1.2,s.calf+1,s.calf+2.2+m*(isF?.8:2.2),7.6];
  [-1,1].forEach(function(sg){out+=path(cr(tube(legJ(sg),legR,.4),true),G);});
  // torse
  out+=path(cr([[CX-s.nW,62],[CX+s.nW,62],[CX+s.nW+2,90],[CX-s.nW-2,90]],true),G);
  out+=ell(CX,hy+31,s.nW+2,7,sk.lo,' opacity=".38"');
  var tw=[[s.nW,82],[s.nW+14,88],[sh-13,91],[sh-2,100],[sh-1,112],[ch+3,128],[ch+bu*4,142],[wa+5,160],[wa,178],[wa+3,206],[hp+3,226],[hp-6,242],[2,248]];
  out+=path(cr(both(pts(tw),CX),true),G);
  // anatomie légère
  if(!isF){
    var pc=ch-5;
    ln('M'+CX+',103L'+CX+',134',A*.8);
    ln('M'+(CX-3)+',136Q'+(CX-pc*.5)+',143 '+(CX-pc+3)+',124',A*1.05,2);ln('M'+(CX+3)+',136Q'+(CX+pc*.5)+',143 '+(CX+pc-3)+',124',A*1.05,2);
    hi('M'+(CX-6)+',110Q'+(CX-22)+',107 '+(CX-pc+7)+',117Q'+(CX-24)+',122 '+(CX-6)+',123Z',.2*(.5+m));
    ln('M'+(CX-8)+',92Q'+(CX-24)+',93 '+(CX-sh+16)+',99',A*.7,1.4);ln('M'+(CX+8)+',92Q'+(CX+24)+',93 '+(CX+sh-16)+',99',A*.7,1.4);
    ln('M'+CX+',146L'+CX+',200',A*.75,1.4);
    [[154,12],[169,11.5],[184,10.5]].forEach(function(r){ln('M'+(CX-r[1])+','+r[0]+'Q'+(CX-r[1]/2)+','+(r[0]+3)+' '+(CX-2)+','+r[0],A*.9,1.6);ln('M'+(CX+r[1])+','+r[0]+'Q'+(CX+r[1]/2)+','+(r[0]+3)+' '+(CX+2)+','+r[0],A*.9,1.6)});
    ln('M'+(CX-wa+3)+',150Q'+(CX-wa+10)+',172 '+(CX-wa+7)+',196',A*.5,1.3);ln('M'+(CX+wa-3)+',150Q'+(CX+wa-10)+',172 '+(CX+wa-7)+',196',A*.5,1.3);
  } else {
    ln('M'+(CX-ch+5)+',142Q'+(CX-ch*.45)+',153 '+(CX-3)+',139',A*.5,1.6);ln('M'+(CX+ch-5)+',142Q'+(CX+ch*.45)+',153 '+(CX+3)+',139',A*.5,1.6);
    hi('M'+(CX-6)+',116Q'+(CX-20)+',113 '+(CX-ch+8)+',124Q'+(CX-20)+',131 '+(CX-6)+',130Z',.18);
    ln('M'+CX+',158L'+CX+',200',A*.5,1.3);
    [[168,8],[182,7.5]].forEach(function(r){ln('M'+(CX-r[1])+','+r[0]+'Q'+(CX-r[1]/2)+','+(r[0]+2)+' '+(CX-2)+','+r[0],A*.5,1.3);ln('M'+(CX+r[1])+','+r[0]+'Q'+(CX+r[1]/2)+','+(r[0]+2)+' '+(CX+2)+','+r[0],A*.5,1.3)});
  }
  [-1,1].forEach(function(sg){
    var cx=CX+sg*(sh-5);
    if(!HIP){hi('M'+(cx-sg*5)+',119Q'+(cx-sg*1)+',134 '+(cx-sg*4)+',146Q'+(cx-sg*10)+',134 '+(cx-sg*9)+',119Z',.26*(.3+m));
    ln('M'+(cx+sg*8)+',125Q'+(cx+sg*9)+',142 '+(cx+sg*5)+',152',A*.55,1.4);
    ln('M'+(cx+sg*4)+',170Q'+(cx+sg*6)+',192 '+(cx+sg*8)+',208',A*.4,1.2);}
    var lx=CX+sg*25;
    ln('M'+(lx-sg*5)+',262Q'+(lx-sg*8)+',284 '+(lx-sg*4)+',300',A*.7,1.6);
    hi('M'+(lx-sg*3)+',254Q'+(lx-sg*10)+',276 '+(lx-sg*4)+',296Q'+(lx+sg*3)+',276 '+(lx-sg*3)+',254Z',.18*(.4+m));
    out+=ell(lx,308,8,6,sk.lo,' opacity=".2"');
    ln('M'+(lx-sg*5)+',326Q'+(lx-sg*8)+',344 '+(lx-sg*3)+',358',A*.5,1.5);
  });
  // tenue
  var ol=o.outfit||'tank', cld=hsl(o.cl[0],o.cl[1],o.cl[2]-20), acc=hsl(o.ac[0],o.ac[1],o.ac[2]);
  var sl=ol==='long'?330:ol==='tight'?300:278;
  [-1,1].forEach(function(sg){
    var j=[[CX+sg*17,230],[CX+sg*24,258],[CX+sg*(ol==='tight'?25:27),sl-6],[CX+sg*(ol==='tight'?25:27),sl]], pad=ol==='tight'?1.5:6;
    var r=[th+3,th+pad-.5+m*1.3,th-2+pad+m*1.2,th-3+pad+m*1.2];
    out+=path(cr(tube(j,r,0.05),true),SH);
    out+=line('M'+(CX+sg*(th+m*2.5+pad+18))+','+(ol==='long'?268:250)+'L'+(CX+sg*(th+m*2.5+pad+17))+','+(sl-3),acc,2.2,' opacity=".95"');
  });
  out+=path(cr(both(pts([[wa+7,200],[hp+3,214],[hp+5,228],[hp-5,244],[2,250]]),CX),true),SH);
  out+=path(cr(both(pts([[wa+7.5,199],[wa+8,207.5],[0,209]]),CX),true),cld);
  out+=line('M'+(CX-wa-4)+',204L'+(CX+wa+4)+',204',hsl(o.cl[0],o.cl[1],o.cl[2]+28),1.1,' opacity=".45"');
  out+=line('M'+CX+',209L'+CX+',240',cld,1.3,' opacity=".6"');
  if(ol!=='none'){
    var top=[[0,106],[s.nW+4,90],[s.nW+13,88],[sh-16,92],[sh-11,100],[ch+1,124],[ch+2+bu*3.5,142],[wa+3,160],[wa+3,180],[wa+4.5,201],[0,204]];
    out+=path(cr(both(pts(top),CX),true),CL);
    // panneaux latéraux (couleur accent) + col
    [-1,1].forEach(function(sg){out+=path(cr([[CX+sg*(ch+2),126],[CX+sg*(ch-4),132],[CX+sg*(wa-1),178],[CX+sg*(wa+6),200],[CX+sg*(wa+4),180],[CX+sg*(ch+3),142]],true),AC,' opacity=".95"');});
    out+=line(cr(pts([[-s.nW-4,89],[-s.nW-2,98],[-s.nW+6,105],[0,107.5],[s.nW-6,105],[s.nW+2,98],[s.nW+4,89]]),false),cld,2.2,' opacity=".85"');
    out+=path(cr(both(pts([[sh-15,92],[sh-9,100],[ch+2,124],[ch+bu*3,140],[ch-8,134],[ch-12,112]]),CX),true),'rgba(255,255,255,.09)');
    // chevron de marque
    out+=path('M'+(CX-9)+',138L'+CX+',128L'+(CX+9)+',138L'+(CX+9)+',143L'+CX+',133L'+(CX-9)+',143Z',hsl(0,0,100),' opacity=".9"');
    out+=path(cr([[CX-wa-3,197],[CX+wa+3,197],[CX+wa+4,201.5],[CX-wa-4,201.5]],true),acc);
  }
  if(o.wrist) [-1,1].forEach(function(sg){var e=armJ(sg)[4];if(HIP)out+=path(cr([[e[0]-wr-2,e[1]-6],[e[0]+wr+2,e[1]-6],[e[0]+wr+2,e[1]+3],[e[0]-wr-2,e[1]+3]],true),AC);else out+=path(cr([[e[0]-wr-2.2,e[1]-7],[e[0]+wr+2.2,e[1]-7],[e[0]+wr+2.2,e[1]+4],[e[0]-wr-2.2,e[1]+4]],true),AC);});
  [-1,1].forEach(function(sg){
    var x=CX+sg*22.5, fx=sg*3;
    out+=path(cr([[x-11,366],[x+11,366],[x+13,380],[x+20+fx,386],[x+20+fx,394],[x-17,394],[x-13,382]],true),SN);
    out+=path(cr([[x-17,389],[x+20+fx,389],[x+20+fx,396],[x-17,396]],true),hsl(0,0,95));
    out+=path('M'+(x+(sg>0?-15:2))+',384Q'+(x+sg)+',376 '+(x+(sg>0?-1:15))+',384Z',AC);
    out+=path(cr([[x-9,360],[x+9,360],[x+10,368],[x-10,368]],true),hsl(0,0,94));
  });
  if(HIP)[-1,1].forEach(function(sg){var e=armJ(sg)[5];out+=ell(e[0]-sg*1,e[1]+2,wr+3.4,wr+3.8,G)+path('M'+(e[0]-sg*(wr+2))+','+(e[1]-1)+'q'+(sg*(wr+2))+',3 '+(sg*(wr*2+3))+',0',sk.deep,' opacity=".0"');});
  // tête
  var hw=s.jaw?21:19.5, hd=s.jaw?[[0,-29],[14,-26.5],[20.5,-12],[hw,3],[17.5,15],[10.5,26],[0,29.5]]:[[0,-29],[14,-26.5],[19.5,-12],[hw-.5,3],[14.5,16],[8,27],[0,30]];
  [-1,1].forEach(function(sg){out+=ell(CX+sg*(hw+.4),hy+4,3.8,6.4,G)+ell(CX+sg*(hw+.2),hy+4.4,1.6,3.4,sk.lo,' opacity=".45"')});
  out+=path(cr(both(pts(hd.map(function(p){return [p[0],p[1]+hy]})),CX),true),G);
  out+=path(cr(both(pts([[0,hy+18],[10,hy+17],[hw-3,hy+9],[12,hy+27],[0,hy+30]]),CX),true),sk.lo,' opacity=".10"');
  if(isF)[-1,1].forEach(function(sg){out+=ell(CX+sg*11.5,hy+14,6,3.6,sk.blush,' opacity=".38"')});
  var ec=o.eyeCol||[24,30,20];
  [-1,1].forEach(function(sg){
    var ex=CX+sg*9.6, ey=hy+2, w=isF?5.8:5.2, hg=isF?3.8:3.1;
    out+=path('M'+(ex-w)+','+ey+'Q'+ex+','+(ey-hg*1.7)+' '+(ex+w)+','+ey+'Q'+ex+','+(ey+hg)+' '+(ex-w)+','+ey+'Z','#fcfaf8');
    out+=circ(ex+sg*.3,ey-.2,2.7,hsl(ec[0],ec[1],ec[2]))+circ(ex+sg*.3,ey-.2,1.3,'#150f0d')+circ(ex+sg*.3-.9,ey-1.1,.9,'#fff');
    out+=line('M'+(ex-w-.4)+','+(ey+.3)+'Q'+ex+','+(ey-hg*1.85)+' '+(ex+w+.4)+','+(ey+.3),'#2a1b15',isF?1.6:1.3);
    if(isF)out+=line('M'+(ex+sg*(w))+','+(ey-.2)+'L'+(ex+sg*(w+2.4))+','+(ey-1.5),'#2a1b15',1.2);
    var by=ey-(isF?8:6.6);
    out+=line('M'+(ex-w-1.2)+','+(by+(isF?.8:1.6))+'Q'+(ex+sg*1.2)+','+(by-(isF?2.4:1.4))+' '+(ex+w+1.6)+','+(by+(isF?1.8:.5)),H2,isF?1.4:2.3);
  });
  out+=line('M'+(CX-1.2)+','+(hy+4.5)+'Q'+(CX-2.4)+','+(hy+11.5)+' '+(CX-3.8)+','+(hy+13)+'Q'+CX+','+(hy+14.8)+' '+(CX+3.8)+','+(hy+13),sk.deep,1.3,' opacity=".6"');
  var my=hy+20.4;
  out+=path('M'+(CX-5.8)+','+my+'Q'+(CX-2.6)+','+(my-2.2)+' '+CX+','+(my-1)+'Q'+(CX+2.6)+','+(my-2.2)+' '+(CX+5.8)+','+my+'Q'+CX+','+(my+3.4)+' '+(CX-5.8)+','+my+'Z',isF?hsl(352,55,52):sk.lip);
  out+=line('M'+(CX-5.6)+','+my+'Q'+CX+','+(my+1)+' '+(CX+5.6)+','+my,sk.deep,.9,' opacity=".6"');
  // cheveux avant
  var cap=[[-21,hy-3],[-22,hy-18],[-13,hy-32],[0,hy-35],[13,hy-32],[22,hy-18],[21,hy-3],[17,hy-13],[8,hy-19],[-3,hy-20],[-14,hy-14]];
  if(hair==='fade'||hair==='quiff'||hair==='ponytail'||hair==='bun'){out+=path(cr(pts(cap),true),H0)+line(cr(pts([[-14,hy-27],[-2,hy-32],[11,hy-29]]),false),H1,2.4,' opacity=".7"');}
  if(hair==='quiff')out+=path(cr(pts([[-17,hy-22],[-11,hy-40],[6,hy-47],[24,hy-39],[23,hy-25],[10,hy-29],[-4,hy-25]]),true),H0)+line(cr(pts([[-9,hy-36],[4,hy-43],[17,hy-37]]),false),H1,2.5,' opacity=".7"');
  if(hair==='bun')out+=circ(CX,hy-42,12.5,H0)+line(cr(pts([[-7,hy-46],[0,hy-49],[8,hy-46]]),false),H1,2,' opacity=".6"');
  if(hair==='buzz')out+=path(cr(pts(cap),true),H0,' opacity=".5"');
  if(hair==='long'){
    out+=path(cr(pts([[-22,hy+4],[-23,hy-18],[-13,hy-33],[0,hy-36],[13,hy-33],[23,hy-18],[22,hy+4],[27,hy+38],[30,hy+76],[20,hy+74],[19,hy+30],[17,hy-6],[9,hy-18],[-2,hy-21],[-14,hy-10],[-19,hy+30],[-20,hy+74],[-30,hy+76],[-27,hy+38]]),true),H0);
    out+=line(cr(pts([[-14,hy-29],[0,hy-34],[14,hy-29]]),false),H1,2.6,' opacity=".7"')+line(cr(pts([[-24,hy+14],[-26,hy+42],[-24,hy+66]]),false),H1,1.8,' opacity=".5"');
  }
  if(hair==='ponytail')out+=path(cr(pts([[18,hy-8],[26,hy-10],[24,hy-2]]),true),H0);
  if(hair==='curly'){out+=circ(CX-15,hy-25,14,H0)+circ(CX+15,hy-25,14,H0)+circ(CX,hy-32,15,H0)+circ(CX-24,hy-9,11,H0)+circ(CX+24,hy-9,11,H0)+path(cr(pts([[-17,hy-12],[-8,hy-19],[8,hy-19],[17,hy-12],[12,hy-18],[0,hy-24],[-12,hy-18]]),true),H0)+circ(CX-12,hy-31,4.5,H1,' opacity=".55"')+circ(CX+9,hy-34,3.6,H1,' opacity=".55"');}
  return '<svg viewBox="0 0 240 410" xmlns="http://www.w3.org/2000/svg">'+defs+out+'</svg>';
}
window.AVA={render:render};
})();
