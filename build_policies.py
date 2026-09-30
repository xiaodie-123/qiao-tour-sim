"""生成 data/policies.json。没有密钥时写入备用规则，并标明来源。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts import load_nodes, load_profiles
from policy import build_policies


def main() -> None:
    parser = argparse.ArgumentParser(description="生成游客群体策略文件")
    parser.add_argument("--out", required=True, help="输出的 policies.json 路径")
    args = parser.parse_args()
    nodes = load_nodes()
    profiles = load_profiles()
    policies = build_policies(nodes, profiles)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(policies, ensure_ascii=False, indent=2), encoding="utf-8")
    sources = {item["source"] for item in policies["items"]}
    print(f"已写入 {target} ，共 {len(policies['items'])} 组，来源：{', '.join(sorted(sources))}，API 次数：{policies['api_calls']}")


if __name__ == "__main__":
    main()
