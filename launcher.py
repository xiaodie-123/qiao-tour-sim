"""桌面启动器:内置启动 Streamlit 服务并自动打开浏览器。"""
import os

# 必须在导入 streamlit 之前设定,否则打包后会误判为开发模式
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

import sys
import threading
import time
import webbrowser
from pathlib import Path

from streamlit.testing.v1 import AppTest  # 顶层导入,确保 PyInstaller 打包该模块

# 以下为 app.py/ui.py/simulator.py 的运行时依赖:这些文件以数据文件方式打包,
# PyInstaller 不分析其 import,故在此顶层导入以强制打包
import networkx  # noqa
import numpy  # noqa
import openai  # noqa
import pandas  # noqa
import plotly  # noqa
import pyarrow  # noqa
from dotenv import load_dotenv  # noqa


def main():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    cred = Path.home() / ".streamlit" / "credentials.toml"
    try:
        cred.parent.mkdir(parents=True, exist_ok=True)
        if not cred.exists():
            cred.write_text('[general]\nemail = ""\n', encoding="utf-8")
    except Exception:
        pass
    port = int(os.environ.get("QIAOSIM_PORT", "8502"))
    from streamlit.web import cli as stcli

    app_path = os.path.join(base, "app.py")

    if os.environ.get("QIAOSIM_SELFTEST"):
        try:
            at = AppTest.from_file(app_path, default_timeout=180)
            at.run()
            errs = [str(e.value)[:200] for e in at.exception]
            if errs:
                print("SELFTEST-FAIL:", errs)
                sys.exit(2)
            print("SELFTEST-OK")
            sys.exit(0)
        except Exception as exc:
            print("SELFTEST-FAIL:", str(exc)[:300])
            sys.exit(2)

    print("运筹三晋 · 景区运营沙盘启动中,请稍候……")

    def open_browser():
        time.sleep(7)
        if not os.environ.get("QIAOSIM_NO_BROWSER"):
            webbrowser.open("http://localhost:%d" % port)

    threading.Thread(target=open_browser, daemon=True).start()

    sys.argv = ["streamlit", "run", app_path,
                "--server.headless", "true",
                "--server.port", str(port),
                "--browser.gatherUsageStats", "false",
                "--global.developmentMode", "false"]
    stcli.main()


if __name__ == "__main__":
    main()
