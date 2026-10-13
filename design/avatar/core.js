/* proto avatar — noyau de dessin (face) */
(function(){
var n1=function(x){return Math.round(x*10)/10};
var P=function(p){return n1(p[0])+','+n1(p[1])};
function cr(pts,closed,t){ // Catmull-Rom -> cubic
  t=t==null?1/6:t; var n=pts.length,d='M'+P(pts[0]),i,p0,p1,p2,p3,last=closed?n:n-1;
  for(i=0;i<last;i++){p0=pts[closed?(i-1+n)%n:Math.max(i-1,0)];p1=pts[i];p2=pts[(i+1)%n];p3=pts[closed?(i+2)%n:Math.min(i+2,n-1)];
    d+='C'+P([p1[0]+(p2[0]-p0[0])*t,p1[1]+(p2[1]-p0[1])*t])+' '+P([p2[0]-(p3[0]-p1[0])*t,p2[1]-(p3[1]-p1[1])*t])+' '+P(p2);}
  return d+(closed?'Z':'');
}
function mir(pts,cx){return pts.map(function(p){return [2*cx-p[0],p[1]]})}
function both(pts,cx){ // moitié droite (de haut en bas) -> contour fermé symétrique
  return pts.concat(mir(pts.slice().reverse(),cx));
}
// tube : joints [[x,y],...], radii [..] -> contour lisse
function tube(J,R,cap){
  var L=[],Rr=[],n=J.length,i,nx,ny,dx,dy,l;
  for(i=0;i<n;i++){
    var a=J[Math.max(i-1,0)],b=J[Math.min(i+1,n-1)];dx=b[0]-a[0];dy=b[1]-a[1];l=Math.hypot(dx,dy)||1;nx=-dy/l;ny=dx/l;
    L.push([J[i][0]+nx*R[i],J[i][1]+ny*R[i]]);Rr.push([J[i][0]-nx*R[i],J[i][1]-ny*R[i]]);
  }
  var e=J[n-1],pe=J[n-2],ux=e[0]-pe[0],uy=e[1]-pe[1],ul=Math.hypot(ux,uy)||1;ux/=ul;uy/=ul;
  var tip=[e[0]+ux*R[n-1]*(cap==null?.9:cap),e[1]+uy*R[n-1]*(cap==null?.9:cap)];
  var s=J[0],ps=J[1],sx=s[0]-ps[0],sy=s[1]-ps[1],sl=Math.hypot(sx,sy)||1;sx/=sl;sy/=sl;
  var top=[s[0]+sx*R[0]*.7,s[1]+sy*R[0]*.7];
  return L.concat([tip]).concat(Rr.reverse()).concat([top]);
}
function ell(cx,cy,rx,ry,f,x){return '<ellipse cx="'+n1(cx)+'" cy="'+n1(cy)+'" rx="'+n1(rx)+'" ry="'+n1(ry)+'" fill="'+f+'"'+(x||'')+'/>'}
function circ(cx,cy,r,f,x){return ell(cx,cy,r,r,f,x)}
function path(d,f,x){return '<path d="'+d+'" fill="'+f+'"'+(x||'')+'/>'}
function line(d,s,w,x){return '<path d="'+d+'" fill="none" stroke="'+s+'" stroke-width="'+w+'" stroke-linecap="round" stroke-linejoin="round"'+(x||'')+'/>'}
function hsl(h,s,l,a){return 'hsl('+Math.round(h)+','+Math.round(s)+'%,'+Math.round(l)+'%'+(a==null?'':','+a)+')'}
function clamp(x,a,b){return Math.max(a,Math.min(b,x))}
function lerp(a,b,t){return a+(b-a)*t}
// teinte de peau : [h,s,l] -> palette
function skinPal(sk){var h=sk[0],s=sk[1],l=sk[2];return{base:hsl(h,s,l),hi:hsl(h,s-4,l+9),lo:hsl(h-4,s+6,l-13),deep:hsl(h-8,s+10,l-24),blush:hsl(h-6,s+14,l-2),lip:hsl(h-10,s+8,l-14)}}
window.AVC={cr:cr,mir:mir,both:both,tube:tube,ell:ell,circ:circ,path:path,line:line,hsl:hsl,clamp:clamp,lerp:lerp,skinPal:skinPal,n1:n1,P:P};
})();
