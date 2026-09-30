"""指标统计与改善率计算。"""
ROUND = 2


def compute_metrics(frames, visitors, config):
    node_ids = [f["node_id"] for f in frames[0]["nodes"]]
    congested = {n: 0 for n in node_ids}
    peak_queue = 0
    for fr in frames:
        q_total = 0
        for nd in fr["nodes"]:
            if nd["load"] > 1.0:
                congested[nd["node_id"]] += 1
            q_total += nd["queue"]
        peak_queue = max(peak_queue, q_total)
    entered = sum(1 for v in visitors.values() if v["entered_min"] is not None)
    total_wait = sum(v["queue_minutes"] for v in visitors.values())
    exited = sum(1 for v in visitors.values() if v["status"] == "exited")
    remaining = sum(1 for v in visitors.values() if v["status"] in ("walking", "queue", "visiting"))
    angry = sum(1 for v in visitors.values() if v.get("mood") == "angry")
    return {
        "congested_node_minutes": congested,
        "total_congested_node_minutes": sum(congested.values()),
        "mean_wait_min": round(total_wait / entered, ROUND) if entered else 0.0,
        "peak_queue": peak_queue,
        "exited": exited,
        "remaining": remaining,
        "entered": entered,
        "angry_visitors": angry,
        "observation_minutes": int(config.get("duration_min", 120)),
    }


def improvement_pct(base, inter):
    """改善率 = (基线-干预)/基线*100%;基线<=0 返回 None(显示"不适用")。"""
    if base is None or inter is None or base <= 0:
        return None
    return round((base - inter) / base * 100.0, 1)
