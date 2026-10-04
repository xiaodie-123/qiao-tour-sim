# 节点表与路网来源

本文说明 `data/nodes.csv` 与 `data/edges.csv` 是怎么来的，以及换成官方节点表之后哪些旧结果作废。负责人：何梓泰（资料与节点表）；转换与校验在 2026-10-03 完成。

## 1. 原始资料

节点资料来自乔家大院官网与官方电子导览，逐条记网址，存成 WPS 表格 `节点.xlsx`（工作表 `qjdy_nodes`），字段：

```text
node_id,map_id,name,node_type,longitude,latitude,source_url,note
```

- `node_id`：稳定编号，如 `HALL_ZZT`（在中堂）、`G583801`（大门）、`S93299`（厕所）、`COURT_5`（第五院）、`R01`（轨迹折点）。
- `map_id`：官方电子导览的点位编号，没有对应点位时留空。
- `node_type`：景区 / 堂院 / 园林 / 路径 / 院 / 服务点 / 景点 / 轨迹折点。
- `longitude,latitude`：官方电子导览点位经纬度；只在名称有据、点位未单列时留空。
- `source_url`、`note`：来源网址与核对说明，写清是「官方明示」还是「推导」。

另外三张表：

| 文件 | 内容 |
|---|---|
| `data/source/qjdy_edges.csv` | 节点之间的关系：包含 / 位于 / 连接 / 同指 / 又名 / 讲解顺序 / 邻近轨迹段 / 路线下一段，带 `evidence_url`、`evidence_class`（官方明示 / 官方讲解推导 / 官方轨迹邻近推导）、`confidence`、`note` |
| `data/source/qjdy_official_route.csv` | 官方电子导览「全景游」轨迹的 25 个折点，按 `seq` 排序，带 `mark` |
| `data/source/qjdy_route_marker_proximity.csv` | 每个点位到轨迹的最近折点、直线距离、所属线段与沿线里程 |

这四张表都原样复制进 `data/source/`，和 `节点.xlsx` 一起作为可追溯的来源。

## 2. 谁进仿真路网

进路网的规则：**有经纬度、且 `node_type` 属于 堂院 / 院 / 园林 / 景点 / 服务点**。

- 共 34 个点：景点 17、院 5、堂院 2、服务点 10。
- 不进路网的：`SITE_QJDY`（乔家大院景区，是整体不是点位）、`PATH_YD`（甬道，是路径不是停留点）、25 个轨迹折点（R01—R25，只用来定顺序），以及没有点位坐标的结构性条目 `HALL_BYT`（保元堂）、`HALL_NST`（宁守堂）、`GARDEN_QJHY`（乔家花园）、`COURT_1`（第一院）。
- 那些没进路网的条目没有丢，仍在 `data/source/qjdy_nodes.csv` 与 `节点.xlsx` 里，`qjdy_edges.csv` 也保留了「四堂一园」「甬道连接六个大院」这些官方关系。

`kind` 按下面的规则从官方表映射到任务书要求的四种取值：

| 官方条目 | kind | 说明 |
|---|---|---|
| `G583801` 大门 | `entry` | 入园通过性节点 |
| `S93304 / S93305 / S93306` 出入口 | `exit` | 出入口是通过性节点 |
| 厕所 / 停车场 / 游客中心 | `service` | 服务点 |
| 堂院 / 院 / 景点 | `attraction` | 可停留参观 |

## 3. 坐标怎么来

官方经纬度先按本地平面近似换算成米（经度乘 cos(纬度)，纬度按 1°≈110540 米），再把两轴各自线性铺满 4—96，得到任务书要求的 0—100 示意图坐标。

两点说明：

- 这是**示意图坐标**，不冒充经纬度，也不保持真实比例。乔家大院东西向比南北向长很多，两轴各自铺满会把南北向拉开，目的是让点位在正方形画布上不挤在一起。
- 只用进路网的 34 个点定范围，轨迹折点不参与定范围（折点只用来排顺序，不画进图里）。

## 4. 容量、停留、遮蔽与道路：都是演示假设

有一说一：**官方资料只给了名称、点位、经纬度和相互关系，没有给容量、停留时间、遮蔽和路时。** 这些数字全部是演示假设，写在每一行的 `assumption_note` 里，页面上也标明「非实测」。

`data/nodes.csv` 用的假设值：

| 类别 | capacity | service_per_min | dwell_min | sheltered |
|---|---:|---:|---:|---:|
| 入口 / 出入口 | 10000 | 10000 | 0 | 1 |
| 堂院 | 16 | 4 | 20 | 1 |
| 院 | 12 | 3 | 16 | 1 |
| 露天大门 / 牌楼 | 20 | 6 | 4 | 0 |
| 景区标识点（乔家大院） | 20 | 5 | 10 | 0 |
| 展室 / 居室 | 8 | 2 | 12 | 1 |
| 厕所服务点 | 6 | 3 | 6 | 1 |
| 停车场 | 8 | 4 | 4 | 0 |
| 游客中心 | 12 | 4 | 15 | 1 |

道路：把 34 个点按它们在「全景游」轨迹上的**沿线里程**排序，相邻两点连一条双向边，`travel_min = round(沿线距离 ÷ 66)`（1.1 米/秒，至少 1 分钟）。`source_url` 用官方轨迹页，`assumption_note` 写明线段距离和步行速度假设。共 33 条边，整张图连通，入口与出口都能到达每个点。

## 5. 仿真路网（data/nodes.csv 实际内容）

字段与任务书 5.1 一致：`node_id,name,x,y,kind,capacity,service_per_min,dwell_min,sheltered,source_url,assumption_note`。

| 顺序 | node_id | 名称 | kind | x | y | 容量 | 接纳/分 | 停留/分 | 遮蔽 |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `G583802` | 景区牌楼 | attraction | 96.0 | 58.8 | 20 | 6 | 4 | 无 |
| 2 | `G583801` | 大门 | entry | 79.4 | 49.8 | 10000 | 10000 | 0 | 有 |
| 3 | `S93300` | 厕所(93300) | service | 78.9 | 57.2 | 6 | 3 | 6 | 有 |
| 4 | `S93308` | 游客中心 | service | 78.8 | 62.4 | 12 | 4 | 15 | 有 |
| 5 | `S93299` | 厕所(93299) | service | 78.4 | 79.7 | 6 | 3 | 6 | 有 |
| 6 | `S93301` | 厕所(93301) | service | 61.9 | 47.8 | 6 | 3 | 6 | 有 |
| 7 | `S93307` | 停车场 | service | 54.9 | 54.1 | 8 | 4 | 4 | 无 |
| 8 | `G583803` | 乔家大院 | attraction | 46.3 | 96.0 | 20 | 5 | 10 | 无 |
| 9 | `S93306` | 出入口(93306) | exit | 38.1 | 63.1 | 10000 | 10000 | 0 | 有 |
| 10 | `S93305` | 出入口(93305) | exit | 26.1 | 47.4 | 10000 | 10000 | 0 | 有 |
| 11 | `S93304` | 出入口(93304) | exit | 27.8 | 92.8 | 10000 | 10000 | 0 | 有 |
| 12 | `G583780` | 大厨房 | attraction | 22.1 | 73.0 | 8 | 2 | 12 | 有 |
| 13 | `G583782` | 乔景俨居室 | attraction | 19.8 | 72.6 | 8 | 2 | 12 | 有 |
| 14 | `G583781` | 乔致庸居室 | attraction | 19.0 | 83.7 | 8 | 2 | 12 | 有 |
| 15 | `G583783` | 乔景僖居室 | attraction | 18.3 | 72.7 | 8 | 2 | 12 | 有 |
| 16 | `G583785` | 乔映霞居室 | attraction | 15.9 | 72.2 | 8 | 2 | 12 | 有 |
| 17 | `G583784` | 静怡 | attraction | 14.6 | 84.1 | 8 | 2 | 12 | 有 |
| 18 | `G583786` | 乔映璜居室 | attraction | 14.1 | 71.8 | 8 | 2 | 12 | 有 |
| 19 | `G583791` | 乔映南居室 | attraction | 15.9 | 53.7 | 8 | 2 | 12 | 有 |
| 20 | `COURT_2` | 第二院 | attraction | 21.7 | 32.4 | 12 | 3 | 16 | 有 |
| 21 | `G583800` | 福德祠 | attraction | 20.1 | 46.3 | 8 | 2 | 12 | 有 |
| 22 | `HALL_ZZT` | 在中堂 | attraction | 15.5 | 43.1 | 16 | 4 | 20 | 有 |
| 23 | `G583798` | 家谱馆 | attraction | 19.8 | 23.7 | 8 | 2 | 12 | 有 |
| 24 | `COURT_5` | 第五院 | attraction | 15.8 | 35.2 | 12 | 3 | 16 | 有 |
| 25 | `G583797` | 教子有方展厅 | attraction | 21.2 | 7.1 | 8 | 2 | 12 | 有 |
| 26 | `COURT_6` | 第六院 | attraction | 11.3 | 32.6 | 12 | 3 | 16 | 有 |
| 27 | `COURT_4` | 第四院 | attraction | 11.7 | 27.3 | 12 | 3 | 16 | 有 |
| 28 | `G583792` | 议事厅 | attraction | 12.0 | 12.7 | 8 | 2 | 12 | 有 |
| 29 | `G583793` | 知足阁 | attraction | 13.6 | 15.0 | 8 | 2 | 12 | 有 |
| 30 | `G583795` | 九龙壁展馆 | attraction | 17.0 | 4.0 | 8 | 2 | 12 | 有 |
| 31 | `S93303` | 厕所(93303) | service | 8.8 | 11.1 | 6 | 3 | 6 | 有 |
| 32 | `HALL_DXT` | 德兴堂 | attraction | 7.6 | 36.0 | 16 | 4 | 20 | 有 |
| 33 | `COURT_3` | 第三院 | attraction | 4.0 | 40.0 | 12 | 3 | 16 | 有 |
| 34 | `S93302` | 厕所(93302) | service | 7.4 | 95.1 | 6 | 3 | 6 | 有 |

`data/spots/qiao/nodes.csv` 与 `data/spots/qiao/edges.csv` 是同一份数据，供页面上的景区切换使用，改的时候要一起改。

## 6. 换表之后必须重跑的东西

节点 id 从 N01—N42 换成官方点位编号（`HALL_ZZT`、`G583801`、`S93299`……），所以用旧节点算出来的东西不能再用：

1. `demo/*.json`（回放、对比示例）：页面会检查 `replay.json` 的节点 id 和当前节点表是否一致，对不上就不加载。跑一次模拟覆盖即可。
2. `outputs/`、`demo/comparison_range.txt`：旧实验数字，重跑 `experiments.py` 或 `exp_new.py` 覆盖。
3. `docs/experiment_report.md` 的表格：等重跑后按新数字改，不要沿用旧的。
4. `data/scenarios.json` 里的演示事件节点已按语义换成新 id：花园相关 → `COURT_6`（第六院，原名花园院），在中堂 → `HALL_ZZT`，戏台 → `G583792`（议事厅），民俗博物馆 → `G583798`（家谱馆）。
5. `data/policies.json`：六组策略的 `crowd_aversion / shelter_bonus / dwell_multiplier / summary` 仍是 2026-09-30 大模型生成的那一份；`attraction_weights` 因为节点换了，按节点类别（堂院·院 / 展室·居室 / 露天 / 服务点）保留原来的数值分布后重映射到新节点 id，每组都加了 `weights_note`。想彻底重来就重跑 `build_policies.py`。

## 7. 怎么核对

```powershell
.\.venv\Scripts\python.exe -m checks.check_sim
.\.venv\Scripts\python.exe run_sim.py --scenario normal --seed 0 --out outputs/normal.json
```

`checks/check_sim.py` 会检查人数、容量、队列先后、可重复性和整张乔家大院图。跑完页面上的点位数应该是 34 个。

## 8. 顺带修好的接口不一致（2026-10-03）

压缩包上一版里 `checks/check_sim.py`、`experiments.py`、`run_sim.py`、`build_policies.py` 用的是另一套接口，跟 `contracts.py` / `policy.py` / `metrics.py` / `simulator.py` 对不上，直接跑会报 `ImportError` 或 `KeyError`。这次统一到当前引擎：

| 补的东西 | 位置 | 作用 |
|---|---|---|
| `DataError` | `contracts.py` | 输入不合法时抛这个（它是 `ValueError` 的子类），自检能精确接住 |
| `load_world(spot_key="")` | `contracts.py` | 一次载入节点、边、画像、场景、策略；返回的策略就是 `run_simulation` 要的 `groups` |
| `improvement_rate(base, treatment)` | `metrics.py` | 4 位小数的改善率，给实验表用；基线 ≤ 0 返回 `None` |
| `format_rate(rate)` | `metrics.py` | `None` → 「不适用」，否则 `+22.2%` 这种文本 |
| `validate_policy_item(item, node_ids)` | `policy.py` | 校验一组策略的权重是否**正好**覆盖全部非出入口节点、数值是否越界 |

同时改了这几处：

- `simulator.run_simulation` 开头先调 `validate_config`，比例之和不是 1、字段缺失就直接抛 `DataError`，不再带着错数据算完。
- `simulator` 的 `meta` 增加了 `policy_hash`（`experiments.py` 和 `run_sim.py` 都要用）。
- `simulator` 每帧的游客记录增加 `queue_minutes`，自检用它检查「后来的人确实等过」。
- `checks/check_sim.py` 按当前帧结构重写：在途的人检查「落在线路上」，排队和游览的人检查「贴在节点上」。
- `build_policies.py` 原来调 `load_nodes()` 没给路径、又读不存在的 `policies["items"]`，一并修好。

跑法没变：

```powershell
.\.venv\Scripts\python.exe -m checks.check_sim
.\.venv\Scripts\python.exe experiments.py --seeds 0 1 2 3 4 --out outputs
```

## 9. 服务点权重的单独处理（2026-10-03）

第 6 节说过：`attraction_weights` 是拿旧地图的数值按类别重映射过来的。这里有一个例外——**服务点没有照搬**。

原因：旧地图（N01—N42）里只有 2 个服务点（茶社 N18、卫生间 N19），游客画像给它们的权重偏高（0.75 / 0.78），因为它们是「休息、喝水、上厕所」这类刚需要去的地方。新节点表里有 **7 个服务点**（5 个厕所、停车场、游客中心），如果照搬 0.75—0.78：

- 厕所会变成全园「最值得去」的点，因为它们的容量只有 6、又贴着入口；
- 页面「游客路线」推荐的顺序会变成「厕所 → 游客中心 → 厕所」；
- 厕所会成为拥堵最集中的点。

所以服务点改成按类型给一组偏低的演示权重：

| 服务点 | 亲子 | 老年 | 普通散客 |
|---|---:|---:|---:|
| 厕所 | 0.45 | 0.50 | 0.40 |
| 停车场 | 0.30 | 0.35 | 0.25 |
| 游客中心 | 0.55 | 0.60 | 0.50 |

这样服务点仍然会被去（尤其老年游客），但不会再压过主要景点。这一处的口径写在每组策略的 `weights_note` 里，改的时候要一起改。

**注意**：这是权重口径，不是仿真公式。游客怎么选点的公式仍然写在 `simulator.py`，见 `docs/simulation_rules.md`。
