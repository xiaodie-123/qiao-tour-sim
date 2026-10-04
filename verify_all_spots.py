# -*- coding: utf-8 -*-
"""五景区合并后跑通验证。"""
import os

from contracts import load_edges, load_nodes, load_profiles, load_scenarios, load_spots, spot_data_dir
from policy import load_policies
from simulator import run_simulation

spots = load_spots()
profiles = load_profiles("data/profiles.json")
pol = load_policies("data/policies.json")
scens = load_scenarios("data/scenarios.json")

for spot in spots:
    base = spot_data_dir(spot["key"])
    nodes = load_nodes(os.path.join(base, "nodes.csv"))
    edges = load_edges(os.path.join(base, "edges.csv"))
    for scene in ("rain", "rain_guide"):
        cfg = dict(scens[scene])
        cfg["spot"] = spot["name"]
        result = run_simulation(nodes, edges, profiles, pol["groups"], cfg)
        metrics = result["metrics"]
        print("%-6s %-11s 节点 %2d 边 %2d 拥堵 %4d 等待 %.2f 冲突 %2d 推送 %2d" % (
            spot["name"], scene, len(nodes), len(edges),
            metrics["total_congested_node_minutes"], metrics["mean_wait_min"],
            metrics.get("conflict_events", 0), result["meta"].get("rerouted_visitors", 0)))
