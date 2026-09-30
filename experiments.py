"""按场景和种子批量仿真。只读已有策略，不调用大模型。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from contracts import load_world
from metrics import improvement_rate
from simulator import run_simulation

SCENARIOS = ("normal", "rain", "rain_guide")


def main() -> None:
    parser = argparse.ArgumentParser(description="批量比较正常、雨天和雨天分流")
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    nodes, edges, profiles, scenarios, policies = load_world()
    rows = []
    paired: dict[int, dict] = {seed: {} for seed in args.seeds}
    for scenario in SCENARIOS:
        for seed in args.seeds:
            config = dict(scenarios[scenario])
            config["seed"] = seed
            result = run_simulation(nodes, edges, profiles, policies, config)
            metrics = result["metrics"]
            row = {
                "scenario": scenario,
                "seed": seed,
                "policy_hash": result["meta"]["policy_hash"],
                "mean_wait_min": metrics["mean_wait_min"],
                "congested_node_minutes": metrics["congested_node_minutes"],
                "peak_queue": metrics["peak_queue"],
                "exited": metrics["exited"],
                "remaining": metrics["remaining"],
            }
            rows.append(row)
            if scenario in {"rain", "rain_guide"}:
                paired[seed][scenario] = row
            print(
                f"{scenario} seed={seed} 等待={metrics['mean_wait_min']} "
                f"拥堵={metrics['congested_node_minutes']} 离园={metrics['exited']}"
            )
    _write_summary(out / "experiment_summary.csv", rows)
    comparisons = _comparisons(paired, args.seeds)
    _write_comparison(out / "comparison.csv", comparisons)
    _write_range_note(out / "comparison_range.txt", comparisons)
    print(f"已写入 {out / 'experiment_summary.csv'} 和 {out / 'comparison.csv'}")


def _comparisons(paired: dict[int, dict], seeds: list[int]) -> list[dict]:
    rows = []
    for seed in seeds:
        rain = paired[seed]["rain"]
        guide = paired[seed]["rain_guide"]
        rows.append(
            {
                "seed": seed,
                "policy_hash": rain["policy_hash"],
                "rain_mean_wait_min": rain["mean_wait_min"],
                "guide_mean_wait_min": guide["mean_wait_min"],
                "wait_delta_rain_minus_guide": round(rain["mean_wait_min"] - guide["mean_wait_min"], 4),
                "wait_improvement_pct": _rate(rain["mean_wait_min"], guide["mean_wait_min"]),
                "rain_congested_node_minutes": rain["congested_node_minutes"],
                "guide_congested_node_minutes": guide["congested_node_minutes"],
                "congested_delta_rain_minus_guide": rain["congested_node_minutes"] - guide["congested_node_minutes"],
                "congested_improvement_pct": _rate(rain["congested_node_minutes"], guide["congested_node_minutes"]),
                "rain_peak_queue": rain["peak_queue"],
                "guide_peak_queue": guide["peak_queue"],
                "rain_exited": rain["exited"],
                "guide_exited": guide["exited"],
                "rain_remaining": rain["remaining"],
                "guide_remaining": guide["remaining"],
            }
        )
    return rows


def _rate(baseline: float, treatment: float) -> str:
    rate = improvement_rate(baseline, treatment)
    if rate is None:
        return "不适用"
    return f"{rate:.4f}"


def _write_summary(path: Path, rows: list[dict]) -> None:
    fields = [
        "scenario",
        "seed",
        "policy_hash",
        "mean_wait_min",
        "congested_node_minutes",
        "peak_queue",
        "exited",
        "remaining",
    ]
    _write(path, fields, rows)


def _write_comparison(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0].keys()) if rows else ["seed"]
    _write(path, fields, rows)


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_range_note(path: Path, rows: list[dict]) -> None:
    lines = [
        "配对差值 = 只下雨 - 下雨并分流。正数表示分流后数值更低。",
        "五组种子都列入，不挑效果最好的一组。",
    ]
    for key, title in (
        ("congested_delta_rain_minus_guide", "拥堵节点分钟差值"),
        ("wait_delta_rain_minus_guide", "平均等待差值"),
    ):
        values = [float(row[key]) for row in rows]
        lines.append(
            f"{title}：均值 {_mean(values):.4f}，最小 {min(values):.4f}，最大 {max(values):.4f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


if __name__ == "__main__":
    main()
