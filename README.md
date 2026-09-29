# 乔家大院游客仿真沙盘(qiao-tour-sim)

华北五省计算机应用大赛参赛作品(内部开发期 2026-09-29 — 10-03)。

一句话:网页沙盘模拟 100 名游客(亲子/老年/散客三类画像)在乔家大院约 10 个节点游览 120 分钟,第 30 分钟下雨,对比"第 20 分钟引导分流"与"不引导"的拥堵指标,提供轨迹回放、拥堵标记、结果对比与下载。

## 团队与分工

- 队长:画像/场景配置、实验对比、验收与汇报
- A:DeepSeek API 与游客策略
- B:网页、整合与公网部署
- C:仿真引擎与指标统计
- D:资料、文档、测试与视频

## 目录结构

| 路径 | 作用 | 负责人 |
|---|---|---|
| app.py / ui.py | 网页入口与绘图 | B |
| contracts.py | 共同数据结构 | C 起草,B 审核 |
| llm_client.py / policy.py / build_policies.py / smoke_api.py | API 调用与策略生成 | A |
| simulator.py / metrics.py / run_sim.py | 仿真引擎、指标、命令行 | C |
| checks/ | 正确性自检 | C |
| experiments.py | 多场景多种子实验 | 队长 |
| data/ | 地图、画像、场景、策略 | D 填表/队长配置/A 生成 |
| docs/ | 设计文档与报告 | D 汇总、队长审定 |
| prompts/ | 提示词 | A |
| demo/ | 可公开回放示例 | A/B/C 提供、D 整理 |
| outputs/ | 程序生成结果(不入库) | 程序 |

## 本地运行

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

网页入口 app.py 开发中;环境装好后可先执行 `.\.venv\Scripts\python.exe -m streamlit hello` 验证环境。

## 密钥

复制 `.env.example` 为 `.env` 并填入真实密钥;`.env` 与 `.streamlit/secrets.toml` 不提交仓库。密钥只由队长保管与发放。

## 数据声明

地图为节点/道路示意图,坐标 0—100,不冒充经纬度;容量、停留时间等无实测数据的字段为队长批准的演示假设并标注来源;画像为建模画像;演示参数不代表乔家大院真实客流。
