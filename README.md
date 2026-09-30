# 运筹三晋

给景区管理人员看的课程演示网页。它用三类游客的群体偏好，加上每个人自己的走路、排队和停留，回放 120 分钟里的拥堵，并比较下雨后开不开分流。

这不是实时客流，也不是乔家大院的实测预测。地图坐标、容量、停留和走路时间都是演示假设。

## 直接打开

安装过 Python 3.12 后，双击 `启动沙盘.bat`。浏览器打开后，左侧点「开始模拟」或「对比雨天与分流」。

终端里也可以：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

地址一般是 http://localhost:8501 。关掉网页不会停止程序，回到终端按 Ctrl+C。

## 页面上有什么

- 参数：场景、人数（20–300）、随机种子、下雨时刻、分流时刻和服从比例
- 模拟：点一次按钮才计算
- 回放：图上的播放、暂停、重置和时间轴只看已经算好的结果
- 拥堵：节点黄/红，右侧给出拥堵节点分钟
- 对比：同一随机种子下，「只下雨」和「下雨并分流」两条曲线
- 下载：JSON 和 CSV

打开页面时如果存在 `demo/replay.json`，会先显示这场历史回放。

## 不打开网页时怎么跑

```powershell
.\.venv\Scripts\python.exe build_policies.py --out data/policies.json
.\.venv\Scripts\python.exe run_sim.py --scenario rain_guide --seed 0 --out outputs/rain_guide.json
.\.venv\Scripts\python.exe experiments.py --seeds 0 1 2 3 4 --out outputs
.\.venv\Scripts\python.exe -m checks.check_sim
```

`experiments.py` 跑 3 个场景 × 5 个种子，共 15 次，运行中不调用大模型。

## 策略从哪来

平时仿真只读 `data/policies.json`。当前六组都是 DeepSeek 生成，来源标记为 `llm`，模型名 `deepseek-flash`，指纹 `c6ea1f159a372cb9`。仿真时不再请求接口。

队长要把真实密钥放在本机 `.env`（由 `.env.example` 复制，不要发到群里，不要放进压缩包），然后自己运行：

```powershell
.\.venv\Scripts\python.exe smoke_api.py
.\.venv\Scripts\python.exe build_policies.py --out data/policies.json
```

成功后页面上的来源会变成大模型生成，并显示接口返回的模型名。密钥只放 `.env` 或云平台 Secrets。

## 数据声明

节点名称参照乔家大院公开游览常识，用来做示意图。容量、遮蔽、停留和路时没有实测来源，表里写了「演示假设」。不要把这些数字写成景区官方数据。

本项目借鉴 RAPPIE 论文里「用角色代理表达一类人」的思路，没有复现该论文，也没有使用它的数据集、情感模型或图神经网络。论文：Liao 等，My Words Imply Your Opinion: Reader Agent-Based Propagation Enhancement for Personalized Implicit Emotion Analysis，ACL 2025。仿真公式和排队规则是本项目自己写的，见 `docs/simulation_rules.md`。