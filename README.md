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

平时仿真只读 `data/policies.json`。当前六组的行为参数（crowd_aversion、shelter_bonus、dwell_multiplier、summary）都是 2026-09-30 DeepSeek 生成，来源标记为 `llm`，模型名 `deepseek-flash`；换节点表后只有 `attraction_weights` 按类别重映射过，每组都带 `weights_note`。策略指纹不再固定在文件里，而是在跑仿真时按当前策略现场计算（结果 `meta.policy_hash`），页面上的“策略指纹”也是这一份。仿真时不再请求接口。

队长要把真实密钥放在本机 `.env`（由 `.env.example` 复制，不要发到群里，不要放进压缩包），然后自己运行：

```powershell
.\.venv\Scripts\python.exe smoke_api.py
.\.venv\Scripts\python.exe build_policies.py --out data/policies.json
```

成功后页面上的来源会变成大模型生成，并显示接口返回的模型名。密钥只放 `.env` 或云平台 Secrets。

## 数据声明

**节点名称与位置来自官方资料。** `data/nodes.csv` 由 `节点.xlsx`（WPS 节点表，工作表 qjdy_nodes）转换而来，节点 id、名称、来源网址逐条保留在 `data/source/`：

- `data/source/qjdy_nodes.csv`：官方节点表原始版（含地图点位编号、经纬度、来源网址、说明）
- `data/source/qjdy_edges.csv`：节点之间「包含 / 位于 / 连接 / 同指 / 又称 / 讲解顺序 / 邻近轨迹段 / 路线下一段」的关系与证据
- `data/source/qjdy_official_route.csv`：官方电子导览「全景游」轨迹的 25 个折点
- `data/source/qjdy_route_marker_proximity.csv`：每个点位到轨迹的最近折点、垂距与沿线里程

节点表里有经纬度、可做停留的点共 34 个（景点 17、院 5、堂院 2、服务点 10），进入仿真；只有名称、没有坐标的结构性条目（乔家大院景区、保元堂、宁守堂、乔家花园、甬道、第一院）与 25 个轨迹折点不进仿真路网，仍完整保留在 `data/source/` 和 `节点.xlsx` 里。

**坐标是示意图坐标。** 官方经纬度按本地平面近似换算后，两轴各自线性铺满 4—96，得到任务书要求的 0—100 示意图坐标，不冒充经纬度，也不保持真实比例。

**容量、接纳速率、停留和遮蔽没有实测来源**，`data/nodes.csv` 里按类别写死为演示假设，并在每条记录的 `assumption_note` 里标明「非实测」。不要把 `data/nodes.csv` 里的数字写成景区官方数据。

**道路用沿线顺序连接**：把 34 个可停留点按它们在「全景游」轨迹上的沿线里程排序，相邻两点连一条双向边，步行时间按沿线距离 ÷ 1.1 米/秒估算。这是演示假设，不是景区实测路网。

### 换了节点表之后要重跑的东西

节点 id 从 N01—N42 变成官方点位编号（如 `HALL_ZZT`、`G583801`、`S93299`），所以下面这些用旧节点算出来的文件**必须重新生成**，不能沿用：

- `demo/*.json`：旧节点表的回放。页面检测到对不上会跳过 `replay.json`，跑一次模拟即可覆盖。
- `outputs/`、`demo/comparison_range.txt`：旧节点表的实验数字。
- `docs/experiment_report.md` 里的表格：等重跑 `experiments.py` 后再更新。

六组策略（`data/policies.json`）的参数仍是 2026-09-30 大模型生成的那一份；吸引权重 `attraction_weights` 因为节点换了，按节点类别保留原数值分布后重映射到新节点 id，每组里都加了 `weights_note` 说明。

本项目借鉴 RAPPIE 论文里「用角色代理表达一类人」的思路，没有复现该论文，也没有使用它的数据集、情感模型或图神经网络。论文：Liao 等，My Words Imply Your Opinion: Reader Agent-Based Propagation Enhancement for Personalized Implicit Emotion Analysis，ACL 2025。仿真公式和排队规则是本项目自己写的，见 `docs/simulation_rules.md`。