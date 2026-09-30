# -*- coding: utf-8 -*-
"""打包源代码 zip(排除环境、构建产物、密钥与日志)。"""
import zipfile
from pathlib import Path

BASE = Path(".")
OUT = Path("../3-源代码.zip")

EXCLUDE_DIRS = {".venv", "build", "dist", "tmp_pdf", "edge_profile", "edge_profile2", "__pycache__", "screenshots", "teammate_proj"}
EXCLUDE_NAMES = {"cloudflared.exe", "web_home.html", "QiaoSim.spec", "deploy_key", "deploy_key.pub",
                 "gh_push_key", "gh_push_key.pub", "merge_test.7z",
                 "0c46cc66928ef46a4ad57f0525ea8065.pdf", "982e121c9878b790cab02f033ee283b3.pdf",
                 "屏幕截图 2026-09-29 223145.png"}

if OUT.exists():
    OUT.unlink()

count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(BASE.rglob("*")):
        if p.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_NAMES or p.name.endswith(".log") or p.name.endswith(".spec"):
            continue
        z.write(p, "qiao-tour-sim/" + str(p.relative_to(BASE)).replace("\\", "/"))
        count += 1

print("entries:", count)
print("size MB:", round(OUT.stat().st_size / 1048576, 2))