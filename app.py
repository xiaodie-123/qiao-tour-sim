"""网页入口:场景预设、参数设置、模拟计算、轨迹回放、拥堵标记、事件系统、分流对比、结果下载。"""
import json
import os

import pandas as pd
import streamlit as st

from contracts import (load_edges, load_nodes, load_profiles, load_scenarios,
                        load_spots, spot_data_dir)
from metrics import improvement_pct
from policy import load_policies, policy_hash
from route_plan import plan_route
from simulator import run_simulation
import ui

BASE = os.path.dirname(os.path.abspath(__file__))


@st.cache_resource
def load_all(spot_key=""):
    base = spot_data_dir(spot_key)
    nodes = load_nodes(os.path.join(base, "nodes.csv"))
    edges = load_edges(os.path.join(base, "edges.csv"))
    profiles = load_profiles(os.path.join(BASE, "data", "profiles.json"))
    pol = load_policies(os.path.join(BASE, "data", "policies.json"))
    scenarios = load_scenarios(os.path.join(BASE, "data", "scenarios.json"))
    return nodes, edges, profiles, pol, scenarios


SCENARIO_NAME = {
    "normal": "正常游览",
    "rain": "雨天",
    "rain_guide": "雨天分流",
    "conflict_demo": "拥堵冲突",
    "dispute_demo": "工作人员纠纷",
    "festival_demo": "互动演出",
}

st.set_page_config(page_title="运筹三晋 · 景区运营沙盘", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()

spots = load_spots()


def make_config(count, seed, weather_min, weather_after, guide_on, guide_start, acceptance,
                max_visits, budget, conflict_on, conflict_threshold, events, name):
    change = int(weather_min) if weather_after == "rain" else None
    return {
        "name": name, "visitor_count": int(count), "duration_min": 120, "seed": int(seed),
        "profile_ratios": {"family": 0.3, "senior": 0.3, "individual": 0.4},
        "arrival_window_min": 20,
        "weather_change_min": change, "weather_after": weather_after,
        "guidance_enabled": bool(guide_on), "guidance_start_min": int(guide_start),
        "guidance_acceptance": float(acceptance),
        "max_visits": int(max_visits), "visit_budget_min": int(budget),
        "conflict_enabled": bool(conflict_on),
        "conflict_threshold": float(conflict_threshold),
        "events": events,
    }


def run_result(cfg):
    out = run_simulation(nodes, edges, profiles, pol["groups"], cfg)
    out["meta"]["weather_after"] = cfg.get("weather_after")
    out["meta"]["guidance_enabled"] = bool(cfg.get("guidance_enabled"))
    out["metrics"]["longest_queue"] = ui.longest_queue(out["frames"])
    return out


if st.session_state.get("_jump_sim"):
    st.session_state["board_tab"] = "游客模拟"
    st.session_state["_jump_sim"] = False
if "board_tab" not in st.session_state:
    st.session_state["board_tab"] = "游客模拟"

brand_col, spot_col, nav_col = st.columns([1.2, 0.8, 2.2], vertical_alignment="center")
with brand_col:
    ui.render_brand()
with spot_col:
    spot_name = st.selectbox("景区", ["全览"] + [spot["name"] for spot in spots],
                             key="spot_name", label_visibility="collapsed")
spot_key = next((spot["key"] for spot in spots if spot["name"] == spot_name), "")
if st.session_state.get("loaded_spot") != spot_key:
    st.session_state.loaded_spot = spot_key
    st.session_state.pop("result", None)
    st.session_state.pop("cmp", None)
    st.session_state.pop("plan", None)
if spot_name == "全览":
    st.caption("山西省 5A 景区分布示意(非行政区划地图)。点击地图上的景区点位,或使用上方下拉,进入对应景区的运营沙盘。")
    event = st.plotly_chart(ui.build_spot_overview(spots), width="stretch", key="overview_chart",
                            on_select="rerun", selection_mode="points",
                            config={"displaylogo": False, "displayModeBar": False})
    points = []
    try:
        points = (event or {}).get("selection", {}).get("points", [])
    except Exception:
        points = []
    if points:
        point = points[0]
        curve = int(point.get("curve_number", point.get("curveNumber", -1)))
        if 0 <= curve < len(spots):
            st.session_state["spot_name"] = spots[curve]["name"]
        else:
            px = float(point.get("x", 0))
            py = float(point.get("y", 0))
            st.session_state["spot_name"] = min(spots, key=lambda s: (s["x"] - px) ** 2 + (s["y"] - py) ** 2)["name"]
        st.rerun()
    cols = st.columns(len(spots))
    for index, spot in enumerate(spots):
        cols[index].markdown("**" + spot["name"] + "**\n\n" + spot["city"] + "\n\n" + spot["tag"])
    st.markdown("**系统定位**:面向景区管理人员,基于游客智能体行为模拟,对园内运营先演后调——预判拥堵、比较分流引导、突发事件时推送替代游览路线。")
    st.stop()

nodes, edges, profiles, pol, scenarios = load_all(spot_key)

with nav_col:
    tab = st.radio(
        "板块",
        ["场景设置", "游客模拟", "结果分析", "优化建议", "游客路线"],
        horizontal=True,
        label_visibility="collapsed",
        key="board_tab",
    )

left_col, mid_col, right_col = st.columns([1.12, 2.35, 0.76], gap="large")

with left_col:
    st.markdown("<div class='panel-label'>设置景区参数</div>", unsafe_allow_html=True)
    preset = st.selectbox(
        "场景",
        ["自定义"] + list(scenarios),
        format_func=lambda key: SCENARIO_NAME.get(key, key),
        key="preset",
    )
    applied = st.session_state.get("applied_preset")
    if applied != preset:
        st.session_state["applied_preset"] = preset
        st.session_state["preset_cfg"] = {} if preset == "自定义" else dict(scenarios[preset])
        if applied is not None:
            st.session_state["skip_demo"] = True
            st.session_state.pop("result", None)
            st.session_state.pop("cmp", None)
        st.rerun()
    pcfg = st.session_state.get("preset_cfg") or {}
    if not pcfg:
        weather_default = 30
    elif pcfg.get("weather_after") == "rain":
        weather_default = int(pcfg.get("weather_change_min") or 30)
    else:
        weather_default = 0
    left, right = st.columns(2)
    count = left.slider("人数", 20, 300, int(pcfg.get("visitor_count", 100)), 10, key="count_s_%s" % preset)
    seed = right.slider("种子", 0, 999, int(pcfg.get("seed", 0)), 1, key="seed_s_%s" % preset)
    left, right = st.columns(2)
    weather_min = left.slider("下雨", 0, 120, weather_default, 5, key="weather_s_%s" % preset)
    guide_start = right.slider("引导", 0, 120, int(pcfg.get("guidance_start_min", 20)), 5, key="guide_s_%s" % preset)
    left, right = st.columns(2)
    acceptance = left.slider("服从", 0.0, 1.0, float(pcfg.get("guidance_acceptance", 0.6)), 0.05, key="accept_s_%s" % preset)
    max_visits = right.slider("节点", 1, 8, int(pcfg.get("max_visits", 4)), key="visits_s_%s" % preset)
    budget = st.slider("预算（分）", 30, 120, int(pcfg.get("visit_budget_min", 90)), 5, key="budget_s_%s" % preset)
    left, right = st.columns(2)
    guide_on = left.checkbox("分流引导", value=bool(pcfg.get("guidance_enabled", True)), key="guide_on_%s" % preset)
    conflict_on = right.checkbox("拥堵冲突", value=bool(pcfg.get("conflict_enabled", True)), key="conflict_on_%s" % preset)
    note = "亲子 30% · 老年 30% · 散客 40%"
    if preset != "自定义" and (pcfg.get("weather_after") or "clear") != "rain":
        note = "本场景不下雨。亲子 30% · 老年 30% · 散客 40%"
    st.caption(note)
    btn_run = st.button("开始模拟", type="primary", width="stretch")
    btn_cmp = st.button("对比雨天与分流", width="stretch")

if btn_run or btn_cmp:
    evs = pcfg.get("events", []) if preset != "自定义" else []
    if preset == "自定义":
        weather_after = "rain"
        threshold = 1.6
    else:
        weather_after = pcfg.get("weather_after") or "clear"
        threshold = pcfg.get("conflict_threshold", 1.6)
    cfg = make_config(count, seed, weather_min, weather_after, guide_on, guide_start, acceptance,
                      max_visits, budget, conflict_on, threshold, evs,
                      preset if preset != "自定义" else "custom")
    cfg["spot"] = spot_name
    with st.spinner("正在按这套规则模拟，算完才能播放。"):
        if btn_run:
            st.session_state["result"] = run_result(cfg)
            st.session_state["cmp"] = None
        if btn_cmp:
            base_cfg = dict(cfg)
            base_cfg["name"] = "rain"
            base_cfg["guidance_enabled"] = False
            base_cfg["weather_after"] = "rain"
            base_cfg["weather_change_min"] = int(weather_min) or 30
            guide_cfg = dict(base_cfg)
            guide_cfg["name"] = "rain_guide"
            guide_cfg["guidance_enabled"] = True
            guide_cfg["guidance_start_min"] = int(guide_start)
            guide_cfg["guidance_acceptance"] = float(acceptance)
            rain_res = run_result(base_cfg)
            guide_res = run_result(guide_cfg)
            st.session_state["result"] = guide_res
            st.session_state["cmp"] = (rain_res, guide_res)
    st.session_state["_jump_sim"] = True
    st.rerun()

DEMO = os.path.join(BASE, "demo", "replay.json")
if ("result" not in st.session_state and not st.session_state.get("skip_demo")
        and os.path.isfile(DEMO) and spot_name == "乔家大院"):
    with open(DEMO, encoding="utf-8") as handle:
        loaded = json.load(handle)
    # 节点表已换成官方点位,旧回放文件可能对不上;对不上就不加载,避免地图报错。
    ids_now = {node["node_id"] for node in nodes}
    ids_demo = {nd["node_id"] for frame in loaded.get("frames", [])[:1] for nd in frame.get("nodes", [])}
    if ids_demo and ids_demo <= ids_now:
        loaded["meta"]["spot"] = spot_name
        st.session_state["result"] = loaded
    else:
        st.caption("demo/replay.json 是用旧节点表算的,与当前节点对不上,已跳过;跑一次模拟即可生成新的回放。")

qp = st.query_params
if "autorun" in qp and "result" not in st.session_state:
    scenario_key = str(qp.get("autorun", ""))
    if scenario_key in scenarios:
        auto_cfg = dict(scenarios[scenario_key])
        auto_cfg["seed"] = int(str(qp.get("seed", "0")))
        auto_cfg["spot"] = spot_name
        st.session_state["result"] = run_result(auto_cfg)
        st.session_state["cmp"] = None

res = st.session_state.get("result")
frames = res["frames"] if res else []
m = res["metrics"] if res else None
cmp = st.session_state.get("cmp")
rows = ui.node_table(frames, nodes) if res else []
names = {n["node_id"]: n["name"] for n in nodes}
shelter_line = ui.shelter_note(frames, nodes, res.get("events")) if res else ""
advice = ui.suggestions(
    m, res["meta"], rows,
    (cmp[0]["metrics"], cmp[1]["metrics"]) if cmp else None,
) if res else []
advice_groups = ui.suggestion_groups(
    m, res["meta"], rows,
    (cmp[0]["metrics"], cmp[1]["metrics"]) if cmp else None,
    shelter_line,
    nodes,
) if res else []

with mid_col:
    if not res:
        st.markdown('<div class="origin">在左侧选择场景，然后点「开始模拟」。打开后先停在排队最长的那一分钟。</div>', unsafe_allow_html=True)
    elif tab == "场景设置":
        st.markdown("<div class='panel-label'>场景与游客偏好</div>", unsafe_allow_html=True)
        st.caption("选场景后，左侧的人数、下雨和分流会换成这套预设。游客选下一个点时，用下面写好的偏好，模拟过程中不再重新生成。")
        meta = pol["meta"]
        groups = pol["groups"]
        llm_n = sum(1 for g in groups.values() if g.get("source") == "llm")
        st.caption("策略来源：%s。生成时间：%s。策略指纹：%s。仿真模式：%s。" % (
            "已写入的偏好" if llm_n else "规则默认值",
            meta.get("generated_at", "规则文件"),
            meta.get("policy_hash") or policy_hash(groups),
            "群体偏好加个体仿真" if llm_n else "规则偏好加个体仿真"))
        profile_label = {"family": "亲子", "senior": "老年", "individual": "散客"}
        weather_label = {"clear": "晴天", "rain": "雨天"}
        order = ["family|clear", "family|rain", "senior|clear", "senior|rain", "individual|clear", "individual|rain"]
        for key in order:
            group = groups.get(key)
            if not group:
                continue
            title = "%s · %s" % (
                profile_label.get(group["profile_id"], group["profile_id"]),
                weather_label.get(group["weather"], group["weather"]),
            )
            if group.get("source") != "llm":
                title += " · 规则默认值"
            top = sorted(group["attraction_weights"].items(), key=lambda item: item[1], reverse=True)[:3]
            liked = "、".join("%s %.2f" % (names.get(nid, nid), score) for nid, score in top)
            st.markdown(
                "<div class='policy-card'><b>%s</b><p>%s</p><p>最想去：%s</p><p>怕挤 %.2f · 遮蔽 %.2f · 停留 %.2f</p></div>" % (
                    title, group.get("summary", ""), liked,
                    group["crowd_aversion"], group["shelter_bonus"], group["dwell_multiplier"],
                ),
                unsafe_allow_html=True,
            )
    elif tab == "游客模拟":
        st.markdown("<div class='panel-label'>游客行为模拟</div>", unsafe_allow_html=True)
        st.caption("大点颜色是这个点的负荷。播放只翻已经算好的分钟。")
        who = st.radio("地图上显示哪一类", ["全部", "亲子", "老年", "散客"], horizontal=True, key="map_who")
        only_profile = {"亲子": "family", "老年": "senior", "散客": "individual"}.get(who)
        st.plotly_chart(
            ui.build_replay(frames, nodes, edges, only_profile, height=560),
            width="stretch", config={"displayModeBar": False})
    elif tab == "结果分析":
        st.markdown("<div class='panel-label'>结果分析</div>", unsafe_allow_html=True)
        ui.render_metrics(m, (cmp[0]["metrics"], cmp[1]["metrics"]) if cmp else None)
        rerouted = res["meta"].get("rerouted_visitors", 0)
        counts = res["meta"].get("event_counts", {})
        if rerouted:
            st.success("突发事件处置:已为 %d 名在途游客推送替代游览路线(冲突 %d 起 · 纠纷 %d 起 · 演出 %d 场)"
                       % (rerouted, counts.get("conflict", 0), counts.get("dispute", 0), counts.get("performance", 0)))
        st.plotly_chart(ui.plot_congestion(frames, res["events"]), width="stretch", config={"displayModeBar": False})
        chart_left, chart_right = st.columns(2)
        chart_left.plotly_chart(ui.plot_activity(frames), width="stretch", config={"displayModeBar": False})
        chart_right.plotly_chart(ui.plot_shelter(frames, nodes), width="stretch", config={"displayModeBar": False})
        rain_line = ui.shelter_note(frames, nodes, res.get("events"))
        if rain_line:
            st.caption(rain_line)
        chart_left, chart_right = st.columns(2)
        chart_left.plotly_chart(ui.plot_hot_nodes(rows), width="stretch", config={"displayModeBar": False})
        chart_right.plotly_chart(ui.plot_profile_stay(frames, nodes), width="stretch", config={"displayModeBar": False})
        st.caption("三类游客那张图按游览人分钟来数：一个人在这个点参观一分钟，记 1。")
        focus_names = [row["节点"] for row in rows if row["拥堵分钟"] > 0] or [row["节点"] for row in rows[:8]]
        picked = st.selectbox("看某一个点", focus_names, key="node_focus")
        id_of = {name: nid for nid, name in names.items()}
        st.plotly_chart(ui.plot_node_focus(frames, nodes, id_of[picked]), width="stretch", config={"displayModeBar": False})
        with st.expander("每个点的拥堵分钟、峰值排队和峰值负荷"):
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        if res["events"]:
            st.subheader("事件列表")
            type_names = {"weather": "天气", "guidance": "引导", "conflict": "游客冲突",
                          "dispute": "与工作人员纠纷", "performance": "互动演出"}
            body = "".join(
                "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    e["minute"], type_names.get(e["type"], e["type"]),
                    names.get(e["node_id"], "-") if e.get("node_id") else "-",
                    e["message"].replace("&", "&amp;").replace("<", "&lt;"),
                ) for e in res["events"])
            st.markdown(
                "<table class='event-table'><thead><tr><th>分钟</th><th>类型</th><th>节点</th><th>说明</th></tr></thead><tbody>%s</tbody></table>" % body,
                unsafe_allow_html=True)
        st.subheader("结果下载")
        vis_rows, node_rows = [], []
        for fr in frames:
            for v in fr["visitors"]:
                if v["status"] not in ("not_arrived", "exited"):
                    vis_rows.append({"minute": fr["minute"], "visitor_id": v["id"], "profile_id": v["profile_id"],
                                     "status": v["status"], "mood": v.get("mood", "normal"), "x": v["x"], "y": v["y"]})
            for nd in fr["nodes"]:
                node_rows.append({"minute": fr["minute"], "node_id": nd["node_id"], "inside": nd["inside"],
                                  "queue": nd["queue"], "load": nd["load"], "weather": fr["weather"]})
        metric_row = pd.DataFrame([{
            "拥堵分钟": m["total_congested_node_minutes"], "平均等待": m["mean_wait_min"],
            "同时排队最多": m["peak_queue"], "最长一队": m.get("longest_queue", ""),
            "离园": m["exited"], "仍在园": m["remaining"], "不满游客": m.get("angry_visitors", 0),
            "游客冲突": m.get("conflict_events", 0), "工作人员纠纷": m.get("dispute_events", 0),
        }])
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.download_button("下载指标 CSV", metric_row.to_csv(index=False).encode("utf-8-sig"), "metrics.csv", "text/csv")
        dc2.download_button("下载游客逐分钟 CSV", pd.DataFrame(vis_rows).to_csv(index=False).encode("utf-8-sig"), "visitors.csv", "text/csv")
        dc3.download_button("下载节点逐分钟 CSV", pd.DataFrame(node_rows).to_csv(index=False).encode("utf-8-sig"), "nodes.csv", "text/csv")
        dc4.download_button("下载完整结果 JSON", json.dumps(res, ensure_ascii=False, indent=1).encode("utf-8"), "result.json", "application/json")
    elif tab == "游客路线":
        st.markdown("<div class='panel-label'>游客路线规划</div>", unsafe_allow_html=True)
        st.caption("按所选分钟的拥堵情况和画像偏好,给出推荐游览顺序与预计耗时(演示估算)。")
        profile_label = {"family": "亲子", "senior": "老年", "individual": "散客"}
        c1, c2, c3 = st.columns(3)
        plan_who = c1.selectbox("游客画像", list(profile_label),
                                format_func=lambda key: profile_label[key], key="plan_who")
        plan_minute = c2.slider("按第几分钟规划", 0, max(0, len(frames) - 1), 0, 5, key="plan_minute")
        plan_weather = c3.selectbox("天气", ["clear", "rain"],
                                    format_func=lambda w: "晴天" if w == "clear" else "雨天", key="plan_weather")
        if st.button("生成推荐路线", key="plan_btn"):
            loads_now = {item["node_id"]: item["load"] for item in frames[min(plan_minute, len(frames) - 1)]["nodes"]}
            st.session_state["plan"] = plan_route(nodes, edges, pol["groups"], plan_who, plan_weather, loads_now)
        plan = st.session_state.get("plan")
        valid_ids = {node["node_id"] for node in nodes}
        if plan and not all(stop["node_id"] in valid_ids for stop in plan["stops"]):
            st.session_state.pop("plan", None)
            plan = None
            st.info("景区已切换,请重新点「生成推荐路线」。")
        if plan:
            st.plotly_chart(ui.build_route_figure(nodes, edges, plan), width="stretch",
                            config={"displayModeBar": False})
            st.markdown("**推荐路线**:%s" % plan["text"])
            st.caption("预计总耗时约 %s 分钟(步行 + 停留 + 排队,演示估算)。" % plan["total_min"])
            st.dataframe(pd.DataFrame([{"顺序": s["order"], "节点": s["name"], "步行(分)": s["travel_min"],
                                        "停留(分)": s["est_dwell_min"], "预计排队(分)": s["est_queue_min"],
                                        "当前负荷": s["load"]} for s in plan["stops"]]),
                         width="stretch", hide_index=True)
        else:
            st.info("选好画像后点「生成推荐路线」。突发事件时,系统也会自动为在途游客推送替代路线。")
    else:
        st.markdown("<div class='panel-label'>优化建议</div>", unsafe_allow_html=True)
        st.caption("下面按拥堵、排队、分流、天气、秩序和离园分开写。每条都对应当次模拟的数字。")
        for title, paragraphs in advice_groups:
            body = "".join("<p>%s</p>" % p.replace("&", "&amp;").replace("<", "&lt;") for p in paragraphs)
            st.markdown("<div class='advice-card'><b>%s</b>%s</div>" % (title, body), unsafe_allow_html=True)
        st.caption("这些建议只说明这套演示规则下的走线、排队和事件，不代表票价、消费或踩踏风险。")
        if cmp:
            res_rain, res_guide = cmp
            mr, mg = res_rain["metrics"], res_guide["metrics"]
            st.plotly_chart(ui.plot_comparison(res_rain["frames"], res_guide["frames"]), width="stretch", config={"displayModeBar": False})
            st.plotly_chart(ui.plot_guidance_shift(res_rain["frames"], res_guide["frames"], nodes), width="stretch", config={"displayModeBar": False})
            st.caption("绿色表示分流后这个点的拥堵分钟更少，红色表示更多。图上是有变化的点。")
            compare_rows = []
            for label, key in [("总拥堵节点分钟", "total_congested_node_minutes"),
                               ("平均累计等待(分钟)", "mean_wait_min"),
                               ("同时排队最多", "peak_queue"),
                               ("最长一队", "longest_queue"),
                               ("冲突事件数", "conflict_events"),
                               ("不满游客数", "angry_visitors")]:
                base, inter = mr.get(key, 0), mg.get(key, 0)
                imp = improvement_pct(base, inter)
                compare_rows.append({"指标": label, "无引导": base, "分流引导": inter,
                                     "改善率": "不适用(基线为0)" if imp is None else ("%+.1f%%" % imp)})
            st.table(pd.DataFrame(compare_rows))
            st.caption("改善率 = (无引导 − 分流引导) / 无引导 × 100%。负值表示分流后更差，如实显示。")
        else:
            st.caption("左侧点「对比雨天与分流」，会用同一随机种子再算一场只下雨、一场下雨并分流。")
        seed_path = os.path.join(BASE, "demo", "comparison_range.txt")
        if os.path.isfile(seed_path):
            with st.expander("五个随机种子：只下雨和雨天分流"):
                st.text(open(seed_path, encoding="utf-8").read())

with right_col:
    if res:
        ui.render_ops_panel(m, rows, advice)
    else:
        st.markdown("<div class='ops-head'>这场模拟的结果</div>", unsafe_allow_html=True)
        st.markdown('<div class="origin">开始模拟之后，这里显示拥堵热点、点位占用和可以怎么调。</div>', unsafe_allow_html=True)

st.caption("拥堵持续超过阈值会触发游客冲突，纠纷会让该点暂停接待，互动演出会吸引游客。这些都是演示规则。")
st.caption("节点容量、停留和遮蔽是演示假设。地图是示意图，不是实测客流，也不是未来预测。")
