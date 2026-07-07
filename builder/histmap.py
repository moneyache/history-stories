# -*- coding: utf-8 -*-
"""
地理精确的历史地图 SVG 引擎
--------------------------------
按真实经纬度等距投影（带纬度余弦校正），画出：
  - 可识别的中国轮廓 / 海岸线
  - 黄河、长江等真实走向的水系
  - 主要山脉（秦岭 / 太行 / 燕山 等）
  - 按经纬度准确摆放的聚落、战场、文化遗址标注
  - 罗盘、比例尺、图例、核心活动区高亮、中国定位小图
先支持「区域视图」（聚焦某一片），后续朝代可复用。
"""

import math

# ----------------------------------------------------------------------
# 投影
# ----------------------------------------------------------------------
def make_proj(lon0, lat_top, span_lon, span_lat, W, H, mx=30, my=30):
    """返回一个 proj(lon,lat)->(x,y) 与一些尺寸信息。"""
    sy = (H - 2 * my) / span_lat
    sx = sy * math.cos(math.radians(35.5))   # 东向压缩，保持真实比例
    def proj(lon, lat):
        return (mx + (lon - lon0) * sx, my + (lat_top - lat) * sy)
    return proj, dict(mx=mx, my=my, sx=sx, sy=sy, W=W, H=H)


# ----------------------------------------------------------------------
# 平滑路径（Catmull-Rom -> 三次贝塞尔）
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# 中国轮廓锚点 (lon, lat) —— 顺时针，约 50 个控制点，形状可识别
# ----------------------------------------------------------------------
CHINA_OUTLINE = [
    (73.5, 39.5), (75.0, 40.6), (80.0, 42.0), (82.5, 45.0), (85.0, 47.0),
    (88.0, 48.6), (91.0, 47.0), (95.0, 44.0), (96.5, 42.5), (100.5, 42.5),
    (104.0, 41.8), (108.0, 42.0), (111.0, 43.6), (115.0, 44.0), (119.0, 46.0),
    (121.0, 49.0), (124.0, 50.0), (126.5, 52.6), (128.5, 53.4), (130.5, 53.3),
    (134.0, 48.2), (133.0, 45.5), (131.0, 44.6), (130.2, 42.6), (128.2, 42.0),
    (126.2, 41.2), (124.2, 40.0), (122.2, 39.2), (121.2, 37.6), (122.6, 37.0),
    (119.8, 35.0), (120.6, 33.0), (121.6, 31.2), (121.0, 28.6), (119.6, 25.6),
    (117.2, 23.6), (113.6, 22.0), (110.2, 21.0), (108.2, 21.6), (108.0, 19.0),
    (106.2, 21.6), (102.6, 22.0), (101.0, 21.6), (99.0, 22.6), (97.6, 24.0),
    (98.0, 25.6), (97.0, 28.6), (94.6, 28.6), (91.0, 27.6), (88.0, 27.6),
    (85.0, 28.6), (81.0, 30.0), (78.6, 32.0), (76.0, 35.0), (74.6, 37.0),
    (73.5, 39.5),
]
# 海南 / 台湾（独立小形状）
HAINAN = [(109.5, 19.8), (110.6, 19.6), (110.8, 18.6), (109.8, 18.4), (109.2, 19.3)]
TAIWAN = [(121.0, 25.0), (121.9, 24.0), (120.9, 22.5), (120.2, 22.0), (120.6, 23.6)]


# ----------------------------------------------------------------------
# 中国定位小图（左上角「你在这里」）
# ----------------------------------------------------------------------
def china_locator(dot_lon, dot_lat, x=0, y=0, scale=1.0):
    proj, _ = make_proj(73, 54, 62, 37, 150, 110, mx=10, my=8)
    outline = " ".join("%.1f,%.1f" % proj(a, b) for a, b in CHINA_OUTLINE)
    hai = " ".join("%.1f,%.1f" % proj(a, b) for a, b in HAINAN)
    tai = " ".join("%.1f,%.1f" % proj(a, b) for a, b in TAIWAN)
    dx, dy = proj(dot_lon, dot_lat)
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


# ----------------------------------------------------------------------
# 山脉（一排小三角 + 标签）
# ----------------------------------------------------------------------
def mountain_range(proj, lon, lat, label, half=0.9, count=4, vert=False):
    cx, cy = proj(lon, lat)
    span = half * 27.0  # 约 half 个经度宽
    tris = []
    for i in range(count):
        if vert:
            yy = cy - span + (2 * span) * i / (count - 1)
            xx = cx
            tris.append(f'<path d="M{xx-5:.1f},{yy+7:.1f} L{xx:.1f},{yy-7:.1f} L{xx+5:.1f},{yy+7:.1f} Z" fill="#9c7b46" stroke="#6e521f" stroke-width="0.8"/>')
        else:
            xx = cx - span + (2 * span) * i / (count - 1)
            yy = cy
            tris.append(f'<path d="M{xx-5:.1f},{yy+7:.1f} L{xx:.1f},{yy-7:.1f} L{xx+5:.1f},{yy+7:.1f} Z" fill="#9c7b46" stroke="#6e521f" stroke-width="0.8"/>')
    lab = f'<text x="{cx:.1f}" y="{cy-12 if not vert else cy+22:.1f}" text-anchor="middle" font-size="12" font-family="ZCOOL KuaiLe,sans-serif" fill="#6e521f">{label}</text>'
    return "".join(tris) + lab


# ----------------------------------------------------------------------
# 标注（聚落 / 战场 / 文化 / 陵墓）
# ----------------------------------------------------------------------
STAR = "M0,-9 L2.6,-2.8 L9,-2.8 L4,1.8 L5.6,8.6 L0,4.4 L-5.6,8.6 L-4,1.8 L-9,-2.8 L-2.6,-2.8 Z"

def marker(proj, m):
    x, y = proj(m["lon"], m["lat"])
    kind = m.get("kind", "other")
    col = {"capital": "#E67E22", "battle": "#E74C3C", "culture": "#27AE60",
           "tomb": "#7F8C8D", "other": "#3498DB"}.get(kind, "#3498DB")
    # 图标
    if kind == "capital":
        icon = f'<path d="{STAR}" transform="translate({x:.1f},{y:.1f}) scale(0.95)" fill="{col}" stroke="#fff" stroke-width="1"/>'
    elif kind == "battle":
        icon = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{col}" stroke="#fff" stroke-width="2"/>'
                f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle" font-size="12" fill="#fff">⚔</text>')
    elif kind == "culture":
        icon = (f'<rect x="{x-8:.1f}" y="{y-8:.1f}" width="16" height="16" rx="3" transform="rotate(45 {x:.1f} {y:.1f})" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
                f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="10" fill="#fff">稻</text>')
    elif kind == "tomb":
        icon = f'<rect x="{x-8:.1f}" y="{y-8:.1f}" width="16" height="16" rx="2" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
    else:
        icon = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}" stroke="#fff" stroke-width="2"/>'
    # 标签
    lx = x + m.get("dx", 12)
    ly = y + m.get("dy", -14)
    anchor = m.get("anchor", "start")
    label = (f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="13" font-weight="700" '
             f'font-family="Noto Sans SC,sans-serif" fill="#2C3E50">{m["label"]}</text>')
    sub = ""
    if m.get("modern"):
        sub = (f'<text x="{lx:.1f}" y="{ly+14:.1f}" text-anchor="{anchor}" font-size="10.5" '
               f'font-family="Noto Sans SC,sans-serif" fill="#7F8C8D">{m["modern"]}</text>')
    return icon + label + sub


# ----------------------------------------------------------------------
# 主图：区域视图
# ----------------------------------------------------------------------
def render_hist_map(region, markers, rivers, mountains, title, core=None, theme=None,
                    locator=(112, 35), width=720, height=560):
    """
    region: (lon0, lat_top, span_lon, span_lat)
    rivers: [{"name":..,"color":..,"pts":[(lon,lat)...]}, ...]
    mountains: [{"lon","lat","label","half","vert"}]
    core: (lon,lat,lon,lat) 核心高亮框（可选）
    """
    lon0, lat_top, span_lon, span_lat = region
    proj, dim = make_proj(lon0, lat_top, span_lon, span_lat, width, height, mx=34, my=30)
    W, H = dim["W"], dim["H"]

    # 背景海
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}" font-family="Noto Sans SC,sans-serif">']
    parts.append(f'<defs>'
                 f'<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">'
                 f'<stop offset="0" stop-color="#eaf4f8"/><stop offset="1" stop-color="#dcebf2"/></linearGradient>'
                 f'<radialGradient id="coreglow" cx="50%" cy="50%" r="50%">'
                 f'<stop offset="0" stop-color="#F1C40F" stop-opacity="0.45"/><stop offset="1" stop-color="#F1C40F" stop-opacity="0"/></radialGradient>'
                 f'<filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" result="n"/>'
                 f'<feColorMatrix in="n" type="saturate" values="0"/>'
                 f'<feComponentTransfer><feFuncA type="linear" slope="0.06"/></feComponentTransfer>'
                 f'<feComposite operator="over" in2="SourceGraphic"/></filter>'
                 f'</defs>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="url(#sea)"/>')

    # 陆地（用全中国轮廓在区域投影下裁剪显示，只显示落在框内的部分）
    # —— 为简洁与真实感，这里用一段「陆地底色」多边形覆盖框内主要陆地，
    #    再在上面叠真实河流/山脉/标注；陆地边界用浅色块示意。
    land_poly = _land_block(proj, region)
    parts.append(f'<path d="{land_poly}" fill="#efe2c2" stroke="#c9b483" stroke-width="2" filter="url(#paper)"/>')

    # 核心高亮
    if core:
        cx0, cy0 = proj(core[0], core[1])
        cx1, cy1 = proj(core[2], core[3])
        gx, gy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        gw = abs(cx1 - cx0) + 60
        gh = abs(cy1 - cy0) + 60
        parts.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{gw/2:.1f}" ry="{gh/2:.1f}" fill="url(#coreglow)"/>')
        parts.append(f'<text x="{gx:.1f}" y="{gy - gh/2 + 16:.1f}" text-anchor="middle" font-size="13" '
                     f'font-family="ZCOOL KuaiLe,sans-serif" fill="#b8860b" opacity="0.85">★ 核心活动区</text>')

    # 河流
    for r in rivers:
        pts = [proj(a, b) for a, b in r["pts"]]
        d = smooth_path(pts, closed=False)
        parts.append(f'<path d="{d}" fill="none" stroke="{r["color"]}" stroke-width="3.2" '
                     f'stroke-linecap="round" opacity="0.92"/>')
        # 河流名
        mxr, myr = pts[len(pts) // 2]
        parts.append(f'<text x="{mxr:.1f}" y="{myr-8:.1f}" text-anchor="middle" font-size="12" '
                     f'font-family="ZCOOL KuaiLe,sans-serif" fill="{r["color"]}" opacity="0.9">{r["name"]}</text>')

    # 山脉
    for mo in mountains:
        parts.append(mountain_range(proj, mo["lon"], mo["lat"], mo["label"],
                                    half=mo.get("half", 0.9), count=mo.get("count", 4),
                                    vert=mo.get("vert", False)))

    # 标注
    for m in markers:
        parts.append(marker(proj, m))

    # 标题 cartouche
    parts.append(f'<g transform="translate(20,18)">'
                 f'<rect x="0" y="0" width="230" height="40" rx="9" fill="#fbf3df" stroke="#b89b5e" stroke-width="1.5"/>'
                 f'<text x="14" y="26" font-size="16" font-family="ZCOOL KuaiLe,sans-serif" fill="#7a5c2e">{title}</text></g>')

    # 罗盘
    parts.append(_compass(W - 64, 64, 34))

    # 比例尺（约 500 公里）
    km = 500
    deg = km / 95.0  # 1°纬≈111km, 此处用约95km/°(中原纬度) 估算
    px = deg * dim["sy"]
    parts.append(f'<g transform="translate(28,{H-30})">'
                 f'<rect x="0" y="0" width="{px:.1f}" height="7" fill="#8a6d3b"/>'
                 f'<rect x="0" y="0" width="{px/2:.1f}" height="7" fill="#efe2c2" stroke="#8a6d3b" stroke-width="0.8"/>'
                 f'<text x="0" y="-6" font-size="11" fill="#6e521f" font-family="Noto Sans SC,sans-serif">约 {km} 公里</text></g>')

    # 图例
    parts.append(_legend(W - 150, H - 92))

    # 定位小图
    parts.append(china_locator(locator[0], locator[1], x=W - 168, y=92, scale=1.0))

    parts.append('</svg>')
    return "\n".join(parts)


def _land_block(proj, region):
    """用一组覆盖框内主要陆地的粗多边形（在真实经纬度下定义，再投影）。"""
    # 大致覆盖 中原+华北+华东+华中的陆地轮廓（真实坐标，简化）
    block = [
        (101, 43), (104, 41), (110, 41), (115, 41.5), (120, 41), (123, 40),
        (122, 37), (121, 35), (121, 31), (119, 28), (116, 27), (112, 28),
        (109, 30), (106, 31), (103, 33), (101, 35), (100, 38), (101, 43),
    ]
    pts = [proj(a, b) for a, b in block]
    return smooth_path(pts, closed=True)


def _compass(cx, cy, r):
    return (f'<g transform="translate({cx},{cy})">'
            f'<circle r="{r}" fill="#fbf3df" stroke="#b89b5e" stroke-width="1.5" opacity="0.95"/>'
            f'<circle r="{r-6}" fill="none" stroke="#d9c08a" stroke-width="1"/>'
            f'<path d="M0,{-r+4} L6,0 L0,{r-4} L-6,0 Z" fill="#E74C3C"/>'
            f'<path d="M{-r+4},0 L0,6 L{r-4},0 L0,-6 Z" fill="#7a5c2e" opacity="0.85"/>'
            f'<text x="0" y="{-r+12}" text-anchor="middle" font-size="12" font-weight="700" fill="#7a5c2e">北</text>'
            f'<text x="0" y="{r-6}" text-anchor="middle" font-size="10" fill="#7a5c2e">南</text>'
            f'<text x="{r-6}" y="4" text-anchor="middle" font-size="10" fill="#7a5c2e">东</text>'
            f'<text x="{-r+6}" y="4" text-anchor="middle" font-size="10" fill="#7a5c2e">西</text>'
            f'</g>')


def _legend(x, y):
    items = [
        ("#E67E22", "★", "重要聚落 / 都城"),
        ("#E74C3C", "⚔", "古战场"),
        ("#27AE60", "◆", "文化遗址"),
        ("#3498DB", "●", "其他地点"),
    ]
    h = 22 * len(items) + 14
    s = [f'<g transform="translate({x},{y})">'
         f'<rect x="0" y="0" width="140" height="{h}" rx="9" fill="#fbf3df" stroke="#b89b5e" stroke-width="1.5" opacity="0.96"/>']
    for i, (c, sym, txt) in enumerate(items):
        yy = 20 + i * 22
        s.append(f'<text x="14" y="{yy}" font-size="14" fill="{c}" font-weight="700">{sym}</text>')
        s.append(f'<text x="34" y="{yy}" font-size="12" fill="#5b4a2a" font-family="Noto Sans SC,sans-serif">{txt}</text>')
    s.append('</g>')
    return "".join(s)


if __name__ == "__main__":
    # 自测：生成一个三皇五帝示例地图并写文件，校验 XML 合法性
    import xml.dom.minidom as M
    mk = [
        {"lon": 113.7, "lat": 34.4, "label": "黄帝·有熊", "modern": "今河南新郑", "kind": "capital", "dx": 12, "dy": -14, "anchor": "start"},
        {"lon": 115.0, "lat": 40.4, "label": "涿鹿", "modern": "今河北涿鹿", "kind": "battle", "dx": 12, "dy": -10, "anchor": "start"},
    ]
    rv = [{"name": "黄河", "color": "#c8923a", "pts": [(96, 34), (100, 37), (104, 38), (108, 41), (111, 41), (113, 38), (112, 35), (114, 35), (118, 38), (119, 38.5)]}]
    svg = render_hist_map((100, 43, 23, 15), mk, rv, [{"lon": 112, "lat": 34, "label": "秦岭"}], "三皇五帝·活动范围", core=(108, 41, 118, 32))
    M.parseString(svg)
    print("SVG OK, length=", len(svg))
