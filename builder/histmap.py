# -*- coding: utf-8 -*-
"""
历史地图 SVG 引擎 —— 「地图帝」风格
====================================
参考谭其骧《中国历史地图集》与「地图帝」公众号的视觉风格：
  - 地形底色分层渲染（海洋蓝 / 平原米黄 / 山地绿褐 / 高原棕）
  - 粗线蓝色水系（黄河 / 长江 / 淮河 / 海河）
  - 可识别的中国海岸线轮廓
  - 中文大字地名标注（主名 + 今地小字）
  - 左侧 / 左下角 图例框（带符号说明）
  - 右上角罗盘 + 比例尺
  - 战役模式额外支持：渐变箭头路线、编号阶段圈、日期文字

输出为自包含 <svg> 字符串，可直接嵌入 HTML。
"""

import math

# ================================================================
# 投影：等距圆柱投影（带纬度余弦校正）
# ================================================================
def make_proj(lon0, lat_top, span_lon, span_lat, W, H, mx=30, my=30):
    """返回 proj(lon,lat)->(x,y) 函数和尺寸字典。"""
    sy = (H - 2 * my) / span_lat
    sx = sy * math.cos(math.radians(35.5))
    def proj(lon, lat):
        return (mx + (lon - lon0) * sx, my + (lat_top - lat) * sy)
    return proj, dict(mx=mx, my=my, sx=sx, sy=sy, W=W, H=H)


# ================================================================
# 平滑路径
# ================================================================
def smooth_path(pts, closed=True, tension=1.0):
    if len(pts) < 3:
        d = "M%.1f,%.1f" % pts[0]
        for p in pts[1:]:
            d += " L%.1f,%.1f" % p
        return d
    P = list(pts)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
        start = 1
        end = len(P) - 2
    else:
        P = [P[0]] + P + [P[-1]]
        start = 1
        end = len(P) - 2
    d = "M%.1f,%.1f" % P[start]
    for i in range(start, end):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += " C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        d += " Z"
    return d


# ================================================================
# 中国海岸线锚点（简化但可识别）
# ================================================================
CHINA_COAST = [
    (135.5, 49), (133, 47.5), (130, 45.5), (127, 42), (125, 40),
    (123, 39), (122, 37.5), (121, 36), (120.5, 34.5), (121, 33),
    (121.5, 31.5), (121, 30), (120, 28.5), (118.5, 27), (117, 25.5),
    (115.5, 23.5), (113.5, 22.5), (111.8, 21.5), (110.3, 21),
    (108.5, 21.2), (107.8, 19.5), (106.5, 18.5), (109.5, 18.4),
    (110.7, 17.3), (110, 16.5), (108, 15),
]

HAINAN_POLY = [(109.5, 20.2), (110.6, 20), (111, 19), (110.3, 18.2), (109.2, 18.8), (108.8, 19.6)]

TAIWAN_POLY = [(121.5, 25.2), (122, 24), (121.5, 22.8), (120.8, 22.2), (120.5, 23.5)]


# ================================================================
# 地形区域定义（用于底色分层）
# ================================================================
TERRAIN_REGIONS = {
    # 各区域的 (lon,lat) 多边形，按绘制顺序（先画大的/后面的覆盖小的）
    "sea": None,  # 特殊处理：整个背景就是海
    "plateau": [  # 蒙古高原 / 西北（棕色）
        (99, 43), (105, 44), (112, 44.5), (119, 46), (124, 48),
        (126, 44), (120, 41), (114, 41), (108, 40.5), (103, 41), (99, 43),
    ],
    "mountain_west": [  # 西部山区（深绿）
        (100, 38), (104, 40), (108, 40.5), (110, 38), (108, 35),
        (104, 33), (101, 35), (100, 38),
    ],
    "qinling": [  # 秦岭山脉区（绿色条带）
        (104, 34.5), (108, 34.5), (110, 33), (108, 31.5), (105, 32), (104, 34.5),
    ],
    "taihang": [  # 太行山区（绿色条带）
        (112, 37), (113.5, 39), (115, 40), (116, 38.5), (115, 36.5), (113, 35.5), (112, 37),
    ],
    "yanshan": [  # 燕山区（绿色条带）
        (115, 40), (118, 41), (120, 40.5), (119, 39), (116, 38.5), (115, 40),
    ],
    "plain_central": [  # 中原平原（浅米黄——最核心的活动区）
        (108, 35.5), (112, 36), (114, 37), (116, 36.5), (117, 35.5),
        (116, 34), (114, 33.5), (111, 33.8), (109, 34.5), (108, 35.5),
    ],
    "plain_east": [  # 华东平原（稍深米黄）
        (116, 36.5), (119, 37), (121, 36.5), (122, 35), (121, 33),
        (118, 32.5), (116, 33.5), (116, 36.5),
    ],
    "plain_north": [  # 华北平原北部
        (114, 38.5), (118, 39.5), (120, 39), (119, 37), (116, 36.5), (114, 38.5),
    ],
}

TERRAIN_COLORS = {
    "plateau":   "#c9b896",   # 浅棕——高原/西北
    "mountain_west": "#a8c4a2",  # 深绿——西部山
    "qinling":   "#b8d4a8",   # 中绿——秦岭
    "taihang":   "#b8d4a8",   # 太行
    "yanshan":   "#b8d4a8",   # 燕山
    "plain_central": "#f5e6c8",  # 浅米黄——中原核心
    "plain_east": "#eddab0",   # 米黄——华东
    "plain_north": "#eddab0",  # 华北北
}
LAND_BASE = "#e8dba0"  # 默认陆地底色


# ================================================================
# 水系数据（完整版，可按需裁剪）
# ================================================================
RIVER_SYSTEMS = {
    "yellow": {  # 黄河（几字形）
        "color": "#4A90D9",
        "width": 3.5,
        "pts": [
            (96, 34.5), (98.5, 36), (100, 37.2), (102, 38.5), (104, 38),
            (106, 39.5), (108, 40.8), (110, 40.5), (112, 40),
            (113.5, 38.5), (113, 36.5), (111.5, 35), (112, 34.5),
            (114, 35), (116, 36), (118, 37.2), (119, 38), (119.5, 38.5),
        ],
    },
    "yangtze": {  # 长江
        "color": "#4A90D9",
        "width": 3.5,
        "pts": [
            (97, 33), (100, 32), (103, 31.5), (106, 30.5), (108, 30.2),
            (110, 29.8), (112, 30), (114, 29.8), (116, 29.5),
            (118, 29.8), (120, 30.5), (121.5, 31.5),
        ],
    },
    "huai": {  # 淮河
        "color": "#6BAED6",
        "width": 2.2,
        "pts": [
            (113, 33.5), (115, 33), (116.5, 32.5), (118, 32.3),
        ],
    },
    "hai": {  # 海河
        "color": "#6BAED6",
        "width": 2,
        "pts": [
            (114, 38), (115.5, 38.5), (116.5, 39), (117.5, 39.2),
        ],
    },
    "wei": {  # 渭河（黄河支流）
        "color": "#7BB8D9",
        "width": 1.8,
        "pts": [
            (106, 34.5), (108, 34.8), (110, 35.5),
        ],
    },
    "fen": {  # 汾河
        "color": "#7BB8D9",
        "width": 1.8,
        "pts": [
            (111.5, 36.5), (111.8, 37.5), (112.5, 38.5),
        ],
    },
}


# ================================================================
# 标注图标
# ================================================================
STAR_PATH = "M0,-11 L3,-3.5 L10.5,-3.5 L4.5,1.5 L6.5,9 L0,4.5 L-6.5,9 L-4.5,1.5 L-10.5,-3.5 L-3,-3.5 Z"

def _make_marker(proj, m):
    """单个地点标注：图标 + 主标签 + 副标签(今地)。"""
    x, y = proj(m["lon"], m["lat"])
    kind = m.get("kind", "other")
    col = {
        "capital": "#D35400",   # 橙红——都城/重要聚落
        "battle":  "#C0392B",   # 暗红——战场
        "culture": "#27AE60",  # 绿——文化遗址
        "tomb":    "#7F8C8D",  # 灰——陵墓
        "other":   "#2980B9",  # 蓝——其他
    }.get(kind, "#2980B9")

    icon_html = ""
    if kind == "capital":
        icon_html = (
            f'<g transform="translate({x:.1f},{y:.1f})">'
            f'<path d="{STAR_PATH}" fill="{col}" stroke="#fff" stroke-width="1.2"/>'
            f'</g>')
    elif kind == "battle":
        icon_html = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{col}" stroke="#fff" stroke-width="2"/>'
            f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="13" fill="#fff">⚔</text>')
    elif kind == "culture":
        icon_html = (
            f'<rect x="{x-8:.1f}" y="{y-8:.1f}" width="16" height="16" rx="3" '
            f'transform="rotate(45 {x:.1f} {y:.1f})" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
            f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="10" fill="#fff">文</text>')
    elif kind == "tomb":
        icon_html = (
            f'<rect x="{x-9:.1f}" y="{y-9:.1f}" width="18" height="18" rx="3" '
            f'fill="{col}" stroke="#fff" stroke-width="1.5"/>'
            f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle" font-size="11" fill="#fff">陵</text>')
    else:
        icon_html = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}" stroke="#fff" stroke-width="2"/>')

    lx = x + m.get("dx", 14)
    ly = y + m.get("dy", -16)
    anchor = m.get("anchor", "start")
    label_html = (
        f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
        f'font-size="15" font-weight="700" '
        f'font-family="\'Noto Sans SC\',\'SimHei\',sans-serif" fill="#2C3E50">{m["label"]}</text>')

    sub_html = ""
    if m.get("modern"):
        sub_html = (
            f'<text x="{lx:.1f}" y="{ly+16:.1f}" text-anchor="{anchor}" '
            f'font-size="11" font-family="\'Noto Sans SC\',sans-serif" fill="#666">{m["modern"]}</text>')

    return icon_html + label_html + sub_html


# ================================================================
# 地形渲染（多层叠色）
# ================================================================
def _render_terrain(proj, region):
    """按 TERRAIN_REGIONS 渲染地形底色层。返回 SVG path 列表。"""
    parts = []
    for name, poly in TERRAIN_REGIONS.items():
        if name == "sea":
            continue
        if not poly:
            continue
        # 只画落在视窗内的部分（简单判断：至少有一个点在范围内即可）
        pts = [proj(a, b) for a, b in poly]
        d = smooth_path(pts, closed=True)
        color = TERRAIN_COLORS.get(name, LAND_BASE)
        parts.append(f'<path d="{d}" fill="{color}" opacity="0.85"/>')
    return parts


# ================================================================
# 海岸线 & 陆地基底
# ================================================================
def _render_land_base(proj, region):
    """渲染陆地基底多边形 + 海岸线描边。"""
    coast_pts = [proj(a, b) for a, b in CHINA_COAST]
    hai_pts = [proj(a, b) for a, b in HAINAN_POLY]
    tai_pts = [proj(a, b) for a, b in TAIWAN_POLY]
    parts = []

    # 陆地基底（一个大致的多边形覆盖视窗内陆地）
    land_poly = _land_block(proj, region)
    lp = [proj(a, b) for a, b in land_poly]
    d = smooth_path(lp, closed=True)
    parts.append(f'<path d="{d}" fill="{LAND_BASE}" stroke="none"/>')

    # 海岸线描边
    cd = smooth_path(coast_pts, closed=False)
    parts.append(f'<path d="{cd}" fill="none" stroke="#8B7355" stroke-width="2" stroke-linecap="round"/>')
    # 海南
    hd = smooth_path(hai_pts, closed=True)
    parts.append(f'<path d="{hd}" fill="{LAND_BASE}" stroke="#8B7355" stroke-width="1.2"/>')
    # 台湾
    td = smooth_path(tai_pts, closed=True)
    parts.append(f'<path d="{td}" fill="{LAND_BASE}" stroke="#8B7355" stroke-width="1.2"/>')

    return parts


def _land_block(proj, region):
    """视窗内的陆地范围多边形（真实经纬度）。"""
    block = [
        (100, 42.5), (103, 41), (108, 41.5), (112, 42), (116, 42.2),
        (120, 41.5), (122, 40), (122, 37), (121.5, 35), (121, 33),
        (120, 31), (118.5, 29.5), (116, 28.5), (113, 28.5),
        (110, 29.5), (107, 30.5), (104, 32), (102, 34), (100, 37),
        (99, 40), (100, 42.5),
    ]
    return block


# ================================================================
# 河流渲染
# ================================================================
def _render_rivers(proj, rivers_override=None):
    """渲染河流系统。rivers_override 可为 dict / list（旧格式） / None（用默认全量）。"""
    parts = []
    if rivers_override is None:
        rivers = RIVER_SYSTEMS
    elif isinstance(rivers_override, dict):
        rivers = rivers_override
    elif isinstance(rivers_override, list):
        rivers = {}
        for idx, r in enumerate(rivers_override):
            name = r.get("name", f"river_{idx}")
            rivers[name] = {"color": r.get("color", "#4A90D9"), "width": r.get("width", 3), "pts": r["pts"]}
    else:
        rivers = {}
    for name, rinfo in rivers.items():
        pts = [proj(a, b) for a, b in rinfo["pts"]]
        d = smooth_path(pts, closed=False)
        color = rinfo["color"]
        width = rinfo["width"]
        # 双层：底层白色高亮 + 上层彩色
        parts.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{width+1.5}" '
                     f'stroke-linecap="round" opacity="0.6"/>')
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                     f'stroke-linecap="round" opacity="0.92"/>')
        # 河流名称（在河流中段标出）
        mx_pt = pts[len(pts) // 2]
        parts.append(
            f'<text x="{mx_pt[0]:.1f}" y="{mx_pt[1]-8:.1f}" text-anchor="middle" '
            f'font-size="12" font-weight="600" '
            f'font-family="\'ZCOOL KuaiLe\',\'KaiTi\',sans-serif" fill="{color}">'
            f'{name}</text>')
    return parts


# ================================================================
# 山脉符号（小三角群 + 名称）
# ================================================================
def _render_mountains(proj, mountains_list):
    parts = []
    for mo in mountains_list:
        cx, cy = proj(mo["lon"], mo["lat"])
        half = mo.get("half", 1.0) * 22
        count = mo.get("count", 4)
        vert = mo.get("vert", False)
        tris = ""
        for i in range(count):
            if vert:
                yy = cy - half + (2 * half) * i / max(count - 1, 1)
                xx = cx
            else:
                xx = cx - half + (2 * half) * i / max(count - 1, 1)
                yy = cy
            tris += (f'<path d="M{xx-5:.1f},{yy+8:.1f} L{xx:.1f},{yy-8:.1f} '
                    f'L{xx+5:.1f},{yy+8:.1f}Z" fill="#6B8E5A" stroke="#4a6b3a" '
                    f'stroke-width="0.8"/>')
        ly_offset = cy - 16 if not vert else cy + 26
        tris += (f'<text x="{cx:.1f}" y="{ly_offset:.1f}" text-anchor="middle" '
                 f'font-size="13" font-weight="600" '
                 f'font-family="\'ZCOOL KuaiLe\',sans-serif" fill="#4a6b3a">{mo["label"]}</text>')
        parts.append(tris)
    return parts


# ================================================================
# 图例框（左侧或左下角，地图帝风格）
# ================================================================
def _legend_box(x, y, items, title="图 例"):
    """
    items: [(symbol_svg_snippet, text), ...]
    返回 SVG group。
    """
    row_h = 24
    h = 24 + row_h * len(items) + 12
    w = 155
    parts = [
        f'<g transform="translate({x},{y})">',
        f'  <rect x="0" y="0" width="{w}" height="{h}" rx="8" '
        f'fill="#FFFDF5" stroke="#B8956E" stroke-width="1.5"/>',
        f'  <rect x="0" y="0" width="{w}" height="26" rx="8" '
        f'fill="#F5ECD7"/>',
        f'  <rect x="0" y="18" width="{w}" height="8" fill="#F5ECD7"/>',
        f'  <text x="{w/2:.0f}" y="18" text-anchor="middle" font-size="13" font-weight="700" '
        f'font-family="\'ZCOOL KuaiLe\',\'SimHei\',sans-serif" fill="#5C4A1F">{title}</text>',
    ]
    for i, (sym, txt) in enumerate(items):
        yy = 36 + i * row_h
        parts.append(f'  <text x="14" y="{yy}" font-size="14">{sym}</text>')
        parts.append(f'  <text x="34" y="{yy-1}" font-size="12" '
                     f'font-family="\'Noto Sans SC\',sans-serif" fill="#3D3224">{txt}</text>')
    parts.append('</g>')
    return "\n".join(parts)


def _default_legend_items():
    return [
        ('<path d="' + STAR_PATH + '" transform="scale(0.7)" fill="#D35400"/>', '都城 / 重要聚落'),
        ('<circle r="6" fill="#C0392B"/><text y="4" text-anchor="middle" font-size="10" fill="#fff">⚔</text>', '古战场'),
        ('<rect x="-5" y="-5" width="10" height="10" rx="2" transform="rotate(45)" fill="#27AE60"/>', '文化遗址'),
        ('<rect x="-5" y="-5" width="10" height="10" rx="2" fill="#7F8C8D"/><text y="4" text-anchor="middle" font-size="8" fill="#fff">陵</text>', '陵墓'),
        ('<circle r="5" fill="#2980B9"/>', '其他地点'),
    ]


# ================================================================
# 罗盘（右上角）
# ================================================================
def _compass_rose(cx, cy, r=32):
    return (
        f'<g transform="translate({cx},{cy})">'
        f'  <circle r="{r}" fill="#FFFDF5" stroke="#B8956E" stroke-width="1.3" opacity="0.94"/>'
        f'  <circle r="{r-5}" fill="none" stroke="#D4BC8E" stroke-width="0.8"/>'
        f'  <path d="M0,{-r+5} L7,0 L0,{r-5} L-7,0 Z" fill="#C0392B"/>'
        f'  <path d="M{-r+5},0 L0,7 L{r-5},0 L0,-7 Z" fill="#8B7355" opacity="0.8"/>'
        f'  <text x="0" y="{-r+13}" text-anchor="middle" font-size="12" font-weight="700" '
        f'fill="#C0392B">北</text>'
        f'  <text x="0" y="{r-7}" text-anchor="middle" font-size="10" fill="#8B7355">南</text>'
        f'  <text x="{r-8}" y="4" text-anchor="middle" font-size="10" fill="#8B7355">东</text>'
        f'  <text x="{-r+8}" y="4" text-anchor="middle" font-size="10" fill="#8B7355">西</text>'
        f'</g>')


# ================================================================
# 比例尺
# ================================================================
def _scale_bar(x, y, km=300, dim=None):
    """km 公里对应的像素宽度。"""
    deg_km = km / 95.0  # 约 95km/度
    if dim:
        px = deg_km * dim["sy"]
    else:
        px = km * 1.2  # fallback
    return (
        f'<g transform="translate({x},{y})">'
        f'  <rect x="0" y="0" width="{px:.1f}" height="8" fill="#8B7355"/>'
        f'  <rect x="0" y="0" width="{px/2:.1f}" height="8" fill="#FFFDF5" stroke="#8B7355" stroke-width="0.8"/>'
        f'  <text x="0" y="-5" font-size="11" fill="#5C4A1F" '
        f'font-family="\'Noto Sans SC\',sans-serif">{km} 公里</text>'
        f'</g>')


# ================================================================
# 标题框（左上角，仿古卷轴风格）
# ================================================================
def _title_cartouche(title, subtitle="", x=16, y=14):
    w = 240
    h = 44 if subtitle else 36
    svg = (
        f'<g transform="translate({x},{y})">'
        f'  <rect x="0" y="0" width="{w}" height="{h}" rx="8" '
        f'fill="#FFFDF5" stroke="#B8956E" stroke-width="1.8"/>'
        f'  <rect x="0" y="0" width="{w}" height="{h-2}" rx="8" fill="#FBF5E6" opacity="0.6"/>'
        f'  <text x="16" y="{24 if subtitle else 23}" font-size="17" font-weight="700" '
        f'font-family="\'ZCOOL KuaiLe\',\'SimHei\',sans-serif" fill="#5C4A1F">{title}</text>')
    if subtitle:
        svg += (
            f'  <text x="16" y="{h-4}" font-size="11" '
            f'font-family="\'Noto Sans SC\',sans-serif" fill="#8B7355">{subtitle}</text>')
    svg += '</g>'
    return svg


# ================================================================
# 中国定位小图
# ================================================================
def china_locator(dot_lon, dot_lat, x=0, y=0, scale=1.0):
    proj_l, _ = make_proj(73, 54, 62, 37, 150, 110, mx=10, my=8)
    outline = " ".join("%.1f,%.1f" % proj_l(a, b) for a, b in CHINA_COAST)
    hai = " ".join("%.1f,%.1f" % proj_l(a, b) for a, b in HAINAN_POLY)
    tai = " ".join("%.1f,%.1f" % proj_l(a, b) for a, b in TAIWAN_POLY)
    dx, dy = proj_l(dot_lon, dot_lat)
    s = scale
    return f'''<g transform="translate({x},{y}) scale({s})">
      <rect x="-6" y="-6" width="162" height="124" rx="10" fill="#fbf3df" stroke="#b89b5e" stroke-width="1.5"/>
      <text x="75" y="14" text-anchor="middle" font-size="11" font-family="ZCOOL KuaiLe,sans-serif" fill="#7a5c2e">中原在这里</text>
      <polygon points="{outline}" fill="#e9d6a8" stroke="#a07d3e" stroke-width="1"/>
      <polygon points="{hai}" fill="#e9d6a8" stroke="#a07d3e" stroke-width="0.8"/>
      <polygon points="{tai}" fill="#e9d6a8" stroke="#a07d3e" stroke-width="0.8"/>
      <circle cx="{dx:.1f}" cy="{dy:.1f}" r="5" fill="#E74C3C" stroke="#fff" stroke-width="1.5"/>
      <circle cx="{dx:.1f}" cy="{dy:.1f}" r="10" fill="none" stroke="#E74C3C" stroke-width="1" opacity="0.5"/>
    </g>'''


# ================================================================
# ====== 主函数：渲染「地图帝」风格疆域地图 ======
# ================================================================
def render_hist_map(region, markers, rivers=None, mountains=None, title="",
                    core=None, locator=(112, 35),
                    width=780, height=600, legend_items=None):
    """
    参数：
      region:     (lon0, lat_top, span_lon, span_lat)
      markers:    [{"lon","lat","label","modern","kind","dx","dy","anchor"}, ...]
      rivers:     自定义河流列表（None 则用默认全量 RIVER_SYSTEMS）
      mountains:  [{"lon","lat","label","half","count","vert"}, ...]
      title:      左上角标题文字
      core:       (w_lon,s_lat,e_lon,e_lat) 核心高亮区域（可选）
      locator:    定位小图中心点坐标
      legend_items: 自定义图例列表（None 用默认）
    返回：<svg>...</svg> 字符串。
    """
    lon0, lat_top, span_lon, span_lat = region
    proj, dim = make_proj(lon0, lat_top, span_lon, span_lat, width, height, mx=30, my=30)
    W, H = dim["W"], dim["H"]

    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}" '
             f'font-family="\'Noto Sans SC\',\'SimHei\',sans-serif" xmlns="http://www.w3.org/2000/svg">']

    # ---- defs ----
    parts.append('''<defs>
    <!-- 海洋渐变 -->
    <linearGradient id="ocean_bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#D4E8F2"/>
      <stop offset="100%" stop-color="#B8D4E8"/>
    </linearGradient>
    <!-- 核心区发光 -->
    <radialGradient id="core_glow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#F4D03F" stop-opacity="0.40"/>
      <stop offset="100%" stop-color="#F4D03F" stop-opacity="0"/>
    </radialGradient>
    <!-- 战役箭头渐变 -->
    <linearGradient id="arrow_red" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#E74C3C" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#C0392B" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="arrow_blue" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#3498DB" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#2980B9" stop-opacity="0.95"/>
    </linearGradient>
    <!-- 箭头 marker -->
    <marker id="head_red" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#C0392B"/>
    </marker>
    <marker id="head_blue" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#2980B9"/>
    </marker>
    <!-- 阴影 -->
    <filter id="shadow" x="-3%" y="-3%" width="106%" height="108%">
      <feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.15"/>
    </filter>
    </defs>''')

    # ---- 背景（海洋）----
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="12" fill="url(#ocean_bg)"/>')

    # ---- 陆地基底 ----
    parts.extend(_render_land_base(proj, region))

    # ---- 地形分层着色 ----
    parts.extend(_render_terrain(proj, region))

    # ---- 核心活动区高亮 ----
    if core:
        c_x0, c_y0 = proj(core[0], core[1])
        c_x1, c_y1 = proj(core[2], core[3])
        gx, gy = (c_x0 + c_x1) / 2, (c_y0 + c_y1) / 2
        gw = abs(c_x1 - c_x0) + 50
        gh = abs(c_y1 - c_y0) + 50
        parts.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{gw/2:.1f}" ry="{gh/2:.1f}" '
                     f'fill="url(#core_glow)" filter="url(#shadow)"/>')
        parts.append(f'<text x="{gx:.1f}" y="{gy - gh/2 + 18:.1f}" text-anchor="middle" '
                     f'font-size="14" font-weight="700" '
                     f'font-family="\'ZCOOL KuaiLe\',sans-serif" fill="#B7950B"'
                     f' filter="url(#shadow)">★ 核心活动区</text>')

    # ---- 河流 ----
    parts.extend(_render_rivers(proj, rivers))

    # ---- 山脉 ----
    if mountains:
        parts.extend(_render_mountains(proj, mountains))

    # ---- 标注点 ----
    for m in markers:
        parts.append(_make_marker(proj, m))

    # ---- 标题 ----
    parts.append(_title_cartouche(title))

    # ---- 罗盘（右上）----
    parts.append(_compass_rose(W - 56, 56, 30))

    # ---- 比例尺（右下偏上）----
    parts.append(_scale_bar(W - 200, H - 28, km=300, dim=dim))

    # ---- 图例框（左下）----
    leg_items = legend_items or _default_legend_items()
    parts.append(_legend_box(16, H - (24 + 24 * len(leg_items) + 20), leg_items))

    # ---- 中国定位小图 ----
    parts.append(china_locator(locator[0], locator[1], x=W - 160, y=88, scale=0.95))

    parts.append('</svg>')
    return "\n".join(parts)


# ================================================================
# ====== 战役地图专用（地图帝风格：箭头+编号圈+日期）======
# ================================================================
def render_battle_map(region, title, subtitle="",
                      armies=[],          # [{"name","color","origin_pos","label"},...]
                      arrows=[],          # [{"from","to","color","label","num"},...]
                      key_places=[],     # [{"lon","lat","label","kind"},...]
                      phases=[],         # [{"num","lon","lat","desc"},...] 编号阶段圈
                      water=None,        # 水域多边形 [[(lon,lat),...],...]（湖泊/海）
                      rivers=None,       # 自定义河流列表（None 则不画）
                      width=780, height=600):
    """
    渲染战役地图（带箭头路线 + 编号阶段圈 + 两军位置）。

    armies: 军队信息 [{name, color, origin_pos=(lon,lat), label}]
    arrows: 箭头路线 [{from:(lon,lat), to:(lon,lat), color('red'|'blue'), label, num}]
    key_places: 关键地点 [{lon,lat,label,kind}]
    phases: 战役阶段 [{num, lon, lat, desc}]  编号圆圈+描述
    """
    lon0, lat_top, span_lon, span_lat = region
    proj, dim = make_proj(lon0, lat_top, span_lon, span_lat, width, height, mx=30, my=30)
    W, H = dim["W"], dim["H"]

    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}" '
             f'font-family="\'Noto Sans SC\',\'SimHei\',sans-serif" xmlns="http://www.w3.org/2000/svg">']

    # defs（同上，复用箭头等）
    parts.append('''<defs>
    <linearGradient id="b_ocean" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#D4E8F2"/><stop offset="100%" stop-color="#B8D4E8"/>
    </linearGradient>
    <marker id="bh_red" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#C0392B"/></marker>
    <marker id="bh_blue" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#2980B9"/></marker>
    <filter id="bsh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.15"/></filter>
    </defs>''')

    # 背景（浅陆地色，铺满视窗，保证远处战役也落在陆地上）
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="12" fill="#EFE6C8"/>')
    lb = [(lon0 - 2, lat_top + 2), (lon0 + span_lon + 2, lat_top + 2),
          (lon0 + span_lon + 2, lat_top - span_lat - 2), (lon0 - 2, lat_top - span_lat - 2)]
    lpts = [proj(a, b) for a, b in lb]
    parts.append(f'<path d="{smooth_path(lpts, closed=True)}" fill="{LAND_BASE}" '
                 f'stroke="#8B7355" stroke-width="1.5"/>')
    # 水域（湖泊 / 海）—— 画在陆地上方
    if water:
        for poly in water:
            wpts = [proj(a, b) for a, b in poly]
            parts.append(f'<path d="{smooth_path(wpts, closed=True)}" fill="#B8D4E8" '
                         f'stroke="#8fb8d0" stroke-width="1.5"/>')
    # 地形分层（远处多数落在视窗外，无害）
    parts.extend(_render_terrain(proj, region))
    # 河流（仅当显式提供，避免远处出现无关河流）
    if rivers:
        parts.extend(_render_rivers(proj, rivers))

    # ---- 军队位置（大圆 + 名字）----
    for army in armies:
        ax, ay = proj(*army["origin_pos"])
        acolor = army.get("color", "#E74C3C")
        alabel = army.get("label", army.get("name", ""))
        # 大圆表示军队
        parts.append(
            f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="22" fill="{acolor}" '
            f'opacity="0.25" stroke="{acolor}" stroke-width="2" stroke-dasharray="6,3"/>')
        parts.append(
            f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="14" fill="{acolor}" stroke="#fff" stroke-width="2.5"/>')
        parts.append(
            f'<text x="{ax:.1f}" y="{ay+5:.1f}" text-anchor="middle" font-size="14" '
            f'font-weight="700" fill="#fff">{alabel[:2]}</text>')
        # 旁边名字
        parts.append(
            f'<text x="{ax+28:.1f}" y="{ay-10:.1f}" font-size="16" font-weight="700" '
            f'fill="{acolor}">{army["name"]}</text>')

    # ---- 箭头路线 ----
    for arr in arrows:
        fx, fy = proj(*arr["from"])
        tx, ty = proj(*arr["to"])
        color_key = arr.get("color", "red")
        grad_id = "arrow_red" if color_key == "red" else "arrow_blue"
        marker_id = "bh_red" if color_key == "red" else "bh_blue"
        line_color = "#C0392B" if color_key == "red" else "#2980B9"

        # 曲线箭头（稍微弯曲更有动感）
        mx_pt = ((fx + tx) / 2, min(fy, ty) - 25)

        # 箭头主线
        parts.append(
            f'<path d="M{fx:.1f},{fy:.1f} Q{mx_pt[0]:.1f},{mx_pt[1]:.1f} {tx:.1f},{ty:.1f}" '
            f'fill="none" stroke="{line_color}" stroke-width="4" stroke-linecap="round" '
            f'marker-end="url(#{marker_id})" opacity="0.88"/>')

        # 箭头上方的文字（如果有）
        if arr.get("label"):
            lx = (fx + tx) / 2 + (10 if tx > fx else -20)
            ly = mx_pt[1] - 8
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="12" '
                f'font-weight="600" fill="{line_color}" filter="url(#bsh)">'
                f'{arr["label"]}</text>')

        # 编号圈（如果有）
        if arr.get("num") is not None:
            nx = (fx + tx * 2) / 3
            ny = mx_pt[1] + 6
            parts.append(
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="13" fill="#fff" '
                f'stroke="{line_color}" stroke-width="2"/>')
            parts.append(
                f'<text x="{nx:.1f}" y="{ny+5:.1f}" text-anchor="middle" font-size="13" '
                f'font-weight="700" fill="{line_color}">{arr["num"]}</text>')

    # ---- 关键地点 ----
    for kp in key_places:
        kx, ky = proj(kp["lon"], kp["lat"])
        kcol = {"city": "#D35400", "battle": "#C0392B", "other": "#2980B9"}.get(kp.get("kind", "other"), "#2980B9")
        parts.append(
            f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="6" fill="{kcol}" stroke="#fff" stroke-width="1.5"/>')
        parts.append(
            f'<text x="{kx+10:.1f}" y="{ky-4:.1f}" font-size="13" font-weight="600" '
            f'fill="#2C3E50">{kp["label"]}</text>')

    # ---- 阶段编号圈（独立于箭头的）----
    for ph in phases:
        px, py = proj(ph["lon"], ph["lat"])
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="16" fill="#F4D03F" '
            f'stroke="#B7950B" stroke-width="2.5" filter="url(#bsh)"/>')
        parts.append(
            f'<text x="{px:.1f}" y="{py+6:.1f}" text-anchor="middle" font-size="14" '
            f'font-weight="700" fill="#7D6608">{ph["num"]}</text>')
        if ph.get("desc"):
            parts.append(
                f'<text x="{px:.1f}" y="{py+30:.1f}" text-anchor="middle" font-size="11" '
                f'fill="#5C4A1F">{ph["desc"]}</text>')

    # ---- 标题（居中大标题）----
    parts.append(
        f'<g transform="translate({W/2-140}, 12)">'
        f'  <rect x="0" y="0" width="280" height="46" rx="10" '
        f'fill="#FFFDF5" stroke="#C0392B" stroke-width="2.2" filter="url(#bsh)"/>'
        f'  <text x="140" y="22" text-anchor="middle" font-size="19" font-weight="700" '
        f'fill="#C0392B">{title}</text>')
    if subtitle:
        parts.append(
            f'  <text x="140" y="38" text-anchor="middle" font-size="11" fill="#8B7355">{subtitle}</text>')
    parts.append('</g>')

    # ---- 图例（按实际两军命名）----
    red_name = armies[0]["name"] if armies else "红方"
    blue_name = armies[1]["name"] if len(armies) > 1 else "蓝方"
    battle_legend = [
        ('<circle r="7" fill="#E74C3C" opacity="0.5" stroke="#C0392B" stroke-dasharray="4,2"/>', red_name),
        ('<circle r="7" fill="#2980B9" opacity="0.5" stroke="#2980B9" stroke-dasharray="4,2"/>', blue_name),
        ('<line x1="-10" y1="0" x2="10" y2="0" stroke="#C0392B" stroke-width="3" marker-end="url(#bh_red)"/>', '进攻方向'),
        ('<circle r="8" fill="#F4D03F" stroke="#B7950B" stroke-width="2"/><text y="4" text-anchor="middle" font-size="10" font-weight="700" fill="#7D6608">①</text>', '战役阶段'),
    ]
    parts.append(_legend_box(16, H - (24 + 24 * len(battle_legend) + 20), battle_legend, "战役图例"))

    # ---- 比例尺 ----
    parts.append(_scale_bar(W - 180, H - 28, km=150, dim=dim))

    parts.append('</svg>')
    return "\n".join(parts)


# ================================================================
# 自测
# ================================================================
if __name__ == "__main__":
    import xml.dom.minidom as M

    # --- 测试疆域地图 ---
    mk = [
        {"lon": 113.7, "lat": 34.4, "label": "黄帝·有熊", "modern": "今河南新郑", "kind": "capital"},
        {"lon": 115.0, "lat": 40.4, "label": "涿鹿", "modern": "今河北涿鹿", "kind": "battle"},
        {"lon": 111.5, "lat": 33.9, "label": "炎帝·神农", "modern": "今河南淮阳", "kind": "capital"},
        {"lon": 120.3, "lat": 30.4, "label": "良渚", "modern": "今浙江杭州", "kind": "culture"},
    ]
    mts = [
        {"lon": 110, "lat": 33.5, "label": "秦岭", "half": 2.2, "count": 5},
        {"lon": 114.2, "lat": 37.5, "label": "太行山", "half": 2.4, "count": 5, "vert": True},
        {"lon": 117.5, "lat": 40.6, "label": "燕山", "half": 1.6, "count": 4},
    ]

    svg1 = render_hist_map(
        region=(100, 43, 23, 15),
        markers=mk,
        mountains=mts,
        title="三皇五帝 · 主要活动区域",
        core=(107, 41.5, 119, 31),
        width=780, height=600,
    )
    try:
        M.parseString(svg1)
        print("✓ 疆域地图 SVG 合法,", len(svg1), "bytes")
    except Exception as e:
        print("✗ 疆域地图 SVG 错误:", e)

    # --- 测试战役地图 ---
    svg2 = render_battle_map(
        region=(111, 42, 12, 10),
        title="涿鹿之战",
        subtitle="黄帝 vs 蚩尤 · 约公元前 2600 年",
        armies=[
            {"name": "黄帝部落", "color": "#E74C3C", "origin_pos": (113.5, 36), "label": "黄"},
            {"name": "蚩尤部落", "color": "#2980B9", "origin_pos": (117.5, 38.5), "label": "蚩"},
        ],
        arrows=[
            {"from": (113.5, 36), "to": (115.5, 39.5), "color": "red", "label": "北上迎战", "num": "①"},
            {"from": (117.5, 38.5), "to": (115.5, 39.5), "color": "blue", "label": "西进", "num": "②"},
            {"from": (115.5, 39.5), "to": (115.0, 40.4), "color": "red", "label": "追击", "num": "③"},
        ],
        key_places=[
            {"lon": 115.0, "lat": 40.4, "label": "涿鹿之野", "kind": "battle"},
            {"lon": 114.6, "lat": 39.9, "label": "阪泉", "kind": "city"},
        ],
        phases=[
            {"num": "①", "lon": 114, "lat": 37.5, "desc": "两军对峙"},
            {"num": "②", "lon": 115.5, "lat": 39.5, "desc": "激战涿鹿"},
            {"num": "③", "lon": 115.0, "lat": 40.4, "desc": "擒获蚩尤"},
        ],
        width=780, height=550,
    )
    try:
        M.parseString(svg2)
        print("✓ 战役地图 SVG 合法,", len(svg2), "bytes")
    except Exception as e:
        print("✗ 战役地图 SVG 错误:", e)
