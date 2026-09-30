# -*- coding: utf-8 -*-
"""把项目源码复制进克隆的仓库,排除环境/构建/密钥/日志等。"""
import shutil
from pathlib import Path

src = Path("qiao-tour-sim")
dst = Path("_push_clone")

EXCLUDE_DIRS = {".venv", "build", "dist", "tmp_pdf", "edge_profile", "edge_profile2",
                "__pycache__", "teammate_proj", "screenshots"}
EXCLUDE_NAMES = {"gh_push_key", "gh_push_key.pub", "deploy_key", "deploy_key.pub",
                 "cloudflared.exe", "web_home.html", "ssh_test.txt", "token.txt",
                 "QiaoSim.spec", ".env"}
EXCLUDE_SUFFIX = (".log", ".spec")

# 清空克隆里除 .git 外的内容
for item in dst.iterdir():
    if item.name == ".git":
        continue
    if item.is_dir():
        shutil.rmtree(item, ignore_errors=True)
    else:
        item.unlink(missing_ok=True)

copied = 0
for path in sorted(src.rglob("*")):
    if path.is_dir():
        continue
    parts = path.relative_to(src).parts
    if any(part in EXCLUDE_DIRS for part in parts):
        continue
    name = path.name
    if name in EXCLUDE_NAMES or name.endswith(EXCLUDE_SUFFIX):
        continue
    if name.startswith("0c46cc66") or name.startswith("982e121c") or name.startswith("屏幕截图"):
        continue
    target = dst / Path(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    copied += 1

print("copied files:", copied)
