"""生成 data/policies.json。没有密钥时写入备用规则，并标明来源。"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from contracts import load_nodes, load_profiles
from policy import build_policies, policy_hash

BASE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="生成游客群体策略文件")
    parser.add_argument("--out", required=True, help="输出的 policies.json 路径")
    args = parser.parse_args()
    nodes = load_nodes(str(BASE / "data" / "nodes.csv"))
    profiles = load_profiles(str(BASE / "data" / "profiles.json"))
    groups = build_policies(nodes, profiles)
    payload = {
        "groups": groups,
        "meta": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "policy_hash": policy_hash(groups),
            "note": "六组偏好由大模型生成；失败的组保留备用规则并标明来源",
        },
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sources = sorted({group.get("source", "unknown") for group in groups.values()})
    print(f"已写入 {target} ，共 {len(groups)} 组，来源：{', '.join(sources)}，指纹：{payload['meta']['policy_hash']}")


if __name__ == "__main__":
    main()
