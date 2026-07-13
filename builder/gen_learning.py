"""
生成 learning.html — 个人学习记录页
从 dynasty_data.py / figures_data.py 读取内容列表，嵌入到页面中
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(ROOT, "builder")
sys.path.insert(0, BUILDER)

from dynasty_data import DYNASTIES
from figures_data import FIGURES

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;").replace('"', "&quot;")

# 朝代列表
dyns = []
for d in DYNASTIES:
    dyns.append({"id": d["id"], "name": d["name"], "emoji": d.get("emoji", "🏯")})

# 人物列表（只取信息，不取故事正文）
figs = []
for f in FIGURES:
    figs.append({"id": f["file"].replace("figures/", "").replace(".html", ""), "file": f["file"], "name": f["name"], "emoji": f.get("emoji", "🧑")})

dyn_json = json.dumps(dyns, ensure_ascii=False)
fig_json = json.dumps(figs, ensure_ascii=False)

css = '''
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  background:#0d0a06;color:#d4c5a0;min-height:100vh;}
/* ===== 导航 ===== */
.auth-topbar{position:fixed;top:0;left:0;right:0;z-index:500;
  display:flex;align-items:center;gap:12px;padding:8px 18px;
  background:rgba(13,10,6,0.94);backdrop-filter:blur(10px);
  border-bottom:1px solid rgba(200,164,92,0.15);}
.auth-topbar .auth-home{font-family:"Ma Shan Zheng","KaiTi",cursive;
  color:#c8a45c;font-size:1.1rem;text-decoration:none;transition:opacity .2s;}
.auth-topbar .auth-home:hover{opacity:.8;}
.auth-status{display:flex;align-items:center;gap:8px;margin-left:auto;
  font-size:.85rem;opacity:0;transition:opacity .3s;}
.auth-status.auth-loaded{opacity:1;}
.auth-user{color:#c8a45c;font-weight:700;}
.auth-login,.auth-register,.auth-logout{color:#a09070;text-decoration:none;
  padding:4px 10px;border-radius:12px;font-size:.8rem;transition:all .2s;}
.auth-login:hover,.auth-register:hover{color:#c8a45c;background:rgba(200,164,92,0.1);}
.auth-logout:hover{color:#e74c3c;}

/* ===== 页面容器 ===== */
.lr-container{max-width:800px;margin:0 auto;padding:70px 16px 40px;}
.lr-title{font-family:"ZCOOL KuaiLe","Ma Shan Zheng",cursive;
  font-size:clamp(1.5rem,4vw,2rem);color:#c8a45c;text-align:center;margin-bottom:8px;}
.lr-title .uname{color:#e8c84a;}

/* ===== 星星展示 ===== */
.lr-stars-box{text-align:center;margin:20px 0 8px;padding:24px 16px;
  background:linear-gradient(135deg,rgba(200,164,92,0.08),rgba(200,164,92,0.02));
  border-radius:20px;border:1px solid rgba(200,164,92,0.15);}
.lr-stars-display{font-size:2.5rem;letter-spacing:6px;margin-bottom:6px;
  line-height:1.4;}
.lr-stars-count{font-size:1.1rem;color:#a09070;margin-bottom:4px;}
.lr-stars-legend{font-size:.8rem;color:#6a5d4a;}
.lr-breakdown{text-align:center;font-size:.9rem;color:#a09070;margin-bottom:20px;}

/* ===== 分区标题 ===== */
.lr-section{margin-top:32px;}
.lr-sec-title{font-family:"Ma Shan Zheng","KaiTi",cursive;
  font-size:1.35rem;color:#c8a45c;margin-bottom:16px;
  border-bottom:2px solid rgba(200,164,92,0.2);padding-bottom:8px;}
.lr-sub{font-size:1rem;color:#a09070;margin:14px 0 10px;padding-left:4px;}

/* ===== 卡片网格 ===== */
.lr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;}
.lr-card{padding:12px 16px;border-radius:14px;
  display:flex;align-items:center;gap:10px;
  transition:transform .2s,box-shadow .2s;}
.lr-card.done{background:rgba(39,174,96,0.1);border:1px solid rgba(39,174,96,0.2);}
.lr-card.todo{background:rgba(255,255,255,0.03);border:1px solid rgba(200,164,92,0.08);text-decoration:none;color:inherit;}
.lr-card.todo:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(200,164,92,0.1);}
.lr-icon{font-size:1.3rem;}
.lr-name{flex:1;font-size:.95rem;font-weight:600;color:#d4c5a0;}
.lr-stars{font-size:.9rem;color:#f1c40f;}
.lr-date{font-size:.75rem;color:#6a5d4a;}
.lr-go{font-size:.8rem;color:#c8a45c;white-space:nowrap;}

/* ===== 状态提示 ===== */
.lr-empty,.lr-loading,.lr-error,.lr-complete{text-align:center;padding:40px 20px;
  font-size:1.1rem;color:#a09070;}
.lr-complete{color:#27ae60;font-size:1.3rem;font-weight:700;}
.lr-empty a,.lr-error a{color:#c8a45c;}

/* ===== 响应式 ===== */
@media(max-width:480px){
  .lr-grid{grid-template-columns:1fr;}
  .lr-stars-display{font-size:2rem;}
}

/* ===== 星星动画 keyframes（与 learning.js 一致） ===== */
@keyframes starFlyUp{0%{bottom:-60px;opacity:0;transform:scale(0.3) rotate(-20deg);}30%{opacity:1;transform:scale(1.3) rotate(10deg);}70%{opacity:1;transform:scale(1) rotate(0deg);}100%{bottom:105%;opacity:0;transform:scale(0.5) rotate(20deg);}}
'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>学习记录 · 上下五千年</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#C0392B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="上下五千年">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<style>{css}</style>
</head>
<body>

<div class="auth-topbar">
  <a href="index.html" class="auth-home">🏠 上下五千年</a>
  <a href="dynasties.html" class="auth-home" style="font-size:0.9rem;margin-left:4px">朝代</a>
  <a href="learning.html" class="auth-home" style="font-size:0.9rem;margin-left:4px;color:#f1c40f">📚 学习记录</a>
  <div class="auth-status"></div>
</div>

<div class="lr-container" id="learning-main">
  <div class="lr-loading">加载中...</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="https://cdn.jsdelivr.net/npm/crypto-js@4.2.0/crypto-js.js"></script>
<script src="auth.js"></script>
<script src="learning.js"></script>
<script>
  window.__PAGE_TYPE__ = 'learning';
  window.__ALL_DYNASTIES__ = {dyn_json};
  window.__ALL_FIGURES__ = {fig_json};
</script>
<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('/history-stories/sw.js');</script>
</body>
</html>'''

out_path = os.path.join(ROOT, "learning.html")
with open(out_path, "w", encoding="utf-8") as fp:
    fp.write(html)
print(f"✓ 生成 learning.html（{len(dyns)} 个朝代 + {len(figs)} 个人物）")
