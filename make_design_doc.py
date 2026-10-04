# -*- coding: utf-8 -*-
"""生成软件设计文档 PDF(华北五省赛方向一要求:缺创意文档则作品无效)。"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = r"C:\Windows\Fonts\simhei.ttf"
pdfmetrics.registerFont(TTFont("Hei", FONT))

S = {}
S["title"] = ParagraphStyle("title", fontName="Hei", fontSize=22, leading=30,
                            alignment=1, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
S["subtitle"] = ParagraphStyle("subtitle", fontName="Hei", fontSize=12, leading=18,
                               alignment=1, textColor=colors.HexColor("#555555"))
S["h1"] = ParagraphStyle("h1", fontName="Hei", fontSize=15, leading=22,
                         spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#16325c"))
S["h2"] = ParagraphStyle("h2", fontName="Hei", fontSize=12.5, leading=18,
                         spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#333333"))
S["body"] = ParagraphStyle("body", fontName="Hei", fontSize=10.5, leading=17,
                           spaceAfter=4, firstLineIndent=21)
S["cell"] = ParagraphStyle("cell", fontName="Hei", fontSize=9.5, leading=14)
S["cellb"] = ParagraphStyle("cellb", fontName="Hei", fontSize=9.5, leading=14)

def P(text, style="body"):
    return Paragraph(text, S[style])

def table(rows, widths, header=True):
    data = [[Paragraph(c, S["cellb" if (header and i == 0) else "cell"]) for c in row]
            for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t

story = []
story.append(Spacer(1, 30 * mm))
story.append(P("运筹三晋", "title"))
story.append(P("基于游客智能体的行为模拟与景区运营沙盘", "title"))
story.append(Spacer(1, 6 * mm))
story.append(P("软 件 设 计 文 档", "subtitle"))
story.append(P("参赛赛道:方向一(大模型与智能体应用)| 版本 v1.1 | 2026-09-30", "subtitle"))
story.append(Spacer(1, 4 * mm))
story.append(P("(团队名称、成员、指导教师在此填写)", "subtitle"))
story.append(PageBreak())

story.append(P("1. 需求分析", "h1"))
story.append(P("1.1 背景", "h2"))
story.append(P("节假日景区客流集中,拥堵、纠纷与应急管理多凭经验。山西文旅资源密集,景区管理者缺少\u201c先演后调\u201d的量化预演工具:在改路线、加引导之前,先知道人会堵在哪里、突发事件会如何传播。"))
story.append(P("1.2 目标", "h2"))
story.append(P("面向景区管理人员,提供覆盖山西省内五个 5A 景区(乔家大院、平遥古城、五台山、云冈石窟、壶口瀑布)的游客行为仿真与运营沙盘:推演 120 分钟园内客流,预判拥堵热点,对比分流引导效果,并在突发事件发生时向游客推送替代游览路线。"))
story.append(P("1.3 用户与典型场景", "h2"))
story.append(P("用户:景区运营与管理人员。典型场景:①客流预判——高峰时段哪些节点会拥堵;②分流对比——同一随机种子下\u201c只下雨\u201d与\u201c下雨并分流\u201d的指标差异;③突发事件处置——拥堵冲突、游客与工作人员纠纷、互动演出,以及面向游客的替代路线推送;④游客服务——按当前拥堵推荐游览顺序。"))
story.append(P("1.4 范围声明", "h2"))
story.append(P("首版为演示沙盘,不声称具备真实景区预测精度;地图为节点道路示意图,容量与事件规则为演示假设,均如实标注。"))

story.append(P("2. 设计思路", "h1"))
story.append(P("2.1 总体架构:群体LLM偏好 + 个体状态仿真", "h2"))
story.append(P("借鉴 RAPPIE 论文\u201c画像驱动智能体\u201d思路并做务实改造:由大模型(DeepSeek,deepseek-flash)一次性生成 3 类画像 × 晴/雨共 6 组游客群体偏好(景点吸引力、拥挤厌恶、遮雨偏好、停留倍数),再由确定性仿真引擎对每名游客逐分钟推进(未入园/行走/排队/游览/离园),个体差异由与游客编号绑定的固定随机值刻画。模拟与网页运行不调用 API,保证低成本与可复现;页面如实标注策略来源。"))
story.append(P("2.2 数据链", "h2"))
story.append(P("画像/场景配置 → LLM 群体偏好(policies.json) → 游客逐分钟状态(121 帧) → 排队与拥堵指标 → 分流对比与路线推送。任何指标均可追溯到配置、程序与运行记录。"))
story.append(P("2.3 多景区架构", "h2"))
story.append(P("每个景区一套 nodes.csv/edges.csv:乔家大院 34 个官方点位(点位编号、名称与来源取自公开导游地图资料,原始表见 data/source/qjdy_nodes.csv 与 qjdy_edges.csv),平遥古城 15 个、五台山 14 个、云冈石窟 14 个、壶口瀑布 12 个点位。后四者按各景区公开地图上的相对方位与经纬度换算成平面坐标绘制,因此路网形态各自不同——平遥为方形城郭与十字街巷、五台山为南北山谷两侧台地、云冈为东西向崖壁长条、壶口为南北向黄河岸线。首页为山西省 5A 景区分布示意(散点图,不绘制行政区划边界,不涉及疆域地图),点击点位或下拉选择即可进入对应景区沙盘。"))

story.append(P("3. 功能模块", "h1"))
story.append(table([
    ["模块", "说明", "实现文件"],
    ["景区选择", "山西省 5 个 5A 景区分布示意与切换", "app.py, ui.py"],
    ["参数设置", "人数、随机种子、天气与引导参数", "app.py"],
    ["模拟计算", "乔家大院 34 节点/121 帧;入园、行走、排队、游览、离园", "simulator.py"],
    ["轨迹回放", "地图 + 时间轴 + 播放暂停", "ui.py"],
    ["拥堵标记", "节点按拥堵度着色;指标卡片与拥堵排行", "ui.py, metrics.py"],
    ["分流对比", "同一随机种子对比雨天无引导与雨天分流", "app.py, metrics.py"],
    ["事件系统", "拥堵自动冲突、工作人员纠纷、互动演出", "simulator.py"],
    ["路线推送", "突发事件时为在途游客推送替代路线", "simulator.py"],
    ["游客路线规划", "按当前拥堵与画像偏好生成推荐游览顺序", "route_plan.py"],
    ["结果下载", "游客/节点逐分钟 CSV、完整 JSON", "ui.py"],
    ["桌面安装包", "PyInstaller 打包,双击即用,免装 Python", "launcher.py"],
], [95, 290, 120]))
story.append(P("4. 工具平台", "h1"))
story.append(table([
    ["类别", "名称与版本"],
    ["开发语言", "Python 3.10.11"],
    ["网页框架", "Streamlit 1.64.0"],
    ["可视化", "Plotly 7.1.0"],
    ["数据处理", "pandas 2.3.3、numpy 2.2.6"],
    ["图算法", "networkx 3.4.2(最短路径)"],
    ["大模型", "DeepSeek 官方 API,model=deepseek-flash(核验于 2026-09-28)"],
    ["打包工具", "PyInstaller 6.x"],
    ["运行环境", "Windows 10/11(网页亦可经 Streamlit Cloud 部署公网)"],
], [90, 420]))
story.append(P("4.1 形态说明", "h2"))
story.append(P("本作品面向景区管理人员,采用 PC 浏览器形态,可在电脑与大屏演示,符合方向一\u201c可在计算机上演示\u201d要求;非 Android/鸿蒙/iOS/小程序平台作品,故安装包按 PC 软件提供 Windows 版。网页部署公网后亦可经手机浏览器访问。"))

story.append(P("5. 关键算法与规则(团队原创设计)", "h1"))
story.append(P("5.1 目的地选择", "h2"))
story.append(P("score(i,j) = 画像吸引力 + 演出加成 − 拥挤厌恶×min(load,2) − 0.1×路程分钟 + 雨天遮雨偏好×遮蔽 − 0.5×已访问 + 个体扰动;load=(节点内人数+排队人数)/容量。"))
story.append(P("5.2 排队模型", "h2"))
story.append(P("容量约束,满员入队,FIFO 先来先服务;接待速率受事件影响(纠纷暂停、冲突减半、演出+2)。"))
story.append(P("5.3 分流引导", "h2"))
story.append(P("引导开启后,接受引导的游客(按服从比例确定)在重新选择目标时对排队更敏感——拥挤厌恶权重加倍,系统据此把客流导向距离合适、排队更短的景点;不接受引导的游客仍按原偏好走。"))
story.append(P("5.4 事件与路线推送(演示规则)", "h2"))
story.append(P("拥堵冲突:节点 load≥1.6 持续 3 分钟且冷却结束,自动触发,接待效率减半;纠纷/演出为可编排事件。事件激活时,系统为在途前往受影响节点的游客重算目的地,计为\u201c推送替代路线\u201d人次。"))
story.append(P("5.5 指标定义", "h2"))
story.append(P("拥堵分钟(load>1)、总拥堵节点分钟、平均累计等待(120 分钟窗口)、峰值排队、改善率=(基线−干预)/基线×100%,基线为 0 显示\u201c不适用\u201d,负值如实显示。"))

story.append(P("6. 实验与结果", "h1"))
story.append(P("以乔家大院 34 个官方点位、6 组 DeepSeek 生成偏好、200 人场景做 5 个种子的对照运行:雨天分流引导使总拥堵节点分钟平均下降 4.6(最大 15),5 个种子里 2 个下降 15%~21%,其余 3 个场景本身未出现明显排队,引导无可优化空间、也没有变差;平均累计等待同步下降(均值 0.08 分钟,最大 0.31 分钟)。平遥古城、五台山、云冈石窟、壶口瀑布四个景区各按新路网跑通验证,拥堵自动冲突与替代路线推送正常触发(单场为 3~50 名在途游客推送替代路线)。实验明细见 outputs/experiment_summary.csv 与 outputs/comparison.csv,全部由程序输出,固定种子可复现。"))

story.append(P("7. 操作步骤", "h1"))
story.append(P("方式一(安装包):解压\u201c运筹三晋-v1.0-win64.zip\u201d,双击 QiaoSim.exe,浏览器自动打开 http://localhost:8502;左侧选择景区与参数,点\u201c开始模拟\u201d。"))
story.append(P("方式二(源码):py -3.10 -m venv .venv;pip install -r requirements.txt;streamlit run app.py"))
story.append(P("软件无需用户名密码。回放拖动时间轴不重新计算;\u201c对比雨天与分流\u201d用同一随机种子;\u201c生成推荐路线\u201d按所选分钟拥堵给出推荐顺序。"))

story.append(P("8. 测试", "h1"))
story.append(table([
    ["测试项", "结果"],
    ["人数守恒、容量上限、队列 FIFO、同种子可复现", "通过"],
    ["非法节点/比例错误被拒绝", "通过"],
    ["三场景 100 人 121 帧", "通过"],
    ["五个景区地图均通过路网可达性校验并可运行", "通过"],
    ["事件系统(冲突触发、路线推送计数)生效", "通过"],
    ["网页全流程(选择景区/模拟/对比/路线规划)AppTest 零异常", "通过"],
    ["安装包 exe 内置自检(SELFTEST)与健康检查", "通过"],
], [300, 210]))
story.append(P("9. AI 使用说明(大赛要求明示)", "h1"))
story.append(P("9.1 使用的大模型:DeepSeek 官方 API(model=deepseek-flash),用于一次性生成 6 组游客群体偏好;未配置密钥时使用规则默认值并标注\u201c未调用 LLM\u201d。"))
story.append(P("9.2 AI 辅助编程:本项目代码主要借助 AI 编程助手(DeepSeek 系列模型,对话式与 Harness 环境)辅助生成,AI 生成代码占比约 90%;系统接口、数据结构、评分与事件规则、场景参数、实验设计与验收由团队人工设计与审定,文档结论经人工核验。"))
story.append(P("10. 原创声明与第三方库", "h1"))
story.append(P("原创部分:整体架构(群体偏好+个体仿真)、多景区沙盘组织、效用评分公式、事件与路线推送规则、指标定义、场景与参数设计、实验方案。参考 RAPPIE 论文思路并明确改造,未复现其原公式。"))
story.append(P("第三方开源库:streamlit、plotly、pandas、numpy、networkx、openai、python-dotenv、pyarrow、PyInstaller(仅打包),许可证以各项目官方为准。地图为自绘节点道路示意图与景区分布散点图,不涉及行政疆域地图。"))
story.append(P("11. 局限与展望", "h1"))
story.append(P("演示参数不代表实测;事件规则为演示级;各景区共享一套群体偏好结构。展望:逐景区生成偏好、接入真实客流与容量数据、满意度模型、公网持久化部署。"))

out = os.path.join(BASE, "docs", "软件设计文档.pdf")
os.makedirs(os.path.dirname(out), exist_ok=True)
doc = SimpleDocTemplate(out, pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm,
                        title="运筹三晋-软件设计文档")
doc.build(story)
print("PDF OK:", out)