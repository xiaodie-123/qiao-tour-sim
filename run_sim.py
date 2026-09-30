"""命令行跑一场仿真。不调用大模型。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts import load_world
from simulator import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="运行乔家大院游客仿真")
    parser.add_argument("--scenario", required=True, choices=["normal", "rain", "rain_guide"])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    nodes, edges, profiles, scenarios, policies = load_world()
    config = dict(scenarios[args.scenario])
    if args.seed is not None:
        config["seed"] = args.seed
    result = run_simulation(nodes, edges, profiles, policies, config)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    metrics = result["metrics"]
    print(
        f"{args.scenario} seed={result['meta']['seed']} "
        f"等待={metrics['mean_wait_min']} 拥堵节点分钟={metrics['congested_node_minutes']} "
        f"峰值排队={metrics['peak_queue']} 离园={metrics['exited']} 仍在园={metrics['remaining']}"
    )
    print(f"已写入 {target}")


if __name__ == "__main__":
    main()
