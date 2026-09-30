# 乔家大院游客仿真沙盘：五人任务书

版本：2026-09-28。计划开发期：9月29日—10月3日。以下日期是团队内部目标，不代表学校公布的截止时间。

这是一份待团队实施的开发任务书，不是已经完成的软件。文中约定的项目文件、函数和命令入口需要各负责人创建。只有环境安装命令和文中的 smoke_api.py 示例可以在准备好环境与密钥后直接执行。本方案没有使用你们的密钥进行真实API测试，也没有替你们开通账号、充值或部署。

## 1. 全组统一决定

- 作品：乔家大院游客行为仿真与拥堵干预沙盘。
- 使用者：景区管理人员；首版展示设定条件下的模拟结果，不声称已具备真实景区预测精度。
- 软件形态：电脑浏览器网页。开发语言统一为Python，页面用Streamlit，地图和图表用Plotly。普通电脑运行，不训练或本地部署大模型。
- 首版：约10个节点、100名个体游客、亲子/老年/普通散客3类画像、120个模拟分钟、每步1分钟。
- 场景：正常游览；第30分钟开始下雨；同样的雨情下，从第20分钟启用分流引导。分钟数均为演示假设，页面可调。
- 优先完成：参数设置、模拟计算、轨迹回放、拥堵标记、分流对比、结果下载。
- 不纳入五天必做项：自由画地图、实时真实客流接入、消费预测、训练模型、移动App、多景区、精确踩踏风险预测。
- 地图背景不是核心依赖：先画节点和道路的示意图，真实地图素材授权、来源未核实前不用作正式背景。

## 2. 安装哪些软件

| 人员 | 必装/使用 | 用途 |
|---|---|---|
| 你、A、B、C | Python 3.12、VS Code、VS Code的Microsoft Python扩展、Edge/Chrome、GitHub Desktop | 编写、运行、检查代码；同步代码 |
| D | Edge/Chrome、WPS或Office、剪映 | 查资料，填表，写文档，剪辑视频；不要求D先学编程 |
| 你 | DeepSeek开放平台账号 | 保管项目API密钥，管理预算与账单 |
| B | GitHub账号、Streamlit Community Cloud账号 | 建立统一代码仓库，部署测试网页 |

官方下载入口：
- Python：https://www.python.org/downloads/
- VS Code：https://code.visualstudio.com/
- GitHub Desktop：https://desktop.github.com/
- DeepSeek开放平台：https://platform.deepseek.com/
- Streamlit部署平台：https://share.streamlit.io/

Windows作为本文命令示例。其他系统也可用，不要求重装系统；Mac/Linux改用python3创建环境和 .venv/bin/python 运行。D不必做下面的Python环境步骤。

### 2.1 所有开发成员统一环境

1. 安装Python 3.12，Windows安装时启用Python launcher及PATH选项。不要删除已有机器人开发环境。
2. 安装VS Code；在左侧Extensions中安装Microsoft发布的Python扩展。
3. B先建立GitHub私有仓库 `qiao-tour-sim`，邀请你、A、C加入。由B准备基础文件后，大家用GitHub Desktop克隆该仓库到没有空格、没有中文的路径，如 `D:\qiao-tour-sim`。没有D盘可放C盘。
4. VS Code选择“文件→打开文件夹”，打开项目根目录。
5. VS Code选择“终端→新建终端”，使用PowerShell。在根目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit hello
```

6. 浏览器出现Streamlit示例页面即表示环境基本正常。回到终端按Ctrl+C停止。
7. 按Ctrl+Shift+P，输入 `Python: Select Interpreter`，选择项目的 `.venv\Scripts\python.exe`。

这里直接调用虚拟环境里的python，不需要执行PowerShell激活脚本，也不需要修改执行策略。

B第一天先创建的 `requirements.txt` 内容：

```text
streamlit
plotly
pandas
networkx
openai
python-dotenv
```

B成功安装并跑通后，在自己的干净虚拟环境中执行下列命令锁定版本，并提交requirements.txt。A/C/你再次执行安装命令与B对齐。全组之后不要各自升级依赖。

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.txt
```

## 3. 指定调用哪个模型、怎么控制花费

采用DeepSeek官方API，配置如下（核对于2026-09-28）：

| 配置项 | 取值 |
|---|---|
| API基础地址 | `https://api.deepseek.com` |
| model参数 | `deepseek-flash` |
| 官方当前对应模型 | DeepSeek-V4.1-Flash |
| 调用方式 | Python的OpenAI兼容SDK，实际请求发送给DeepSeek |
| 思考模式 | 关闭，`extra_body={"thinking":{"type":"disabled"}}` |
| 输出方式 | `response_format={"type":"json_object"}` |
| 每次输出上限 | 正式画像策略调用先设 `max_tokens=1200` |
| 超时和重试 | `timeout=30`，SDK `max_retries=0`；A控制最多一次重试，避免多层重试 |

不使用聊天网页地址，也不依赖DeepSeek Harness的内部接口。`openai`在此是兼容客户端库，不代表必须购买另一家的API。

预算是支出上限，不是价格报价：先给API划20元额度；公网部署优先试免费平台；其余80元暂留给部署或必要追加。先做少量调用并查账单，不一次用完预算。充值金额以平台允许的档位为准。

密钥只放本地 `.env` 或云平台Secrets，不能出现在Python源码、GitHub、截图、录屏、提交压缩包中。你创建项目专用密钥，按需单独提供给A和B；D与仿真测试不需要密钥。开发结束或发生泄露时更换密钥。

项目 `.env.example`（可提交仓库）内容：

```dotenv
DEEPSEEK_API_KEY=replace_with_your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

使用时复制成 `.env`，填真实密钥。B的 `.gitignore` 至少包含：

```gitignore
.venv/
.env
.streamlit/secrets.toml
__pycache__/
outputs/
```

### 3.1 A第一项可直接操作的任务：连通API

在项目根目录新建 `smoke_api.py`，保存以下代码。先完成环境与.env配置再运行。

```python
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("DEEPSEEK_API_KEY")
if not key or key == "replace_with_your_key":
    raise SystemExit("请先在本地.env配置DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    timeout=30.0,
    max_retries=0,
)
response = client.chat.completions.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
    messages=[
        {"role": "system", "content": '只输出JSON对象，格式示例：{"status":"ok"}。'},
        {"role": "user", "content": '返回JSON对象{"status":"ok"}。'},
    ],
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    max_tokens=128,
)
text = response.choices[0].message.content
if response.choices[0].finish_reason == "length":
    raise RuntimeError("响应被截断，请检查max_tokens")
if not text:
    raise RuntimeError("API返回空内容")
data = json.loads(text)
if data.get("status") != "ok":
    raise RuntimeError("返回结构不符合约定")
print(json.dumps(data, ensure_ascii=False))
print("response_model:", response.model)
print("usage:", response.usage)
```

在VS Code终端运行：

```powershell
.\.venv\Scripts\python.exe smoke_api.py
```

验收：出现 `{"status":"ok"}`，能看见返回模型与token用量。401先查密钥；余额或计费问题查平台账户；超时先查网络及服务状态，不能无限重试。

该示例依据官方文档编写，未用你们的真实密钥进行在线验证。正式程序还必须验证业务字段，JSON可解析不代表业务值正确。

## 4. 统一项目结构与负责人

| 文件/目录 | 唯一主要负责人 | 作用 |
|---|---|---|
| `app.py`、`ui.py` | B | 网页入口、页面与地图绘制 |
| `requirements.txt`、`.gitignore`、`.env.example`、`README.md` | B | 环境、密钥模板、启动部署说明 |
| `contracts.py` | C起草，B审核 | 共同的数据结构；修改必须通知A/B/队长 |
| `llm_client.py` | A | DeepSeek调用、重试、用量记录 |
| `policy.py`、`prompts/visitor_policy.txt` | A | 生成、校验、载入游客群体偏好 |
| `smoke_api.py`、`build_policies.py` | A | API验证、生成正式策略文件 |
| `simulator.py`、`metrics.py`、`run_sim.py` | C | 模拟引擎、统计和命令行入口 |
| `checks/check_sim.py` | C | 人数、路网、队列等基本正确性检查 |
| `data/nodes.csv`、`data/edges.csv` | D填原始表，C审核转换 | 节点与路网，未核实内容不能当事实 |
| `data/profiles.json`、`data/scenarios.json` | 你 | 画像比例和场景配置；A/C帮助验证格式 |
| `data/policies.json` | A的程序生成 | 固定下来的大模型输出及来源标记 |
| `experiments.py` | 你 | 自动运行多种场景和随机种子，比较结果 |
| `docs/` | D汇总，你审定 | 设计文档、操作说明、来源、AI使用说明 |
| `outputs/` | 程序生成 | 模拟结果、实验数据、决策及运行记录 |
| `demo/` | B与A/C提供、D整理 | 可公开的已生成示例结果，用于无密钥回放 |

不把整份机器人工程复制进本项目。不下载或训练RAPPIE。借鉴论文画像驱动的智能体思路，引用论文并明确自己的改动。

## 5. 先约定接口，再各自写代码

### 5.1 D提供的地图数据

`nodes.csv` 字段：

```text
node_id,name,x,y,kind,capacity,service_per_min,dwell_min,sheltered,source_url,assumption_note
```

- `node_id`：N01、N02等稳定编号；名字修改不影响程序。
- `x,y`：0—100的示意图坐标，不冒充经纬度。
- `kind`：entry/attraction/service/exit。
- `capacity`：节点内可容纳人数，正整数；`service_per_min`：每分钟最多从队列接纳的人数。
- `dwell_min`：基础停留分钟数；`sheltered`：0或1。
- `source_url`与`assumption_note`：记录来源及假设。没有实际容量数据时，由你批准演示值，不能由D编成官方值。

`edges.csv` 字段：

```text
edge_id,from_id,to_id,travel_min,bidirectional,source_url,assumption_note
```

首版按节点排队建模，道路提供旅行时间，不做道路挤压或精确行人碰撞模拟。页面不宣称道路微观安全预测。所有关键节点必须连通出口。

D先交WPS表格也可以，C负责另存为UTF-8 CSV并验证。第一天可以先用3节点测试图推进代码；正式演示前替换成核对过的约10节点。

### 5.2 你提供的运行配置

`profiles.json` 顶层必须是列表，示例：

```json
[
  {"profile_id":"family","name":"亲子游客","description":"带孩子游览，偏好易于休息的节点，注意排队负担"},
  {"profile_id":"senior","name":"老年游客","description":"偏好较慢节奏和遮蔽休息条件，避免长时间等待"},
  {"profile_id":"individual","name":"普通散客","description":"关注展览内容和游览效率，可以根据拥挤情况调整路线"}
]
```

这些是建模画像，不能理解为所有对应年龄或家庭游客都会如此。比例仅写在场景配置中，避免两处冲突。

`scenarios.json` 中每个场景结构一致，例如：

```json
{
  "name": "rain_guide",
  "visitor_count": 100,
  "duration_min": 120,
  "seed": 0,
  "profile_ratios": {"family": 0.3, "senior": 0.3, "individual": 0.4},
  "arrival_window_min": 20,
  "weather_change_min": 30,
  "weather_after": "rain",
  "guidance_enabled": true,
  "guidance_start_min": 20,
  "guidance_acceptance": 0.6,
  "max_visits": 4,
  "visit_budget_min": 90
}
```

上述数值仅为初版建议的演示参数，可修改；不代表乔家大院真实客流构成。普通场景 `weather_change_min=null`、`weather_after="clear"`、`guidance_enabled=false`。雨天无干预场景与雨天分流场景仅在引导设置上不同。

`scenarios.json` 顶层以场景名为键，结构为 `{"normal": {...}, "rain": {...}, "rain_guide": {...}}`，每个值都包含完整配置，不使用省略号作为实际文件内容。

### 5.3 A输出什么：固定可审计的游客策略

为让五天方案可完成，首版采用“群体LLM偏好＋个体状态仿真”。A给每类画像生成晴天/雨天策略，共6组；模拟运行时不为每个游客的每一步请求API。

游客仍然分别拥有位置、已访问节点、停留时间、等待时间和随机差异；共享的是同一类游客的基础偏好。不要把这描述成100个全程独立调用大模型的智能体。

每组输出示例（`attraction_weights`必须覆盖输入中所有非出入口节点，下例仅示意两项）：

```json
{
  "profile_id": "family",
  "weather": "rain",
  "attraction_weights": {"N02": 0.7, "N03": 0.9},
  "crowd_aversion": 1.2,
  "shelter_bonus": 1.0,
  "dwell_multiplier": 0.8,
  "summary": "雨天亲子游客更倾向有遮蔽且较空闲的节点"
}
```

校验范围：吸引力0—1；拥挤厌恶0—2；遮雨偏好0—2；停留倍数0.5—1.5。模型只能使用给定节点ID，不能创造景区事实。

`policy.py`提供：

```python
def build_policies(nodes: list[dict], profiles: list[dict]) -> dict:
    """生成6组策略，含模型名、时间、prompt版本、usage及来源标记。"""

def load_policies(path: str) -> dict:
    """读取并校验已生成的策略，不调用API。"""
```

`build_policies.py`解析 `--out` 参数，读取data目录输入并调用build_policies。遇空内容/无效JSON/非法字段，至多重试一次；仍失败则写明 `source=rule_fallback` 并使用透明默认值。不能把备用规则标成LLM生成。

A保存每组输入摘要、输出、生成时间、请求与返回模型名、token统计；缓存标记原始LLM来源。一次完整生成最多12次请求（含重试），不允许循环自动重生成。页面平时只加载policies.json；“重新生成策略”作为本地开发命令，默认不暴露给公网访客。

### 5.4 C如何执行这些偏好

`simulator.py`提供：

```python
def run_simulation(nodes: list[dict], edges: list[dict],
                   profiles: list[dict], policies: dict,
                   config: dict) -> dict:
    """不依赖Streamlit；运行完整仿真并返回frames/events/metrics/meta。"""
```

建议选择规则，全部写在代码和文档中，不能暗中调整来保证效果好看：

```text
load(j) = (节点内人数 + 队列人数) / 节点容量
score(i,j) = 画像对j的吸引力
             - 拥挤厌恶 × min(load(j), 2)
             - 0.1 × 预计旅行分钟数
             + 雨天遮雨偏好 × 是否有遮蔽
             - 0.5 × 已访问标记
             + 个体固定偏好扰动
```

以上是演示用效用规则，不是论文原公式或经过真实数据校准的模型。

- 用NetworkX按travel_min求到候选目的地的最短路线，沿每条真实连接移动，不允许瞬移。
- 首版人数按设定比例分配，确保总数恰好100；入园时间在前20分钟内生成。
- 每步先处理离开与到达、再按FIFO入场、再进行新决策，统一同步更新，防止循环顺序造成不公平。
- 节点空间不足或接纳速率用完时进入队列；禁止人数超出capacity。
- 停留时间由dwell_min、画像倍数和固定随机差异计算，至少1分钟。
- 每位游客到达4个目标或达到90分钟个人游览预算后，以出口为目的地；仿真结束未离园者单独统计，不能算已完成游客。
- 入口与出口只承担入园/离园功能，不按展览节点停留；计数时区分未入园、园内与已离园。队列归属于目的地节点，可单独绘制在节点旁，不占节点内部capacity。
- 下雨只影响事件发生后的选择；正在路上的游客到达当前道路终点后再决策，不中途瞬移。
- 引导时在合法候选中推荐较空闲节点，以guidance_acceptance比例接受；其余游客照原规则走。建议决策时机限制为到达节点、结束停留或初次入园，首版不额外实现排队中途退出。
- 个体偏好、到达时间、服从倾向用由seed与visitor_id派生的固定随机值，减少场景分支改变随机抽样顺序导致的对比偏差。

`metrics.py`至少计算：

1. 每节点拥堵分钟数：该分钟load>1即计为拥堵；图示黄色阈值0.8、红色阈值1，均为演示阈值。
2. 总拥堵节点分钟：对各节点拥堵分钟数求和，不称为“全景区持续拥堵时长”。
3. 平均累计等待分钟：所有已入园游客累计等待总和 / 已入园人数；未完成者也包括在内，并标明120分钟观察窗口。
4. 峰值排队人数、已离园人数、观察结束仍在园人数。
5. 干预改善率：基线大于0时 `(基线-干预)/基线*100%`；基线等于0显示“不适用”；负值必须如实显示。

### 5.5 C返回给B的数据

```json
{
  "meta": {"seed": 0, "scenario": "rain_guide", "mode": "llm_policy_hybrid", "policy_hash": "..."},
  "frames": [
    {
      "minute": 0,
      "nodes": [{"node_id":"N01","inside":0,"queue":0,"load":0}],
      "visitors": [{"id":"v001","x":10,"y":20,"status":"not_arrived","profile_id":"family"}]
    }
  ],
  "events": [{"minute":30,"type":"weather","message":"开始下雨"}],
  "metrics": {"mean_wait_min":0,"congested_node_minutes":0,"peak_queue":0,"exited":0,"remaining":0}
}
```

上面是结构示例，不是模拟结果。正式frames需要0到120分钟共121帧；status限定为not_arrived/walking/queue/visiting/exited；每帧游客状态人数之和恒为visitor_count。UI隐藏not_arrived和exited游客。

## 6. 各人的具体任务卡

### 6.1 队长（你）：配置、实验、验收与汇报

使用：VS Code＋Python、WPS、浏览器。

按顺序完成：
1. 确认首版范围，不再临时新增功能；把任务书发给全组，让每个人确认自己负责的文件。
2. 申请项目API账号与密钥；记录开支，不发群聊明文密钥。
3. 写 `profiles.json`：family/senior/individual三个ID、中文描述、需求与行为偏好。写 `scenarios.json`：normal、rain、rain_guide三个场景。JSON字段请A/C检查。
4. 确认D提供的景区名称/道路证据；对缺失容量和停留时间批准演示假设并留记录。
5. 在AI帮助下写 `experiments.py`，调用C的run_simulation，依次跑三个场景及seed 0、1、2、3、4，共15次。全部加载同一policies.json；实验过程中不重新请求模型。
6. 输出 `outputs/experiment_summary.csv`，每行包含场景、seed、policy_hash、平均等待、拥堵节点分钟、峰值排队、离园与剩余人数；另输出 `outputs/comparison.csv`，按同seed配对比较rain与rain_guide。
7. 汇总五组配对差值的均值和范围；不只选效果最好的一组。效果不好时检查设计，禁止改结果数字。
8. 写 `docs/project_scope.md`、`docs/experiment_report.md`、`docs/presentation_script.md`。讲稿覆盖问题、架构、LLM作用、演示、对比、局限。
9. 审核D汇总的设计文档，确认每个图和数字能追溯到程序结果。

你需要编写的程序入口（与C模块接好后可运行）：

```powershell
.\.venv\Scripts\python.exe experiments.py --seeds 0 1 2 3 4 --out outputs
```

验收：15次运行有记录；固定输入能复现；能解释模型负责什么、程序负责什么；干预没改善时也如实呈现。

### 6.2 A：API与游客策略

使用：VS Code＋Python、DeepSeek开放平台。

按顺序完成：
1. 跑通第3节smoke_api.py。
2. 写llm_client.py，实现配置读取、一次调用、限次重试、usage记录，不打印密钥。
3. 写prompts/visitor_policy.txt；输入包含核对过的节点属性、一个画像、天气；要求返回第5.3节的JSON，强调演示假设与禁止杜撰节点。
4. 写policy.py与build_policies.py；生成6组策略并执行字段校验，保存data/policies.json。
5. 晴天/雨天、三类画像的输出即使差异不大也如实保留；不能手改LLM输出并仍标为模型生成。需要调整时修改提示词重新生成并记录版本。
6. 故意用空密钥、非法节点ID、超时模拟检查错误处理；证据写进docs/A_module.md。
7. 交给C：policies.json、函数说明、一个校验通过样例和一个错误样例。交给B：LLM模型名、策略来源和简短偏好说明的显示字段。

A负责实现并运行的命令：

```powershell
.\.venv\Scripts\python.exe smoke_api.py
.\.venv\Scripts\python.exe build_policies.py --out data/policies.json
```

验收：6组结构完整；非法ID被拒绝；断网后已有策略仍可载入；数据来源标记准确；用量可查。

### 6.3 B：网页、仓库与整合部署

使用：VS Code＋Python、GitHub Desktop、Edge/Chrome、Streamlit Community Cloud。

按顺序完成：
1. 创建私有仓库、环境文件、README、data/docs/checks等目录；建一个可运行的app.py，首日中午前让A/C/队长拿到项目。
2. 使用Streamlit写app.py，使用Plotly在ui.py画二维节点和连线。节点悬停显示名字、人数、容量、队列；颜色按load阈值；游客用散点按画像着色。
3. 侧栏放人数、随机种子、天气与发生时间、引导开关与开始时间、服从比例；人数首版限制20—300，默认100。
4. 点“运行模拟”后只调用一次C的run_simulation，结果保存在st.session_state。拖动时间轴、点击播放或更换图表不重新计算、不请求API。
5. 使用Plotly frames与播放/暂停控件回放预计算轨迹；配时间轴和重置。明确界面写“模拟结果回放”，不是实时真实客流。
6. 写“对比运行”按钮：相同seed及游客配置，生成rain与rain_guide两个结果；显示两条拥堵曲线及指标变化。缓存按所有配置＋地图版本＋policy_hash区分，防止读错结果。
7. 显示“群体LLM策略＋个体仿真”、策略生成时间、模型名、真实LLM/备用规则状态；给出CSV/JSON结果下载。
8. 将一次不含敏感信息的正式结果存demo/，供无密钥查看已保存结果；明确标“历史模拟回放”。
9. 记录启动方式，锁定依赖；检查Linux大小写路径，不写死D盘路径，使用相对项目路径。
10. 按第8节完成公网部署和外网访问测试。

启动方式：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

在Edge/Chrome打开终端给出的地址，通常为 `http://localhost:8501`。终端保持运行，Ctrl+C停止。这个地址只代表本机，不等于公网部署完成。

验收：改参数会改变仿真；播放暂停可用；重复拖动时间轴不调用模型；能看到正常/大雨/分流的可追溯结果；第二台电脑可访问公网版本。

### 6.4 C：仿真引擎与统计

使用：VS Code＋Python。无需API密钥；通过A保存的策略文件接入。

按顺序完成：
1. 与B确定contracts.py；先用3个节点和10名游客实现走路、停留、排队。
2. 写读取与校验代码，检查节点ID唯一、容量为正、边的端点存在、各节点能到出口、画像比例合计为1。
3. 实现第5.4节状态更新与选择规则；每步计算坐标，沿边插值，在进入下一条边前完成上一条。
4. 加入天气改变及分流引导；不调用Streamlit，不把网页逻辑塞进模拟引擎。
5. 写metrics.py，按明确公式计算指标；生成第5.5节的数据。
6. 写run_sim.py，使用argparse实现下列命令入口；读取scenarios.json中对应场景并允许seed覆盖。
7. 写checks/check_sim.py，用简单确定性场景检查人数守恒、容量上限、无非法跳跃、队列FIFO、相同seed和策略产生相同结果，以及基线为0的改善率处理。
8. 交给B一个完整sample_result.json，交给队长run_simulation调用例子；写docs/C_module.md解释规则和限制。

```powershell
.\.venv\Scripts\python.exe run_sim.py --scenario normal --seed 0 --out outputs/normal.json
.\.venv\Scripts\python.exe run_sim.py --scenario rain --seed 0 --out outputs/rain.json
.\.venv\Scripts\python.exe run_sim.py --scenario rain_guide --seed 0 --out outputs/rain_guide.json
.\.venv\Scripts\python.exe -m checks.check_sim
```

验收：脚本能独立运行；100名游客有完整121帧；正确性检查通过；无LLM网络依赖；异常输入给清楚错误。

### 6.5 D：资料、文档、测试与视频

使用：浏览器＋WPS/Office＋剪映。无需先学习Python。

按顺序完成：
1. 搜索乔家大院官网或官方导览发布渠道，收集能核实的导览图、节点名称和连接关系。不要只依据AI生成地图填表。
2. WPS建“节点表”“道路表”“来源表”三个工作表；按第5.1节字段填写，未知处写“待确认”。交C转换CSV，交队长核对内容。
3. 从比赛官网获取设计文档模板，能下载就按模板建文档；如拿不到记录障碍，由队长协调，先用需求/架构/模块/操作/测试/来源/AI使用/局限的内容框架推进。
4. 向A/B/C和队长收集各自模块说明与实验报告，汇总成设计文档，技术结论由作者审核。
5. 系统连通后按清单实际操作：正常运行；下雨；引导开关；固定seed重复；极小人数；切换参数后重跑；播放暂停；下载结果；无密钥回放；第二台电脑公网访问。每个问题记录操作步骤、预期、实际、截图。
6. 截取3张真实核心界面：沙盘与预警、雨天情境、干预对比。导出JPG/PNG，每张不超过1MB。
7. 用剪映录屏功能或系统录屏工具录制真实程序，剪为3—4分钟：问题20秒、系统配置30秒、正常/雨天演示60秒、干预对比60秒、技术与局限30秒。根据实际录制调整，最终必须≤5分钟。
8. 导出MP4，建议720p、约2Mbps视频码率；检查实际文件≤150MB，超出则降低码率重新导出。
9. 按公告准备≤400个汉字的简介；PDF设计文档、截图、视频由队长最终审定。软件包和完整源代码由B提供，不由D自行删文件。

验收：资料有来源，参数假设不冒充实测；视频与真实程序一致；没有密钥和私人聊天；文档能指导陌生人运行或访问系统。

## 7. 如何协作，不互相覆盖

- GitHub Desktop日常流程：Fetch/Pull取最新代码 → 切到自己的分支 → 修改本人文件 → 本地运行 → Commit说明改动 → Push → 发合并请求，由B整合。
- 分支建议：A `feature/policy`，B `feature/ui`，C `feature/simulation`，你 `feature/experiments`。D通过团队共享目录交材料，由B或你入库。
- B创建空的 `checks/__init__.py`，确保 `python -m checks.check_sim` 按项目包解析。
- 每次交付必须有：代码/数据、运行命令、运行结果、未解决问题。只有截图不算代码交付。
- 改函数名、输入字段、输出字段之前在群里通知；B、C确认后同步更新contracts.py和示例。禁止各自用同名不同含义的字段。
- 卡住30分钟仍没有进展，就发“执行命令＋完整报错＋相关文件”，及时求助；不要求连续在线，但不能到截止才报告无法完成。
- 给AI编程助手任务时，附本任务书第5节和自己的任务卡，并要求“只改本人负责文件，遵守接口，给出运行命令与自检结果，不将假数据标作真实结果，不写入密钥”。

## 8. 公网部署：B的明确操作路线

首选Streamlit Community Cloud免费平台。平台免费不代表国内每个网络都稳定；必须首日验证访问，不能到第五天才发现不通。

1. B在GitHub完成最简单的app.py、requirements.txt，推送仓库。
2. 打开https://share.streamlit.io/，登录并按平台流程授权所需仓库。
3. Create app → 选择仓库和分支，入口填 `app.py`。
4. Advanced settings中选Python 3.12，部署。
5. 先用不调用API的页面验证。最终版本预生成policies.json可以直接运行仿真，不必向云端放API密钥。
6. 如确实要在云端生成策略，密钥放平台Secrets，app.py只在服务器端读st.secrets后传给A的调用函数；不可把密钥发给浏览器。公网初版默认不提供策略重生成功能。
7. 你用手机流量、D用另一台电脑分别访问真实生成的https地址并操作，记录结果；让D检查无账号访客是否具备预期访问权限。
8. 配置、数据与代码更新后重新检查；演示前打开应用预热，保存本地完整版本和清楚标注的回放文件。

若9月29日20:00前平台无法满足访问要求：B记录问题并让队长决定是否从剩余预算租一个能公网访问的普通CPU服务器。不要自行购买GPU服务器，也不要把localhost或校园内网地址当作满足公网要求。具体供应商及价格须当时核实，本任务书不承诺80元一定能覆盖任意服务器方案。

## 9. 五天交付节点

| 截止时间 | 你 | A | B | C | D |
|---|---|---|---|---|---|
| 9/29 12:00 | 发范围和任务书，准备API账号 | 安装环境 | 仓库、基础文件、安装说明 | 草拟接口、3节点测试数据 | 开始官方资料收集 |
| 9/29 20:00 | 画像/场景初稿 | smoke_api成功；结构样例 | 可打开地图页；公网小页面访问检查 | 3节点10人移动/排队；共同接口确定 | 导览来源、节点候选表 |
| 9/30 20:00 | 冻结场景和假设；实验脚本初版 | 6组策略及校验、记录 | 接C样例显示地图/时间轴 | 完整路网、天气/引导、指标和CLI | 核实后的表格、模板和文档框架 |
| 10/1 20:00 | 验收三种场景 | 联调修复 | 完整网页与公网版本 | 与A/B联调，检查守恒 | 第一轮用户测试、操作截图 |
| 10/2 20:00 | 15次实验、报告和讲稿 | 修复错误、模块说明 | 修复、锁版本、打包初稿 | 修复、规则说明 | 文档/视频初稿、问题清单 |
| 10/3 18:00 | 最终验收与提交包审定 | 确認来源与用量 | 第二台电脑启动及部署复查、源代码包 | 实验与指标复查 | PDF、3图、简介、MP4齐全 |

10/3 18:00—22:00仅作缓冲，不新加功能。以上是交付时间，不要求所有人每天在线；有困难在该节点之前说明。

第一天的小样决定分工能否维持，不能仅凭获奖次数推定C会后端。如果C当天不能跑通，B与C共同缩小为3节点规则原型再推进；同时削减扩展功能。若B也无法完成网页小样，队长应当天向老师申请熟悉开发的同学短时指导，并重新评估五天可交范围，不能承诺靠最后一天补救。

## 10. 提交前必须核对

- 公告要求的设计PDF、完整源代码、简介、3张截图、MP4视频齐全；网页类如何填写“软件安装包”以校赛/报名系统实际字段为准，B准备可复现源码压缩包与README、公网地址，不自行断言免交。
- 软件源码包排除.env、secrets.toml、.venv、个人聊天和无关资料；保留requirements.txt、示例配置、已批准的数据与策略、启动方法。
- 写明使用DeepSeek API的模型名和版本/核验日期，AI编程工具及版本以实际界面为准；记录AI辅助代码比例的估计方法，不编造比例。
- 引用RAPPIE论文和使用的开源库；自己开发的仿真公式与实现不冒称论文复现。
- 标明地图来源、必要的使用权限与适用地图要求；演示参数不是实测数据；没有应用证明就不写已有部署应用。
- 可以完整解释一条数据链：画像/场景 → 模型偏好 → 游客状态变化 → 排队与拥堵指标 → 干预对比。

## 11. 官方技术依据

以下为核对API与部署步骤使用的官方页面，访问日期2026-09-28。模型服务会变动，提交文档应记录实际运行返回的模型名与当时页面说明。

1. DeepSeek模型与计费：https://api-docs.deepseek.com/quick_start/pricing/
2. DeepSeek更新日志：https://api-docs.deepseek.com/updates/
3. DeepSeek思考模式：https://api-docs.deepseek.com/guides/thinking_mode/
4. DeepSeek JSON输出：https://api-docs.deepseek.com/guides/json_mode/
5. Streamlit本地安装：https://docs.streamlit.io/get-started/installation/command-line
6. Streamlit部署：https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
7. Streamlit Secrets：https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

比赛材料要求来自用户提供的2026年比赛公告；项目方向来自用户提供的老师录音记录。当前尚无真实景区客流、容量测量或实际运行验证数据。
