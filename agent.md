# 朝代历史学习项目 · agent.md

> 给 AI 助手的项目上下文。子项目归属：给儿子做的「上下五千年」互动历史学习站。
> 仓库：`moneyache/history-stories` ｜ 线上：`https://moneyache.github.io/history-stories/`

## 1. 项目定位
纯静态 HTML 站，GitHub Pages 托管。每个朝代一页（疆域 / 历史进程时间轴 / 特点 / 重要人物 / 制度·文化·经济三栏 / 著名战役 canvas 动画 / 小测验），三皇五帝人物可跳转独立故事页。无构建框架，由 `builder/` 下的 Python 脚本生成。

## 2. 目录结构
| 路径 | 说明 |
|------|------|
| `index.html` | 主页，红色大按钮「朝代历史大全」→ `dynasties.html` |
| `dynasties.html` | 16 朝代总览 |
| `<朝代id>.html`（16 个） | 朝代页：han / tang / xia / zhou / qin / sanguo / jin / nanbei / song / yuan / ming / qing / wudai / shang / sui / sanhuang |
| `caocao.html` / `zhuyuanzhang.html` | 早期独立人物故事页，不在 16 朝代生成流程内 |
| `figures/` | 三皇五帝人物故事页（huangdi / yan_di / chiyou / yao / shun / yu.html） |
| `maps/` | 13 张朝代疆域地图 jpg（来自 Wikimedia Commons，已本地化） |
| `builder/` | 全部生成脚本（见下） |

## 3. builder 脚本
| 脚本 | 职责 |
|------|------|
| `build_dynasties.py` | 主生成器。读 `dynasty_data.py`，输出 16 朝代页 + index/dynasties。支持 `--only <id>` 只重建指定朝代（逗号分隔）。 |
| `build_figures.py` | 读 `figures_data.py`，生成 `figures/*.html` 人物页（复用朝代页样式与战斗 JS）。 |
| `dynasty_data.py` | 16 朝代结构化数据（疆域/进程/人物/战役/测验）。 |
| `figures_data.py` | 人物故事数据。 |
| `histmap.py` | 地理精确 SVG 地图引擎（中国轮廓/黄河长江/山脉/标注/罗盘比例尺），用于无权威地图的朝代。 |
| `battle_maps.py` | 战役战斗动画（canvas）。 |
| `push_via_gh.py` | **全量推送**到 GitHub（gh api，二进制安全）。 |
| `push_sanhuang.py` | **增量推送**仅三皇五帝相关文件（sanhuang.html + figures/* + 部分 builder）。 |
| `push_all.py` | 早期推送脚本，已弃用（仅内联文本会损坏二进制图片），勿再用。 |
| `gen_icons.py` | 生成 PWA 图标（192x192 + 512x512 PNG）。 |

## 4. 地图方案（关键）
- **15 个朝代**（除 sanhuang 外）用权威历史疆域图：从 Wikimedia Commons 取图，经 `wsrv.nl` 代理下载到 `maps/<id>.jpg`，页面引用同域本地文件（部署后浏览器直连加载，不受国内墙限制）。
- 页面底部标注来源：`地图来源：Wikimedia Commons（文件 <原名> ｜ 许可 <许可>）`。
- **仅 sanhuang** 无可用权威地图，回落 `histmap.render_hist_map()` 的 SVG 引擎（shang / sui 已于 2026-07-08 补上权威地图）。
- 映射表在 `build_dynasties.py` 的 `MAP_IMAGE` 字典（15 条）。注意 `upload.wikimedia.org` 直连被墙，必须用 `wsrv.nl` 代理 + `quote(u, safe=':/')` 仅编码文件名；频繁下载会 429，需重试+延时。下载时务必用**绝对路径** + `curl -fsS`，否则沙箱里相对路径+URL `&` 会被 shell 误处理导致文件不落盘。

## 5. 部署 / 推送（关键，有坑）
- ✅ **常规推送用 `git push` 即可**（2026-07-11 验证通过：本机 `git` over HTTPS 连 GitHub 正常，`git push origin main` 成功 `5a701c7..1383715`）。
  - 前置：需配 git 身份（`git config --global user.name "钱腾"` / `user.email "qianteng@QtHomeMac.local"`，仓库级已配）；remote 已设 `origin = https://github.com/moneyache/history-stories.git`。
  - 工作流：改文件 → `git add -A` → `git commit` → `git push origin main`（GitHub Pages 自动重建）。
  - 注意：改 `.gitignore` 等应先提交/stash，避免 `git checkout -- .` 或 `git reset --hard` 回退未提交改动；`git clean -fd` 会清掉未忽略的未跟踪目录（曾误删 `.workbuddy/`，已加进 `.gitignore` 隔离）。
- 🔁 `gh` CLI 走 **GitHub Git Database API** 作为备用方案（沙箱若禁用 git 传输，或需精细控制远端 tree 时用）：
  - `push_via_gh.py`：blobs（文本 utf-8 / 二进制 base64）→ tree（基于 base_tree，未列出的远程文件自动保留）→ commit → 更新 main 引用。覆盖根 html + `maps/*.jpg`（二进制）+ `builder/*.py`。
  - `push_sanhuang.py`：只替换列出的三皇五帝相关文件，其余远程页保持不变。
  - `DRY_RUN=1 python3 builder/push_via_gh.py` 可只打印待推送文件列表。
- ⚠️ 推送后 **GitHub Pages 有 ~40s 缓存**，刚推送完图片可能 404，需等待部署完成再验证（用 `curl` 而非 WebFetch 验证线上状态，WebFetch 可能有陈旧缓存）。
- ⚠️ `gh` 偶尔限流（429 too many requests），遇 429 等待重试即可。

## 6. 用户偏好 / 约定
- **迭代式开发**：先搞定三皇五帝让用户看是否满意，再扩展后续朝代——不要一次性全做。
- 聚焦推送：改动小范围时用 `push_sanhuang.py`，不要每次全量推送。
- 用户审美要求高：嫌旧版疆域地图「太水」（紫色椭圆+图钉），已升级为接近谭其骧《中国历史地图集》风格的 `histmap.py`（真实经纬度投影）。
- 朝代页固定含：疆域 / 历史进程时间轴 / 特点 / 重要人物 / 制度·文化·经济三栏 / 著名战役(canvas 动画) / 小测验(交互判分)。
- **内容深度标准（2026-07-09 确立，分支 `content-depth-upgrade`）**：用户认为原文案对一个小学生「太幼稚」，已整体升级为「稍丰富有深度」档。升级铁律：① 去奶化语言（不写「香喷喷的熟食」「好首领」），保留画面感与趣味；② 每个知识点多问一层「为什么 / 机制 / 后来怎样」（如启立世袭→国家变大后选贤难管理的制度演进）；③ features 从 3 条扩到 4-5 条，每条带影响；④ **人物要丰富**：必含「中兴之主」（如少康/光武帝/周宣王/宇文邕/柴荣/张居正）与「亡国之君」（如有特点：汉平帝·孺子婴/汉献帝/桀/纣/胡亥/晋惠帝/陈后主/唐哀帝/刘禅/宋徽宗/元顺帝/崇祯/宣统）；⑤ 小测验每朝代加 2 道深度思辨题（非纯死记）。此标准同样适用于 figures/ 人物页（待批量升级）。

## 7. PWA 支持（2026-07-13）

已全站添加 PWA 支持：
- `manifest.json`：App名"上下五千年"、独立窗口模式(display:standalone)、主题色#C0392B
- `sw.js`：Service Worker，cache-first缓存静态资源(图片/CSS/JS)、network-first更新HTML
- `icons/`：192x192 + 512x512 PNG 图标（山水印章风格，红日+褐山+蓝水）
- 所有页面（index.html + 16朝代页 + dynasties.html + 106个人物页）已注入：`<link rel="manifest">` / `<meta name="theme-color">` / Apple PWA 标签 / SW 注册脚本

**手机端使用**：用浏览器打开线上地址 → Safari/Chrome "分享→添加到主屏幕" → 独立App图标打开，无地址栏，支持离线缓存。

## 8. 常用命令
```bash
cd ~/github-workspace/儿子历史故事学习
python3 builder/build_dynasties.py                        # 全量重建 16 朝代
python3 builder/build_dynasties.py --only sanhuang        # 只重建三皇五帝页
python3 builder/build_figures.py                          # 重建人物页
python3 builder/push_via_gh.py                            # 全量推送到 GitHub Pages
DRY_RUN=1 python3 builder/push_via_gh.py                   # 预览待推送文件
python3 builder/push_sanhuang.py                          # 只推送三皇五帝改动
```
