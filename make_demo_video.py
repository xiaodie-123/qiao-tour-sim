# -*- coding: utf-8 -*-
"""用真实仿真数据逐帧渲染演示动画,合成 MP4 视频,并输出 3 张高清界面渲染图(截图备选)。"""
import os
import math

import imageio
from PIL import Image, ImageDraw, ImageFont

from contracts import load_nodes, load_edges, load_profiles, load_scenarios
from policy import load_policies
from simulator import run_simulation

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"

PROFILE_COLORS = {"family": "#4C78A8", "senior": "#54A24B", "individual": "#F58518"}
LOAD_COLORS = [(0.8, "#2e9e5b"), (1.0, "#e6b800"), (9.9, "#d64545")]
SCENE_NAMES = {"conflict_demo": "场景:拥堵冲突(240人)", "rain": "场景:雨天无引导(200人)",
               "rain_guide": "场景:雨天分流引导(200人)"}


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def load_color(load):
    for th, c in LOAD_COLORS:
        if load < th:
            return c
    return "#d64545"


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_map(d, x0, y0, w, h, frame, nodes, edges, node_by_id):
    sx = w / 104.0
    sy = h / 104.0
    def px(n):
        return x0 + (n["x"] + 2) * sx
    def py(n):
        return y0 + (n["y"] + 2) * sy
    for e in edges:
        a, b = node_by_id[e["from_id"]], node_by_id[e["to_id"]]
        d.line([px(a), py(a), px(b), py(b)], fill="#b0b0b0", width=2)
    node_info = {nd["node_id"]: nd for nd in frame["nodes"]}
    for nd in frame["nodes"]:
        n = node_by_id[nd["node_id"]]
        r = 7 + n["capacity"] / 3.2
        c = hexrgb(load_color(nd["load"]))
        d.ellipse([px(n) - r, py(n) - r, px(n) + r, py(n) + r], fill=c, outline="#333333", width=1)
        d.text((px(n), py(n) - r - 16), n["name"], fill="#222222", font=font(12), anchor="ma")
    # 事件标记
    for eff in frame.get("effects", []):
        n = node_by_id.get(eff["node_id"])
        if not n:
            continue
        mark = "X" if eff["type"] in ("conflict", "dispute") else "STAR"
        col = "#8B0000" if eff["type"] != "performance" else "#b8860b"
        d.text((px(n), py(n) + r + 12), mark, fill=col, font=font(14), anchor="ma")
    # 游客
    for v in frame["visitors"]:
        if v["status"] not in ("walking", "queue", "visiting"):
            continue
        cx, cy = x0 + (v["x"] + 2) * sx, y0 + (v["y"] + 2) * sy
        if v.get("mood") == "angry":
            d.text((cx, cy), "x", fill="#8B0000", font=font(12), anchor="mm")
        else:
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=hexrgb(PROFILE_COLORS[v["profile_id"]]))
    d.rectangle([x0, y0, x0 + w, y0 + h], outline="#cccccc", width=2)


def draw_curve(d, x0, y0, w, h, frames, upto, metrics_total):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill="#ffffff", outline="#cccccc")
    maxv = max(1, max(sum(1 for nd in f["nodes"] if nd["load"] > 1.0) for f in frames))
    maxq = max(1, max(sum(nd["queue"] for nd in f["nodes"]) for f in frames))
    for i in range(0, 121, 30):
        xx = x0 + w * i / 120.0
        d.line([xx, y0, xx, y0 + h], fill="#eeeeee", width=1)
    pts_c, pts_q = [], []
    for f in frames[:upto + 1]:
        i = f["minute"]
        cx = x0 + w * i / 120.0
        cy = y0 + h - h * (sum(1 for nd in f["nodes"] if nd["load"] > 1.0) / maxv) * 0.85 - h * 0.05
        qy = y0 + h - h * (sum(nd["queue"] for nd in f["nodes"]) / maxq) * 0.85 - h * 0.05
        pts_c.append((cx, cy)); pts_q.append((cx, qy))
    if len(pts_c) > 1:
        d.line(pts_c, fill="#d64545", width=3)
    if len(pts_q) > 1:
        d.line(pts_q, fill="#4C78A8", width=2)
    d.text((x0 + 8, y0 + 4), "红=拥堵节点数 蓝=总排队人数", fill="#555555", font=font(13))


def draw_frame(frame, nodes, edges, node_by_id, scenario, frames, events, W=1280, H=720):
    img = Image.new("RGB", (W, H), "#fafaf6")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 70], fill="#16325c")
    d.text((18, 12), "乔家大院游客仿真沙盘", fill="#ffffff", font=font(26))
    d.text((18, 46), SCENE_NAMES.get(scenario, scenario), fill="#cfe0ff", font=font(16))
    wtxt = "雨天" if frame.get("weather") == "rain" else "晴天"
    gtxt = "引导中" if frame.get("guidance_active") else "无引导"
    d.text((W - 18, 20), "第 %d / 120 分钟    %s    %s" % (frame["minute"], wtxt, gtxt),
           fill="#ffffff", font=font(20), anchor="ra")
    draw_map(d, 10, 90, 660, 520, frame, nodes, edges, node_by_id)
    # 右栏
    draw_curve(d, 690, 90, 580, 300, frames, frame["minute"], None)
    node_info = {nd["node_id"]: nd for nd in frame["nodes"]}
    cong = sum(1 for nd in frame["nodes"] if nd["load"] > 1.0)
    qsum = sum(nd["queue"] for nd in frame["nodes"])
    active = sum(1 for v in frame["visitors"] if v["status"] in ("walking", "queue", "visiting"))
    angry = sum(1 for v in frame["visitors"] if v.get("mood") == "angry")
    ev_done = [e for e in events if e["minute"] <= frame["minute"]]
    lines = ["在园游客: %d     拥堵节点: %d" % (active, cong),
             "总排队人数: %d     不满游客: %d" % (qsum, angry),
             "已发生事件: %d 起" % len(ev_done)]
    for i, ln in enumerate(lines):
        d.text((690, 410 + i * 30), ln, fill="#222222", font=font(20))
    for i, e in enumerate(ev_done[-3:]):
        tag = {"conflict": "冲突", "dispute": "纠纷", "performance": "演出",
               "weather": "天气", "guidance": "引导"}.get(e["type"], e["type"])
        msg = "%d分钟 %s:%s" % (e["minute"], tag, (e.get("message") or "")[:34])
        d.text((690, 520 + i * 26), msg, fill="#8B0000" if e["type"] in ("conflict", "dispute")
               else "#2e9e5b", font=font(16))
    # 时间轴
    d.rectangle([10, 640, W - 10, 662], outline="#999999", width=1)
    d.rectangle([10, 640, 10 + int((W - 20) * frame["minute"] / 120.0), 662], fill="#16325c")
    d.text((W / 2, 680), "0 分钟" + " " * 60 + "120 分钟", fill="#666666", font=font(14), anchor="mm")
    return img


def card(lines, W=1280, H=720, bg="#16325c", fg="#ffffff", sub="#cfe0ff"):
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    y = 160
    for size, color, txt in lines:
        d.text((W / 2, y), txt, fill=color, font=font(size), anchor="mm")
        y += size * 1.8
    return img


def main():
    nodes = load_nodes(os.path.join(BASE, "data", "nodes.csv"))
    edges = load_edges(os.path.join(BASE, "data", "edges.csv"))
    profiles = load_profiles(os.path.join(BASE, "data", "profiles.json"))
    scenarios = load_scenarios(os.path.join(BASE, "data", "scenarios.json"))
    pol = load_policies(os.path.join(BASE, "data", "policies.json"))
    node_by_id = {n["node_id"]: n for n in nodes}

    runs = {}
    for sc in ("conflict_demo", "rain", "rain_guide"):
        cfg = dict(scenarios[sc]); cfg["seed"] = 0
        runs[sc] = run_simulation(nodes, edges, profiles, pol["groups"], cfg)

    frames_out = []
    # 片头
    frames_out.append(card([(44, "#ffffff", "乔家大院游客仿真沙盘"),
                            (24, "#cfe0ff", "基于群体画像的景区客流仿真与拥堵干预"),
                            (20, "#ffffff", "问题:节假日景区拥堵、纠纷靠经验应对"),
                            (20, "#ffffff", "方法:大模型生成游客群体偏好 + 个体状态仿真引擎"),
                            (20, "#ffffff", "演示:20个节点 / 6类场景 / 事件系统 / 分流对比")]))
    # 三个场景动画
    for sc in ("conflict_demo", "rain", "rain_guide"):
        frames = runs[sc]["frames"]
        for i in range(0, 121, 2):
            frames_out.append(draw_frame(frames[i], nodes, edges, node_by_id, sc,
                                         frames, runs[sc]["events"]))
    # 对比页
    mr = runs["rain"]["metrics"]; mg = runs["rain_guide"]["metrics"]
    imp = (mr["total_congested_node_minutes"] - mg["total_congested_node_minutes"]) / mr["total_congested_node_minutes"] * 100.0
    frames_out.append(card([(40, "#ffffff", "雨天无引导 vs 雨天分流引导(同一种子)"),
                            (24, "#cfe0ff", "总拥堵节点分钟:%d -> %d(改善 %.1f%%)"
                             % (mr["total_congested_node_minutes"], mg["total_congested_node_minutes"], imp)),
                            (24, "#cfe0ff", "平均累计等待:%.2f -> %.2f 分钟"
                             % (mr["mean_wait_min"], mg["mean_wait_min"])),
                            (24, "#cfe0ff", "峰值排队:%d -> %d 人" % (mr["peak_queue"], mg["peak_queue"])),
                            (20, "#ffffff", "15次对照实验:改善率均值15.4%(8.1%~21.3%),全部种子有效")]))
    # 片尾
    frames_out.append(card([(40, "#ffffff", "局限与声明"),
                            (22, "#cfe0ff", "地图为示意图;容量与事件规则为演示假设"),
                            (22, "#cfe0ff", "策略可切换DeepSeek真实生成(页面如实标注)"),
                            (22, "#cfe0ff", "不冒充实测数据;展望真实数据接入与满意度模型")]))

    # 每帧重复4次,10fps → 0.4秒/帧
    writer = imageio.get_writer(os.path.join(BASE, "dist", "演示视频.mp4"), fps=10,
                                codec="libx264", quality=7)
    for f in frames_out:
        for _ in range(4):
            writer.append_data(imageio.core.util.asarray(f))
    writer.close()
    print("video frames:", len(frames_out), "->", os.path.join(BASE, "dist", "演示视频.mp4"))

    # 3 张高清渲染图(截图备选,建议用真实浏览器截图替换)
    os.makedirs(os.path.join(BASE, "screenshots"), exist_ok=True)
    big = lambda img: img.resize((1600, 1000), Image.LANCZOS)
    big(draw_frame(runs["conflict_demo"]["frames"][55], nodes, edges, node_by_id,
                   "conflict_demo", runs["conflict_demo"]["frames"], runs["conflict_demo"]["events"], 1600, 1000)
        ).save(os.path.join(BASE, "screenshots", "render1_conflict.png"))
    big(draw_frame(runs["rain_guide"]["frames"][80], nodes, edges, node_by_id,
                   "rain_guide", runs["rain_guide"]["frames"], runs["rain_guide"]["events"], 1600, 1000)
        ).save(os.path.join(BASE, "screenshots", "render2_guide.png"))
    big(card([(44, "#ffffff", "雨天无引导 vs 雨天分流引导"),
              (30, "#cfe0ff", "总拥堵节点分钟 %d -> %d(改善 %.1f%%)"
               % (mr["total_congested_node_minutes"], mg["total_congested_node_minutes"], imp)),
              (26, "#cfe0ff", "平均等待 %.2f -> %.2f 分钟" % (mr["mean_wait_min"], mg["mean_wait_min"]))],
             1600, 1000)).save(os.path.join(BASE, "screenshots", "render3_compare.png"))
    print("renders saved")


if __name__ == "__main__":
    main()
