# -*- coding: utf-8 -*-
"""用更敏感的指标核对分流是否真的改变了排队。"""
from contracts import load_edges, load_nodes, load_profiles, load_scenarios, spot_data_dir
from policy import load_policies
from simulator import run_simulation

nodes = load_nodes(spot_data_dir("qiao") + "/nodes.csv")
edges = load_edges(spot_data_dir("qiao") + "/edges.csv")
profiles = load_profiles("data/profiles.json")
scens = load_scenarios("data/scenarios.json")
pol = load_policies("data/policies.json")

def queue_minutes(result):
    total = 0
    for frame in result["frames"]:
        for node in frame["nodes"]:
            total += node["queue"]
    return total

def wait_sum(result):
    return sum(v.get("wait_min", 0) for v in result["frames"][-1]["visitors"]) if result["frames"] else 0

for seed in (0, 1, 2, 3, 4):
    out = {}
    for scene in ("rain", "rain_guide"):
        cfg = dict(scens[scene]); cfg["seed"] = seed
        out[scene] = run_simulation(nodes, edges, profiles, pol["groups"], cfg)
    a, b = out["rain"], out["rain_guide"]
    qa, qb = queue_minutes(a), queue_minutes(b)
    print("种子 %d | 总排队分钟 %5d → %5d (%+.2f%%) | 累计等待 %6.0f → %6.0f (%+.2f%%) | 拥堵 %d→%d" % (
        seed, qa, qb, (qa - qb) / qa * 100 if qa else 0.0,
        wait_sum(a), wait_sum(b),
        (wait_sum(a) - wait_sum(b)) / wait_sum(a) * 100 if wait_sum(a) else 0.0,
        a["metrics"]["total_congested_node_minutes"], b["metrics"]["total_congested_node_minutes"]))
