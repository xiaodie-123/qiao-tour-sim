"""人数、容量、路线、队列和可重复性检查。

跑法:`python -m checks.check_sim`(要先在项目根目录)。全部通过会打印「全部检查通过」。
"""

from __future__ import annotations

import copy
import math

from contracts import DataError, load_world
from metrics import format_rate, improvement_rate
from policy import validate_policy_item
from simulator import run_simulation

CHECK_COUNT = 100          # 自检固定用 100 人,页面上的场景配置是多少不影响这里
CHECK_DURATION = 120


def main() -> None:
    check_improvement_rate()
    check_policy_rejection()
    check_fifo_and_capacity()
    check_reproducible()
    check_full_qiao()
    print("全部检查通过")


def check_improvement_rate() -> None:
    if improvement_rate(0, 5) is not None or format_rate(None) != "不适用":
        raise AssertionError("基线为 0 时应显示不适用")
    if improvement_rate(10, 4) != 60:
        raise AssertionError("改善率算错")
    if improvement_rate(10, 12) != -20:
        raise AssertionError("变差时必须得到负数")
    print("通过：改善率")


def check_policy_rejection() -> None:
    nodes, _, _, _, policies = load_world()
    if len(policies) != 6:
        raise AssertionError("应该有 6 组策略")
    ids = {node["node_id"] for node in nodes if node["kind"] in {"attraction", "service"}}
    for key, group in policies.items():
        # 权重必须正好覆盖全部非出入口节点,缺一个多一个都不行
        validate_policy_item(group, ids)
    sample = copy.deepcopy(policies[sorted(policies)[0]])
    sample["attraction_weights"]["NOT_A_REAL_NODE"] = 0.5
    try:
        validate_policy_item(sample, ids)
    except ValueError:
        print("通过：策略覆盖全部节点，非法节点编号会被拒绝")
        return
    raise AssertionError("非法节点编号没有被拒绝")


def check_fifo_and_capacity() -> None:
    nodes = [
        _node("A", "入口", 0, 0, "entry", 10, 10, 0, 1),
        _node("B", "展厅", 10, 0, "attraction", 1, 1, 3, 1),
        _node("C", "出口", 20, 0, "exit", 10, 10, 0, 1),
    ]
    edges = [
        _edge("E1", "A", "B", 1),
        _edge("E2", "B", "C", 1),
    ]
    profiles = [{"profile_id": "individual", "name": "散客", "description": "测试"}]
    policies = _two_weather_policy("individual", {"B": 0.9})
    config = {
        "name": "fifo",
        "visitor_count": 2,
        "duration_min": 40,
        "seed": 1,
        "profile_ratios": {"individual": 1},
        "arrival_window_min": 1,
        "weather_change_min": None,
        "weather_after": "clear",
        "guidance_enabled": False,
        "guidance_start_min": 20,
        "guidance_acceptance": 0.6,
        "max_visits": 1,
        "visit_budget_min": 90,
    }
    result = run_simulation(nodes, edges, profiles, policies, config)
    _assert_frames(result, nodes, edges, 2, 40)
    queued = [
        frame["minute"]
        for frame in result["frames"]
        for node in frame["nodes"]
        if node["node_id"] == "B" and node["queue"] >= 1
    ]
    if not queued:
        raise AssertionError("容量为 1 时第二个人应该排队")
    exits = {visitor_id: _first_minute(result, visitor_id, "exited") for visitor_id in ("v001", "v002")}
    if exits["v001"] is None or exits["v002"] is None or exits["v001"] >= exits["v002"]:
        raise AssertionError(f"先进入的人应该先离开，实际 {exits}")
    waits = {visitor_id: _last_wait(result, visitor_id) for visitor_id in ("v001", "v002")}
    if waits["v002"] < 1:
        raise AssertionError(f"后进入的人等待应至少 1 分钟，实际 {waits}")
    print("通过：容量上限和队列先后")


def check_reproducible() -> None:
    nodes, edges, profiles, scenarios, policies = load_world()
    config = dict(scenarios["rain"])
    config["seed"] = 3
    config["visitor_count"] = 40
    first = run_simulation(nodes, edges, profiles, policies, config)
    second = run_simulation(nodes, edges, profiles, policies, config)
    if _signature(first) != _signature(second):
        raise AssertionError("相同种子和策略两次结果不一致")
    try:
        bad = dict(config)
        bad["profile_ratios"] = {"family": 0.5, "senior": 0.5, "individual": 0.5}
        run_simulation(nodes, edges, profiles, policies, bad)
    except DataError:
        print("通过：相同输入可复现，比例错误会拒绝")
        return
    raise AssertionError("比例之和不为 1 时没有报错")


def check_full_qiao() -> None:
    nodes, edges, profiles, scenarios, policies = load_world()
    for name in ("normal", "rain", "rain_guide"):
        config = dict(scenarios[name])
        config["visitor_count"] = CHECK_COUNT
        result = run_simulation(nodes, edges, profiles, policies, config)
        _assert_frames(result, nodes, edges, CHECK_COUNT, CHECK_DURATION)
        if result["meta"]["policy_hash"] == "":
            raise AssertionError(f"{name} 没有记录策略指纹")
    guide = run_simulation(nodes, edges, profiles, policies, dict(scenarios["rain_guide"], visitor_count=CHECK_COUNT))
    types = {event["type"] for event in guide["events"]}
    if "weather" not in types or "guidance" not in types:
        raise AssertionError("雨天分流场景应该记录下雨和引导事件")
    print(f"通过：三场景 {CHECK_COUNT} 人 {CHECK_DURATION + 1} 帧")


def _assert_frames(result: dict, nodes: list[dict], edges: list[dict], count: int, duration: int) -> None:
    by_id = {node["node_id"]: node for node in nodes}
    capacities = {node["node_id"]: node["capacity"] for node in nodes}
    segments = _segments(nodes, edges)
    if len(result["frames"]) != duration + 1:
        raise AssertionError("帧数不对")
    for frame in result["frames"]:
        visitors = frame["visitors"]
        if len(visitors) != count:
            raise AssertionError(f"第 {frame['minute']} 分钟人数不是 {count}")
        statuses = [visitor["status"] for visitor in visitors]
        if any(status not in {"not_arrived", "walking", "queue", "visiting", "exited"} for status in statuses):
            raise AssertionError("出现了约定之外的状态")
        for node in frame["nodes"]:
            if node["inside"] > capacities[node["node_id"]]:
                raise AssertionError(f"{node['node_id']} 超过容量")
            # 引擎写帧时把负荷 round 到 3 位,这里必须用同一个口径比
            expected = round((node["inside"] + node["queue"]) / capacities[node["node_id"]], 3)
            if abs(node["load"] - expected) > 1e-9:
                raise AssertionError("负荷公式不对")
        for visitor in visitors:
            _assert_position(visitor, by_id, segments)


def _segments(nodes: list[dict], edges: list[dict]) -> list[tuple]:
    by_id = {node["node_id"]: node for node in nodes}
    return [
        ((by_id[edge["from_id"]]["x"], by_id[edge["from_id"]]["y"]),
         (by_id[edge["to_id"]]["x"], by_id[edge["to_id"]]["y"]))
        for edge in edges
    ]


def _assert_position(visitor: dict, by_id: dict, segments: list[tuple]) -> None:
    """在途的人必须落在某条道路上;排队和游览的人必须贴在节点上。"""
    status = visitor["status"]
    if status in {"not_arrived", "exited"}:
        return
    point = (visitor["x"], visitor["y"])
    if status == "walking":
        offset = min(_point_segment_distance(point, segment) for segment in segments)
        if offset > 0.05:
            raise AssertionError(f"{visitor['id']} 没有沿道路移动(偏离最近路段 {offset:.3f})")
        return
    node = by_id[visitor["node_id"]]
    if math.hypot(point[0] - node["x"], point[1] - node["y"]) > 1e-6:
        raise AssertionError(f"{visitor['id']} 的位置离开了节点")


def _point_segment_distance(point: tuple, segment: tuple) -> float:
    px, py = point
    (ax, ay), (bx, by) = segment
    vx, vy = bx - ax, by - ay
    length2 = vx * vx + vy * vy
    if length2 == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * vx + (py - ay) * vy) / length2
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _signature(result: dict) -> tuple:
    packed = []
    for frame in result["frames"]:
        for visitor in frame["visitors"]:
            packed.append((frame["minute"], visitor["id"], visitor["status"], visitor["x"], visitor["y"]))
    return tuple(packed)


def _first_minute(result: dict, visitor_id: str, status: str) -> int | None:
    for frame in result["frames"]:
        for visitor in frame["visitors"]:
            if visitor["id"] == visitor_id and visitor["status"] == status:
                return frame["minute"]
    return None


def _last_wait(result: dict, visitor_id: str) -> int:
    for visitor in result["frames"][-1]["visitors"]:
        if visitor["id"] == visitor_id:
            return visitor["queue_minutes"]
    raise AssertionError(f"找不到 {visitor_id}")


def _node(node_id, name, x, y, kind, capacity, service, dwell, sheltered) -> dict:
    return {
        "node_id": node_id,
        "name": name,
        "x": x,
        "y": y,
        "kind": kind,
        "capacity": capacity,
        "service_per_min": service,
        "dwell_min": dwell,
        "sheltered": sheltered,
        "source_url": "-",
        "assumption_note": "测试",
    }


def _edge(edge_id, from_id, to_id, travel) -> dict:
    return {
        "edge_id": edge_id,
        "from_id": from_id,
        "to_id": to_id,
        "travel_min": travel,
        "bidirectional": 1,
        "source_url": "-",
        "assumption_note": "测试",
    }


def _two_weather_policy(profile_id: str, weights: dict) -> dict:
    """自检用的最小策略:同一个画像的晴天/雨天两组。"""
    groups = {}
    for weather in ("clear", "rain"):
        groups[profile_id + "|" + weather] = {
            "profile_id": profile_id,
            "weather": weather,
            "attraction_weights": dict(weights),
            "crowd_aversion": 1,
            "shelter_bonus": 0.2,
            "dwell_multiplier": 1,
            "summary": "测试策略",
            "source": "rule_fallback",
            "model": None,
        }
    return groups


if __name__ == "__main__":
    main()
