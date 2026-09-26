"""Self-contained illustrated 3D station approach for live TfL predictions."""
import json


def render_train_scene(line_name, station, rows, retrieved_at, *, mode="Underground", accent="#0098d4"):
    """Return embeddable HTML. The approach is illustrative, not a vehicle position."""
    payload = {
        "line": line_name,
        "mode": mode,
        "accent": accent,
        "station": station,
        "retrieved": retrieved_at.isoformat(),
        "trains": [
            {
                "destination": row["destination"],
                "platform": row["platform"],
                "expected": row["expected_arrival"],
                "minutes": row["minutes"],
            }
            for row in rows[:6]
        ],
    }
    # TfL text is untrusted. Avoid terminating the inline script or inserting HTML.
    data = json.dumps(payload, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return _HTML.replace("/*__DATA__*/", f"const feed = {data};")


_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#091222;color:#e8f1ff;font:14px system-ui,-apple-system,Segoe UI,sans-serif}
.shell{border:1px solid #24415d;border-radius:20px;overflow:hidden;background:#101e34;box-shadow:0 16px 40px #03091455}
.head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:15px 20px;background:#0d1a2e}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#8fb2d3}.title{font-size:20px;font-weight:750;margin-top:3px}
.badge{border-radius:40px;background:color-mix(in srgb,var(--accent) 22%,#0d1a2e);border:1px solid var(--accent);color:#f3f8ff;padding:7px 11px;white-space:nowrap;font-size:12px}
.scene{position:relative;height:370px;background:#06101e}.scene canvas{display:block;width:100%;height:100%}
.overlay{position:absolute;top:14px;left:16px;padding:11px 14px;background:#091726d9;border:1px solid #47647e;border-radius:11px;max-width:min(70%,370px)}
.overlay strong{display:block;font-size:17px;margin:3px 0}.overlay span{color:#a8c4db;font-size:12px}
.count{position:absolute;bottom:15px;right:16px;background:#09263bdd;border:1px solid #368fad;border-radius:12px;padding:9px 15px;text-align:right}
.count b{display:block;font-size:22px;color:#a9f4ec;font-variant-numeric:tabular-nums}.count small{color:#b8d2e5}
.strip{display:flex;gap:8px;overflow:auto;padding:12px 16px;background:#0d1b30}
button{border:1px solid #345575;background:#152b46;color:#e2efff;border-radius:10px;min-width:150px;text-align:left;padding:9px 12px;cursor:pointer;font:inherit}
button:hover,button:focus-visible{border-color:var(--accent);outline:none}button.active{background:#174c61;border-color:var(--accent)}button strong{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}button small{color:#b5cfe3}
.foot{padding:11px 17px;color:#a9c5da;font-size:12px;line-height:1.4;background:#10213a;border-top:1px solid #29445b}
@media(max-width:600px){.head{padding:12px}.title{font-size:16px}.scene{height:310px}.overlay strong{font-size:14px}.count b{font-size:17px}}
</style></head><body><section class="shell" aria-label="Illustrated 3D train approach">
<div class="head"><div><div class="eyebrow" id="mode"></div><div class="title" id="station"></div></div><div class="badge" id="line"></div></div>
<div class="scene"><canvas id="scene" role="img" aria-label="Illustrated train approaching a station"></canvas>
<div class="overlay"><span>SELECTED PREDICTION</span><strong id="destination"></strong><span id="platform"></span></div>
<div class="count"><b id="eta"></b><small id="status"></small></div></div>
<div class="strip" id="choices" role="group" aria-label="Choose an upcoming predicted train"></div>
<div class="foot">Illustration only: train movement is animated from TfL's predicted arrival time, not GPS or actual train position. Predictions change; use Refresh TfL feed above for new data. Feed retrieved <span id="stamp"></span> UTC.</div>
</section><script>
/*__DATA__*/
const canvas=document.getElementById('scene'), ctx=canvas.getContext('2d');
let selected=0, width=0,height=0, ratio=1;
const $=id=>document.getElementById(id);
document.documentElement.style.setProperty('--accent',feed.accent);
$('station').textContent=feed.station;
$('mode').textContent=feed.mode+' · live prediction explorer · illustrated scene';
$('line').textContent=feed.line;
$('stamp').textContent=new Date(feed.retrieved).toLocaleString('en-GB',{timeZone:'UTC',dateStyle:'medium',timeStyle:'medium'});
function remaining(t){const d=Date.parse(t.expected);return Number.isFinite(d)?Math.max(0,(d-Date.now())/1000):null}
function label(t){const seconds=remaining(t);return seconds===null?'ETA unavailable':seconds<=0?'Prediction passed':seconds<60?Math.ceil(seconds)+' sec':Math.ceil(seconds/60)+' min'}
function update(){
  const t=feed.trains[selected], seconds=remaining(t);
  $('destination').textContent=t.destination;
  $('platform').textContent=t.platform;
  $('eta').textContent=label(t);
  $('status').textContent=seconds===null?'Check arrival table':seconds<=0?'Refresh for latest':'Predicted arrival';
  document.querySelectorAll('.strip button').forEach((button,i)=>{button.classList.toggle('active',i===selected);button.querySelector('small').textContent=label(feed.trains[i])+' · '+feed.trains[i].platform});
}
feed.trains.forEach((t,i)=>{
 const b=document.createElement('button');b.type='button';b.setAttribute('aria-label','Train to '+t.destination);
 const name=document.createElement('strong'), info=document.createElement('small');
 name.textContent=t.destination;info.textContent=label(t);b.append(name,info);
 b.onclick=()=>{selected=i;update()};$('choices').append(b);
});
function resize(){const rect=canvas.getBoundingClientRect();ratio=Math.min(devicePixelRatio||1,2);width=rect.width;height=rect.height;canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0)}
addEventListener('resize',resize);resize();update();setInterval(update,1000);
const color=feed.accent;
function poly(points,fill,stroke){ctx.beginPath();ctx.moveTo(...points[0]);for(const p of points.slice(1))ctx.lineTo(...p);ctx.closePath();ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=2;ctx.stroke()}}
function line(x1,y1,x2,y2,stroke,weight=2){ctx.strokeStyle=stroke;ctx.lineWidth=weight;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()}
function draw(time){
 const w=width,h=height,vx=w*.5,vy=h*.32;
 const bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#172e4c');bg.addColorStop(.55,'#0d213b');bg.addColorStop(1,'#071323');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
 // Tunnel walls and glowing ceiling ribs converge at a vanishing point.
 poly([[0,0],[w,0],[vx+55,vy],[vx-55,vy]],'#1b3552');
 poly([[0,0],[vx-55,vy],[vx-62,vy+22],[0,h]],'#122944');
 poly([[w,0],[vx+55,vy],[vx+62,vy+22],[w,h]],'#10243b');
 poly([[vx-62,vy+22],[vx+62,vy+22],[w,h],[0,h]],'#132338');
 for(let j=0;j<8;j++){let z=(j+(time*.00016)%1)/8,depth=z*z, yy=vy+depth*(h-vy);let spread=55+depth*w*.55;line(vx-spread,yy,vx+spread,yy,'#28415b',1+depth*4);}
 // Platform edges and two rails.
 poly([[0,h],[vx-88,vy+18],[vx-52,vy+20],[w*.25,h]],'#33465a');
 poly([[w,h],[vx+88,vy+18],[vx+52,vy+20],[w*.75,h]],'#273d53');
 line(vx-18,vy+20,w*.36,h,'#9cc3c9',4);line(vx+18,vy+20,w*.64,h,'#9cc3c9',4);
 line(vx-56,vy+22,0,h,'#ffd36f',3);line(vx+56,vy+22,w,h,'#ffd36f',3);
 for(let j=0;j<10;j++){let z=((j/10+time*.00012)%1);let d=z*z;line(vx-(18+d*w*.14),vy+20+d*(h-vy),vx+(18+d*w*.14),vy+20+d*(h-vy),'#40546a',1+d*5)}
 // Three projected faces form a train in perspective. Position follows ETA only.
 const secs=remaining(feed.trains[selected]);
 const progress=secs===null?.2:secs<=0?1:Math.max(.12,Math.min(.95,1-secs/600));
 const p=progress*progress, cx=vx, bottom=vy+38+p*(h-vy-42), tw=32+p*Math.min(w*.38,220), th=28+p*185;
 const left=cx-tw/2,right=cx+tw/2,top=bottom-th,side=Math.min(25,tw*.12);
 ctx.fillStyle='#0008';ctx.beginPath();ctx.ellipse(cx,bottom+5,tw*.7,7+p*15,0,0,Math.PI*2);ctx.fill();
 poly([[right,top],[right+side,top-10*p],[right+side,bottom-7*p],[right,bottom]],'#26374b','#7b9bad');
 poly([[left,top],[right,top],[right+side,top-10*p],[left+side,top-10*p]],'#658099');
 const isTram=feed.mode==='Tram', isSurface=feed.mode==='Overground'||feed.mode==='Elizabeth line';
 poly([[left,top],[right,top],[right,bottom],[left,bottom]],isTram?'#e3e5d9':isSurface?'#e9e4de':'#d6e1e8','#eefaff');
 poly([[left+tw*.08,top+th*.12],[right-tw*.08,top+th*.12],[right-tw*.08,top+th*(isTram?.57:.48)],[left+tw*.08,top+th*(isTram?.57:.48)]],'#102b43');
 poly([[left+tw*.12,top+th*.55],[right-tw*.12,top+th*.55],[right-tw*.12,top+th*.61],[left+tw*.12,top+th*.61]],color);
 if(isSurface || feed.mode==='DLR'){
   line(left+tw*.5,top+th*.12,left+tw*.5,top+th*.48,'#8196a8',1+p*3);
 }
 ctx.fillStyle='#fff5bd';for(const x of [left+tw*.16,right-tw*.16]){ctx.beginPath();ctx.arc(x,bottom-th*.14,2+p*5,0,Math.PI*2);ctx.fill()}
 if(tw>80){ctx.fillStyle='#f0f6fc';ctx.font=`bold ${Math.min(13,7+p*9)}px system-ui`;ctx.textAlign='center';ctx.fillText(feed.line.toUpperCase(),cx,top+th*.35)}
 ctx.fillStyle='#ffffff16';ctx.fillRect(0,0,w,2);requestAnimationFrame(draw)
}
requestAnimationFrame(draw);
</script></body></html>"""
