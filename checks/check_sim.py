"""人数、容量、路线、队列和可重复性检查。"""

from __future__ import annotations

import copy
import math

from contracts import DataError, load_world
from metrics import format_rate, improvement_rate
from policy import validate_policy_item
from simulator import run_simulation


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
    nodes, _, profiles, _, policies = load_world()
    if len(policies["items"]) != 6:
        raise AssertionError("应该有 6 组策略")
    sample = copy.deepcopy(policies["items"][0])
    sample["attraction_weights"]["N99"] = 0.5
    try:
        validate_policy_item(sample, {node["node_id"] for node in nodes if node["kind"] in {"attraction", "service"}})
    except ValueError:
        print("通过：非法节点会被拒绝")
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
    _assert_frames(result, nodes, 2, 40)
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
        result = run_simulation(nodes, edges, profiles, policies, scenarios[name])
        _assert_frames(result, nodes, 100, 120)
        if len(result["frames"]) != 121:
            raise AssertionError(f"{name} 应该有 121 帧")
    guide = run_simulation(nodes, edges, profiles, policies, scenarios["rain_guide"])
    types = {event["type"] for event in guide["events"]}
    if "weather" not in types or "guidance" not in types:
        raise AssertionError("雨天分流场景应该记录下雨和引导事件")
    print("通过：三场景 100 人 121 帧")


def _assert_frames(result: dict, nodes: list[dict], count: int, duration: int) -> None:
    by_id = {node["node_id"]: node for node in nodes}
    capacities = {node["node_id"]: node["capacity"] for node in nodes}
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
            expected = (node["inside"] + node["queue"]) / capacities[node["node_id"]]
            if abs(node["load"] - expected) > 1e-9:
                raise AssertionError("负荷公式不对")
        for visitor in visitors:
            _assert_position(visitor, by_id)


def _assert_position(visitor: dict, by_id: dict) -> None:
    status = visitor["status"]
    if status in {"not_arrived", "exited"}:
        return
    node = by_id[visitor["node_id"]]
    if status == "walking":
        end = by_id[visitor["edge_to"]]
        frac = visitor["edge_pos"] / visitor["edge_travel"]
        x = node["x"] + (end["x"] - node["x"]) * frac
        y = node["y"] + (end["y"] - node["y"]) * frac
        if abs(visitor["x"] - x) > 1e-6 or abs(visitor["y"] - y) > 1e-6:
            raise AssertionError(f"{visitor['id']} 没有沿道路移动")
        return
    distance = math.hypot(visitor["x"] - node["x"], visitor["y"] - node["y"])
    limit = 2.2 if status == "visiting" else 40
    if distance > limit:
        raise AssertionError(f"{visitor['id']} 的位置离开了节点")


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
            return visitor["wait_min"]
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
    items = []
    for weather in ("clear", "rain"):
        items.append(
            {
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
        )
    return {"items": items, "generated_at": "test", "prompt_version": "test"}


if __name__ == "__main__":
    main()
