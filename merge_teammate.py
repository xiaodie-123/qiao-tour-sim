# -*- coding: utf-8 -*-
"""合并队友版本:采用他的官方数据与代码改进,保留我们的 app.py 防护。"""
import shutil
from pathlib import Path

his = Path("../预览-队友版/qiao-tour-sim")
ours = Path(".")

# 1) 采用他的文件
take = [
    "data/nodes.csv", "data/edges.csv", "data/scenarios.json", "data/policies.json",
    "data/source", "data/spots/qiao/nodes.csv", "data/spots/qiao/edges.csv",
    "contracts.py", "policy.py", "metrics.py", "simulator.py", "experiments.py",
    "build_policies.py", "checks/check_sim.py", "route_plan.py", "ui.py",
    "README.md", "节点.xlsx",
    "docs/ai_usage.md", "docs/experiment_report.md", "docs/intro_400.txt",
    "docs/node_table.md", "docs/presentation_script.md", "docs/project_scope.md",
    "docs/simulation_rules.md", "docs/乔家大院_节点与连接关系.svg",
    "demo/comparison_range.txt",
]
for rel in take:
    src = his / rel
    dst = ours / rel
    if not src.exists():
        print("  跳过(队友没有): %s" % rel)
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    print("  采用 %s" % rel)

# 2) app.py 保留我们的版本,补上他的"演示回放对不上就跳过"保护
app = (ours / "app.py").read_text(encoding="utf-8")
old = """    with open(DEMO, encoding="utf-8") as handle:
        loaded = json.load(handle)
        loaded["meta"]["spot"] = spot_name
        st.session_state["result"] = loaded"""
new = """    with open(DEMO, encoding="utf-8") as handle:
        loaded = json.load(handle)
    # 节点表已换成官方点位,旧回放文件可能对不上;对不上就不加载,避免地图报错。
    ids_now = {node["node_id"] for node in nodes}
    ids_demo = {nd["node_id"] for frame in loaded.get("frames", [])[:1] for nd in frame.get("nodes", [])}
    if ids_demo and ids_demo <= ids_now:
        loaded["meta"]["spot"] = spot_name
        st.session_state["result"] = loaded
    else:
        st.caption("demo/replay.json 是用旧节点表算的,与当前节点对不上,已跳过;跑一次模拟即可生成新的回放。")"""
if old in app:
    app = app.replace(old, new)
    (ours / "app.py").write_text(app, encoding="utf-8")
    print("  app.py:已补上队友的演示回放保护(我们的两处路线防护保留)")
else:
    print("  app.py:锚点未匹配,需手动检查")
