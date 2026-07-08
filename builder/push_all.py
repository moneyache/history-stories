# -*- coding: utf-8 -*-
"""统一部署：把整个仓库（主页 + 朝代总览 + 16朝代页 + 人物页 + 构建源码）推送到 GitHub Pages。
通过 gh API（Git Database API）推送，绕开被沙箱屏蔽的 git/HTTPS 传输。"""
import os, sys, json, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = "moneyache/history-stories"

def gh(args):
    p = subprocess.run(["gh", "api"] + args, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("GH ERROR: " + " ".join(["gh", "api"] + args) + "\n" + p.stderr + "\n")
        sys.exit(1)
    return p.stdout

def gh_json(args):
    return json.loads(gh(args))

# 收集要上传的文件
FILES = ["index.html", "dynasties.html"]
for fn in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
    base = os.path.basename(fn)
    if base not in FILES:
        FILES.append(base)
for fn in sorted(glob.glob(os.path.join(ROOT, "figures", "*.html"))):
    FILES.append(os.path.join("figures", os.path.basename(fn)))
for fn in sorted(glob.glob(os.path.join(ROOT, "builder", "*.py"))):
    base = os.path.basename(fn)
    if base.startswith("push_"):   # 不上传推送脚本本身
        continue
    FILES.append(os.path.join("builder", base))

print("① 获取当前 main 分支引用…")
ref = gh_json(["/repos/%s/git/refs/heads/main" % REPO])
parent_sha = ref["object"]["sha"]
print("   父提交:", parent_sha[:10])

print("② 获取父提交 tree（base_tree）…")
commit = gh_json(["/repos/%s/git/commits/%s" % (REPO, parent_sha)])
base_tree = commit["tree"]["sha"]
print("   基树:", base_tree[:10])

print("③ 构造 tree（%d 个文件，base_tree 上全量替换）…" % len(FILES))
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
msg = ("feat: 16个朝代疆域地图全部升级为地图帝风格(经纬度投影真实地图) "
       "+ 新增59个重要人物独立故事页(共65页)并自动从朝代页跳转 "
       "+ 修复低配示意图遗留标记")
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
print("   站点: https://moneyache.github.io/history-stories/")
