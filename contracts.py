"""共同数据结构与读写校验。修改字段必须通知全组,以本文件为准。"""
import csv
import json
import os

NODE_FIELDS = ["node_id", "name", "x", "y", "kind", "capacity",
               "service_per_min", "dwell_min", "sheltered", "source_url", "assumption_note"]
EDGE_FIELDS = ["edge_id", "from_id", "to_id", "travel_min",
               "bidirectional", "source_url", "assumption_note"]
KINDS = ("entry", "attraction", "service", "exit")
STATUSES = ("not_arrived", "walking", "queue", "visiting", "exited")


class DataError(ValueError):
    """输入数据不合法:字段缺失、比例不对、端点不存在、节点缺 entry/exit 等。"""


def _read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_nodes(path):
    rows = _read_csv(path)
    nodes = []
    for r in rows:
        nodes.append({
            "node_id": r["node_id"].strip(),
            "name": r["name"].strip(),
            "x": float(r["x"]),
            "y": float(r["y"]),
            "kind": r["kind"].strip(),
            "capacity": int(r["capacity"]),
            "service_per_min": int(r["service_per_min"]),
            "dwell_min": int(r["dwell_min"]),
            "sheltered": int(r["sheltered"]),
            "source_url": (r.get("source_url") or "").strip(),
            "assumption_note": (r.get("assumption_note") or "").strip(),
        })
    validate_nodes(nodes)
    return nodes


def load_edges(path):
    rows = _read_csv(path)
    edges = []
    for r in rows:
        edges.append({
            "edge_id": r["edge_id"].strip(),
            "from_id": r["from_id"].strip(),
            "to_id": r["to_id"].strip(),
            "travel_min": int(r["travel_min"]),
            "bidirectional": int(r["bidirectional"]),
            "source_url": (r.get("source_url") or "").strip(),
            "assumption_note": (r.get("assumption_note") or "").strip(),
        })
    return edges


def load_profiles(path):
    with open(path, encoding="utf-8") as f:
        profiles = json.load(f)
    validate_profiles(profiles)
    return profiles


def load_scenarios(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_nodes(nodes):
    ids = [n["node_id"] for n in nodes]
    if len(ids) != len(set(ids)):
        raise DataError("node_id 重复")
    kinds = [n["kind"] for n in nodes]
    if "entry" not in kinds or "exit" not in kinds:
        raise DataError("路网必须包含 entry 与 exit 节点")
    for n in nodes:
        if n["kind"] not in KINDS:
            raise DataError("非法 kind: %s -> %s" % (n["node_id"], n["kind"]))
        if n["capacity"] <= 0 or n["service_per_min"] < 0:
            raise DataError("节点 %s 容量必须为正、接纳速率非负" % n["node_id"])
    return nodes


def validate_edges(edges, node_ids):
    for e in edges:
        if e["from_id"] not in node_ids or e["to_id"] not in node_ids:
            raise DataError("边 %s 的端点不存在" % e["edge_id"])
        if e["travel_min"] <= 0:
            raise DataError("边 %s 的 travel_min 必须为正" % e["edge_id"])
    return edges


def validate_profiles(profiles):
    if not isinstance(profiles, list) or not profiles:
        raise DataError("profiles 必须是列表")
    ids = [p["profile_id"] for p in profiles]
    if len(ids) != len(set(ids)):
        raise DataError("profile_id 重复")
    for p in profiles:
        for k in ("profile_id", "name", "description"):
            if k not in p:
                raise DataError("画像缺字段: %s" % p.get("profile_id"))
    return profiles


def load_spots():
    """景区清单(分布示意与选择页使用)。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "spots.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def spot_data_dir(spot_key):
    """spot_key 为空时用默认 data 目录,否则用 data/spots/<key>。"""
    base = os.path.dirname(os.path.abspath(__file__))
    if not spot_key:
        return os.path.join(base, "data")
    return os.path.join(base, "data", "spots", spot_key)


def validate_config(config):
    required = ["visitor_count", "duration_min", "seed", "profile_ratios",
                "arrival_window_min", "max_visits", "visit_budget_min"]
    for k in required:
        if k not in config:
            raise DataError("场景缺字段: %s" % k)
    ratios = config["profile_ratios"]
    if abs(sum(ratios.values()) - 1.0) > 1e-6:
        raise DataError("profile_ratios 合计必须为 1")
    return config


def load_world(spot_key=""):
    """一次载入一整套仿真输入:返回 (nodes, edges, profiles, scenarios, policies)。

    spot_key 为空用 data/,否则用 data/spots/<key>/。
    policies 是 "画像|天气" 到策略组的字典,可以直接传给 run_simulation。
    """
    from policy import load_policies  # 局部导入,避免 contracts 与 policy 互相 import

    base = spot_data_dir(spot_key)
    root = os.path.dirname(os.path.abspath(__file__))
    nodes = load_nodes(os.path.join(base, "nodes.csv"))
    edges = load_edges(os.path.join(base, "edges.csv"))
    validate_edges(edges, {n["node_id"] for n in nodes})
    profiles = load_profiles(os.path.join(root, "data", "profiles.json"))
    scenarios = load_scenarios(os.path.join(root, "data", "scenarios.json"))
    for name, config in scenarios.items():
        try:
            validate_config(config)
        except DataError as exc:
            raise DataError("场景 %s 不合法: %s" % (name, exc)) from exc
    groups = load_policies(os.path.join(root, "data", "policies.json"))["groups"]
    return nodes, edges, profiles, scenarios, groups
