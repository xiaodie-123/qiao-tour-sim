# -*- coding: utf-8 -*-
"""检查四个景区路网形态是否各具特色,并跑通模拟。"""
import math
import os

from contracts import load_edges, load_nodes, load_profiles, load_scenarios, load_spots, spot_data_dir
from policy import load_policies
from simulator import run_simulation

spots = load_spots()
profiles = load_profiles("data/profiles.json")
pol = load_policies("data/policies.json")
scens = load_scenarios("data/scenarios.json")

print("%-6s %-8s %5s %5s %8s %8s %7s %s" % ("景区", "节点数", "宽", "高", "纵横比", "步行时长", "拥堵", "形态"))
for spot in spots:
    base = spot_data_dir(spot["key"])
    nodes = load_nodes(os.path.join(base, "nodes.csv"))
    edges = load_edges(os.path.join(base, "edges.csv"))
    xs = [n["x"] for n in nodes]
    ys = [n["y"] for n in nodes]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    ratio = width / height if height else float("inf")
    walks = [e["travel_min"] for e in edges]
    cfg = dict(scens["rain_guide"])
    cfg["spot"] = spot["name"]
    result = run_simulation(nodes, edges, profiles, pol["groups"], cfg)
    shape = "东西向长条" if ratio > 2 else ("南北向长条" if ratio < 0.5 else "接近方正/团块")
    print("%-6s %-8d %5.0f %5.0f %8.2f %8s %7d %s" % (
        spot["name"], len(nodes), width, height, ratio,
        "%d—%d 分" % (min(walks), max(walks)),
        result["metrics"]["total_congested_node_minutes"], shape))
