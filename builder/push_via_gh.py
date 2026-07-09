# -*- coding: utf-8 -*-
"""通过 gh api（Git Database API）把本地文件推送到 GitHub，绕过被屏蔽的 git/HTTPS 传输。
正确处理二进制（图片）：文本用 utf-8、二进制用 base64，经 /git/blobs 创建后组装 tree+commit。
需要：gh 已登录且拥有 repo 权限。
设置环境变量 DRY_RUN=1 可只打印待推送文件列表而不实际推送。
"""
import os, sys, json, subprocess, base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = "moneyache/history-stories"
DRY = os.environ.get("DRY_RUN") == "1"

# ---------- 收集待推送文件 ----------
FILES = []
# 根目录所有 html（含 index / dynasties / 16 朝代 / caocao / zhuyuanzhang 等）
for fn in sorted(os.listdir(ROOT)):
    if fn.endswith(".html"):
        FILES.append(fn)
# maps/ 下所有文件（地图图片，二进制）
maps_dir = os.path.join(ROOT, "maps")
if os.path.isdir(maps_dir):
    for fn in sorted(os.listdir(maps_dir)):
        FILES.append(os.path.join("maps", fn))
# builder/ 下所有 .py
builder_dir = os.path.join(ROOT, "builder")
if os.path.isdir(builder_dir):
    for fn in sorted(os.listdir(builder_dir)):
        if fn.endswith(".py"):
            FILES.append(os.path.join("builder", fn))
# figures/ 下所有 .html（人物故事页）
fig_dir = os.path.join(ROOT, "figures")
if os.path.isdir(fig_dir):
    for fn in sorted(os.listdir(fig_dir)):
        if fn.endswith(".html"):
            FILES.append(os.path.join("figures", fn))

# 本地已删除的 stale 孤儿页：部署时显式删除（sha=null）
DELETES = ["caocao.html", "zhuyuanzhang.html"]


def gh(args):
    cmd = ["gh", "api"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("GH ERROR: " + " ".join(cmd) + "\n" + p.stderr + "\n")
        sys.exit(1)
    return p.stdout


def gh_json(args):
    return json.loads(gh(args))


def make_blob(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
        body = {"content": text, "encoding": "utf-8"}
    except UnicodeDecodeError:
        body = {"content": base64.b64encode(data).decode("ascii"), "encoding": "base64"}
    with open("/tmp/blob_body.json", "w") as f:
        json.dump(body, f)
    out = gh_json(["-X", "POST", "/repos/%s/git/blobs" % REPO, "--input", "/tmp/blob_body.json"])
    return out["sha"]


if DRY:
    print("【DRY_RUN】待推送 %d 个文件：" % len(FILES))
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        sz = os.path.getsize(p)
        print("  %8d B  %s" % (sz, rel))
    sys.exit(0)

print("① 获取当前 main 分支引用…")
ref = gh_json(["/repos/%s/git/refs/heads/main" % REPO])
parent_sha = ref["object"]["sha"]
print("   父提交:", parent_sha[:10])

print("② 获取父提交对应的 tree…")
commit = gh_json(["/repos/%s/git/commits/%s" % (REPO, parent_sha)])
base_tree = commit["tree"]["sha"]
print("   基树:", base_tree[:10])

print("③ 创建 %d 个 blob…" % len(FILES))
entries = []
for rel in FILES:
    path = os.path.join(ROOT, rel)
    sha = make_blob(path)
    entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": sha})
    print("   ✓", rel)

# 显式删除本地已移除的孤儿页（Git DB API：sha=null 即删除，需带 mode/type）
for d in DELETES:
    entries.append({"path": d, "mode": "100644", "type": "blob", "sha": None})
    print("   ✗ (delete)", d)

print("④ 构造 tree（基于基树，未列出的文件自动保留）…")
body = {"base_tree": base_tree, "tree": entries}
with open("/tmp/tree_body.json", "w") as f:
    json.dump(body, f, ensure_ascii=False)
new_tree = gh_json(["-X", "POST", "/repos/%s/git/trees" % REPO, "--input", "/tmp/tree_body.json"])
new_tree_sha = new_tree["sha"]
print("   新树:", new_tree_sha[:10])

print("⑤ 创建提交…")
msg = "feat: 历史人物故事页内容深度升级（去奶化+历史影响+深度题）+ 规范人物页至 figures/ 目录"
cbody = {"message": msg, "tree": new_tree_sha, "parents": [parent_sha]}
with open("/tmp/commit_body.json", "w") as f:
    json.dump(cbody, f, ensure_ascii=False)
new_commit = gh_json(["-X", "POST", "/repos/%s/git/commits" % REPO, "--input", "/tmp/commit_body.json"])
new_commit_sha = new_commit["sha"]
print("   新提交:", new_commit_sha[:10])

print("⑥ 更新 main 分支引用…")
rbody = {"sha": new_commit_sha, "force": False}
with open("/tmp/ref_body.json", "w") as f:
    json.dump(rbody, f, ensure_ascii=False)
gh(["-X", "PATCH", "/repos/%s/git/refs/heads/main" % REPO, "--input", "/tmp/ref_body.json"])
print("✅ 推送成功！")
print("   提交:", new_commit_sha)
print("   站点: https://moneyache.github.io/history-stories/")
print("   朝代总览: https://moneyache.github.io/history-stories/dynasties.html")
