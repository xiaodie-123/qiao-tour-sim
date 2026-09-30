"""面向游客的游览路线规划(基于当前拥堵与画像偏好的推荐路线,演示功能)。"""
from __future__ import annotations

import networkx as nx


def plan_route(nodes: list[dict], edges: list[dict], policies: dict, profile_id: str,
               weather: str, loads: dict[str, float], start_node: str | None = None,
               max_stops: int = 4) -> dict:
    by_id = {node["node_id"]: node for node in nodes}
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(node["node_id"])
    for edge in edges:
        graph.add_edge(edge["from_id"], edge["to_id"], weight=edge["travel_min"])
        if edge["bidirectional"]:
            graph.add_edge(edge["to_id"], edge["from_id"], weight=edge["travel_min"])
    dist = {src: targets for src, targets in nx.all_pairs_dijkstra_path_length(graph, weight="weight")}
    if start_node is None:
        start_node = next(node["node_id"] for node in nodes if node["kind"] == "entry")
    if isinstance(policies, dict) and "items" in policies:
        items = {(item["profile_id"], item["weather"]): item for item in policies["items"]}
        policy = items[(profile_id, weather)]
    else:
        policy = policies[profile_id + "|" + weather]
    candidates = [node["node_id"] for node in nodes if node["kind"] in ("attraction", "service")]

    stops: list[dict] = []
    visited: set[str] = set()
    current = start_node
    for _ in range(max_stops):
        best: str | None = None
        best_score: float | None = None
        for node_id in candidates:
            if node_id in visited or current not in dist or node_id not in dist[current]:
                continue
            load = float(loads.get(node_id, 0.0))
            shelter = policy["shelter_bonus"] * by_id[node_id]["sheltered"] if weather == "rain" else 0
            score = (
                policy["attraction_weights"].get(node_id, 0.6)
                - policy["crowd_aversion"] * min(load, 2)
                - 0.1 * dist[current][node_id]
                + shelter
            )
            if best is None or score > best_score:
                best, best_score = node_id, score
        if best is None:
            break
        node = by_id[best]
        queue_est = max(0.0, float(loads.get(best, 0.0)) - 1.0) * node["capacity"] / max(1, node["service_per_min"])
        stops.append({
            "node_id": best,
            "name": node["name"],
            "order": len(stops) + 1,
            "travel_min": int(dist[current][best]),
            "est_dwell_min": int(node["dwell_min"]),
            "est_queue_min": round(queue_est, 1),
            "load": round(float(loads.get(best, 0.0)), 2),
        })
        visited.add(best)
        current = best

    total = sum(s["travel_min"] + s["est_dwell_min"] + s["est_queue_min"] for s in stops)
    text = " -> ".join("%d.%s" % (s["order"], s["name"]) for s in stops)
    return {"profile_id": profile_id, "weather": weather, "stops": stops,
            "total_min": round(total, 1), "text": text}