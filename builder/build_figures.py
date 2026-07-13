# -*- coding: utf-8 -*-
"""把 figures_data.py 里的人物渲染成童趣人物故事页 figures/<id>.html。
页面风格与朝代页（build_dynasties.py）统一：顶部返回栏、HERO、章节导航、
滚动入场、小测验、可跳转回朝代页。从 sanhuang.html 的人物卡片点进来。
运行：python3 builder/build_figures.py
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figures_data import FIGURES  # noqa
from build_dynasties import PAGE_CSS, BATTLE_JS, esc, hl_text  # 复用样式与战斗JS

ROOT = os.path.dirname(HERE)  # 仓库根目录
FIG_DIR = os.path.join(ROOT, "figures")


def css(theme):
    return (PAGE_CSS
            .replace("__PRIMARY__", theme["primary"])
            .replace("__SECONDARY__", theme["secondary"])
            .replace("__ACCENT__", theme["accent"]))


def render(f, idx, total):
    th = f["theme"]
    c = css(th)
    # 动态来源朝代（不再写死"三皇五帝"）
    dyn_id = f.get("dynasty_id", "sanhuang")
    dyn_name = f.get("dynasty_name", "三皇五帝")
    back_href = "../%s.html" % dyn_id

    nav_items = [
        ("who", "👤 他是谁"), ("story", "📖 他的故事"),
        ("achv", "🏆 他的成就"), ("fun", "💡 趣闻"), ("quiz", "📝 小测验"),
    ]
    nav_html = "".join(f'<a href="#{a}">{t}</a>' for a, t in nav_items)

    # 他是谁
    who = f'''
    <div class="section" id="who">
      <div class="sec-head"><div class="sec-badge">👤</div>
        <div class="sec-title">他是谁<small>先认识一下这位大人物</small></div></div>
      <div class="sec-body"><p>{hl_text(f['who'])}</p></div>
    </div>'''

    # 他的故事（时间轴）
    tl = "".join(f'''
      <div class="tl-item">
        <div class="tl-year">{esc(p['year'])}</div>
        <div class="tl-title">{esc(p['title'])}</div>
        <div class="tl-text">{hl_text(p['text'])}</div>
      </div>''' for p in f["story"])
    story = f'''
    <div class="section" id="story">
      <div class="sec-head"><div class="sec-badge">📖</div>
        <div class="sec-title">他的故事<small>一生中发生的大事</small></div></div>
      <div class="timeline">{tl}</div>
    </div>'''

    # 他的成就
    ach = "".join(f'<li><span class="dot">🏆</span><span>{hl_text(a)}</span></li>' for a in f["achievements"])
    achv = f'''
    <div class="section" id="achv">
      <div class="sec-head"><div class="sec-badge">🏆</div>
        <div class="sec-title">他的成就<small>他给后人留下了什么</small></div></div>
      <ul class="feat-list">{ach}</ul>
    </div>'''

    # 趣闻
    fun = f'''
    <div class="section" id="fun">
      <div class="sec-head"><div class="sec-badge">💡</div>
        <div class="sec-title">趣闻小故事<small>一个好玩的小插曲</small></div></div>
      <div class="sec-body"><p>{hl_text(f['fun'])}</p></div>
    </div>'''

    # 战役（可选）
    battle_html = ""
    battle_js_calls = ""
    if f.get("battle"):
        b = f["battle"]
        cid, bid, nid, rid = "bcanvas0", "bbtn0", "bnarr0", "bres0"
        lc, rc = th["secondary"], "#E74C3C"
        battle_html = f'''
    <div class="section" id="battle">
      <div class="sec-head"><div class="sec-badge">⚔️</div>
        <div class="sec-title">著名战役<small>动动手指，看大军对决</small></div></div>
      <div class="battle-box">
        <div class="battle-title">⚔️ {esc(b['name'])}</div>
        <div class="battle-sub">{esc(b['left'])} &nbsp;VS&nbsp; {esc(b['right'])}</div>
        <canvas class="battle-canvas" id="{cid}" width="680" height="300"></canvas>
        <button class="battle-btn" id="{bid}">⚔️ 开战！</button>
        <div class="battle-narrate" id="{nid}">点击「开战！」看看这场大战是怎么打的～</div>
        <div class="battle-result" id="{rid}"></div>
      </div>
    </div>'''
        battle_js_calls = f"""
      initBattle({{
        canvas:'{cid}', btnId:'{bid}', narrateId:'{nid}', resultId:'{rid}',
        leftName:'{esc(b['left'])}', rightName:'{esc(b['right'])}',
        leftColor:'{lc}', rightColor:'{rc}', winner:'{b['winner']}', type:'{b['type']}',
        narrate:'{esc(b['narrate'])}'
      }});"""

    # 小测验
    q_html = ""
    for i, q in enumerate(f["quiz"]):
        opts = "".join(
            f'<button class="opt" data-i="{i}" data-o="{j}">'
            f'<b>{chr(65+j)}.</b> {esc(o)}</button>'
            for j, o in enumerate(q["options"]))
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
      <div class="quiz-score">得分：<b id="score">0</b> / {len(f['quiz'])}</div>
      {q_html}
    </div>'''

    # 翻页（回到朝代页 / 总览 / 主页，注意在子目录要用 ../）
    pager = f'''
    <div class="pager">
      <a href="{back_href}"><span class="label">← 回到{dyn_name}</span><span class="pname">{dyn_name}</span></a>
      <a href="../dynasties.html"><span class="label">↑ 朝代总览</span><span class="pname">全部朝代</span></a>
      <a href="../index.html"><span class="label">🏠 主页</span><span class="pname">上下五千年</span></a>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(f['name'])}的故事 · {dyn_name}</title>
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#C0392B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="上下五千年">
<link rel="apple-touch-icon" href="../icons/icon-192.png">
<style>{c}</style>
</head>
<body>
<div class="topbar">
  <a class="home-btn" href="../index.html">🏠 主页</a>
  <a class="home-btn" href="../learning.html" style="background:#f39c12">📚 学习</a>
  <span class="crumb">{dyn_name} / <b>{esc(f['name'])}</b></span>
  <div class="auth-status"></div>
</div>
<nav class="section-nav">{nav_html}</nav>

<header class="hero">
  <div class="blob"></div><div class="blob b2"></div>
  <div class="hero-emoji">{f['emoji']}</div>
  <h1 class="hero-title">{esc(f['name'])}</h1>
  <div class="hero-era">🕰️ {esc(f['era'])}</div>
  <div class="hero-sub">{esc(f['role'])}</div>
  <div class="scroll-hint">向下滚动，听他的故事 ↓</div>
</header>

<main class="wrap">
  {who}
  {story}
  {achv}
  {fun}
  {battle_html}
  {quiz}
  {pager}
</main>

<footer>
  <p class="poem">读史明志 · 以史为镜</p>
  <p>— {dyn_name} · 大人物小故事 · 给小朋友看的历史 —</p>
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="https://cdn.jsdelivr.net/npm/crypto-js@4.2.0/crypto-js.js"></script>
<script src="../auth.js"></script>
<script src="../learning.js"></script>
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
var score=0, answered={{}}, quizCompleted=false;
var QUIZ_TOTAL={len(f['quiz'])};
document.querySelectorAll('.quiz-q').forEach(function(qbox){{
  var qi=+qbox.id.replace('q','');
  qbox.querySelectorAll('.opt').forEach(function(btn){{
    btn.addEventListener('click',function(){{
      if(answered[qi]) return;
      answered[qi]=true;
      var ans=window.__ANS__[qi];
      qbox.querySelectorAll('.opt').forEach(function(b){{
        b.classList.add('disabled');
        if(+b.dataset.o===ans) b.classList.add('correct');
      }});
      if(+btn.dataset.o===ans){{ score++; }} else {{ btn.classList.add('wrong'); }}
      document.getElementById('score').textContent=score;
      document.getElementById('exp'+qi).classList.add('show');
      // 检查是否全部答完
      if(!quizCompleted && Object.keys(answered).length===QUIZ_TOTAL){{
        quizCompleted=true;
        onQuizComplete('figure','{esc(f["file"].replace("figures/","").replace(".html",""))}','{esc(f["name"])}',1);
      }}
    }});
  }});
}});
</script>
<script>window.__ANS__={json.dumps([q['answer'] for q in f['quiz']])};</script>
<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('/history-stories/sw.js');</script>
</body>
</html>'''
    return html


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    total = len(FIGURES)
    for i, f in enumerate(FIGURES):
        html = render(f, i, total)
        out = os.path.join(ROOT, f["file"])  # file 含 figures/ 前缀
        with open(out, "w", encoding="utf-8") as fp:
            fp.write(html)
        print("✓", f["file"])
    print(f"共生成 {total} 个人物故事页 → figures/")


if __name__ == "__main__":
    main()
