# -*- coding: utf-8 -*-
"""解包队友版本到预览目录,并列出他的关键数据。"""
import shutil
import zipfile
from pathlib import Path

src = Path("../融入优化(3).zip")
out = Path("../预览-队友版")
if out.exists():
    shutil.rmtree(out)
out.mkdir()
with zipfile.ZipFile(src) as z:
    z.extractall(out)
proj = out / "qiao-tour-sim"
print("解包完成:", proj)

# 节点表对比
ours = Path("data/nodes.csv").read_text(encoding="utf-8-sig").strip().splitlines()
his = (proj / "data/nodes.csv").read_text(encoding="utf-8-sig").strip().splitlines()
print()
print("=== 节点表对比 ===")
print("我们: %d 个节点(编号 N01—N42 人工示意)" % (len(ours) - 1))
print("队友: %d 个节点(官方地图点位编号)" % (len(his) - 1))
print()
print("队友的节点(前 20 个):")
import csv
import io
reader = csv.DictReader(io.StringIO("\n".join(his)))
for index, row in enumerate(reader):
    if index >= 20:
        break
    print("  %-10s %-8s %s" % (row["node_id"], row["kind"], row["name"]))
edges = (proj / "data/edges.csv").read_text(encoding="utf-8-sig").strip().splitlines()
print()
print("边数: 我们 %d → 队友 %d" % (len(Path("data/edges.csv").read_text(encoding="utf-8-sig").strip().splitlines()) - 1, len(edges) - 1))
print()
print("=== 他新增的原始数据文件 ===")
for path in sorted((proj / "data/source").iterdir()):
    print("  %8.1f KB  %s" % (path.stat().st_size / 1024, path.name))
