# -*- coding: utf-8 -*-
"""只推送「三皇五帝」相关改动：sanhuang.html + figures/* + 更新的构建源码。
其余 15 个朝代页在远程保持不变（tree POST 基于 base_tree，只替换列出的文件）。"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = "moneyache/history-stories"

FILES = [
    "sanhuang.html",
    "figures/huangdi.html",
    "figures/yan_di.html",
    "figures/chiyou.html",
    "figures/yao.html",
    "figures/shun.html",
    "figures/yu.html",
    "builder/histmap.py",          # 重写为地图帝风格
    "builder/build_dynasties.py",  # 新增战役地图渲染
    "builder/dynasty_data.py",     # 涿鹿之战加 battle_map 配置
    "builder/figures_data.py",
    "builder/build_figures.py",
]

def gh(args):
    cmd = ["gh", "api"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("GH ERROR: " + " ".join(cmd) + "\n" + p.stderr + "\n")
        sys.exit(1)
    return p.stdout

def gh_json(args):
    return json.loads(gh(args))

print("① 获取当前 main 分支引用…")
ref = gh_json(["/repos/%s/git/refs/heads/main" % REPO])
parent_sha = ref["object"]["sha"]
print("   父提交:", parent_sha[:10])

print("② 获取父提交对应的 tree（作为 base_tree）…")
commit = gh_json(["/repos/%s/git/commits/%s" % (REPO, parent_sha)])
base_tree = commit["tree"]["sha"]
print("   基树:", base_tree[:10])

print("③ 构造 tree（%d 个文件，base_tree 上只替换这些）…" % len(FILES))
tree_entries = []
for rel in FILES:
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    tree_entries.append({"path": rel, "mode": "100644", "type": "blob", "content": content})
body = {"base_tree": base_tree, "tree": tree_entries}
with open("/tmp/tree_body.json", "w", encoding="utf-8") as f:
    json.dump(body, f, ensure_ascii=False)
print("   上传 tree…")
new_tree = gh_json(["-X", "POST", "/repos/%s/git/trees" % REPO, "--input", "/tmp/tree_body.json"])
new_tree_sha = new_tree["sha"]
print("   新树:", new_tree_sha[:10])

print("④ 创建提交…")
msg = "feat(三皇五帝): 地图帝风格地图引擎+涿鹿之战战役地图+人物跳转"
cbody = {"message": msg, "tree": new_tree_sha, "parents": [parent_sha]}
with open("/tmp/commit_body.json", "w", encoding="utf-8") as f:
    json.dump(cbody, f, ensure_ascii=False)
new_commit = gh_json(["-X", "POST", "/repos/%s/git/commits" % REPO, "--input", "/tmp/commit_body.json"])
new_commit_sha = new_commit["sha"]
print("   新提交:", new_commit_sha[:10])

print("⑤ 更新 main 分支引用…")
rbody = {"sha": new_commit_sha, "force": False}
with open("/tmp/ref_body.json", "w", encoding="utf-8") as f:
    json.dump(rbody, f, ensure_ascii=False)
gh(["-X", "PATCH", "/repos/%s/git/refs/heads/main" % REPO, "--input", "/tmp/ref_body.json"])
print("✅ 推送成功！")
print("   提交:", new_commit_sha)
print("   三皇五帝: https://moneyache.github.io/history-stories/sanhuang.html")
print("   黄帝故事: https://moneyache.github.io/history-stories/figures/huangdi.html")
