# -*- coding: utf-8 -*-
"""按真实地理经纬度生成四个景区的路网(平遥/五台山/云冈/壶口)。

坐标换算:等距圆柱投影(局部平面),再归一化到 0—100 的绘图范围。
步行时间:按 1.2 m/s(72 米/分钟)估算,最少 1 分钟。
来源:公开地图上各点位的相对方位(近似经纬度),非实测测绘数据。
"""
import csv
import math
from pathlib import Path

SPEED_M_PER_MIN = 72.0
SOURCE_NOTE = "公开地图相对方位(近似经纬度)"

SPOTS = {
    "pingyao": {
        "name": "平遥古城",
        "nodes": [
            # id, 名称, kind, lat, lon, 容量, 每分钟接待, 停留分钟, 遮蔽, 说明
            ("PY01", "游客中心(北关)", "entry", 37.2092, 112.1795, 80, 10, 2, 1, "北门外集散与检票"),
            ("PY02", "拱极门(北门)", "attraction", 37.2066, 112.1762, 30, 4, 3, 0, "城墙上北门城楼"),
            ("PY03", "马家大院", "attraction", 37.2040, 112.1700, 25, 3, 12, 1, "西大街北侧民居院落"),
            ("PY04", "日升昌票号", "attraction", 37.2018, 112.1692, 30, 4, 15, 1, "西大街,中国第一家票号"),
            ("PY05", "市楼", "attraction", 37.2008, 112.1760, 40, 6, 3, 0, "古城中心地标"),
            ("PY06", "明清街(南大街)", "attraction", 37.1992, 112.1762, 90, 12, 10, 0, "南北主商业步行街"),
            ("PY07", "平遥县衙", "attraction", 37.1990, 112.1712, 35, 4, 18, 1, "古城中部偏西"),
            ("PY08", "城隍庙", "attraction", 37.2010, 112.1832, 30, 4, 12, 1, "东大街北侧"),
            ("PY09", "文庙", "attraction", 37.1976, 112.1802, 30, 4, 15, 1, "东南角文庙建筑群"),
            ("PY10", "清虚观", "attraction", 37.2042, 112.1840, 20, 3, 10, 1, "东大街道教建筑"),
            ("PY11", "镖局博物馆", "attraction", 37.2052, 112.1702, 20, 3, 12, 1, "西大街北侧"),
            ("PY12", "迎薰门(南门)", "exit", 37.1946, 112.1762, 60, 10, 2, 0, "南门及城外广场"),
            ("PY13", "城墙东南角楼", "attraction", 37.1958, 112.1848, 25, 4, 8, 0, "城墙环线东南角"),
            ("PY14", "城墙西北角楼", "attraction", 37.2058, 112.1690, 25, 4, 8, 0, "城墙环线西北角"),
            ("PY15", "便民服务点(明清街)", "service", 37.1998, 112.1766, 20, 6, 4, 1, "咨询/饮水/卫生间"),
        ],
        "edges": [
            ("PY01", "PY02"), ("PY01", "PY14"), ("PY02", "PY03"), ("PY02", "PY10"),
            ("PY03", "PY04"), ("PY03", "PY11"), ("PY04", "PY05"), ("PY05", "PY06"),
            ("PY05", "PY08"), ("PY05", "PY07"), ("PY06", "PY07"), ("PY06", "PY15"),
            ("PY06", "PY09"), ("PY07", "PY12"), ("PY09", "PY12"), ("PY09", "PY13"),
            ("PY08", "PY09"), ("PY10", "PY08"), ("PY04", "PY07"), ("PY15", "PY12"),
            ("PY13", "PY12"), ("PY11", "PY14"), ("PY10", "PY13"), ("PY14", "PY03"),
        ],
    },
    "wutai": {
        "name": "五台山(台怀镇)",
        "nodes": [
            ("WT01", "游客中心(台怀镇南)", "entry", 38.9925, 113.5868, 90, 12, 3, 1, "台怀镇南侧集散中心"),
            ("WT02", "殊像寺", "attraction", 39.0027, 113.5860, 40, 5, 12, 1, "文殊菩萨道场"),
            ("WT03", "五爷庙(万佛阁)", "attraction", 39.0071, 113.5921, 60, 7, 10, 1, "香火最盛"),
            ("WT04", "塔院寺(大白塔)", "attraction", 39.0078, 113.5906, 45, 6, 12, 1, "五台山标志大白塔"),
            ("WT05", "显通寺", "attraction", 39.0087, 113.5916, 50, 6, 18, 1, "五台山规模最大寺院"),
            ("WT06", "圆照寺", "attraction", 39.0093, 113.5886, 25, 3, 10, 1, "显通寺西侧"),
            ("WT07", "菩萨顶", "attraction", 39.0110, 113.5892, 40, 5, 15, 0, "灵鹫峰上,需登台阶"),
            ("WT08", "黛螺顶", "attraction", 39.0044, 113.5994, 45, 5, 20, 0, "东峰,1080 级台阶"),
            ("WT09", "广化寺", "attraction", 39.0058, 113.5850, 25, 3, 10, 1, "台怀镇西侧"),
            ("WT10", "南山寺", "attraction", 38.9942, 113.5818, 25, 3, 15, 0, "台怀镇南山上"),
            ("WT11", "镇海寺", "attraction", 38.9905, 113.5836, 20, 3, 10, 1, "清水河畔"),
            ("WT12", "素斋堂(服务点)", "service", 39.0066, 113.5902, 30, 8, 25, 1, "团队用餐"),
            ("WT13", "台怀镇商业街(服务点)", "service", 39.0048, 113.5894, 40, 10, 12, 1, "餐饮与纪念品"),
            ("WT14", "出口(镇南停车场)", "exit", 38.9975, 113.5852, 70, 12, 2, 0, "离镇通道"),
        ],
        "edges": [
            ("WT01", "WT11"), ("WT01", "WT10"), ("WT01", "WT02"), ("WT02", "WT09"),
            ("WT02", "WT03"), ("WT03", "WT04"), ("WT04", "WT05"), ("WT05", "WT06"),
            ("WT05", "WT07"), ("WT06", "WT07"), ("WT05", "WT12"), ("WT03", "WT13"),
            ("WT03", "WT08"), ("WT08", "WT13"), ("WT13", "WT14"), ("WT12", "WT14"),
            ("WT02", "WT14"), ("WT11", "WT10"), ("WT09", "WT11"),
        ],
    },
    "yungang": {
        "name": "云冈石窟",
        "nodes": [
            ("YG01", "游客中心(景区东门)", "entry", 40.1120, 113.1398, 80, 10, 3, 1, "景区东入口集散"),
            ("YG02", "昙曜广场", "attraction", 40.1112, 113.1360, 50, 6, 6, 0, "昙曜高僧像与广场"),
            ("YG03", "礼佛大道", "attraction", 40.1106, 113.1332, 60, 8, 8, 0, "东西向主通道"),
            ("YG04", "灵岩寺(山堂水殿)", "attraction", 40.1100, 113.1306, 40, 5, 12, 1, "窟前水景寺院"),
            ("YG05", "云冈博物馆", "attraction", 40.1078, 113.1300, 50, 6, 20, 1, "主通道南侧"),
            ("YG06", "第1—4窟", "attraction", 40.1109, 113.1342, 30, 4, 12, 1, "石窟群东段"),
            ("YG07", "第5—6窟(大佛阁)", "attraction", 40.1107, 113.1320, 35, 4, 15, 1, "释迦坐佛与佛传故事"),
            ("YG08", "第7—8窟", "attraction", 40.1106, 113.1306, 25, 3, 12, 1, "六美人窟"),
            ("YG09", "五华洞(第9—13窟)", "attraction", 40.1104, 113.1288, 30, 4, 15, 1, "彩绘洞窟群"),
            ("YG10", "昙曜五窟(第16—20窟)", "attraction", 40.1102, 113.1262, 40, 5, 18, 1, "北魏早期大像窟"),
            ("YG11", "第20窟露天大佛", "attraction", 40.1100, 113.1248, 45, 6, 12, 0, "云冈标志露天大佛"),
            ("YG12", "云冈演艺中心", "attraction", 40.1074, 113.1322, 60, 12, 30, 1, "实景演出场地"),
            ("YG13", "游客服务点(窟区入口)", "service", 40.1108, 113.1336, 25, 8, 4, 1, "咨询/饮水/卫生间"),
            ("YG14", "出口(景区西门)", "exit", 40.1094, 113.1232, 60, 10, 2, 0, "西侧离场通道"),
        ],
        "edges": [
            ("YG01", "YG02"), ("YG02", "YG03"), ("YG03", "YG13"), ("YG03", "YG06"),
            ("YG03", "YG04"), ("YG03", "YG12"), ("YG12", "YG05"), ("YG04", "YG05"),
            ("YG06", "YG07"), ("YG07", "YG08"), ("YG08", "YG09"), ("YG09", "YG10"),
            ("YG10", "YG11"), ("YG11", "YG14"), ("YG10", "YG14"), ("YG05", "YG14"),
        ],
    },
    "hukou": {
        "name": "壶口瀑布",
        "nodes": [
            ("HK01", "游客中心(景区北门)", "entry", 36.1600, 110.4500, 70, 9, 3, 1, "景区北入口"),
            ("HK02", "黄河博物馆", "attraction", 36.1582, 110.4506, 40, 5, 18, 1, "黄河与瀑布地质展陈"),
            ("HK03", "黄河祭坛", "attraction", 36.1560, 110.4472, 35, 5, 8, 0, "观景前区平台"),
            ("HK04", "主观瀑台", "attraction", 36.1496, 110.4436, 80, 10, 15, 0, "正对瀑布,水雾大"),
            ("HK05", "龙洞(观瀑洞)", "attraction", 36.1487, 110.4428, 30, 4, 12, 1, "下至河沿仰视瀑布"),
            ("HK06", "旱地行船景观", "attraction", 36.1520, 110.4456, 25, 3, 8, 0, "历史航运遗迹"),
            ("HK07", "十里龙槽", "attraction", 36.1382, 110.4400, 40, 5, 12, 0, "瀑布下游深切槽谷"),
            ("HK08", "孟门山", "attraction", 36.1300, 110.4372, 30, 4, 15, 0, "河中孤岛,需摆渡/远观"),
            ("HK09", "观景台(东岸南段)", "attraction", 36.1442, 110.4416, 35, 5, 10, 0, "下游侧观景平台"),
            ("HK10", "圪针滩商贸街", "service", 36.1548, 110.4482, 45, 10, 12, 1, "餐饮与特产"),
            ("HK11", "餐饮休息区", "service", 36.1572, 110.4492, 40, 10, 20, 1, "团队用餐"),
            ("HK12", "出口(景区南门)", "exit", 36.1356, 110.4396, 60, 10, 2, 0, "南侧离场通道"),
        ],
        "edges": [
            ("HK01", "HK02"), ("HK01", "HK11"), ("HK02", "HK03"), ("HK11", "HK10"),
            ("HK03", "HK10"), ("HK03", "HK04"), ("HK04", "HK05"), ("HK04", "HK06"),
            ("HK04", "HK09"), ("HK09", "HK07"), ("HK07", "HK08"), ("HK07", "HK12"),
            ("HK08", "HK12"), ("HK10", "HK06"), ("HK06", "HK04"), ("HK09", "HK12"),
        ],
    },
}


def project(nodes):
    """经纬度 → 局部平面坐标(m),再归一化到 0—100。"""
    lats = [n[3] for n in nodes]
    lons = [n[4] for n in nodes]
    lat0 = sum(lats) / len(lats)
    lon0 = sum(lons) / len(lons)
    cos_lat = math.cos(math.radians(lat0))
    points = {}
    for node in nodes:
        x_m = (node[4] - lon0) * 111320.0 * cos_lat
        y_m = (node[3] - lat0) * 110540.0
        points[node[0]] = (x_m, y_m)
    xs = [p[0] for p in points.values()]
    ys = [p[1] for p in points.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    scale = 100.0 / span
    result = {}
    for node_id, (x_m, y_m) in points.items():
        result[node_id] = (round((x_m - min(xs)) * scale, 1), round((y_m - min(ys)) * scale, 1))
    return result, points


for key, spot in SPOTS.items():
    out_dir = Path("data/spots") / key
    out_dir.mkdir(parents=True, exist_ok=True)
    coords, metric = project(spot["nodes"])

    with open(out_dir / "nodes.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["node_id", "name", "x", "y", "kind", "capacity",
                         "service_per_min", "dwell_min", "sheltered", "source_url", "assumption_note"])
        for node in spot["nodes"]:
            x, y = coords[node[0]]
            writer.writerow([node[0], node[1], x, y, node[2], node[5], node[6], node[7],
                             node[8], SOURCE_NOTE, node[9]])

    with open(out_dir / "edges.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["edge_id", "from_id", "to_id", "travel_min", "bidirectional",
                         "source_url", "assumption_note"])
        for index, (a, b) in enumerate(spot["edges"], start=1):
            (xa, ya), (xb, yb) = metric[a], metric[b]
            distance = math.hypot(xa - xb, ya - yb)
            travel = max(1, int(round(distance / SPEED_M_PER_MIN)))
            writer.writerow(["E%02d" % index, a, b, travel, 1, SOURCE_NOTE,
                             "按直线距离 %.0f 米、步行 1.2 米/秒估算" % distance])

    print("%-4s %-10s 节点 %2d 边 %2d" % (key, spot["name"], len(spot["nodes"]), len(spot["edges"])))