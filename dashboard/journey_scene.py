"""Illustrated journey route view. Never portrays a real train position."""
import json


def render_journey_scene(journey, colours=None):
    colours = colours or {}
    payload = {
        "legs": [{
            "mode": leg["mode"], "line": leg["line"], "from": leg["from"],
            "to": leg["to"], "duration": leg["duration"], "stops": leg["stops"],
            "accent": colours.get(leg["line"], "#52b7df"),
        } for leg in journey["legs"]],
    }
    data = (json.dumps(payload, ensure_ascii=True).replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("&", "\\u0026"))
    return _HTML.replace("/*__DATA__*/", f"const journey = {data};")


_HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1628;color:#eff7ff;font:14px system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{border-radius:18px;overflow:hidden;border:1px solid #2c526f;background:#101f34}
.top{padding:15px 18px;background:#102b42}.top small{color:#9ec8da;letter-spacing:.12em;text-transform:uppercase}.top h2{font-size:19px;margin:5px 0 0}
.scene{height:220px;position:relative;overflow:hidden;background:radial-gradient(ellipse at 50% 90%,#335570 0%,#172c44 47%,#0a182a 100%)}
.scene:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0 13%,#ffffff0b 13.2% 13.5%);transform:perspective(500px) rotateX(58deg) scale(1.4);transform-origin:bottom}
.track{position:absolute;bottom:0;left:10%;width:80%;height:80%;background:linear-gradient(90deg,transparent 0 18%,#b4d4d9 18.3% 19%,transparent 19.3% 80%,#b4d4d9 80.3% 81%,transparent 81.3%);clip-path:polygon(44% 0,56% 0,100% 100%,0 100%)}
.vehicle{position:absolute;left:50%;top:45%;width:135px;height:95px;transform:translate(-50%,-5%) perspective(450px) rotateY(-9deg);border:4px solid #f1fbff;background:linear-gradient(#d8e4e9 0 60%,var(--accent) 60% 72%,#d8e4e9 72%);border-radius:16px 16px 8px 8px;box-shadow:14px 10px 0 #36546a,0 10px 30px #0009;animation:approach 7s ease-in-out infinite alternate}
.vehicle:before{content:"";position:absolute;top:12px;left:12px;right:12px;height:37px;background:#0a2b47;border-radius:7px}
.vehicle span{position:absolute;top:22px;left:12px;right:12px;text-align:center;font-size:12px;font-weight:700;z-index:2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@keyframes approach{from{transform:translate(-50%,-5%) perspective(450px) rotateY(-9deg) scale(.55)}to{transform:translate(-50%,-5%) perspective(450px) rotateY(-9deg) scale(1)}}
.card{position:absolute;left:15px;top:13px;max-width:42%;padding:11px 13px;background:#0a1c30e8;border:1px solid #557694;border-radius:10px;line-height:1.35}
.card strong{display:block;font-size:16px;margin:4px 0}.card small{color:#b6d1e5}.legend{padding:10px 16px;background:#142a40;color:#b9d2e5;font-size:12px;line-height:1.45}
.legs{display:flex;gap:8px;padding:12px 14px;overflow:auto}button{min-width:180px;max-width:240px;background:#193049;color:#eff7ff;text-align:left;border:1px solid #49627c;border-radius:10px;padding:10px;cursor:pointer;font:inherit}
button.active,button:focus-visible{border-color:var(--accent);outline:none;background:#20516a}button strong{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}button small{display:block;margin-top:4px;color:#c2d6e5}
.stops{padding:4px 16px 17px;color:#cfe1ef;max-height:100px;overflow:auto}.stops b{display:block;margin-bottom:8px}.stop{display:inline-block;border-radius:30px;border:1px solid #37526a;background:#1a344b;padding:4px 9px;margin:0 5px 6px 0;font-size:12px}
@media(max-width:600px){.card{max-width:60%}.card strong{font-size:13px}.scene{height:190px}}
</style></head><body><section class="wrap" aria-label="Illustrated journey route">
<div class="top"><small>Chosen TfL journey</small><h2>Explore each leg</h2></div>
<div class="scene"><div class="track"></div><div class="card"><small id="mode"></small><strong id="segment"></strong><small id="duration"></small></div><div class="vehicle"><span id="train"></span></div></div>
<div class="legend">Illustrated travel only. This animation is a route story, not a live train position, vehicle tracking or a guarantee of arrival time.</div>
<div class="legs" id="legs" role="group" aria-label="Choose journey leg"></div><div class="stops"><b id="stops-title"></b><div id="stops"></div></div>
</section><script>
/*__DATA__*/
const $=id=>document.getElementById(id);let selected=0;
function show(i){selected=i;const leg=journey.legs[i];document.documentElement.style.setProperty('--accent',leg.accent);
 $('mode').textContent=leg.line||leg.mode;$('segment').textContent=leg.from+' → '+leg.to;
 $('duration').textContent=(leg.duration===null?'Duration unavailable':leg.duration+' min')+' · '+leg.mode;
 $('train').textContent=leg.line||leg.mode;
 document.querySelectorAll('button').forEach((b,j)=>b.classList.toggle('active',i===j));
 $('stops-title').textContent=leg.stops.length?'Stops listed by TfL for this leg':'Stops not listed for this leg';
 $('stops').replaceChildren();for(const name of leg.stops){const span=document.createElement('span');span.className='stop';span.textContent=name;$('stops').append(span)}
}
journey.legs.forEach((leg,i)=>{const button=document.createElement('button');button.type='button';
 const title=document.createElement('strong'),detail=document.createElement('small');title.textContent=(i+1)+'. '+(leg.line||leg.mode);
 detail.textContent=leg.from+' → '+leg.to;button.append(title,detail);button.onclick=()=>show(i);$('legs').append(button)});show(0);
</script></body></html>"""
