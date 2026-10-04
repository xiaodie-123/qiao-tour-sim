"""绘图模块:地图回放、拥堵曲线、对比图、事件标记。"""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROFILE_COLORS = {"family": "#E9C46A", "senior": "#4CC9F0", "individual": "#F28482"}
PROFILE_NAMES = {"family": "亲子游客", "senior": "老年游客", "individual": "普通散客"}
ANGRY_COLOR = "#FFD6A5"
EVENT_COLORS = {"conflict": "#E76F51", "dispute": "#F4A261", "performance": "#2EC4B6",
                "weather": "#4CC9F0", "guidance": "#E9C46A"}
SHORT_NAMES = {
    "G583802": "牌楼", "G583801": "大门", "G583803": "乔家大院",
    "S93299": "厕所1", "S93300": "厕所2", "S93301": "厕所3",
    "S93302": "厕所4", "S93303": "厕所5", "S93304": "出入口A",
    "S93305": "出入口B", "S93306": "出入口C", "S93307": "停车场",
    "S93308": "游客中心", "HALL_ZZT": "在中堂", "HALL_DXT": "德兴堂",
    "COURT_2": "第二院", "COURT_3": "第三院", "COURT_4": "第四院",
    "COURT_5": "第五院", "COURT_6": "第六院", "G583780": "大厨房",
    "G583800": "福德祠", "G583798": "家谱馆", "G583797": "教子有方",
    "G583795": "九龙壁", "G583784": "静怡", "G583791": "乔映南",
    "G583786": "乔映璜", "G583785": "乔映霞", "G583783": "乔景僖",
    "G583782": "乔景俨", "G583781": "乔致庸", "G583792": "议事厅",
    "G583793": "知足阁",
}
EVENT_MARK = {"conflict": "冲突", "dispute": "纠纷", "performance": "演出"}


def load_color(load):
    if load is None:
        return "#8FCBB8"
    if load < 0.8:
        return "#2A9D8F"
    if load < 1.0:
        return "#E9C46A"
    return "#E76F51"


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at 20% 0%, #1a4d52 0%, #10282d 38%, #0b171b 100%);
            color: #e7f3ef;
        }
        section[data-testid="stSidebar"] {
            background: #0c2226;
            border-right: 1px solid rgba(140, 205, 185, .2);
            width: 318px !important;
            min-width: 318px !important;
            max-width: 318px !important;
            position: relative;
        }
        [data-testid="stSidebarContent"] {
            height: 100vh;
            display: flex !important;
            flex-direction: column;
        }
        [data-testid="stSidebarHeader"] {
            flex: 0 0 auto;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }
        [data-testid="stSidebarHeader"] button {
            position: absolute;
            top: 8px;
            right: 6px;
            z-index: 3;
        }
        .side-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 2px 28px 8px 0;
        }
        .side-mark {
            width: 36px;
            height: 36px;
            flex: 0 0 36px;
        }
        .side-title { margin: 0; color: #f4fbf8; font-size: 16px; font-weight: 700; line-height: 1.2; }
        .side-note { margin: 2px 0 0 0; color: #b7ddd2; font-size: 12px; line-height: 1.2; }
        [data-testid="stSidebarUserContent"] {
            flex: 1 1 auto !important;
            min-height: 0;
            height: auto !important;
            overflow: hidden !important;
            padding-bottom: 0 !important;
        }
        [data-testid="stSidebarUserContent"] > div {
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
            flex: 1;
            height: 100%;
            justify-content: space-between;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0.4rem;
            padding-bottom: 0.6rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        section[data-testid="stSidebar"] [data-testid="stSlider"] { padding-bottom: 0; }
        section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] { margin-top: -2px; padding-bottom: 0; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { margin-bottom: 6px; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin: 0; font-size: 15px; }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            margin: 2px 0 8px 0 !important;
            min-height: 20px;
        }
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label {
            font-size: 12px;
            line-height: 1.15;
        }
        section[data-testid="stSidebar"] [data-baseweb="input"],
        section[data-testid="stSidebar"] [data-baseweb="select"] > div { min-height: 32px; }
        section[data-testid="stSidebar"] [data-baseweb="input"] input { padding-top: 2px; padding-bottom: 2px; }
        section[data-testid="stSidebar"] .stButton > button,
        .stButton > button,
        [data-testid="stSelectbox"] div,
        [data-testid="stSlider"] [role="group"] > div > div,
        [data-testid="stSlider"] [role="slider"] {
            border-radius: 12px !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            min-height: 2.05rem;
            padding: 0.2rem 0.35rem;
            font-size: 14px;
        }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:last-child {
            margin-bottom: 28px;
        }
        .updatemenu-item-rect {
            rx: 12px;
            ry: 12px;
        }
        section[data-testid="stSidebar"] [data-testid="stCheckbox"] label p { font-size: 13px; white-space: nowrap; }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { margin-top: 0; }
        .policy-lead { font-size: 15px; color: #E7F6F1; line-height: 1.5; margin: 0 0 8px 0; }
        .policy-card {
            background: rgba(255,255,255,.06);
            border-radius: 12px;
            padding: 10px 14px 12px 14px;
            margin: 0 0 8px 0;
        }
        .policy-card b { display: block; font-size: 16px; color: #F4FBF8; }
        .policy-card p { font-size: 15px; color: #D7EFE6; line-height: 1.5; margin: 6px 0 0 0; }
        section[data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stExpandSidebarButton"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
        }
        section[data-testid="stMain"] .block-container {
            max-width: 100%;
            padding-top: 0.6rem;
            padding-bottom: 1.4rem;
            padding-left: 2.6rem;
            padding-right: 2.6rem;
        }
        .top-title { margin: 0; color: #F4FBF8; font-size: 20px; font-weight: 800; line-height: 1.2; }
        .top-note { margin: 2px 0 0 0; color: #B7DDD2; font-size: 12px; }
        .panel-label { margin: 0 0 8px 0; color: #F4FBF8; font-size: 16px; font-weight: 700; }
        .ops-head { margin: 0 0 8px 0; color: #F4FBF8; font-size: 16px; font-weight: 700; }
        .ops { border-radius: 12px; padding: 12px 14px; margin: 0 0 10px 0; color: #10221d; }
        .ops b { display: block; font-size: 15px; margin-bottom: 4px; }
        .ops p { margin: 0; font-size: 14px; line-height: 1.55; word-break: keep-all; }
        .ops-hot { background: #e7f6ef; }
        .ops-use { background: #b6e3d0; }
        .ops-state { background: #78c9aa; }
        .ops-advice { background: #3f9d84; color: #f4fbf8; }
        .advice-card {
            background: rgba(255,255,255,.07);
            border-radius: 12px;
            padding: 14px 18px 16px 18px;
            margin: 0 0 12px 0;
        }
        .advice-card b { display: block; font-size: 18px; color: #F4FBF8; margin-bottom: 8px; }
        .advice-card p { margin: 0 0 8px 0; font-size: 16px; color: #E7F6F1; line-height: 1.65; word-break: keep-all; }
        .advice-card p:last-child { margin-bottom: 0; }
        [data-testid="stRadio"] [role="radiogroup"] { gap: 8px; }
        [data-testid="stRadio"] label {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.1);
            border-radius: 999px;
            padding: 2px 10px 2px 4px;
        }
        header[data-testid="stHeader"], footer, .stDeployButton { display: none; }
        #MainMenu { visibility: hidden; }
        .hero {
            background: linear-gradient(90deg, #0f6b57 0%, #127a68 100%);
            border-radius: 12px;
            padding: 10px 16px 12px 16px;
            margin-bottom: 10px;
        }
        .hero h1 { margin: 0; font-size: 22px; color: white; line-height: 1.25; }
        .hero p { margin: 4px 0 0 0; color: #e5fff6; font-size: 13px; }
        .kicker { color: #d6ffe8; font-size: 12px; font-weight: 700; }
        .card {
            border-radius: 12px;
            padding: 10px 12px 8px 12px;
            color: #10221d;
            min-height: 88px;
        }
        .card b { display: block; font-size: 12px; white-space: nowrap; }
        .card .num { font-size: 22px; font-weight: 800; line-height: 1.2; margin: 2px 0; white-space: nowrap; }
        .card .note { font-size: 12px; line-height: 1.35; word-break: keep-all; }
        .event-table { width: 100%; border-collapse: collapse; font-size: 14px; color: #E7F6F1; }
        .event-table th { text-align: left; color: #B7DDD2; font-weight: 600; padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,.16); }
        .event-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,.08); vertical-align: top; line-height: 1.45; }
        .event-table td:last-child { width: 58%; }
        .card-rose, .card-leaf, .card-sky, .card-sand,
        .card-lilac, .card-clay, .card-mist, .card-bloom { background: #9fcec8; }
        .card-note { min-height: 0; margin-top: 10px; background: #efe4d4; }
        .card-row2 { margin-top: 12px; }
        .origin {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 12px;
            padding: 8px 12px;
            margin: 8px 0;
            color: #dff6ef;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():
    st.markdown(
        """
        <div class="side-brand">
            <svg class="side-mark" viewBox="0 0 36 36" aria-hidden="true">
                <rect width="36" height="36" rx="10" fill="#1A6B5C"/>
                <path d="M6 15.5 L18 7.5 L30 15.5" fill="none" stroke="#E7D3A1" stroke-width="1.8" stroke-linejoin="round"/>
                <path d="M9 15.5 H27" stroke="#E7D3A1" stroke-width="1.4"/>
                <path d="M11 16.2 V27 H25 V16.2" fill="none" stroke="#E7D3A1" stroke-width="1.6"/>
                <path d="M16.2 27 V20.2 H19.8 V27" fill="none" stroke="#E7D3A1" stroke-width="1.5"/>
            </svg>
            <div>
                <div class="top-title">运筹三晋 · 景区运营沙盘</div>
                <div class="top-note">先演后调:预判拥堵、比较分流、突发时推送替代路线</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ops_panel(metrics, rows, lines):
    hot = [row for row in rows if row["拥堵分钟"] > 0][:3]
    if hot:
        hot_body = "<br>".join(
            "%s · 拥堵 %d 分钟 · 峰值负荷 %.2f" % (row["节点"], row["拥堵分钟"], row["峰值负荷"])
            for row in hot)
    else:
        hot_body = "这次没有负荷大于 1 的点。"
    busy = sorted(rows, key=lambda row: -row["峰值负荷"])[:3]
    busy_body = "<br>".join(
        "%s · 峰值占用 %.0f%%" % (row["节点"], row["峰值负荷"] * 100) for row in busy)
    state_body = "离园 %d 人 · 仍在园 %d 人<br>不满游客 %d 人 · 平均等待 %.2f 分钟<br>冲突 %d 次 · 纠纷 %d 次" % (
        metrics["exited"], metrics["remaining"], metrics.get("angry_visitors", 0),
        metrics["mean_wait_min"], metrics.get("conflict_events", 0), metrics.get("dispute_events", 0))
    advice = "<br>".join(line.replace("&", "&amp;").replace("<", "&lt;") for line in lines[:4])
    st.markdown(
        "<div class='ops-head'>这场模拟的结果</div>"
        "<div class='ops ops-hot'><b>拥堵热点</b><p>%s</p></div>"
        "<div class='ops ops-use'><b>点位占用</b><p>%s</p><p>占用是峰值负荷，100%% 表示正好满员。</p></div>"
        "<div class='ops ops-state'><b>在园情况</b><p>%s</p></div>"
        "<div class='ops ops-advice'><b>可以怎么调</b><p>%s</p></div>"
        % (hot_body, busy_body, state_body, advice),
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="hero">
            <div class="kicker">本机软件 · 浏览器窗口</div>
            <h1>乔家大院游客仿真沙盘</h1>
            <p>模拟结果回放，不是实时客流，也不是实测预测。地图是示意图。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card(kind, title, value, note, extra=""):
    st.markdown(
        f"<div class='card {kind} {extra}'><b>{title}</b><div class='num'>{value}</div><div class='note'>{note}</div></div>",
        unsafe_allow_html=True,
    )


def _rate(base, other):
    if not base:
        return None
    return (base - other) / base * 100.0


def render_metrics(metrics, compare=None):
    last = ("card-bloom", "互动演出", str(metrics.get("performance_events", 0)), "演出场次")
    if compare is not None:
        rain, guide = compare
        rate = _rate(rain["total_congested_node_minutes"], guide["total_congested_node_minutes"])
        rate_text = "不适用" if rate is None else "%.1f%%" % rate
        last = (
            "card-bloom",
            "分流对拥堵",
            rate_text,
            "等待 %.2f→%.2f<br>最长一队 %d→%d" % (
                rain["mean_wait_min"], guide["mean_wait_min"],
                rain.get("longest_queue", rain["peak_queue"]),
                guide.get("longest_queue", guide["peak_queue"]),
            ),
        )
    rows = [
        [
            ("card-rose", "拥堵分钟", str(metrics["total_congested_node_minutes"]), "负荷大于 1 的累计"),
            ("card-leaf", "平均等待", "%.2f" % metrics["mean_wait_min"], "分钟"),
            ("card-sky", "离园 / 在园", "%d / %d" % (metrics["exited"], metrics["remaining"]), "观察结束时"),
            ("card-sand", "最长一队", str(metrics.get("longest_queue", 0)), "同时排队最多 %d 人" % metrics["peak_queue"]),
        ],
        [
            ("card-lilac", "不满游客", str(metrics.get("angry_visitors", 0)), "等太久就标出"),
            ("card-clay", "游客冲突", str(metrics.get("conflict_events", 0)), "拥堵持续后触发"),
            ("card-mist", "工作人员纠纷", str(metrics.get("dispute_events", 0)), "演示事件"),
            last,
        ],
    ]
    for index, row in enumerate(rows):
        columns = st.columns(4)
        extra = "card-row2" if index else ""
        for column, item in zip(columns, row):
            with column:
                _card(*item, extra)


def plot_map(frame, nodes, edges):
    node_by_id = {n["node_id"]: n for n in nodes}
    fig = go.Figure()
    for e in edges:
        a, b = node_by_id[e["from_id"]], node_by_id[e["to_id"]]
        fig.add_trace(go.Scatter(
            x=[a["x"], b["x"]], y=[a["y"], b["y"]], mode="lines",
            line=dict(color="#D5EFE4", width=2.2), hoverinfo="skip", showlegend=False))
    xs, ys, colors, sizes, texts, labels, symbols = [], [], [], [], [], [], []
    for nd in frame["nodes"]:
        n = node_by_id[nd["node_id"]]
        xs.append(n["x"]); ys.append(n["y"])
        colors.append(load_color(nd["load"]))
        symbols.append({"entry": "square", "exit": "square", "service": "diamond"}.get(n["kind"], "circle"))
        sizes.append(16 if n["kind"] in ("entry", "exit") else 22)
        short = SHORT_NAMES.get(n["node_id"]) or (n["name"] if len(n["name"]) <= 5 else n["name"][:4] + "…")
        labels.append(short)
        texts.append("<b>%s</b><br>%s<br>园内 %d / 容量 %d<br>排队 %d<br>负荷 %.2f" % (
            n["name"],
            "露天" if n["sheltered"] == 0 else "有遮蔽",
            nd["inside"], n["capacity"], nd["queue"], nd["load"]))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=labels, textposition="top center",
        textfont=dict(size=11, color="#FFF8E8", family="Microsoft YaHei"),
        marker=dict(size=sizes, color=colors, symbol=symbols, line=dict(color="#FFF6E4", width=1.2)),
        hovertext=texts, hoverinfo="text", name="节点", showlegend=False))
    fx, fy, ft = [], [], []
    for eff in frame.get("effects", []):
        n = node_by_id.get(eff["node_id"])
        if not n:
            continue
        fx.append(n["x"]); fy.append(n["y"] - 4.2)
        ft.append(EVENT_MARK.get(eff["type"], ""))
    if fx:
        fig.add_trace(go.Scatter(
            x=fx, y=fy, mode="text", text=ft,
            textfont=dict(size=12, color="#F6E7C1", family="Microsoft YaHei"),
            hoverinfo="skip", showlegend=False))
    # 游客(不满者深红)
    active = [v for v in frame["visitors"] if v["status"] in ("walking", "queue", "visiting")]
    angry = [v for v in active if v.get("mood") == "angry"]
    if angry:
        fig.add_trace(go.Scatter(
            x=[v["x"] for v in angry], y=[v["y"] for v in angry], mode="markers",
            marker=dict(size=8, color=ANGRY_COLOR, symbol="x", line=dict(color="#1A1208", width=0.6)),
            text=["%s 不满(等待%.0f分钟+)" % (v["id"], 20) for v in angry],
            hoverinfo="text", name="不满游客"))
    for pid in ("family", "senior", "individual"):
        sub = [v for v in active if v["profile_id"] == pid and v.get("mood") != "angry"]
        if not sub:
            continue
        fig.add_trace(go.Scatter(
            x=[v["x"] for v in sub], y=[v["y"] for v in sub], mode="markers",
            marker=dict(size=7, color=PROFILE_COLORS[pid], line=dict(color="#1A1208", width=0.4)),
            text=["%s %s %s" % (v["id"], PROFILE_NAMES[pid],
                                {"walking": "走路", "queue": "排队", "visiting": "游览"}[v["status"]])
                  for v in sub],
            hoverinfo="text", name=PROFILE_NAMES[pid], showlegend=True))
    weather_txt = "下雨" if frame.get("weather") == "rain" else "未下雨"
    guide_txt = "分流中" if frame.get("guidance_active") else "未分流"
    fig.update_layout(
        title=dict(text="第 %d 分钟 · %s · %s · 在园 %d 人" % (frame["minute"], weather_txt, guide_txt, len(active)),
                   font=dict(color="#F4FBF8", size=14, family="Microsoft YaHei"),
                   x=1, xanchor="right"),
        xaxis=dict(range=[-1, 101], visible=False, scaleanchor="y", fixedrange=True),
        yaxis=dict(range=[-1, 101], visible=False, fixedrange=True),
        height=640,
        margin=dict(l=8, r=8, t=72, b=8),
        plot_bgcolor="#123E38",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Microsoft YaHei", color="#E7F6F1"),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", font=dict(color="#E7F6F1", family="Microsoft YaHei", size=12)),
        shapes=[{
            "type": "rect", "layer": "below",
            "x0": 1, "y0": 1, "x1": 99, "y1": 99,
            "line": {"color": "#E7D3A1", "width": 2.4},
            "fillcolor": "#123E38",
        }],
    )
    return fig


def plot_congestion(frames, events=None):
    xs = [f["minute"] for f in frames]
    congested = [sum(1 for nd in f["nodes"] if nd["load"] > 1.0) for f in frames]
    total_queue = [sum(nd["queue"] for nd in f["nodes"]) for f in frames]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=xs, y=congested, mode="lines", name="拥堵节点数",
                             line=dict(color="#E76F51", width=2.5)), secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=total_queue, mode="lines", name="总排队人数",
                             line=dict(color="#4CC9F0", width=2.5)), secondary_y=True)
    labels = {"conflict": "冲突", "dispute": "纠纷", "performance": "演出", "weather": "下雨", "guidance": "引导"}
    for index, ev in enumerate(events or []):
        fig.add_vline(x=ev["minute"], line_dash="dash", line_width=1,
                      line_color=EVENT_COLORS.get(ev["type"], "#999999"))
        fig.add_annotation(
            x=ev["minute"], y=0, yref="paper",
            text=labels.get(ev["type"], ""),
            showarrow=False,
            yshift=14 + (index % 2) * 16,
            font=dict(color=EVENT_COLORS.get(ev["type"], "#E7F6F1"), size=12, family="Microsoft YaHei"),
        )
    fig.update_layout(
        title=dict(text="每分钟拥堵节点数和总排队人数", font=dict(color="#F4FBF8", size=15, family="Microsoft YaHei")),
        height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8, 32, 36, .72)",
        font=dict(color="#E7F6F1", family="Microsoft YaHei"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color="#E7F6F1")),
        margin=dict(l=36, r=36, t=64, b=48))
    fig.update_yaxes(title_text="", secondary_y=False, gridcolor="rgba(255,255,255,.08)", color="#D5EBE4")
    fig.update_yaxes(title_text="", secondary_y=True, gridcolor="rgba(255,255,255,.08)", color="#D5EBE4")
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", color="#D5EBE4")
    return fig


def plot_comparison(frames_a, frames_b):
    xs = [f["minute"] for f in frames_a]
    ca = [sum(1 for nd in f["nodes"] if nd["load"] > 1.0) for f in frames_a]
    cb = [sum(1 for nd in f["nodes"] if nd["load"] > 1.0) for f in frames_b]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ca, mode="lines", name="只下雨", line=dict(color="#4CC9F0", width=2.5)))
    fig.add_trace(go.Scatter(x=xs, y=cb, mode="lines", name="下雨并分流", line=dict(color="#F4A261", width=2.5)))
    fig.update_layout(
        title=dict(text="同一随机种子：只下雨 vs 下雨并分流", font=dict(color="#F4FBF8", size=15, family="Microsoft YaHei")),
        height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8, 32, 36, .72)",
        font=dict(color="#E7F6F1", family="Microsoft YaHei"),
        legend=dict(orientation="h", font=dict(color="#E7F6F1")),
        margin=dict(l=40, r=16, t=48, b=32),
        xaxis=dict(gridcolor="rgba(255,255,255,.08)", color="#D5EBE4"),
        yaxis=dict(gridcolor="rgba(255,255,255,.08)", color="#D5EBE4", rangemode="tozero"),
    )
    return fig


def _panel(fig, title, height, left=44, right=16, top=44, bottom=52):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#F4FBF8", size=15, family="Microsoft YaHei")),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8, 32, 36, .72)",
        font=dict(color="#E7F6F1", family="Microsoft YaHei"),
        legend=dict(orientation="h", yanchor="top", y=-0.22, font=dict(color="#E7F6F1"), traceorder="normal"),
        margin=dict(l=left, r=right, t=top, b=bottom),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", color="#D5EBE4")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)", color="#D5EBE4")
    return fig


def plot_activity(frames):
    """在园的人分成走路、排队、游览。"""
    xs = [f["minute"] for f in frames]
    walking, queue, visiting = [], [], []
    for frame in frames:
        counts = {"walking": 0, "queue": 0, "visiting": 0}
        for visitor in frame["visitors"]:
            if visitor["status"] in counts:
                counts[visitor["status"]] += 1
        walking.append(counts["walking"])
        queue.append(counts["queue"])
        visiting.append(counts["visiting"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=visiting, name="正在游览", stackgroup="one",
        line=dict(width=0.6, color="#2EC4B6"), fillcolor="rgba(46,196,182,.55)"))
    fig.add_trace(go.Scatter(
        x=xs, y=walking, name="正在走路", stackgroup="one",
        line=dict(width=0.6, color="#E9C46A"), fillcolor="rgba(233,196,106,.45)"))
    fig.add_trace(go.Scatter(
        x=xs, y=queue, name="正在排队", stackgroup="one",
        line=dict(width=0.6, color="#E76F51"), fillcolor="rgba(231,111,81,.55)"))
    return _panel(fig, "在园的人在做什么", 300)


def _shelter_counts(frames, nodes):
    flag = {n["node_id"]: int(n["sheltered"]) for n in nodes}
    indoor, outdoor = [], []
    for frame in frames:
        inside_n = outside_n = 0
        for nd in frame["nodes"]:
            people = nd["inside"] + nd["queue"]
            if flag.get(nd["node_id"], 1):
                inside_n += people
            else:
                outside_n += people
        indoor.append(inside_n)
        outdoor.append(outside_n)
    return indoor, outdoor


def plot_shelter(frames, nodes):
    """已经到达某个点的人，按该点有没有遮蔽分开。走路的人不在这张图里。"""
    xs = [f["minute"] for f in frames]
    indoor, outdoor = _shelter_counts(frames, nodes)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=indoor, mode="lines", name="有遮蔽", line=dict(color="#2EC4B6", width=2.5)))
    fig.add_trace(go.Scatter(x=xs, y=outdoor, mode="lines", name="露天", line=dict(color="#F4A261", width=2.5)))
    return _panel(fig, "到达各点的人：有遮蔽或露天", 300)


def shelter_note(frames, nodes, events):
    minute = next((e["minute"] for e in (events or []) if e.get("type") == "weather"), None)
    if not minute:
        return ""
    _, outdoor = _shelter_counts(frames, nodes)
    before = outdoor[max(0, minute - 10):minute]
    after = outdoor[minute:min(len(outdoor), minute + 10)]
    if not before or not after:
        return ""
    return "下雨前 10 分钟露天点平均 %.0f 人，下雨后 10 分钟平均 %.0f 人。" % (
        sum(before) / len(before), sum(after) / len(after))


def plot_hot_nodes(rows):
    hot = [row for row in rows if row["拥堵分钟"] > 0][:10]
    hot = list(reversed(hot))
    fig = go.Figure()
    if hot:
        fig.add_trace(go.Bar(
            y=[row["节点"] for row in hot],
            x=[row["拥堵分钟"] for row in hot],
            orientation="h",
            marker_color="#E76F51",
            hovertemplate="%{y}<br>拥堵 %{x} 分钟<extra></extra>",
            showlegend=False,
        ))
    else:
        fig.add_annotation(
            text="这次没有负荷大于 1 的分钟", showarrow=False,
            font=dict(color="#E7F6F1", size=14, family="Microsoft YaHei"))
    return _panel(fig, "拥堵分钟最多的点", 320, left=108, top=56, bottom=28)


def _stay_minutes(frames, nodes):
    pos = {}
    for node in nodes:
        if node["kind"] in ("entry", "exit"):
            continue
        pos[(round(float(node["x"]), 2), round(float(node["y"]), 2))] = node["node_id"]
    stay = {pid: {} for pid in PROFILE_NAMES}
    for frame in frames:
        for visitor in frame["visitors"]:
            if visitor.get("status") != "visiting":
                continue
            pid = visitor.get("profile_id")
            if pid not in stay:
                continue
            nid = visitor.get("node_id") or pos.get((round(float(visitor["x"]), 2), round(float(visitor["y"]), 2)))
            if not nid:
                continue
            stay[pid][nid] = stay[pid].get(nid, 0) + 1
    return stay


def plot_profile_stay(frames, nodes):
    """一个人在某个点参观一分钟，记 1。只数正在游览，排队和走路另算。"""
    stay = _stay_minutes(frames, nodes)
    totals = {}
    for bucket in stay.values():
        for nid, minutes in bucket.items():
            totals[nid] = totals.get(nid, 0) + minutes
    top = sorted(totals, key=totals.get, reverse=True)[:8]
    top = list(reversed(top))
    names = {n["node_id"]: n["name"] for n in nodes}
    fig = go.Figure()
    if top:
        for pid, color in PROFILE_COLORS.items():
            fig.add_trace(go.Bar(
                y=[names.get(nid, nid) for nid in top],
                x=[stay[pid].get(nid, 0) for nid in top],
                orientation="h",
                name={"family": "亲子", "senior": "老年", "individual": "散客"}[pid],
                marker_color=color,
            ))
        fig.update_layout(barmode="stack")
    else:
        fig.add_annotation(
            text="这次还没有人停下来参观", showarrow=False,
            font=dict(color="#E7F6F1", size=14, family="Microsoft YaHei"))
    return _panel(fig, "三类游客实际停在哪", 320, left=108, top=44, bottom=52)


def plot_node_focus(frames, nodes, node_id):
    names = {n["node_id"]: n["name"] for n in nodes}
    xs, inside, queue = [], [], []
    for frame in frames:
        xs.append(frame["minute"])
        found = next((nd for nd in frame["nodes"] if nd["node_id"] == node_id), None)
        inside.append(found["inside"] if found else 0)
        queue.append(found["queue"] if found else 0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=inside, mode="lines", name="园内", line=dict(color="#2EC4B6", width=2.5)))
    fig.add_trace(go.Scatter(x=xs, y=queue, mode="lines", name="排队", line=dict(color="#E76F51", width=2.5)))
    return _panel(fig, "%s：园内人数和排队" % names.get(node_id, node_id), 280)


def plot_guidance_shift(frames_rain, frames_guide, nodes):
    """正数表示分流后这个点的拥堵分钟更少。"""
    def congested(frames):
        out = {}
        for frame in frames:
            for nd in frame["nodes"]:
                if nd["load"] > 1:
                    out[nd["node_id"]] = out.get(nd["node_id"], 0) + 1
        return out

    rain, guide = congested(frames_rain), congested(frames_guide)
    names = {n["node_id"]: n["name"] for n in nodes}
    ids = [nid for nid in names if rain.get(nid, 0) != guide.get(nid, 0)]
    ids.sort(key=lambda nid: abs(rain.get(nid, 0) - guide.get(nid, 0)), reverse=True)
    ids = list(reversed(ids[:12]))
    delta = [rain.get(nid, 0) - guide.get(nid, 0) for nid in ids]
    fig = go.Figure()
    if ids:
        fig.add_trace(go.Bar(
            y=[names[nid] for nid in ids],
            x=delta,
            orientation="h",
            marker_color=["#2A9D8F" if value > 0 else "#E76F51" if value < 0 else "#8FCBB8" for value in delta],
            hovertemplate="%{y}<br>拥堵分钟之差 %{x}<extra></extra>",
            showlegend=False,
        ))
    else:
        fig.add_annotation(
            text="两边都没有拥堵分钟", showarrow=False,
            font=dict(color="#E7F6F1", size=14, family="Microsoft YaHei"))
    return _panel(fig, "各点拥堵分钟之差（只下雨 − 分流）", 360, left=108, top=44, bottom=52)


def node_table(frames, nodes):
    names = {n["node_id"]: n["name"] for n in nodes}
    stats = {n["node_id"]: {"拥堵分钟": 0, "峰值排队": 0, "峰值负荷": 0.0} for n in nodes}
    for frame in frames:
        for nd in frame["nodes"]:
            row = stats[nd["node_id"]]
            if nd["load"] > 1:
                row["拥堵分钟"] += 1
            row["峰值排队"] = max(row["峰值排队"], nd["queue"])
            row["峰值负荷"] = max(row["峰值负荷"], round(nd["load"], 2))
    rows = [{"节点": names[nid], **stats[nid]} for nid in stats]
    rows.sort(key=lambda item: (-item["拥堵分钟"], -item["峰值排队"], item["节点"]))
    return rows


def longest_queue(frames):
    best = 0
    for frame in frames:
        for nd in frame["nodes"]:
            best = max(best, nd["queue"])
    return best


def opening_minute(frames):
    best = frames[0]
    best_key = (-1, -1)
    for frame in frames:
        queues = [nd["queue"] for nd in frame["nodes"]]
        key = (max(queues) if queues else 0, sum(1 for nd in frame["nodes"] if nd["load"] > 1))
        if key > best_key:
            best_key = key
            best = frame
    return best["minute"]


def suggestions(metrics, meta, rows, compare=None):
    lines = []
    if compare is not None:
        rain, guide = compare
        rate = _rate(rain["total_congested_node_minutes"], guide["total_congested_node_minutes"])
        wait_rate = _rate(rain["mean_wait_min"], guide["mean_wait_min"])
        crowd = "只下雨时拥堵分钟为 0，改善率不适用。" if rate is None else "分流后拥堵分钟变化 %.1f%%。" % rate
        lines.append(
            crowd
            + "平均等待从 %.2f 变为 %.2f（改善率 %s）。" % (
                rain["mean_wait_min"], guide["mean_wait_min"],
                "不适用" if wait_rate is None else "%.1f%%" % wait_rate,
            )
            + "最长一队从 %d 人变为 %d 人。拥堵分钟下降，不代表最长的队伍一定变短。" % (
                rain.get("longest_queue", 0), guide.get("longest_queue", 0),
            )
        )
    hot = [row for row in rows if row["拥堵分钟"] > 0]
    if not hot:
        lines.append("这次没有节点出现负荷大于 1 的拥堵分钟。")
    else:
        names = "、".join("%s（%d 分钟）" % (row["节点"], row["拥堵分钟"]) for row in hot[:3])
        lines.append("拥堵分钟集中在：%s。优先把人引向更空的点，或提高这些点每分钟能接纳的人数。" % names)
    if metrics.get("conflict_events"):
        lines.append("出现 %d 次游客冲突。按这套演示规则，冲突后该点接纳会变慢。" % metrics["conflict_events"])
    if metrics.get("dispute_events"):
        lines.append("出现 %d 次与工作人员的纠纷。纠纷期间该点暂停接待。" % metrics["dispute_events"])
    if meta.get("weather_after") == "rain":
        lines.append("雨从设定分钟开始后，已经走在当前这段路上的人要走到路段尽头再改方向。")
    if meta.get("guidance_enabled"):
        lines.append("分流只在游客做新决定时生效，排队中途不会退出。")
    else:
        lines.append("本次地图没有开分流。对比按钮会用同一随机种子再算一场下雨并分流。")
    if metrics.get("remaining"):
        lines.append("观察结束时还有 %d 人在园，他们不算已经完成游览。" % metrics["remaining"])
    lines.append("以上只说明这套演示规则下的走线、排队和事件，不代表票价、消费或踩踏风险。")
    return lines


def suggestion_groups(metrics, meta, rows, compare=None, shelter_line="", nodes=None):
    """按类给出建议。句子都从这次模拟的指标来，不另造分数。"""
    groups = []
    skip = {n["name"] for n in (nodes or []) if n.get("kind") in ("entry", "exit")}
    hot = [row for row in rows if row["拥堵分钟"] > 0 and row["节点"] not in skip]
    calm = sorted(
        (row for row in rows if row["拥堵分钟"] == 0 and row["节点"] not in skip),
        key=lambda row: row["峰值负荷"])
    if not hot:
        crowd = ["这次没有节点出现负荷大于 1 的拥堵分钟。现有接纳速度应付得了这批人。"]
    else:
        crowd = []
        for row in hot[:4]:
            crowd.append("%s拥堵 %d 分钟，峰值排队 %d 人，峰值负荷 %.2f。" % (
                row["节点"], row["拥堵分钟"], row["峰值排队"], row["峰值负荷"]))
        if calm:
            crowd.append("负荷一直没有超过 1 的点里，较空的是%s。还没进队的人，可以优先引向这些点。" % (
                "、".join(row["节点"] for row in calm[:3])))
        crowd.append("已经排上队的人不会中途改去别的点。要缓解这几个点，得在他们做下一个选择时分流，或提高这些点每分钟能接纳的人数。")
    groups.append(("拥堵疏导", crowd))

    wait = [
        "平均等待 %.2f 分钟，最长一队 %d 人，全园同时排队最多 %d 人。" % (
            metrics["mean_wait_min"], metrics.get("longest_queue", 0), metrics["peak_queue"]),
    ]
    angry = metrics.get("angry_visitors", 0)
    if angry:
        wait.append("有 %d 人被标成不满。按演示规则，累计排队超过 20 分钟就会标出来。先处理最长的那一队。" % angry)
    else:
        wait.append("这次没有人累计排队超过 20 分钟，所以没有不满游客。")
    groups.append(("排队与不满", wait))

    guide = []
    if compare is not None:
        rain, guided = compare
        rate = _rate(rain["total_congested_node_minutes"], guided["total_congested_node_minutes"])
        wait_rate = _rate(rain["mean_wait_min"], guided["mean_wait_min"])
        if rate is None:
            guide.append("只下雨时拥堵分钟为 0，拥堵改善率不适用。")
        else:
            guide.append("同一随机种子下，分流后拥堵分钟变化 %.1f%%（%.0f 变为 %.0f）。正数是变少，负数是变多。" % (
                rate, rain["total_congested_node_minutes"], guided["total_congested_node_minutes"]))
        guide.append("平均等待从 %.2f 分钟变为 %.2f 分钟，改善率 %s。最长一队从 %d 人变为 %d 人。" % (
            rain["mean_wait_min"], guided["mean_wait_min"],
            "不适用" if wait_rate is None else "%.1f%%" % wait_rate,
            rain.get("longest_queue", 0), guided.get("longest_queue", 0)))
        guide.append("拥堵分钟下降，不代表最长的队伍一定变短。变差的种子也要留在结果里。")
    elif meta.get("guidance_enabled"):
        guide.append("本次开了分流。游客只有在选下一个点的时候才会听引导，已经在排队的人继续排完。")
        guide.append("要看分流是帮了忙还是添了堵，用左侧「对比雨天与分流」。它会用同一随机种子再算一场只下雨。")
    else:
        guide.append("本次没有开分流，游客完全按自己的偏好选点。")
        guide.append("点左侧「对比雨天与分流」，会用同一随机种子各算一场：只下雨，以及下雨并分流。")
    groups.append(("分流干预", guide))

    weather = []
    if shelter_line:
        weather.append(shelter_line)
        weather.append("下雨之后，有遮蔽的点更吃香。已经走在半路上的人要走到这段路尽头，才会按新的天气改方向。")
    elif meta.get("weather_after") == "rain":
        weather.append("这场设置了下雨。雨开始后，有遮蔽的点会更吸引人，露天的点会相对空一些。")
    else:
        weather.append("这场没有下雨。室内和露天的人数差，主要来自游客本来想去哪里，不是避雨。")
    groups.append(("天气与室内", weather))

    order = []
    conflicts = metrics.get("conflict_events", 0)
    disputes = metrics.get("dispute_events", 0)
    shows = metrics.get("performance_events", 0)
    if conflicts:
        order.append("出现 %d 次游客冲突。按演示规则，冲突后该点接纳速度会减半，队会更难消。" % conflicts)
    else:
        order.append("这次没有游客冲突。负荷连续超过阈值，才会按演示规则触发冲突。")
    if disputes:
        order.append("出现 %d 次与工作人员的纠纷。纠纷期间该点暂停接待。" % disputes)
    else:
        order.append("这次没有与工作人员的纠纷。")
    if shows:
        order.append("出现 %d 场互动演出。演出期间该点会多吸引人，接待也会快一些。" % shows)
    groups.append(("现场秩序", order))

    groups.append(("离园进度", [
        "观察结束时离园 %d 人，还有 %d 人在园。还在园里的人不算已经完成游览。" % (
            metrics["exited"], metrics["remaining"]),
        "人数、停留和天气都会改变离园速度。120 分钟结束时人还没走完，是这套规则下的正常结果。",
    ]))
    return groups


def _legend(only_profile=None):
    traces = []
    items = PROFILE_COLORS.items()
    if only_profile:
        items = [(only_profile, PROFILE_COLORS[only_profile])]
    for pid, color in items:
        traces.append(go.Scatter(x=[None], y=[None], mode="markers", name=PROFILE_NAMES[pid],
                                 marker=dict(color=color, size=9)))
    traces.append(go.Scatter(x=[None], y=[None], mode="markers", name="不满游客",
                             marker=dict(color=ANGRY_COLOR, size=9, symbol="x")))
    for name, color in (("负荷低", "#2A9D8F"), ("接近满", "#E9C46A"), ("已拥堵", "#E76F51")):
        traces.append(go.Scatter(x=[None], y=[None], mode="markers", name=name,
                                 marker=dict(color=color, size=11, symbol="circle",
                                             line=dict(color="#FFF6E4", width=1))))
    return traces


def _edges(edges, by_id):
    xs, ys = [], []
    for edge in edges:
        a, b = by_id[edge["from_id"]], by_id[edge["to_id"]]
        xs.extend([a["x"], b["x"], None])
        ys.extend([a["y"], b["y"], None])
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#D5EFE4", width=2.2),
                      hoverinfo="skip", showlegend=False)


def _nodes(frame, by_id):
    xs, ys, colors, sizes, labels, texts, symbols = [], [], [], [], [], [], []
    for nd in frame["nodes"]:
        n = by_id[nd["node_id"]]
        xs.append(n["x"])
        ys.append(n["y"])
        colors.append(load_color(nd["load"]))
        symbols.append({"entry": "square", "exit": "square", "service": "diamond"}.get(n["kind"], "circle"))
        sizes.append(13 if n["kind"] in ("entry", "exit") else 16)
        short = SHORT_NAMES.get(n["node_id"]) or (n["name"] if len(n["name"]) <= 5 else n["name"][:4] + "…")
        labels.append(short)
        texts.append("<b>%s</b><br>%s<br>园内 %d / 容量 %d<br>排队 %d<br>负荷 %.2f" % (
            n["name"], "露天" if n["sheltered"] == 0 else "有遮蔽",
            nd["inside"], n["capacity"], nd["queue"], nd["load"]))
    return go.Scatter(
        x=xs, y=ys, mode="markers+text", text=labels, textposition="top center",
        textfont=dict(size=10, color="#FFF8E8", family="Microsoft YaHei"),
        marker=dict(size=sizes, color=colors, symbol=symbols, line=dict(color="#FFF6E4", width=1.2)),
        hovertext=texts, hoverinfo="text", showlegend=False,
    )


def _effects(frame, by_id):
    xs, ys, texts = [], [], []
    for eff in frame.get("effects", []):
        n = by_id.get(eff["node_id"])
        if not n:
            continue
        xs.append(n["x"])
        ys.append(n["y"] - 4.2)
        texts.append(EVENT_MARK.get(eff["type"], ""))
    if not xs:
        xs, ys, texts = [None], [None], [""]
    return go.Scatter(x=xs, y=ys, mode="text", text=texts,
                      textfont=dict(size=12, color="#F6E7C1", family="Microsoft YaHei"),
                      hoverinfo="skip", showlegend=False)


def _people(frame, only_profile=None):
    xs, ys, colors, texts = [], [], [], []
    status_name = {"walking": "走路", "queue": "排队", "visiting": "游览"}
    for visitor in frame["visitors"]:
        if only_profile and visitor.get("profile_id") != only_profile:
            continue
        if visitor["status"] not in status_name or visitor.get("x") is None:
            continue
        xs.append(visitor["x"])
        ys.append(visitor["y"])
        angry = visitor.get("mood") == "angry"
        colors.append(ANGRY_COLOR if angry else PROFILE_COLORS.get(visitor["profile_id"], "#FFFFFF"))
        texts.append("%s %s %s%s" % (
            visitor["id"], PROFILE_NAMES.get(visitor["profile_id"], visitor["profile_id"]),
            status_name[visitor["status"]], " · 不满" if angry else "",
        ))
    if not xs:
        xs, ys, colors, texts = [None], [None], ["rgba(0,0,0,0)"], [""]
    return go.Scatter(x=xs, y=ys, mode="markers",
                      marker=dict(size=7, color=colors, line=dict(color="#1A1208", width=0.4)),
                      hovertext=texts, hoverinfo="text", showlegend=False)


def _title(frame, only_profile=None):
    active = [
        v for v in frame["visitors"]
        if v["status"] in ("walking", "queue", "visiting")
        and (not only_profile or v.get("profile_id") == only_profile)
    ]
    weather = "下雨" if frame.get("weather") == "rain" else "未下雨"
    guide = "分流中" if frame.get("guidance_active") else "未分流"
    if only_profile:
        return "第 %d 分钟 · %s · %s · %s %d 人" % (
            frame["minute"], weather, guide, PROFILE_NAMES[only_profile], len(active))
    return "第 %d 分钟 · %s · %s · 在园 %d 人" % (frame["minute"], weather, guide, len(active))


def _bounds(nodes):
    """按节点坐标算绘图范围(留 8% 边距),这样各景区的路网形态按真实比例显示。"""
    xs = [node["x"] for node in nodes]
    ys = [node["y"] for node in nodes]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad_x = max((x1 - x0) * 0.08, 2.0)
    pad_y = max((y1 - y0) * 0.08, 2.0)
    return x0 - pad_x, x1 + pad_x, y0 - pad_y, y1 + pad_y


def _auto_height(bounds, base=360.0, extra=280.0, low=380, high=660):
    """按纵横比自动定图高,避免长条形景区(如云冈石窟)上下留大片空白。"""
    x0, x1, y0, y1 = bounds
    span_x = max(x1 - x0, 1.0)
    span_y = max(y1 - y0, 1.0)
    return int(max(low, min(high, base + extra * (span_y / span_x))))


def _map_layout(title, height=None, bounds=None):
    if bounds is None:
        bounds = (-1.0, 101.0, -1.0, 101.0)
    x0, x1, y0, y1 = bounds
    if height is None:
        height = _auto_height(bounds)
    return dict(
        title=dict(text=title, font=dict(color="#F4FBF8", size=14, family="Microsoft YaHei"), x=1, xanchor="right"),
        xaxis=dict(range=[x0, x1], visible=False, scaleanchor="y", scaleratio=1, constrain="domain", fixedrange=True),
        yaxis=dict(range=[y0, y1], visible=False, constrain="domain", fixedrange=True),
        height=height,
        margin=dict(l=8, r=108, t=56, b=36),
        plot_bgcolor="#123E38",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Microsoft YaHei", color="#E7F6F1"),
        legend=dict(
            orientation="v", y=1, yanchor="top", x=1.02, xanchor="left",
            font=dict(color="#E7F6F1", family="Microsoft YaHei", size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
        shapes=[{
            "type": "rect", "layer": "below", "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "line": {"color": "#E7D3A1", "width": 2.4}, "fillcolor": "#123E38",
        }],
    )


def build_replay(frames, nodes, edges, only_profile=None, height=None):
    """播放、暂停、重置和时间轴都在浏览器里翻已算好的帧，不再重新模拟。"""
    by_id = {n["node_id"]: n for n in nodes}
    start = next(frame for frame in frames if frame["minute"] == opening_minute(frames))
    legend = _legend(only_profile)
    node_at = len(legend) + 1
    figure = go.Figure(
        data=[*legend, _edges(edges, by_id), _nodes(start, by_id), _effects(start, by_id), _people(start, only_profile)],
        frames=[
            go.Frame(
                data=[_nodes(frame, by_id), _effects(frame, by_id), _people(frame, only_profile)],
                name=str(frame["minute"]),
                traces=[node_at, node_at + 1, node_at + 2],
                layout=go.Layout(title=dict(
                    text=_title(frame, only_profile),
                    font=dict(color="#F4FBF8", size=14, family="Microsoft YaHei"),
                    x=1, xanchor="right")),
            )
            for frame in frames
        ],
    )
    figure.update_layout(
        **_map_layout(_title(start, only_profile), height, _bounds(nodes)),
        updatemenus=[{
            "type": "buttons", "direction": "right", "x": 0, "y": 1.09, "xanchor": "left", "showactive": False,
            "bgcolor": "#2EC4B6", "bordercolor": "#2EC4B6", "font": {"color": "#06241F", "family": "Microsoft YaHei"},
            "buttons": [
                {"label": "播放", "method": "animate", "args": [None, {"frame": {"duration": 280, "redraw": True}, "fromcurrent": True, "transition": {"duration": 0}}]},
                {"label": "暂停", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]},
                {"label": "重置", "method": "animate", "args": [["0"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}]},
            ],
        }],
        sliders=[{
            "active": start["minute"],
            "pad": {"t": 12},
            "len": 0.92,
            "x": 0.04,
            "currentvalue": {"visible": False},
            "font": {"color": "#D5EBE4", "size": 10},
            "steps": [
                {
                    "label": str(frame["minute"]) if frame["minute"] % 15 == 0 else "",
                    "method": "animate",
                    "args": [[str(frame["minute"])], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                }
                for frame in frames
            ],
        }],
    )
    return figure

def build_spot_overview(spots):
    """山西省 5A 景区分布示意(散点图,不绘制行政区划边界)。"""
    fig = go.Figure()
    for spot in spots:
        fig.add_trace(go.Scatter(
            x=[spot["x"]], y=[spot["y"]], mode="markers+text",
            marker=dict(size=30, color="#2EC4B6", opacity=0.92,
                        line=dict(color="#FFF6E4", width=2)),
            text=[spot["name"]], textposition="top center",
            textfont=dict(size=17, color="#FFF8E8", family="Microsoft YaHei"),
            hovertemplate="%s<br>%s<br>%s<extra></extra>" % (spot["name"], spot["city"], spot["tag"]),
            name=spot["name"]))
    fig.update_layout(
        title=dict(text="山西省 5A 景区分布示意(点击点位进入景区沙盘)", font=dict(color="#FFF8E8", size=18)),
        xaxis=dict(range=[15, 80], visible=False),
        yaxis=dict(range=[8, 104], visible=False),
        height=520, margin=dict(l=20, r=20, t=56, b=20),
        plot_bgcolor="#0E2B26", paper_bgcolor="#0E2B26",
        font=dict(color="#D7EFE6"),
        dragmode="select")
    return fig


def build_route_figure(nodes, edges, plan):
    """推荐游览路线图。"""
    by_id = {node["node_id"]: node for node in nodes}
    fig = go.Figure()
    for edge in edges:
        a, b = by_id[edge["from_id"]], by_id[edge["to_id"]]
        fig.add_trace(go.Scatter(x=[a["x"], b["x"]], y=[a["y"], b["y"]], mode="lines",
                                 line=dict(color="#3E6F63", width=1.6),
                                 hoverinfo="skip", showlegend=False))
    ids = [stop["node_id"] for stop in plan["stops"]]
    if ids:
        fig.add_trace(go.Scatter(
            x=[by_id[i]["x"] for i in ids], y=[by_id[i]["y"] for i in ids],
            mode="lines+markers+text",
            text=[str(index + 1) for index in range(len(ids))],
            textposition="middle right",
            textfont=dict(size=15, color="#FFE9A8", family="Microsoft YaHei"),
            line=dict(color="#F4A261", width=3.5, dash="dot"),
            marker=dict(size=18, color="#F4A261", line=dict(color="#FFF6E4", width=1.5)),
            name="推荐路线"))
    for node in nodes:
        fig.add_trace(go.Scatter(
            x=[node["x"]], y=[node["y"]], mode="markers+text",
            text=[node["name"]], textposition="top center",
            textfont=dict(size=11, color="#D7EFE6", family="Microsoft YaHei"),
            marker=dict(size=11, color="#2A9D8F" if node["kind"] != "service" else "#E9C46A"),
            hoverinfo="skip", showlegend=False))
    x0, x1, y0, y1 = _bounds(nodes)
    fig.update_layout(title=dict(text="推荐游览路线(按当前拥堵与画像偏好生成,演示)",
                                 font=dict(color="#FFF8E8", size=17)),
                      xaxis=dict(range=[x0, x1], visible=False, scaleanchor="y",
                                 scaleratio=1, constrain="domain", fixedrange=True),
                      yaxis=dict(range=[y0, y1], visible=False, constrain="domain", fixedrange=True),
                      height=_auto_height((x0, x1, y0, y1)),
                      margin=dict(l=20, r=20, t=50, b=20),
                      plot_bgcolor="#0E2B26", paper_bgcolor="#0E2B26")
    return fig
