"""仿真引擎:不依赖 Streamlit;返回 {meta, frames, events, metrics}。
事件系统:拥堵自动冲突(conflict)、游客与工作人员纠纷(dispute)、互动演出(performance)。"""
import random
from collections import deque

import networkx as nx

from contracts import validate_config
from metrics import compute_metrics
from policy import policy_hash


def _build_graph(nodes, edges):
    g = nx.DiGraph()
    g.add_nodes_from(n["node_id"] for n in nodes)
    for e in edges:
        g.add_edge(e["from_id"], e["to_id"], travel_min=e["travel_min"])
        if e["bidirectional"]:
            g.add_edge(e["to_id"], e["from_id"], travel_min=e["travel_min"])
    return g


def _assign_profiles(count, profile_ids, ratios, seed):
    rng = random.Random(seed)
    ordered = list(profile_ids)
    base = [int(round(count * ratios[p])) for p in ordered]
    base[-1] += count - sum(base)
    seq = []
    for p, c in zip(ordered, base):
        seq.extend([p] * c)
    rng.shuffle(seq)
    return seq


def run_simulation(nodes, edges, profiles, policies, config):
    validate_config(config)          # 比例之和、必填字段不对就直接抛 DataError,不带着错数据往下跑
    cfg = dict(config)
    node_by_id = {n["node_id"]: n for n in nodes}
    entry_id = next(n["node_id"] for n in nodes if n["kind"] == "entry")
    exit_id = next(n["node_id"] for n in nodes if n["kind"] == "exit")
    candidate_ids = [n["node_id"] for n in nodes if n["kind"] in ("attraction", "service")]
    cap = {n["node_id"]: n["capacity"] for n in nodes}
    service = {n["node_id"]: n["service_per_min"] for n in nodes}
    dwell_base = {n["node_id"]: n["dwell_min"] for n in nodes}
    sheltered = {n["node_id"]: n["sheltered"] for n in nodes}
    pos_of = {n["node_id"]: (n["x"], n["y"]) for n in nodes}

    g = _build_graph(nodes, edges)
    lengths = dict(nx.all_pairs_dijkstra_path_length(g, weight="travel_min"))
    paths = dict(nx.all_pairs_dijkstra_path(g, weight="travel_min"))

    profile_ids = [p["profile_id"] for p in profiles]
    count = int(cfg["visitor_count"])
    duration = int(cfg["duration_min"])
    seed = int(cfg["seed"])
    seq = _assign_profiles(count, profile_ids, cfg["profile_ratios"], seed)
    arrival_window = int(cfg.get("arrival_window_min", 20))
    max_visits = int(cfg.get("max_visits", 4))
    visit_budget = int(cfg.get("visit_budget_min", 90))
    weather_change_min = cfg.get("weather_change_min")
    guidance_enabled = bool(cfg.get("guidance_enabled", False))
    guidance_start_min = int(cfg.get("guidance_start_min", 20))
    guidance_acceptance = float(cfg.get("guidance_acceptance", 0.6))
    guidance_radius = float(cfg.get("guidance_radius", 10.0))
    conflict_enabled = bool(cfg.get("conflict_enabled", True))
    conflict_threshold = float(cfg.get("conflict_threshold", 1.8))
    conflict_duration = int(cfg.get("conflict_duration", 8))
    conflict_cooldown = int(cfg.get("conflict_cooldown", 20))
    angry_wait_min = float(cfg.get("angry_wait_min", 20.0))
    scheduled = [dict(e) for e in cfg.get("events", [])]

    visitors = {}
    for i in range(count):
        vid = "v%03d" % (i + 1)
        pid = seq[i]
        vr = random.Random("%d:%s" % (seed, vid))
        visitors[vid] = {
            "id": vid, "profile_id": pid,
            "arrival_min": vr.randrange(0, arrival_window),
            "acceptance": vr.random(),
            "dwell_jitter": vr.uniform(0.8, 1.2),
            "jitter": {nid: vr.uniform(-0.15, 0.15) for nid in candidate_ids},
            "status": "not_arrived",
            "pos": list(pos_of[entry_id]),
            "node_id": None,
            "path": [], "edge_idx": 0, "edge_remaining": 0,
            "dwell_remaining": 0,
            "visited": set(),
            "entered_min": None,
            "queue_started": None,
            "queue_minutes": 0,
            "mood": "normal",
        }

    inside = {nid: 0 for nid in node_by_id}
    queue = {nid: deque() for nid in node_by_id}
    effects = {}                    # nid -> {"type", "end_min"}
    overload_streak = {nid: 0 for nid in node_by_id}
    last_conflict = {nid: -999 for nid in node_by_id}
    event_counters = {"conflict": 0, "dispute": 0, "performance": 0}
    rerouted_visitors = 0
    weather = "clear"
    guidance_active = False
    frames = []
    events = []

    def pol(pid):
        return policies[pid + "|" + weather]

    def eff_service(nid):
        lst = effects.get(nid, [])
        if not lst:
            return service[nid]
        worst = 0.0
        boost = 0
        for e in lst:
            if e["type"] == "dispute":
                worst = 1.0
            elif e["type"] == "conflict":
                worst = max(worst, 0.5)
            elif e["type"] == "performance":
                boost += 2
        if worst > 0:
            return max(0, int(service[nid] * (1.0 - worst)))
        return service[nid] + boost

    def node_boost(nid):
        lst = effects.get(nid, [])
        return 0.35 if any(e["type"] == "performance" for e in lst) else 0.0

    def log_event(minute, etype, nid, message):
        events.append({"minute": minute, "type": etype, "node_id": nid, "message": message})
        event_counters[etype] = event_counters.get(etype, 0) + 1

    def activate(minute, etype, nid, dur, message):
        effects.setdefault(nid, []).append({"type": etype, "end_min": minute + int(dur)})
        log_event(minute, etype, nid, message)
        return reroute_toward(minute, nid)

    def compute_dwell(nid, v):
        mult = pol(v["profile_id"])["dwell_multiplier"]
        return max(1, int(round(dwell_base[nid] * mult * v["dwell_jitter"])))

    def choose_target(v, t, cur_id):
        cands = [nid for nid in candidate_ids if nid != cur_id and nid not in v["visited"]]
        if not cands:
            return exit_id
        p = pol(v["profile_id"])
        best = None
        best_score = None
        loads = {}
        scores = {}
        for j in cands:
            if cur_id not in lengths or j not in lengths[cur_id]:
                continue
            load_j = (inside[j] + len(queue[j])) / cap[j]
            loads[j] = load_j
            cav = p["crowd_aversion"] * (0.5 if weather == "rain" else 1.0)
            if guidance_active and v["acceptance"] < guidance_acceptance:
                cav *= 2.0      # 接受引导的游客更在意排队,系统据此重新推荐(分流机制)
            sc = (p["attraction_weights"].get(j, 0.6)
                  + node_boost(j)
                  - cav * min(load_j, 2.0)
                  - 0.1 * lengths[cur_id][j]
                  + (p["shelter_bonus"] if weather == "rain" else 0.0) * sheltered[j]
                  + v["jitter"].get(j, 0.0))
            scores[j] = sc
            if best is None or sc > best_score:
                best, best_score = j, sc
        if best is None:
            return exit_id
        return best

    def start_walk(v, from_id, target, t):
        if target == from_id:
            target = exit_id
        v["path"] = paths[from_id][target]
        v["edge_idx"] = 0
        v["edge_remaining"] = g[v["path"][0]][v["path"][1]]["travel_min"]
        v["status"] = "walking"
        v["node_id"] = None

    def reroute_toward(minute, nid):
        """事件发生时,为在途前往该节点的游客推送替代路线(演示规则)。"""
        moved = 0
        for vid in sorted(visitors):
            v = visitors[vid]
            if v["status"] != "walking" or v.get("heading_exit"):
                continue
            if not v["path"] or v["path"][-1] != nid:
                continue
            cur = v["path"][v["edge_idx"]]
            target = choose_target(v, minute, cur)
            start_walk(v, cur, target, minute)
            moved += 1
        return moved

    def arrive_at(v, nid, t):
        if inside[nid] < cap[nid]:
            v["status"] = "visiting"
            v["node_id"] = nid
            v["dwell_remaining"] = compute_dwell(nid, v)
            inside[nid] += 1
        else:
            v["status"] = "queue"
            v["node_id"] = nid
            v["queue_started"] = t
            queue[nid].append(v["id"])

    def update_pos(v):
        if v["status"] == "walking":
            a = v["path"][v["edge_idx"]]
            b = v["path"][v["edge_idx"] + 1]
            total = g[a][b]["travel_min"]
            frac = 1.0 - v["edge_remaining"] / float(total)
            (xa, ya) = pos_of[a]
            (xb, yb) = pos_of[b]
            v["pos"] = [round(xa + (xb - xa) * frac, 2), round(ya + (yb - ya) * frac, 2)]
        elif v["status"] == "exited":
            v["pos"] = list(pos_of[exit_id])
        elif v["status"] == "not_arrived":
            v["pos"] = list(pos_of[entry_id])
        else:
            v["pos"] = list(pos_of[v["node_id"]])

    def record_frame(t):
        node_rows = []
        for nid in node_by_id:
            load = (inside[nid] + len(queue[nid])) / cap[nid]
            node_rows.append({"node_id": nid, "inside": inside[nid],
                              "queue": len(queue[nid]), "load": round(load, 3)})
        vis_rows = []
        for vid in sorted(visitors):
            v = visitors[vid]
            vis_rows.append({"id": vid, "x": v["pos"][0], "y": v["pos"][1],
                             "status": v["status"], "profile_id": v["profile_id"],
                             "node_id": v["node_id"], "mood": v["mood"],
                             "queue_minutes": v["queue_minutes"]})
        eff_rows = [{"node_id": nid, "type": e["type"], "remaining_min": e["end_min"] - t}
                    for nid, lst in effects.items() for e in lst if e["end_min"] > t]
        frames.append({"minute": t, "nodes": node_rows, "visitors": vis_rows,
                       "weather": weather, "guidance_active": guidance_active,
                       "effects": eff_rows})

    for t in range(0, duration + 1):
        if weather_change_min is not None and t == int(weather_change_min) and t > 0:
            weather = cfg.get("weather_after", "rain")
            events.append({"minute": t, "type": "weather", "node_id": None, "message": "天气变化:开始下雨"})
        if guidance_enabled and t == guidance_start_min:
            guidance_active = True
            events.append({"minute": t, "type": "guidance", "node_id": None, "message": "分流引导启动"})
        # 计划事件
        for ev in scheduled:
            if int(ev.get("minute", -1)) == t:
                etype = ev.get("type", "")
                nid = ev.get("node_id")
                if nid and nid in node_by_id and etype in ("dispute", "performance", "conflict"):
                    rerouted_visitors += activate(t, etype, nid, int(ev.get("duration", 5)),
                                                  str(ev.get("message", etype)))
        # 过期效果清除
        for nid in list(effects):
            effects[nid] = [e for e in effects[nid] if e["end_min"] > t]
            if not effects[nid]:
                del effects[nid]
        # 拥堵自动冲突:load 持续超过阈值触发游客冲突(演示规则)
        if conflict_enabled:
            for nid in node_by_id:
                if node_by_id[nid]["kind"] in ("entry", "exit"):
                    continue
                load = (inside[nid] + len(queue[nid])) / cap[nid]
                if load >= conflict_threshold:
                    overload_streak[nid] += 1
                else:
                    overload_streak[nid] = 0
                if overload_streak[nid] >= 3 and (t - last_conflict[nid]) >= conflict_cooldown:
                    rerouted_visitors += activate(t, "conflict", nid, conflict_duration,
                                                  "游客冲突:%s 持续拥堵引发游客骚动与冲突,服务效率减半(演示规则)"
                                                  % node_by_id[nid]["name"])
                    last_conflict[nid] = t
                    overload_streak[nid] = 0
        # 1) 入园与到达
        for vid in sorted(visitors):
            v = visitors[vid]
            if v["status"] == "not_arrived" and t >= v["arrival_min"]:
                v["entered_min"] = t
                start_walk(v, entry_id, choose_target(v, t, entry_id), t)
        # 2) 行走推进
        for vid in sorted(visitors):
            v = visitors[vid]
            if v["status"] == "walking":
                v["edge_remaining"] -= 1
                if v["edge_remaining"] <= 0:
                    nxt = v["path"][v["edge_idx"] + 1]
                    if nxt == exit_id:
                        v["status"] = "exited"
                        v["node_id"] = None
                    else:
                        v["edge_idx"] += 1
                        if v["edge_idx"] < len(v["path"]) - 1:
                            v["edge_remaining"] = g[v["path"][v["edge_idx"]]][v["path"][v["edge_idx"] + 1]]["travel_min"]
                        else:
                            arrive_at(v, nxt, t)
        # 3) 游览结束与离开决策
        for vid in sorted(visitors):
            v = visitors[vid]
            if v["status"] == "visiting":
                v["dwell_remaining"] -= 1
                if v["dwell_remaining"] <= 0:
                    inside[v["node_id"]] -= 1
                    v["visited"].add(v["node_id"])
                    if len(v["visited"]) >= max_visits or (t - v["entered_min"]) >= visit_budget:
                        target = exit_id
                    else:
                        target = choose_target(v, t, v["node_id"])
                    start_walk(v, v["node_id"], target, t)
        # 4) 队列 FIFO 入场(受事件影响的接纳速率)
        for nid in node_by_id:
            limit = min(cap[nid] - inside[nid], eff_service(nid))
            served = 0
            while queue[nid] and served < limit:
                vid = queue[nid].popleft()
                v = visitors[vid]
                v["queue_minutes"] += t - v["queue_started"]
                v["status"] = "visiting"
                v["node_id"] = nid
                v["dwell_remaining"] = compute_dwell(nid, v)
                inside[nid] += 1
                served += 1
        # 5) 情绪与位置
        for vid in sorted(visitors):
            v = visitors[vid]
            v["mood"] = "angry" if v["queue_minutes"] > angry_wait_min else "normal"
            update_pos(v)
        record_frame(t)

    metrics = compute_metrics(frames, visitors, cfg)
    metrics["conflict_events"] = event_counters.get("conflict", 0)
    metrics["dispute_events"] = event_counters.get("dispute", 0)
    metrics["performance_events"] = event_counters.get("performance", 0)
    any_llm = any(gp.get("source") == "llm" for gp in policies.values())
    meta = {
        "seed": seed,
        "scenario": cfg.get("name", "custom"),
        "spot": cfg.get("spot", ""),
        "mode": "llm_policy_hybrid" if any_llm else "rule_policy_fallback",
        "visitor_count": count,
        "duration_min": duration,
        "policy_hash": policy_hash(policies),
        "event_counts": event_counters,
        "rerouted_visitors": rerouted_visitors,
    }
    return {"meta": meta, "frames": frames, "events": events, "metrics": metrics}
