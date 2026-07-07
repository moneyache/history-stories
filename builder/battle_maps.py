# -*- coding: utf-8 -*-
"""
关键战役的「地图帝」风格战役地图配置
====================================
每个条目对应 dynasty_data.py 中某个 battle 的 name，由 build_dynasties.py
在渲染时自动套用（数据里若已内联 battle_map 则优先）。

坐标为近似经纬度（示意用，非严格考据），重点在于呈现两军位置、
进军方向与关键地点，适合给孩子建立空间感。

字段说明：
  region      : (lon0, lat_top, span_lon, span_lat) 视图范围
  armies      : [{name, color, origin_pos:(lon,lat), label}]  两军（左=红/右=蓝）
  arrows      : [{from, to, color('red'|'blue'), label, num}] 进军箭头
  key_places  : [{lon,lat,label,kind}]  关键地点
  phases      : [{num, lon, lat, desc}]  战役阶段圈
  water       : [[(lon,lat),...],...]  水域多边形（湖泊/海）
  rivers      : [{name,color,width,pts}]  自定义河流
"""

BATTLE_MAPS = {

    # ---------------- 夏 ----------------
    "鸣条之战": {
        "subtitle": "商汤 vs 夏桀 · 约公元前 1600 年",
        "region": (107, 38, 11, 9),
        "armies": [
            {"name": "商汤联军", "color": "#E74C3C", "origin_pos": (115.6, 34.4), "label": "商"},
            {"name": "夏桀大军", "color": "#2980B9", "origin_pos": (112.8, 34.7), "label": "夏"},
        ],
        "arrows": [
            {"from": (115.6, 34.4), "to": (111.0, 35.1), "color": "red", "label": "商汤西进", "num": "①"},
            {"from": (112.8, 34.7), "to": (111.0, 35.1), "color": "blue", "label": "夏桀应战", "num": "②"},
        ],
        "key_places": [
            {"lon": 111.0, "lat": 35.1, "label": "鸣条", "kind": "battle"},
            {"lon": 115.6, "lat": 34.4, "label": "亳（商都）", "kind": "city"},
            {"lon": 112.8, "lat": 34.7, "label": "斟鄩（夏都）", "kind": "city"},
        ],
        "phases": [
            {"num": "①", "lon": 115.6, "lat": 34.4, "desc": "商汤起兵"},
            {"num": "②", "lon": 111.0, "lat": 35.1, "desc": "鸣条决战·夏亡"},
        ],
        "rivers": [{"name": "黄河", "color": "#4A90D9", "width": 3.5,
                    "pts": [(109, 34.8), (111, 35.0), (112.8, 34.7), (114.5, 35.2), (116, 36)]}],
    },

    # ---------------- 商 ----------------
    "牧野之战": {
        "subtitle": "周武王 vs 商纣王 · 约公元前 1046 年",
        "region": (105, 39, 14, 9),
        "armies": [
            {"name": "周武王联军", "color": "#E74C3C", "origin_pos": (108.9, 34.3), "label": "周"},
            {"name": "商纣王大军", "color": "#2980B9", "origin_pos": (114.2, 35.6), "label": "商"},
        ],
        "arrows": [
            {"from": (108.9, 34.3), "to": (114.2, 35.6), "color": "red", "label": "武王东征", "num": "①"},
            {"from": (114.5, 35.7), "to": (114.2, 35.6), "color": "blue", "label": "商军列阵", "num": "②"},
        ],
        "key_places": [
            {"lon": 114.2, "lat": 35.6, "label": "牧野", "kind": "battle"},
            {"lon": 108.9, "lat": 34.3, "label": "镐京", "kind": "city"},
            {"lon": 114.5, "lat": 35.7, "label": "朝歌", "kind": "city"},
            {"lon": 112.5, "lat": 34.9, "label": "孟津", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 112.5, "lat": 34.9, "desc": "孟津会盟"},
            {"num": "②", "lon": 114.2, "lat": 35.6, "desc": "牧野决战·商亡"},
        ],
        "rivers": [{"name": "黄河", "color": "#4A90D9", "width": 3.5,
                    "pts": [(110, 34.5), (112, 35.0), (113.5, 35.2), (114.5, 35.6), (116, 36)]}],
    },

    # ---------------- 周（战国） ----------------
    "长平之战": {
        "subtitle": "秦（白起） vs 赵（赵括） · 公元前 260 年",
        "region": (106, 39, 12, 9),
        "armies": [
            {"name": "秦军（白起）", "color": "#E74C3C", "origin_pos": (108.7, 34.3), "label": "秦"},
            {"name": "赵军（赵括）", "color": "#2980B9", "origin_pos": (114.5, 36.6), "label": "赵"},
        ],
        "arrows": [
            {"from": (108.7, 34.3), "to": (112.9, 35.8), "color": "red", "label": "秦军东进", "num": "①"},
            {"from": (114.5, 36.6), "to": (112.9, 35.8), "color": "blue", "label": "赵军南下", "num": "②"},
        ],
        "key_places": [
            {"lon": 112.9, "lat": 35.8, "label": "长平", "kind": "battle"},
            {"lon": 108.7, "lat": 34.3, "label": "咸阳", "kind": "city"},
            {"lon": 114.5, "lat": 36.6, "label": "邯郸", "kind": "city"},
        ],
        "phases": [
            {"num": "①", "lon": 113.5, "lat": 36.0, "desc": "两军对峙"},
            {"num": "②", "lon": 112.9, "lat": 35.8, "desc": "长平围歼"},
        ],
        "rivers": [{"name": "黄河", "color": "#4A90D9", "width": 3.5,
                    "pts": [(109, 34.8), (111, 35.0), (112.8, 34.7), (114.5, 35.2)]}],
    },

    # ---------------- 秦（秦末） ----------------
    "巨鹿之战": {
        "subtitle": "项羽 vs 秦军（章邯） · 公元前 207 年",
        "region": (112, 40, 10, 9),
        "armies": [
            {"name": "楚军（项羽）", "color": "#E74C3C", "origin_pos": (117.2, 34.3), "label": "楚"},
            {"name": "秦军（章邯）", "color": "#2980B9", "origin_pos": (114.5, 36.6), "label": "秦"},
        ],
        "arrows": [
            {"from": (117.2, 34.3), "to": (115.0, 37.1), "color": "red", "label": "项羽北上", "num": "①"},
            {"from": (114.5, 36.6), "to": (115.0, 37.1), "color": "blue", "label": "秦军阻截", "num": "②"},
        ],
        "key_places": [
            {"lon": 115.0, "lat": 37.1, "label": "巨鹿", "kind": "battle"},
            {"lon": 117.2, "lat": 34.3, "label": "彭城", "kind": "city"},
            {"lon": 114.8, "lat": 36.8, "label": "漳水", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 116.5, "lat": 35.5, "desc": "破釜沉舟"},
            {"num": "②", "lon": 115.0, "lat": 37.1, "desc": "巨鹿决战"},
        ],
        "rivers": [{"name": "黄河", "color": "#4A90D9", "width": 3.5,
                    "pts": [(114.5, 35.6), (115.0, 36.0), (115.2, 37.0)]}],
    },

    # ---------------- 汉 ----------------
    "漠北之战": {
        "subtitle": "汉军（卫青·霍去病） vs 匈奴 · 公元前 119 年",
        "region": (100, 48, 18, 14),
        "armies": [
            {"name": "汉军", "color": "#E74C3C", "origin_pos": (108.7, 34.3), "label": "汉"},
            {"name": "匈奴", "color": "#2980B9", "origin_pos": (110, 46), "label": "匈奴"},
        ],
        "arrows": [
            {"from": (108.7, 34.3), "to": (110, 44), "color": "red", "label": "汉军出塞北伐", "num": "①"},
            {"from": (110, 44), "to": (113, 46), "color": "red", "label": "封狼居胥", "num": "②"},
        ],
        "key_places": [
            {"lon": 110, "lat": 44, "label": "漠北", "kind": "battle"},
            {"lon": 108.7, "lat": 34.3, "label": "长安", "kind": "city"},
            {"lon": 113, "lat": 46, "label": "狼居胥山", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 108.7, "lat": 34.3, "desc": "汉军出塞"},
            {"num": "②", "lon": 110, "lat": 44, "desc": "漠北决战"},
            {"num": "③", "lon": 113, "lat": 46, "desc": "封狼居胥"},
        ],
    },

    # ---------------- 三国 ----------------
    "赤壁之战": {
        "subtitle": "孙刘联军 vs 曹操 · 公元 208 年",
        "region": (110, 33, 11, 9),
        "armies": [
            {"name": "孙刘联军", "color": "#E74C3C", "origin_pos": (114.5, 30.4), "label": "孙刘"},
            {"name": "曹操大军", "color": "#2980B9", "origin_pos": (112.2, 30.3), "label": "曹"},
        ],
        "arrows": [
            {"from": (114.5, 30.4), "to": (113.9, 29.7), "color": "red", "label": "孙刘西上", "num": "①"},
            {"from": (112.2, 30.3), "to": (113.9, 29.7), "color": "blue", "label": "曹操东下", "num": "②"},
        ],
        "key_places": [
            {"lon": 113.9, "lat": 29.7, "label": "赤壁", "kind": "battle"},
            {"lon": 112.2, "lat": 30.3, "label": "江陵", "kind": "city"},
            {"lon": 114.5, "lat": 30.4, "label": "夏口", "kind": "city"},
        ],
        "phases": [
            {"num": "①", "lon": 112.2, "lat": 30.3, "desc": "曹操南下"},
            {"num": "②", "lon": 113.9, "lat": 29.7, "desc": "火烧赤壁"},
        ],
        "rivers": [{"name": "长江", "color": "#4A90D9", "width": 4,
                    "pts": [(111, 30.5), (112.2, 30.3), (113.9, 29.7), (116, 29.8), (119, 30.5)]}],
    },

    # ---------------- 晋 ----------------
    "淝水之战": {
        "subtitle": "东晋 vs 前秦（苻坚） · 公元 383 年",
        "region": (111, 37, 11, 9),
        "armies": [
            {"name": "东晋（谢玄）", "color": "#E74C3C", "origin_pos": (118.8, 32.0), "label": "晋"},
            {"name": "前秦（苻坚）", "color": "#2980B9", "origin_pos": (112, 34.6), "label": "秦"},
        ],
        "arrows": [
            {"from": (112, 34.6), "to": (116.8, 32.6), "color": "blue", "label": "前秦南下", "num": "①"},
            {"from": (118.8, 32.0), "to": (116.8, 32.6), "color": "red", "label": "东晋北上", "num": "②"},
        ],
        "key_places": [
            {"lon": 116.8, "lat": 32.6, "label": "淝水", "kind": "battle"},
            {"lon": 118.8, "lat": 32.0, "label": "建康", "kind": "city"},
            {"lon": 112.4, "lat": 34.6, "label": "洛阳", "kind": "city"},
        ],
        "phases": [
            {"num": "①", "lon": 112, "lat": 34.6, "desc": "前秦举国南下"},
            {"num": "②", "lon": 116.8, "lat": 32.6, "desc": "淝水溃败"},
        ],
        "rivers": [{"name": "淮河", "color": "#6BAED6", "width": 2.6,
                    "pts": [(113, 33), (114.5, 32.8), (116, 32.6), (118, 32.4)]}],
    },

    # ---------------- 南北朝 ----------------
    "钟离之战": {
        "subtitle": "梁（韦睿） vs 北魏 · 公元 507 年",
        "region": (113, 37, 10, 9),
        "armies": [
            {"name": "梁军（韦睿）", "color": "#E74C3C", "origin_pos": (118.8, 32.0), "label": "梁"},
            {"name": "北魏军", "color": "#2980B9", "origin_pos": (115, 33.5), "label": "魏"},
        ],
        "arrows": [
            {"from": (118.8, 32.0), "to": (117.5, 32.9), "color": "red", "label": "梁军北上", "num": "①"},
            {"from": (115, 33.5), "to": (117.5, 32.9), "color": "blue", "label": "北魏南进", "num": "②"},
        ],
        "key_places": [
            {"lon": 117.5, "lat": 32.9, "label": "钟离", "kind": "battle"},
            {"lon": 118.8, "lat": 32.0, "label": "建康", "kind": "city"},
            {"lon": 116.5, "lat": 32.7, "label": "淮水", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 117.5, "lat": 32.9, "desc": "北魏围城"},
            {"num": "②", "lon": 117.0, "lat": 32.9, "desc": "梁军破堤水攻"},
        ],
        "rivers": [{"name": "淮河", "color": "#6BAED6", "width": 2.6,
                    "pts": [(115, 32.8), (116.5, 32.7), (118, 32.5)]}],
    },

    # ---------------- 唐 ----------------
    "怛罗斯之战": {
        "subtitle": "唐军（高仙芝） vs 大食 · 公元 751 年",
        "region": (60, 47, 28, 14),
        "armies": [
            {"name": "唐军（高仙芝）", "color": "#E74C3C", "origin_pos": (82, 41.5), "label": "唐"},
            {"name": "大食（阿拉伯）", "color": "#2980B9", "origin_pos": (62, 43), "label": "大食"},
        ],
        "arrows": [
            {"from": (82, 41.5), "to": (71.4, 42.5), "color": "red", "label": "唐军西征", "num": "①"},
            {"from": (62, 43), "to": (71.4, 42.5), "color": "blue", "label": "大食东进", "num": "②"},
        ],
        "key_places": [
            {"lon": 71.4, "lat": 42.5, "label": "怛罗斯", "kind": "battle"},
            {"lon": 82, "lat": 41.5, "label": "安西·龟兹", "kind": "city"},
            {"lon": 76, "lat": 42.5, "label": "碎叶", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 82, "lat": 41.5, "desc": "唐军西征"},
            {"num": "②", "lon": 71.4, "lat": 42.5, "desc": "怛罗斯决战"},
        ],
    },

    # ---------------- 宋 ----------------
    "崖山之战": {
        "subtitle": "南宋（张世杰） vs 元军（张弘范） · 公元 1279 年",
        "region": (109, 27, 11, 11),
        "armies": [
            {"name": "南宋（张世杰）", "color": "#E74C3C", "origin_pos": (113, 22.3), "label": "宋"},
            {"name": "元军（张弘范）", "color": "#2980B9", "origin_pos": (113, 25), "label": "元"},
        ],
        "arrows": [
            {"from": (113, 25), "to": (113, 22.3), "color": "blue", "label": "元军南下", "num": "①"},
            {"from": (113, 23.5), "to": (113, 22.3), "color": "red", "label": "南宋死守", "num": "②"},
        ],
        "key_places": [
            {"lon": 113, "lat": 22.3, "label": "崖山", "kind": "battle"},
            {"lon": 113.5, "lat": 22.5, "label": "珠江口", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 113, "lat": 25, "desc": "元军南下"},
            {"num": "②", "lon": 113, "lat": 22.3, "desc": "崖山海战·宋亡"},
        ],
        "water": [[(109, 16.5), (120, 16.5), (120, 21.5), (113, 21.8), (109, 21.5)]],
    },

    # ---------------- 元 ----------------
    "襄樊之战": {
        "subtitle": "元军（忽必烈） vs 南宋 · 公元 1267–1273 年",
        "region": (108, 35, 10, 9),
        "armies": [
            {"name": "元军（忽必烈）", "color": "#E74C3C", "origin_pos": (110, 33), "label": "元"},
            {"name": "南宋守军", "color": "#2980B9", "origin_pos": (112.1, 32), "label": "宋"},
        ],
        "arrows": [
            {"from": (110, 33), "to": (112.1, 32), "color": "red", "label": "元军围城", "num": "①"},
            {"from": (112.1, 32), "to": (112.1, 31.6), "color": "blue", "label": "南宋固守", "num": "②"},
        ],
        "key_places": [
            {"lon": 112.1, "lat": 32, "label": "襄阳·樊城", "kind": "battle"},
            {"lon": 112.2, "lat": 32.1, "label": "樊城", "kind": "city"},
            {"lon": 112, "lat": 32.9, "label": "南阳", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 110, "lat": 33, "desc": "元军围城"},
            {"num": "②", "lon": 112.1, "lat": 32, "desc": "襄樊陷落"},
        ],
        "rivers": [
            {"name": "长江", "color": "#4A90D9", "width": 3.5,
             "pts": [(109, 30.5), (110.5, 30.2), (112, 29.8)]},
            {"name": "汉水", "color": "#6BAED6", "width": 2.6,
             "pts": [(112.1, 32), (111, 31), (110, 30.5)]},
        ],
    },

    # ---------------- 明 ----------------
    "鄱阳湖之战": {
        "subtitle": "朱元璋 vs 陈友谅 · 公元 1363 年",
        "region": (113, 32, 9, 8),
        "armies": [
            {"name": "朱元璋", "color": "#E74C3C", "origin_pos": (115.9, 28.7), "label": "朱"},
            {"name": "陈友谅", "color": "#2980B9", "origin_pos": (117.5, 29.8), "label": "陈"},
        ],
        "arrows": [
            {"from": (115.9, 28.7), "to": (116.3, 29.5), "color": "red", "label": "朱元璋北上", "num": "①"},
            {"from": (117.5, 29.8), "to": (116.3, 29.5), "color": "blue", "label": "陈友谅南下", "num": "②"},
        ],
        "key_places": [
            {"lon": 116.3, "lat": 29.5, "label": "鄱阳湖", "kind": "battle"},
            {"lon": 115.9, "lat": 28.7, "label": "洪都·南昌", "kind": "city"},
            {"lon": 116.2, "lat": 29.7, "label": "湖口", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 117.5, "lat": 29.8, "desc": "陈友谅南下"},
            {"num": "②", "lon": 116.3, "lat": 29.5, "desc": "鄱阳湖火攻"},
        ],
        "water": [[(115.5, 29.8), (117.5, 29.9), (117.2, 28.6), (115.5, 28.7)]],
    },

    # ---------------- 清 ----------------
    "雅克萨之战": {
        "subtitle": "清军（康熙） vs 沙俄 · 公元 1685–1686 年",
        "region": (120, 56, 12, 12),
        "armies": [
            {"name": "清军（康熙）", "color": "#E74C3C", "origin_pos": (125, 50), "label": "清"},
            {"name": "沙俄军队", "color": "#2980B9", "origin_pos": (127, 53.5), "label": "俄"},
        ],
        "arrows": [
            {"from": (125, 50), "to": (125, 53.4), "color": "red", "label": "清军出征", "num": "①"},
            {"from": (127, 53.5), "to": (125, 53.4), "color": "blue", "label": "沙俄据守", "num": "②"},
        ],
        "key_places": [
            {"lon": 125, "lat": 53.4, "label": "雅克萨", "kind": "battle"},
            {"lon": 125, "lat": 50, "label": "瑷珲", "kind": "city"},
            {"lon": 126, "lat": 53, "label": "黑龙江", "kind": "other"},
        ],
        "phases": [
            {"num": "①", "lon": 125, "lat": 50, "desc": "清军出征"},
            {"num": "②", "lon": 125, "lat": 53.4, "desc": "雅克萨围城"},
        ],
        "rivers": [{"name": "黑龙江", "color": "#4A90D9", "width": 3.5,
                    "pts": [(123, 54), (125, 53.4), (127, 53.5), (129, 53)]}],
    },
}
