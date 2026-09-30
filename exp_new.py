# -*- coding: utf-8 -*-
"""在新版地图上重跑对照实验:同一随机种子比较雨天无引导与雨天分流。"""
import csv
import os
import sys

from contracts import load_edges, load_nodes, load_profiles, load_scenarios, spot_data_dir
from metrics import improvement_pct
from policy import load_policies
from simulator import run_simulation

SPOT = sys.argv[1] if len(sys.argv) > 1 else "qiao"
SEEDS = [0, 1, 2, 3, 4]
BASE = spot_data_dir(SPOT)
nodes = load_nodes(os.path.join(BASE, "nodes.csv"))
edges = load_edges(os.path.join(BASE, "edges.csv"))
profiles = load_profiles("data/profiles.json")
scens = load_scenarios("data/scenarios.json")
pol = load_policies("data/policies.json")

rows = []
diffs = []
for seed in SEEDS:
    out = {}
    for scene in ("rain", "rain_guide"):
        cfg = dict(scens[scene]); cfg["seed"] = seed; cfg["spot"] = SPOT
        out[scene] = run_simulation(nodes, edges, profiles, pol["groups"], cfg)["metrics"]
    mr, mg = out["rain"], out["rain_guide"]
    imp = improvement_pct(mr["total_congested_node_minutes"], mg["total_congested_node_minutes"])
    imp_s = "不适用" if imp is None else ("%+.1f%%" % imp)
    if imp is not None:
        diffs.append(imp)
    rows.append({"seed": seed,
                 "rain_拥堵分钟": mr["total_congested_node_minutes"],
                 "guide_拥堵分钟": mg["total_congested_node_minutes"],
                 "rain_平均等待": mr["mean_wait_min"], "guide_平均等待": mg["mean_wait_min"],
                 "rain_冲突": mr.get("conflict_events", 0), "guide_冲突": mg.get("conflict_events", 0),
                 "改善率": imp_s})

os.makedirs("outputs", exist_ok=True)
with open("outputs/comparison_new_map.csv", "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
if diffs:
    print("改善率:均值 %.1f%% 范围 %.1f%% ~ %.1f%%(%d 组)" % (sum(diffs)/len(diffs), min(diffs), max(diffs), len(diffs)))
else:
    print("改善率:不适用")
for row in rows:
    print(row)
