# -*- coding: utf-8 -*-
"""把 dynasty_data.py 的内容渲染成小朋友友好的朝代历史 HTML 页面。
输出：(1) 每个朝代一个 html；(2) 朝代总览 hub 页 dynasties.html。
运行：python3 builder/build_dynasties.py
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dynasty_data import DYNASTIES  # noqa
import histmap  # 地理精确的历史地图引擎
from battle_maps import BATTLE_MAPS  # 各关键战役的地图帝风格战役地图配置

ROOT = os.path.dirname(HERE)  # 仓库根目录

# ====================== 通用 CSS（用 __TOKEN__ 占位，稍后替换） ======================
PAGE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Noto+Sans+SC:wght@400;700;900&display=swap');
* { margin:0; padding:0; box-sizing:border-box; }
:root{
  --primary:__PRIMARY__;
  --secondary:__SECONDARY__;
  --accent:__ACCENT__;
  --ink:#2C3E50;
  --paper:#FFFDF7;
  --card-shadow:0 10px 30px rgba(0,0,0,0.12);
}
html{scroll-behavior:smooth;}
body{
  font-family:'Noto Sans SC',sans-serif;
  color:var(--ink);
  background:
    radial-gradient(circle at 15% 10%, color-mix(in srgb, var(--primary) 14%, white) 0%, transparent 45%),
    radial-gradient(circle at 85% 20%, color-mix(in srgb, var(--secondary) 14%, white) 0%, transparent 45%),
    linear-gradient(160deg,#FFFDF7 0%, #FFF6EC 50%, #FDEFF4 100%);
  background-attachment:fixed;
  overflow-x:hidden;
}
a{color:inherit;text-decoration:none;}

/* ===== 顶部返回 ===== */
.topbar{
  position:sticky; top:0; z-index:200;
  display:flex; align-items:center; gap:12px;
  padding:10px 18px;
  background:rgba(255,253,247,0.92);
  backdrop-filter:blur(10px);
  box-shadow:0 2px 16px rgba(0,0,0,0.08);
}
.topbar .home-btn{
  font-family:'ZCOOL KuaiLe',sans-serif;
  background:var(--primary); color:#fff;
  padding:6px 16px; border-radius:20px; font-size:1rem;
  transition:transform .2s, box-shadow .2s;
  box-shadow:0 4px 12px color-mix(in srgb, var(--primary) 40%, transparent);
}
.topbar .home-btn:hover{transform:translateY(-2px) scale(1.04);}
.topbar .crumb{font-size:.9rem;color:#7F8C8D;}
.topbar .crumb b{color:var(--primary);}

/* ===== 章节快捷导航 ===== */
.section-nav{
  position:sticky; top:52px; z-index:150;
  display:flex; flex-wrap:wrap; justify-content:center; gap:8px;
  padding:8px 12px;
  background:rgba(255,253,247,0.85);
  backdrop-filter:blur(8px);
  border-bottom:1px solid rgba(0,0,0,0.06);
}
.section-nav a{
  font-size:.82rem; font-weight:700; color:#7F8C8D;
  padding:5px 13px; border-radius:18px; border:2px solid transparent;
  transition:all .25s; white-space:nowrap;
}
.section-nav a:hover{background:color-mix(in srgb,var(--accent) 30%,white); color:var(--ink); transform:scale(1.05);}
.section-nav a.active{color:var(--primary); border-color:var(--primary); background:#fff;}

/* ===== HERO ===== */
.hero{
  min-height:78vh; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center;
  padding:50px 20px 30px; position:relative; overflow:hidden;
}
.hero .blob{
  position:absolute; border-radius:50%; filter:blur(60px); opacity:.5; z-index:0;
  width:380px; height:380px;
  background:radial-gradient(circle,var(--secondary),transparent 70%);
  animation:floatBlob 9s ease-in-out infinite;
}
.hero .blob.b2{background:radial-gradient(circle,var(--accent),transparent 70%); right:-80px; top:10%; animation-delay:2s;}
@keyframes floatBlob{0%,100%{transform:translateY(0)}50%{transform:translateY(-30px)}}
.hero-emoji{
  font-size:clamp(4rem,14vw,7rem); z-index:1;
  animation:bob 3s ease-in-out infinite;
  filter:drop-shadow(0 8px 18px rgba(0,0,0,0.18));
}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-14px) rotate(3deg)}}
.hero-title{
  font-family:'ZCOOL KuaiLe',sans-serif;
  font-size:clamp(3rem,11vw,6rem);
  color:var(--primary);
  text-shadow:3px 3px 0 #fff, 6px 6px 0 color-mix(in srgb,var(--primary) 25%,transparent);
  margin:8px 0; z-index:1; letter-spacing:.05em;
}
.hero-era{
  font-size:clamp(1rem,2.5vw,1.4rem); color:var(--secondary);
  font-weight:700; z-index:1; margin-bottom:6px;
}
.hero-sub{
  font-size:clamp(.95rem,2vw,1.15rem); color:#5D6D7E; z-index:1;
  max-width:620px; margin:6px auto 0; line-height:1.7;
}
.scroll-hint{
  position:absolute; bottom:18px; left:50%; transform:translateX(-50%);
  font-size:.85rem; color:#95A5A6; animation:bounce 2s infinite; z-index:1;
}
@keyframes bounce{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(8px)}}

/* ===== 内容区块 ===== */
.wrap{max-width:920px; margin:0 auto; padding:10px 18px 40px;}
.section{
  background:#fff; border-radius:24px; padding:28px 26px; margin:26px 0;
  box-shadow:var(--card-shadow); border-top:6px solid var(--primary);
  opacity:0; transform:translateY(40px); transition:all .7s cubic-bezier(.2,.7,.3,1);
}
.section.visible{opacity:1; transform:translateY(0);}
.sec-head{display:flex; align-items:center; gap:12px; margin-bottom:18px;}
.sec-badge{
  font-size:1.6rem; width:54px; height:54px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  background:color-mix(in srgb,var(--primary) 14%,white);
  border-radius:16px; box-shadow:0 4px 10px rgba(0,0,0,0.08);
}
.sec-title{
  font-family:'ZCOOL KuaiLe',sans-serif;
  font-size:clamp(1.6rem,4.5vw,2.3rem); color:var(--ink); line-height:1.2;
}
.sec-title small{display:block; font-family:'Noto Sans SC'; font-weight:400; font-size:.8rem; color:#95A5A6; letter-spacing:.1em; margin-top:2px;}
.sec-body p{font-size:1.05rem; line-height:1.9; margin-bottom:12px; color:#34495E;}
.sec-body p:last-child{margin-bottom:0;}

/* 高亮关键词 */
.hl{background:linear-gradient(120deg,transparent 0%, color-mix(in srgb,var(--accent) 55%,transparent) 50%, transparent 100%); padding:1px 5px; border-radius:5px; font-weight:700; color:var(--ink);}

/* 特点列表 */
.feat-list{list-style:none; display:grid; gap:12px;}
.feat-list li{
  display:flex; gap:12px; align-items:flex-start;
  background:color-mix(in srgb,var(--secondary) 8%,white);
  padding:14px 16px; border-radius:14px; font-size:1.02rem; line-height:1.7;
  border-left:5px solid var(--secondary);
}
.feat-list li .dot{font-size:1.3rem; flex-shrink:0;}

/* 历史进程时间轴 */
.timeline{position:relative; padding-left:30px;}
.timeline::before{content:''; position:absolute; left:9px; top:6px; bottom:6px; width:4px; border-radius:4px; background:linear-gradient(var(--primary),var(--secondary));}
.tl-item{position:relative; margin-bottom:22px;}
.tl-item::before{content:''; position:absolute; left:-26px; top:4px; width:18px; height:18px; border-radius:50%; background:var(--accent); border:3px solid #fff; box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 40%,transparent);}
.tl-year{font-family:'ZCOOL KuaiLe',sans-serif; color:var(--primary); font-size:1.15rem;}
.tl-title{font-weight:700; font-size:1.1rem; margin:2px 0 4px;}
.tl-text{font-size:1rem; line-height:1.8; color:#455A64;}

/* 人物卡片 */
.people-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:16px;}
.person{
  background:linear-gradient(160deg, color-mix(in srgb,var(--primary) 8%,white), #fff);
  border-radius:18px; padding:18px; border:1px solid rgba(0,0,0,0.05);
  transition:transform .25s, box-shadow .25s;
}
.person:hover{transform:translateY(-6px); box-shadow:0 14px 28px rgba(0,0,0,0.12);}
.person .pname{font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.4rem; color:var(--primary);}
.person .prole{font-size:.82rem; color:var(--secondary); font-weight:700; margin:2px 0 8px;}
.person .pdesc{font-size:.95rem; line-height:1.65; color:#455A64;}

/* 三栏通用卡片 */
.mini-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px;}
.mini{background:#fff; border-radius:18px; padding:18px 20px; border-top:5px solid var(--accent); box-shadow:0 6px 18px rgba(0,0,0,0.07);}
.mini h4{font-family:'ZCOOL KuaiLe',sans-serif; color:var(--secondary); font-size:1.25rem; margin-bottom:10px;}
.mini p{font-size:.98rem; line-height:1.8; color:#455A64;}

/* 疆域地图 */
.map-card{display:flex; flex-wrap:wrap; gap:20px; align-items:center;}
.map-svg{flex:1 1 320px; min-width:280px; background:color-mix(in srgb,var(--primary) 5%,white); border-radius:18px; padding:10px; border:2px dashed color-mix(in srgb,var(--primary) 30%,transparent);}
.map-svg svg{width:100%; height:auto; display:block;}
.map-text{flex:1 1 300px; font-size:1.05rem; line-height:1.9; color:#34495E;}

/* 真实地理地图（全宽） */
.map-wide{width:100%; border-radius:18px; overflow:hidden; box-shadow:var(--card-shadow); border:1px solid rgba(0,0,0,0.06);}
.map-wide svg{width:100%; height:auto; display:block;}
.battle-map-wrap{width:100%; border-radius:14px; overflow:hidden; margin-bottom:16px; box-shadow:0 4px 14px rgba(0,0,0,0.12); border:1px solid rgba(0,0,0,0.06);}
.battle-map-wrap svg{width:100%; height:auto; display:block;}

/* 人物卡片可跳转 */
.person-link{text-decoration:none; color:inherit; display:block;}
.person .pstory{margin-top:10px; font-size:.85rem; font-weight:700; color:var(--secondary); opacity:0; transform:translateY(4px); transition:all .25s;}
.person-link:hover .pstory{opacity:1; transform:translateY(0);}

/* 战役 */
.battle-box{background:linear-gradient(160deg,#1b2433,#2c3a52); border-radius:20px; padding:20px; color:#fff; text-align:center;}
.battle-title{font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.6rem; color:#FFD54F; margin-bottom:4px;}
.battle-sub{font-size:.9rem; color:#bcd; margin-bottom:12px;}
.battle-canvas{width:100%; max-width:680px; border-radius:14px; background:#0e1622; display:block; margin:0 auto; box-shadow:0 8px 24px rgba(0,0,0,0.4);}
.battle-btn{
  margin-top:14px; font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.15rem;
  background:linear-gradient(135deg,#FF5252,#FF8A65); color:#fff; border:none;
  padding:10px 34px; border-radius:30px; cursor:pointer; transition:transform .2s, box-shadow .2s;
  box-shadow:0 6px 18px rgba(255,82,82,0.4);
}
.battle-btn:hover{transform:scale(1.06);}
.battle-btn:disabled{opacity:.6; cursor:default; transform:none;}
.battle-narrate{margin-top:14px; min-height:48px; font-size:1rem; line-height:1.7; color:#e8eef5; max-width:620px; margin-left:auto; margin-right:auto;}
.battle-result{font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.5rem; margin-top:6px;}

/* 小测验 */
.quiz-q{background:#fff; border-radius:18px; padding:20px 22px; margin-bottom:18px; box-shadow:0 6px 16px rgba(0,0,0,0.07); border-left:6px solid var(--secondary);}
.quiz-q .q-text{font-size:1.15rem; font-weight:700; margin-bottom:14px;}
.opt{
  display:block; width:100%; text-align:left; cursor:pointer;
  background:#f4f7fa; border:2px solid transparent; border-radius:12px;
  padding:12px 16px; margin-bottom:10px; font-size:1.02rem; transition:all .2s; font-family:inherit;
}
.opt:hover{background:color-mix(in srgb,var(--accent) 22%,white);}
.opt.correct{background:#d5f5e3; border-color:#27AE60; color:#145a32; font-weight:700;}
.opt.wrong{background:#fdecea; border-color:#E74C3C; color:#922b21; font-weight:700;}
.opt.disabled{pointer-events:none;}
.quiz-explain{font-size:.95rem; line-height:1.7; color:#5D6D7E; margin-top:6px; padding:10px 14px; background:#fbf6e9; border-radius:10px; border-left:4px solid var(--accent); display:none;}
.quiz-explain.show{display:block;}
.quiz-score{text-align:center; font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.4rem; color:var(--primary); margin:10px 0 24px;}
.quiz-score b{color:var(--secondary); font-size:1.8rem;}

/* 底部翻页 */
.pager{display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin:30px 0 10px;}
.pager a{
  flex:1 1 200px; text-align:center; padding:14px; border-radius:16px;
  background:#fff; box-shadow:var(--card-shadow); font-weight:700; color:var(--ink);
  transition:transform .2s; border:2px solid transparent;
}
.pager a:hover{transform:translateY(-4px); border-color:var(--primary); color:var(--primary);}
.pager .label{font-size:.78rem; color:#95A5A6; display:block; font-weight:400;}
.pager .pname{font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.2rem;}

footer{text-align:center; padding:30px 20px 50px; color:#95A5A6; font-size:.85rem;}
footer .poem{font-family:'ZCOOL KuaiLe',sans-serif; font-size:1.2rem; color:var(--primary); opacity:.7; margin-bottom:8px;}

@media(max-width:600px){
  .section{padding:22px 16px;}
  .hero-title{font-size:2.6rem;}
}
"""

# ====================== 地图 SVG 生成 ======================
def map_svg(region, theme, name):
    pc = theme["primary"]; sc = theme["secondary"]; ac = theme["accent"]
    # 抽象中国轮廓（装饰用，非精确地理）
    land = "M70,150 C60,90 130,55 210,60 C250,40 330,30 400,55 C470,40 540,70 560,130 " \
           "C585,180 560,250 520,300 C540,350 480,400 400,395 C330,420 240,415 180,390 " \
           "C110,400 60,350 70,280 C40,240 50,190 70,150 Z"
    # 高亮区域（按 region 选中心/范围）
    if region == "all":
        hi = '<ellipse cx="320" cy="225" rx="210" ry="150" fill="__AC__" opacity="0.35"/>'
    elif region == "central":
        hi = '<ellipse cx="300" cy="210" rx="130" ry="95" fill="__AC__" opacity="0.4"/>'
    elif region == "north":
        hi = '<ellipse cx="310" cy="140" rx="150" ry="80" fill="__AC__" opacity="0.4"/>'
    elif region == "south":
        hi = '<ellipse cx="330" cy="320" rx="150" ry="80" fill="__AC__" opacity="0.4"/>'
    else:
        hi = '<ellipse cx="310" cy="220" rx="160" ry="110" fill="__AC__" opacity="0.35"/>'
    hi = hi.replace("__AC__", ac)
    pin_x = "300" if region in ("central","all") else ("310" if region!="south" else "330")
    pin_y = "200" if region!="south" else "310"
    svg = f'''
<svg viewBox="0 0 600 420" role="img" aria-label="疆域示意">
  <defs>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#dff1fb"/><stop offset="1" stop-color="#cfe8f7"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{ac}" stop-opacity="0.55"/><stop offset="1" stop-color="{ac}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="0" y="0" width="600" height="420" rx="16" fill="url(#sea)"/>
  {hi}
  <path d="{land}" fill="{pc}" opacity="0.82" stroke="#fff" stroke-width="3"/>
  <path d="{land}" fill="url(#glow)" opacity="0.6"/>
  <g stroke="#ffffff" stroke-opacity="0.35" stroke-width="1">
    <line x1="40" y1="105" x2="560" y2="105"/><line x1="40" y1="210" x2="560" y2="210"/><line x1="40" y1="315" x2="560" y2="315"/>
    <line x1="160" y1="40" x2="160" y2="400"/><line x1="320" y1="40" x2="320" y2="400"/><line x1="460" y1="40" x2="460" y2="400"/>
  </g>
  <!-- 图钉 -->
  <g transform="translate({pin_x},{pin_y})">
    <circle cx="0" cy="0" r="40" fill="url(#glow)"/>
    <path d="M0,28 C-16,8 -16,-14 0,-14 C16,-14 16,8 0,28 Z" fill="{sc}" stroke="#fff" stroke-width="2"/>
    <circle cx="0" cy="-2" r="7" fill="#fff"/>
  </g>
  <text x="{pin_x}" y="{int(pin_y)+46}" text-anchor="middle" font-family="ZCOOL KuaiLe,sans-serif" font-size="22" fill="{pc}" font-weight="bold">{name}</text>
  <!-- 指南针 -->
  <g transform="translate(540,60)" stroke="{pc}" fill="{pc}">
    <circle r="20" fill="none" stroke-width="2" opacity="0.6"/>
    <path d="M0,-16 L5,4 L0,-1 L-5,4 Z" fill="{ac}"/>
    <text x="0" y="-24" text-anchor="middle" font-size="12" stroke="none">北</text>
  </g>
  <text x="20" y="405" font-size="12" fill="#7f9aa8" font-family="Noto Sans SC">※ 约略示意图，非精确疆界</text>
</svg>'''
    return svg

# ====================== 战斗动画 JS ======================
BATTLE_JS = """
function initBattle(cfg){
  var canvas=document.getElementById(cfg.canvas);
  if(!canvas) return;
  var ctx=canvas.getContext('2d');
  var W=680,H=300;
  function resize(){ var r=canvas.getBoundingClientRect(); canvas.width=W; canvas.height=H; }
  resize();
  var leftColor=cfg.leftColor, rightColor=cfg.rightColor;
  var winner=cfg.winner; // 'left' or 'right'
  var type=cfg.type; // 'land' or 'water'
  var running=false, t=0, finished=false;
  var arrows=[], ships=[], parts=[];
  // 士兵
  function makeArmy(side){
    var arr=[], n=18;
    for(var i=0;i<n;i++){
      var row=Math.floor(i/6), col=i%6;
      arr.push({side:side, x: side==='left'? 40+col*26 : W-40-col*26,
                y: 70+row*55 + (Math.random()*8-4), baseY:70+row*55});
    }
    return arr;
  }
  var armyL=makeArmy('left'), armyR=makeArmy('right');
  if(type==='water'){
    ships=[{x:90,y:H/2-12,side:'left'},{x:W-90,y:H/2-12,side:'right'}];
  }
  function drawSoldier(s){
    ctx.save();
    ctx.fillStyle = s.side==='left'? leftColor : rightColor;
    var x=s.x,y=s.y;
    // 身体
    ctx.beginPath(); ctx.arc(x,y,7,0,Math.PI*2); ctx.fill();
    // 枪/矛
    ctx.strokeStyle='#eee'; ctx.lineWidth=2;
    ctx.beginPath(); ctx.moveTo(x,y-7); ctx.lineTo(x+(s.side==='left'?10:-10),y-18); ctx.stroke();
    ctx.restore();
  }
  function draw(){
    ctx.clearRect(0,0,W,H);
    // 背景
    var g=ctx.createLinearGradient(0,0,0,H);
    if(type==='water'){ g.addColorStop(0,'#16384f'); g.addColorStop(1,'#0e2433'); }
    else { g.addColorStop(0,'#3a2c22'); g.addColorStop(1,'#241a14'); }
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
    // 中线
    ctx.strokeStyle='rgba(255,255,255,0.12)'; ctx.setLineDash([6,8]);
    ctx.beginPath(); ctx.moveTo(W/2,20); ctx.lineTo(W/2,H-20); ctx.stroke(); ctx.setLineDash([]);
    // 旗帜标签
    ctx.font='bold 15px sans-serif'; ctx.textAlign='center';
    ctx.fillStyle=leftColor; ctx.fillText(cfg.leftName, W*0.18, 30);
    ctx.fillStyle=rightColor; ctx.fillText(cfg.rightName, W*0.82, 30);
    // 船（水战）
    if(type==='water'){
      ships.forEach(function(sh){
        ctx.fillStyle = sh.side==='left'?leftColor:rightColor;
        ctx.fillRect(sh.x-34, sh.y, 68, 22);
        ctx.beginPath(); ctx.moveTo(sh.x-34,sh.y); ctx.lineTo(sh.x-46,sh.y+22); ctx.lineTo(sh.x-34,sh.y+22); ctx.fill();
        ctx.beginPath(); ctx.moveTo(sh.x+34,sh.y); ctx.lineTo(sh.x+46,sh.y+22); ctx.lineTo(sh.x+34,sh.y+22); ctx.fill();
      });
    }
    // 士兵
    armyL.concat(armyR).forEach(drawSoldier);
    // 箭
    arrows.forEach(function(a){
      ctx.strokeStyle=a.fire?'#ff7043':'#ffe082'; ctx.lineWidth=2;
      ctx.beginPath(); ctx.moveTo(a.x,a.y);
      ctx.lineTo(a.x+(a.vx>0?10:-10), a.y-4); ctx.stroke();
    });
    // 火花/粒子
    parts.forEach(function(p){
      ctx.globalAlpha=Math.max(0,p.life); ctx.fillStyle=p.c;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
    });
    // 胜利横幅
    if(finished){
      ctx.fillStyle='rgba(0,0,0,0.35)'; ctx.fillRect(0,H/2-34,W,68);
      ctx.font='bold 30px "ZCOOL KuaiLe",sans-serif'; ctx.textAlign='center';
      var txt = (winner==='left'?cfg.leftName:cfg.rightName)+' 胜利！';
      ctx.fillStyle = winner==='left'?leftColor:rightColor;
      ctx.fillText(txt, W/2, H/2+10);
    }
  }
  function step(){
    if(!running){ draw(); return; }
    t+=1;
    // 阶段：0-60 进军；60-130 交锋+放箭；130+ 推进/胜利
    var meetX=W/2;
    armyL.forEach(function(s){ if(s.x<meetX-30) s.x+=2.2; });
    armyR.forEach(function(s){ if(s.x>meetX+30) s.x-=2.2; });
    if(type==='water'){ ships[0].x+=1.1; ships[1].x-=1.1; }
    if(t>50 && t<160 && t%4===0){
      // 放箭
      arrows.push({x:W/2-20,y:H/2-30+(Math.random()*40-20),vx:6,fire:Math.random()<0.4});
      arrows.push({x:W/2+20,y:H/2-30+(Math.random()*40-20),vx:-6,fire:Math.random()<0.4});
    }
    arrows.forEach(function(a){ a.x+=a.vx*3; });
    arrows=arrows.filter(function(a){return a.x>10&&a.x<W-10;});
    // 交锋火花
    if(t>70 && t<150 && Math.random()<0.6){
      parts.push({x:W/2+(Math.random()*40-20),y:H/2+(Math.random()*50-25),vx:(Math.random()-0.5)*4,vy:-Math.random()*3,r:Math.random()*3+1,life:1,c:Math.random()<0.5?'#ffca28':'#ff7043'});
    }
    parts.forEach(function(p){ p.x+=p.vx; p.y+=p.vy; p.vy+=0.15; p.life-=0.03; });
    parts=parts.filter(function(p){return p.life>0;});
    if(t>150){
      // 胜利方推进
      var win = winner==='left'?armyL:armyR;
      win.forEach(function(s){ s.x += winner==='left'?2.4:-2.4; });
      if(!finished && t>200){ finished=true; running=false; showResult(); }
    }
    draw();
    if(running) requestAnimationFrame(step);
  }
  function showResult(){
    var rb=document.getElementById(cfg.resultId);
    if(rb) rb.innerHTML='🏆 '+(winner==='left'?cfg.leftName:cfg.rightName)+' 取得胜利！';
    var btn=document.getElementById(cfg.btnId);
    if(btn){ btn.disabled=false; btn.textContent='再战一次 ⚔️'; }
    running=false;
  }
  draw();
  var btn=document.getElementById(cfg.btnId);
  var narr=document.getElementById(cfg.narrateId);
  if(btn){
    btn.addEventListener('click',function(){
      if(finished){ // 重置
        armyL=makeArmy('left'); armyR=makeArmy('right');
        arrows=[]; parts=[]; t=0; finished=false;
        if(narr) narr.textContent=cfg.narrate;
      }
      running=true; btn.disabled=true; btn.textContent='激战中…';
      if(narr) narr.textContent=cfg.narrate;
      step();
    });
  }
}
"""

# ====================== 页面渲染 ======================
def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def hl_text(s):
    # 把【】包裹的词做成高亮
    import re
    return re.sub(r"【(.+?)】", r'<span class="hl">\1</span>', esc(s))


# ===== 人物名 / 别名 → figures/<id>.html 自动映射 =====
# 让朝代页的重要人物卡片，只要名字能匹配到 figures_data 里的某位人物，
# 就自动加上「看他的故事」跳转链接，无需在 dynasty_data 里逐个手写 story。
from figures_data import FIGURES  # noqa: E402
FIG_MATCH = {}
for _f in FIGURES:
    FIG_MATCH[_f["file"]] = _f["file"]
    for _n in [_f["name"]] + _f.get("match_names", []):
        FIG_MATCH[_n] = _f["file"]


# ====================== 权威疆域地图（本地图片，来源 Wikimedia Commons）======================
# 方案：从维基共享资源（Wikimedia Commons）取权威历史疆域地图，经 wsrv.nl 代理下载到本地 maps/，
#       页面引用同域本地文件，部署到 GitHub Pages 后浏览器可直接加载（不受国内墙限制）。
# 仅在 MAP_IMAGE 中的朝代生效；shang / sui / sanhuang 暂无可用的权威地图，回落到 SVG 引擎（render_hist_map）。
# 元组格式：(本地路径, 许可, 原文件名) —— 许可与原文件名用于页面来源标注。
MAP_IMAGE = {
    "han":    ("maps/han.jpg",    "CC BY-SA 3.0", "Han Civilisation.png"),
    "tang":   ("maps/tang.jpg",   "CC0（公有领域）", "Map of the Tang Empire and Central Asia Protectorates circa 660 CE.png"),
    "xia":    ("maps/xia.jpg",    "CC BY-SA 3.0", "Region of xia.svg"),
    "zhou":   ("maps/zhou.jpg",   "CC BY-SA 3.0", "China Zhou Dynasty.jpg"),
    "qin":    ("maps/qin.jpg",    "CC0（公有领域）", "Qin dynasty territory.svg"),
    "sanguo": ("maps/sanguo.jpg", "Public domain（公有领域）", "Map of China During the Period of the Three Kingdoms.jpg"),
    "jin":    ("maps/jin.jpg",    "Public domain（公有领域）", "The Western Tsin Dynasty 265-316 AD.jpg"),
    "nanbei": ("maps/nanbei.jpg", "CC BY 3.0", "Northern and Southern Dynasties 560 CE.png"),
    "song":   ("maps/song.jpg",   "CC BY-SA 4.0", "China - Song Dynasty-zh.svg"),
    "yuan":   ("maps/yuan.jpg",   "CC BY-SA 4.0", "Yuan dynasty under Kublai Khan.png"),
    "ming":   ("maps/ming.jpg",   "CC BY-SA 4.0", "Ming dynasty under Yongle Emperor.png"),
    "qing":   ("maps/qing.jpg",   "CC0（公有领域）", "Qing Dynasty-1760.png"),
    "wudai":  ("maps/wudai.jpg",  "CC BY 3.0", "Five Dynasties Ten Kingdoms 923 CE.png"),
}
IMG_TPL = """<div style="margin:6px 0 4px">
  <div style="border:3px solid #b8860b;border-radius:14px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.15);background:#fff">
    <img src="__SRC__" alt="__TITLE__" loading="lazy" style="display:block;width:100%;height:auto" />
  </div>
  <p style="font-size:12.5px;color:#6b5b3e;margin:8px 2px 0;text-align:center">🗺️ 地图来源：Wikimedia Commons（文件 <em>__FILE__</em> ｜ 许可 __LIC__）</p>
</div>"""

def render_dynasty(d, idx, total):
    th = d["theme"]
    css = (PAGE_CSS
           .replace("__PRIMARY__", th["primary"])
           .replace("__SECONDARY__", th["secondary"])
           .replace("__ACCENT__", th["accent"]))

    # 章节导航
    nav_items = [
        ("territory","🗺️ 疆域"), ("process","📜 历史进程"), ("features","✨ 特点"),
        ("people","👥 人物"), ("politics","⚖️ 制度文化经济"),
    ]
    if d["battles"]:
        nav_items.append(("battle","⚔️ 战役"))
    nav_items.append(("quiz","📝 小测验"))
    nav_html = "".join(f'<a href="#{a}">{t}</a>' for a,t in nav_items)

    # 疆域
    if d.get("map_markers"):
        mi = MAP_IMAGE.get(d["id"])
        if mi:
            src, lic, fname = mi
            map_html = (IMG_TPL
                        .replace("__SRC__", src)
                        .replace("__TITLE__", d.get("map_title", d["name"] + " · 疆域"))
                        .replace("__FILE__", fname)
                        .replace("__LIC__", lic))
        else:
            map_html = histmap.render_hist_map(
                d["map_region"], d["map_markers"], d["map_rivers"],
                d["map_mountains"], d["map_title"], core=d.get("map_core"),
            )
            map_html = f'<div class="map-wide">{map_html}</div>'
        territory = f'''
    <div class="section" id="territory">
      <div class="sec-head"><div class="sec-badge">🗺️</div>
        <div class="sec-title">疆域范围<small>权威历史疆域地图（来源：维基共享资源）</small></div></div>
      {map_html}
      <div class="map-text" style="margin-top:14px">{hl_text(d['territory'])}</div>
    </div>'''
    else:
        map_html = map_svg(d["region"], th, d["name"])
        territory = f'''
    <div class="section" id="territory">
      <div class="sec-head"><div class="sec-badge">🗺️</div>
        <div class="sec-title">疆域范围<small>这个朝代有多大</small></div></div>
      <div class="map-card">
        <div class="map-svg">{map_html}</div>
        <div class="map-text">{hl_text(d['territory'])}</div>
      </div>
    </div>'''

    # 历史进程
    tl = "".join(f'''
      <div class="tl-item">
        <div class="tl-year">{esc(p['year'])}</div>
        <div class="tl-title">{esc(p['title'])}</div>
        <div class="tl-text">{hl_text(p['text'])}</div>
      </div>''' for p in d["process"])
    process = f'''
    <div class="section" id="process">
      <div class="sec-head"><div class="sec-badge">📜</div>
        <div class="sec-title">历史进程<small>从开创到落幕</small></div></div>
      <div class="timeline">{tl}</div>
    </div>'''

    # 特点
    feats = "".join(f'<li><span class="dot">🌟</span><span>{hl_text(f)}</span></li>' for f in d["features"])
    features = f'''
    <div class="section" id="features">
      <div class="sec-head"><div class="sec-badge">✨</div>
        <div class="sec-title">朝代特点<small>它最特别的地方</small></div></div>
      <ul class="feat-list">{feats}</ul>
    </div>'''

    # 人物
    persons = ""
    for p in d["people"]:
        story = p.get("story") or FIG_MATCH.get(p["name"])
        if story:
            persons += f'''
      <a class="person person-link" href="{esc(story)}">
        <div class="pname">{esc(p['name'])}</div>
        <div class="prole">{esc(p['role'])}</div>
        <div class="pdesc">{hl_text(p['desc'])}</div>
        <div class="pstory">📖 看他的故事 →</div>
      </a>'''
        else:
            persons += f'''
      <div class="person">
        <div class="pname">{esc(p['name'])}</div>
        <div class="prole">{esc(p['role'])}</div>
        <div class="pdesc">{hl_text(p['desc'])}</div>
      </div>'''
    people = f'''
    <div class="section" id="people">
      <div class="sec-head"><div class="sec-badge">👥</div>
        <div class="sec-title">重要人物<small>点一点，跳进去看大人物自己的故事</small></div></div>
      <div class="people-grid">{persons}</div>
    </div>'''

    # 政治/文化/经济 三栏
    mini = f'''
    <div class="section" id="politics">
      <div class="sec-head"><div class="sec-badge">⚖️</div>
        <div class="sec-title">制度 · 文化 · 经济<small>国家怎么管，人们怎么过</small></div></div>
      <div class="mini-grid">
        <div class="mini"><h4>⚖️ 政治制度</h4><p>{hl_text(d['politics'])}</p></div>
        <div class="mini"><h4>🎭 社会文化</h4><p>{hl_text(d['culture'])}</p></div>
        <div class="mini"><h4>💰 经济发展</h4><p>{hl_text(d['economy'])}</p></div>
      </div>
    </div>'''

    # 战役（地图帝风格静态战役图 + Canvas 动画）
    battle_html = ""
    battle_js_calls = ""
    if d["battles"]:
        boxes = ""
        for i,b in enumerate(d["battles"]):
            cid = f"bcanvas{i}"; bid=f"bbtn{i}"; nid=f"bnarr{i}"; rid=f"bres{i}"
            lc = th["secondary"]; rc = "#E74C3C"

            # ---- 战役地图（优先用数据里的 battle_map，否则用 battle_maps.py 统一配置）----
            bmap_html = ""
            bm = b.get("battle_map") or BATTLE_MAPS.get(b["name"])
            if bm:
                bmap_svg = histmap.render_battle_map(
                    region=bm.get("region", d.get("map_region", (110, 42, 14, 12))),
                    title=esc(b['name']),
                    subtitle=bm.get("subtitle", ""),
                    armies=bm.get("armies", []),
                    arrows=bm.get("arrows", []),
                    key_places=bm.get("key_places", []),
                    phases=bm.get("phases", []),
                    water=bm.get("water"),
                    rivers=bm.get("rivers"),
                    width=780, height=520,
                )
                bmap_html = f'''
        <div class="battle-map-wrap">
          {bmap_svg}
        </div>'''

            boxes += f'''
      <div class="battle-box">
        <div class="battle-title">⚔️ {esc(b['name'])}</div>
        <div class="battle-sub">{esc(b['left'])} &nbsp;VS&nbsp; {esc(b['right'])}</div>
        {bmap_html}
        <canvas class="battle-canvas" id="{cid}" width="680" height="300"></canvas>
        <button class="battle-btn" id="{bid}">⚔️ 开战！</button>
        <div class="battle-narrate" id="{nid}">点击「开战！」看看这场大战是怎么打的～</div>
        <div class="battle-result" id="{rid}"></div>
      </div>'''
            battle_js_calls += f"""
      initBattle({{
        canvas:'{cid}', btnId:'{bid}', narrateId:'{nid}', resultId:'{rid}',
        leftName:'{esc(b['left'])}', rightName:'{esc(b['right'])}',
        leftColor:'{lc}', rightColor:'{rc}', winner:'{b['winner']}', type:'{b['type']}',
        narrate:'{esc(b['narrate'])}'
      }});"""
        battle_html = f'''
    <div class="section" id="battle">
      <div class="sec-head"><div class="sec-badge">⚔️</div>
        <div class="sec-title">著名战役<small>动动手指，看大军对决</small></div></div>
      {boxes}
    </div>'''

    # 小测验
    q_html = ""
    for i,q in enumerate(d["quiz"]):
        opts = "".join(
            f'<button class="opt" data-i="{i}" data-o="{j}">'
            f'<b>{chr(65+j)}.</b> {esc(o)}</button>'
            for j,o in enumerate(q["options"]))
        q_html += f'''
      <div class="quiz-q" id="q{i}">
        <div class="q-text">❓ {esc(q['q'])}</div>
        {opts}
        <div class="quiz-explain" id="exp{i}">💡 {esc(q['explain'])}</div>
      </div>'''
    quiz = f'''
    <div class="section" id="quiz">
      <div class="sec-head"><div class="sec-badge">📝</div>
        <div class="sec-title">小测验<small>考考你记住了没</small></div></div>
      <div class="quiz-score">得分：<b id="score">0</b> / {len(d['quiz'])}</div>
      {q_html}
    </div>'''

    # 翻页
    prev_d = DYNASTIES[(idx-1)%total]
    next_d = DYNASTIES[(idx+1)%total]
    pager = f'''
    <div class="pager">
      <a href="{prev_d['id']}.html"><span class="label">← 上一位</span><span class="pname">{esc(prev_d['name'])}</span></a>
      <a href="dynasties.html"><span class="label">↑ 朝代总览</span><span class="pname">全部朝代</span></a>
      <a href="{next_d['id']}.html"><span class="label">下一位 →</span><span class="pname">{esc(next_d['name'])}</span></a>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(d['name'])}的历史 · 上下五千年</title>
<style>{css}</style>
</head>
<body>
<div class="topbar">
  <a class="home-btn" href="index.html">🏠 主页</a>
  <span class="crumb">朝代历史 / <b>{esc(d['name'])}</b></span>
</div>
<nav class="section-nav">{nav_html}</nav>

<header class="hero">
  <div class="blob"></div><div class="blob b2"></div>
  <div class="hero-emoji">{d['emoji']}</div>
  <h1 class="hero-title">{esc(d['name'])}</h1>
  <div class="hero-era">🕰️ {esc(d['era'])}</div>
  <div class="hero-sub">{esc(d['subtitle'])}</div>
  <div class="scroll-hint">向下滚动，开始穿越 ↓</div>
</header>

<main class="wrap">
  {territory}
  {process}
  {features}
  {people}
  {mini}
  {battle_html}
  {quiz}
  {pager}
</main>

<footer>
  <p class="poem">读史明志 · 以史为镜</p>
  <p>— 朝代历史 · 上下五千年 · 给小朋友看的历史 —</p>
</footer>

<script>
{BATTLE_JS}
{battle_js_calls}

// ===== 章节导航高亮 =====
var secNavLinks=document.querySelectorAll('.section-nav a');
var secObserver=new IntersectionObserver(function(entries){{
  entries.forEach(function(e){{
    if(e.isIntersecting){{
      var id=e.target.id;
      secNavLinks.forEach(function(a){{ a.classList.toggle('active', a.getAttribute('href')==='#'+id); }});
    }}
  }});
}},{{threshold:0.3}});
document.querySelectorAll('.section').forEach(function(s){{ if(s.id) secObserver.observe(s); }});

// ===== 滚动入场 =====
var revObserver=new IntersectionObserver(function(entries){{
  entries.forEach(function(e){{ if(e.isIntersecting) e.target.classList.add('visible'); }});
}},{{threshold:0.12}});
document.querySelectorAll('.section').forEach(function(s){{ revObserver.observe(s); }});
document.querySelector('.section').classList.add('visible');

// ===== 小测验 =====
var score=0, answered={{}};
document.querySelectorAll('.quiz-q').forEach(function(qbox){{
  var qi=+qbox.id.replace('q','');
  qbox.querySelectorAll('.opt').forEach(function(btn){{
    btn.addEventListener('click',function(){{
      if(answered[qi]) return;
      answered[qi]=true;
      var correct={d['quiz'][0]['answer'] if False else -1};
      // 正确答案由 data 注入
      var ans=window.__ANS__[qi];
      qbox.querySelectorAll('.opt').forEach(function(b){{
        b.classList.add('disabled');
        if(+b.dataset.o===ans) b.classList.add('correct');
      }});
      if(+btn.dataset.o===ans){{ score++; }} else {{ btn.classList.add('wrong'); }}
      document.getElementById('score').textContent=score;
      document.getElementById('exp'+qi).classList.add('show');
    }});
  }});
}});
</script>
<script>window.__ANS__={json.dumps([q['answer'] for q in d['quiz']])};</script>
</body>
</html>'''
    return html

# ====================== 总览 hub 页 ======================
def render_hub():
    cards = ""
    for d in DYNASTIES:
        th = d["theme"]
        cards += f'''
      <a class="hub-card" href="{d['id']}.html" style="--pc:{th['primary']};--sc:{th['secondary']};--ac:{th['accent']}">
        <div class="hub-emoji">{d['emoji']}</div>
        <div class="hub-name">{esc(d['name'])}</div>
        <div class="hub-era">{esc(d['era'].split('（')[0])}</div>
        <div class="hub-go">去看看 →</div>
      </a>'''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>朝代历史总览 · 上下五千年</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Noto+Sans+SC:wght@400;700;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Noto Sans SC',sans-serif;color:#2C3E50;
  background:linear-gradient(160deg,#FFFDF7,#FFF1E6 50%,#FDE7F0);min-height:100vh;}}
a{{text-decoration:none;color:inherit;}}
.topbar{{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:12px;padding:12px 18px;
  background:rgba(255,253,247,0.92);backdrop-filter:blur(10px);box-shadow:0 2px 16px rgba(0,0,0,0.08);}}
.home-btn{{font-family:'ZCOOL KuaiLe',sans-serif;background:#C0392B;color:#fff;padding:6px 16px;border-radius:20px;font-size:1rem;}}
.hero{{text-align:center;padding:50px 20px 20px;}}
.hero h1{{font-family:'ZCOOL KuaiLe',sans-serif;font-size:clamp(2.4rem,8vw,4.5rem);color:#C0392B;
  text-shadow:3px 3px 0 #fff;}}
.hero p{{font-size:1.1rem;color:#7F8C8D;margin-top:10px;}}
.grid{{max-width:1100px;margin:30px auto;padding:0 20px 60px;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px;}}
.hub-card{{background:#fff;border-radius:22px;padding:22px 16px;text-align:center;
  box-shadow:0 8px 22px rgba(0,0,0,0.1);border-top:6px solid var(--pc);
  transition:transform .25s, box-shadow .25s;}}
.hub-card:hover{{transform:translateY(-8px) scale(1.03);box-shadow:0 16px 34px rgba(0,0,0,0.16);
  border-top-color:var(--sc);}}
.hub-emoji{{font-size:3rem;animation:bob 3s ease-in-out infinite;}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.hub-name{{font-family:'ZCOOL KuaiLe',sans-serif;font-size:1.5rem;color:var(--pc);margin:6px 0;}}
.hub-era{{font-size:.8rem;color:#95A5A6;min-height:34px;}}
.hub-go{{margin-top:8px;font-weight:700;color:var(--sc);font-size:.95rem;}}
footer{{text-align:center;padding:20px;color:#95A5A6;font-size:.85rem;}}
</style>
</head>
<body>
<div class="topbar"><a class="home-btn" href="index.html">🏠 主页</a>
  <span style="font-weight:700;">朝代历史 · 总览</span></div>
<header class="hero">
  <h1>朝代历史大观</h1>
  <p>从三皇五帝到清朝 · 点一点，穿越五千年 👇</p>
</header>
<main class="grid">{cards}</main>
<footer>— 上下五千年 · 给小朋友看的历史 —</footer>
</body>
</html>'''

# ====================== 主流程 ======================
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只生成指定朝代 id（逗号分隔），如 --only sanhuang")
    ap.add_argument("--no-hub", action="store_true", help="不重新生成总览页")
    args = ap.parse_args()

    total = len(DYNASTIES)
    if args.only:
        want = set(args.only.split(","))
        items = [(i, d) for i, d in enumerate(DYNASTIES) if d["id"] in want]
        if not items:
            print("未找到指定 id：", args.only)
            return
    else:
        items = list(enumerate(DYNASTIES))

    for i, d in items:
        html = render_dynasty(d, i, total)
        out = os.path.join(ROOT, d["id"] + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("✓", d["id"] + ".html")

    if not args.no_hub:
        hub = render_hub()
        with open(os.path.join(ROOT, "dynasties.html"), "w", encoding="utf-8") as f:
            f.write(hub)
        print("✓ dynasties.html")
    print(f"本次共生成 {len(items)} 个朝代页面")

if __name__ == "__main__":
    main()
