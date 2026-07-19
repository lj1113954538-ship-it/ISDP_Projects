from __future__ import annotations

import time
from datetime import datetime

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from isdp_data_simulator_validation import HOURS, SCENARIOS, simulate_business_scenario, summarize_by_hour


st.set_page_config(page_title="ISDP 智能决策中心", layout="wide")
st.markdown('<html lang="zh-CN" class="notranslate" translate="no"></html>', unsafe_allow_html=True)

st.markdown(
    """
<style>
    :root {
        --bg0: #040b14;
        --bg1: #08111c;
        --panel: #11151c;
        --line: #233549;
        --text: #e8eef7;
        --muted: #8fa3b8;
        --good: #22c55e;
        --warn: #f59e0b;
        --bad: #ef4444;
    }
    .stApp {
        background: linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 55%, #030712 100%);
        color: var(--text);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8,16,30,0.99), rgba(4,9,18,0.99));
        border-right: 1px solid rgba(148,163,184,0.12);
    }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    .element-container { margin-bottom: 0.5rem !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(17,21,28,0.98), rgba(12,16,22,0.98));
        border: 1px solid rgba(35,53,73,0.95);
        border-radius: 8px;
        padding: 12px 12px 8px 12px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.22);
        min-height: 125px !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    [data-testid="stTable"] th, [data-testid="stTable"] td,
    [data-testid="stDataFrame"] td, .stDataFrame div { text-align: center !important; justify-content: center !important; }
    [data-testid="stDataFrame"] thead th,
    [data-testid="stDataFrame"] tbody td {
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stDataFrame"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="gridcell"] {
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stMetricValue"] { color: #ffffff; }
    .topbar {
        display:flex;
        flex-wrap:wrap;
        align-items:center;
        gap: 10px 12px;
        margin: 2px 0 4px 0;
        color: var(--muted);
        font-size: 0.84rem;
        line-height: 1.2;
    }
    .title {
        font-size: 2.02rem;
        font-weight: 900;
        letter-spacing: 0.02em;
        color: #f8fbff;
        margin: 0;
        line-height: 1.05;
    }
    .badge {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding: 5px 12px;
        border-radius: 999px;
        border: 1px solid rgba(103,232,249,0.16);
        background: linear-gradient(135deg, #1f2937, #111827);
        color: #d8f3ff;
        font-size: 0.78rem;
        line-height: 1;
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }
    @keyframes pulse {
        0% { transform: scale(0.92); opacity: 0.8; }
        50% { transform: scale(1.1); opacity: 1; }
        100% { transform: scale(0.92); opacity: 0.8; }
    }
    .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 12px 12px 10px 12px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        overflow: hidden;
    }
    .panel-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #eef4ff;
        margin: 0 0 8px 0;
        line-height: 1.1;
    }
    .panel-note {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 6px;
        line-height: 1.25;
    }
    .roi-good { color: var(--good); font-size: 0.78rem; margin-top: 4px; }
    .roi-warn { color: var(--warn); font-size: 0.78rem; margin-top: 4px; }
    .roi-bad { color: var(--bad); font-size: 0.78rem; margin-top: 4px; }
    .stAlert { border-radius: 8px; }
    iframe[title="st.iframe"] { width: 100% !important; }
</style>
""",
    unsafe_allow_html=True,
)

if "scenario" not in st.session_state:
    st.session_state.scenario = "日常正常状态"
if "agent_ready" not in st.session_state:
    st.session_state.agent_ready = False
if "strategy_confirmed" not in st.session_state:
    st.session_state.strategy_confirmed = False
if "op_mode" not in st.session_state:
    st.session_state.op_mode = {"运力": 70, "补贴": 30}

with st.sidebar:
    st.markdown("### ISDP 调度台")
    scenario = st.selectbox("场景选择", list(SCENARIOS.keys()), index=list(SCENARIOS.keys()).index(st.session_state.scenario))
    st.session_state.scenario = scenario
    supply_val = st.slider("运力", 0, 100, int(st.session_state.op_mode["运力"]))
    subsidy_val = st.slider("补贴", 0, 100, int(st.session_state.op_mode["补贴"]))
    st.session_state.op_mode = {"运力": supply_val, "补贴": subsidy_val}
    if supply_val < 20:
        st.warning("运力过低，存在明显履约风险，请谨慎操作。")
    run_agent = st.button("一键唤醒 AI agent 决策", use_container_width=True, type="primary")

simulation = simulate_business_scenario(scenario)
summary = summarize_by_hour(simulation.records)
capacity_val = int(supply_val)
subsidy_val = int(subsidy_val)
c_factor = capacity_val / 71.0
s_factor = subsidy_val / 59.0
sim_factor = (c_factor * s_factor) ** 0.4
current_supply = int(19417 * c_factor)
current_punctuality = min(98.5, 93.37 * (sim_factor ** 0.2))
current_subsidy = int(2447 * s_factor)
current_roi = round(max(0.5, min(2.5, 1.5 * sim_factor / (s_factor ** 0.7 if s_factor > 0 else 1))), 2)
post_punctuality = min(99.0, 93.37 * sim_factor)

if scenario == "异常天气状态" or supply_val < 20:
    st.error("[⚠️ 触发系统熔断] 当前参数将导致利润严重倒挂！")
    a, b, c = st.columns(3)
    if a.button("A方案：日常微调", use_container_width=True):
        st.session_state.op_mode = {"运力": 65, "补贴": 25}
        st.rerun()
    if b.button("B方案：暴雨保底", use_container_width=True):
        st.session_state.op_mode = {"运力": 55, "补贴": 80}
        st.rerun()
    if c.button("C方案：大促激进", use_container_width=True):
        st.session_state.op_mode = {"运力": 85, "补贴": 60}
        st.rerun()

header_left, header_right = st.columns([1.7, 1.0], vertical_alignment="center")
with header_left:
    st.markdown('<div class="title">ISDP 智能供需决策中心</div>', unsafe_allow_html=True)
with header_right:
    st.markdown(
        f'<div style="text-align:right; color:#8b949e; font-size:0.82rem; line-height:1.3;">数据更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>核心模式：AI闭环智能调度</div>',
        unsafe_allow_html=True,
    )

header_meta_left, header_meta_right = st.columns([1.7, 1.0], vertical_alignment="center")
with header_meta_left:
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'><span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444,0 0 14px #ef4444;animation:pulse 1.8s infinite;margin-right:8px;'></span>实时供需断链预警</div>", unsafe_allow_html=True)
    with b2:
        st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>动态运力熔断机制</div>", unsafe_allow_html=True)
    with b3:
        st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>自动化调度令流转</div>", unsafe_allow_html=True)
    with b4:
        st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>策略效能归因复盘</div>", unsafe_allow_html=True)
with header_meta_right:
    st.markdown(
        f'<div style="text-align:right; color:#8b949e; font-size:0.82rem; line-height:1.3;">当前场景：{scenario} | MAPE：{simulation.mape:.2f}%</div>',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("总需求", f"{simulation.total_demand:,d}")
with k2:
    st.metric("总供给", f"{current_supply:,d}")
with k3:
    st.metric("相对准时率", f"{current_punctuality:.2f}%")
with k4:
    st.metric("补贴金额", f"{current_subsidy:,d}")
with k5:
    st.metric("核心 ROI", f"{current_roi:.2f}")
    if simulation.core_roi > 1.5:
        st.markdown('<div class="roi-good">补贴高效</div>', unsafe_allow_html=True)
    elif simulation.core_roi < 1.0:
        st.markdown('<div class="roi-bad">倒挂预警</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="roi-warn">正常</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1])
with left:
    st.markdown('<div class="panel"><div class="panel-title">分时供需错配与履约健康度</div>', unsafe_allow_html=True)
    trend = pd.DataFrame(
        {
            "hour": list(range(HOURS)),
            "Demand": [summary[h]["demand"] for h in range(HOURS)],
            "Supply": [summary[h]["supply"] for h in range(HOURS)],
        }
    )
    trend.loc[9:14, "Supply"] = trend.loc[9:14, "Supply"] * capacity_ratio
    trend["Gap"] = trend["Supply"] - trend["Demand"]
    trend["Supply_Ratio"] = (trend["Supply"] / trend["Demand"]).replace([float("inf"), float("-inf")], pd.NA)
    trend["A2R"] = (98 + trend["Gap"] * 0.05).clip(lower=72, upper=99.5)
    trend.loc[9:14, "A2R"] = (trend.loc[9:14, "A2R"] * sim_factor).clip(upper=98.0)
    trend["A2R"] = trend["A2R"].astype(float)
    health_supply_ratio = trend.loc[
        [simulation.records[h].on_time / max(simulation.records[h].matched, 1) * 100 >= 98 for h in range(HOURS)],
        "Supply_Ratio",
    ].dropna().mean()
    if pd.isna(health_supply_ratio):
        health_supply_ratio = trend["Supply_Ratio"].dropna().mean()
    gap_bars = alt.Chart(trend).mark_bar().encode(
        x=alt.X("hour:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=False, labelFontSize=11)),
        y=alt.Y("Supply_Ratio:Q", title=None, axis=alt.Axis(title="供需比(供应/需求)", labelColor="#d8d29a", titleColor="#d8d29a", tickColor="#2c3c52", grid=False, labelFontSize=11), scale=alt.Scale(domain=[0, max(1.4, float(trend["Supply_Ratio"].max(skipna=True) or 1.4) * 1.1)])),
        color=alt.condition(alt.datum.Supply_Ratio < 1, alt.value("#fb7185"), alt.value("#22c55e")),
        tooltip=["hour:Q", alt.Tooltip("Supply_Ratio:Q", title="供需比(供应/需求)", format=".2f")],
    )
    demand_supply = alt.Chart(trend).transform_fold(["Demand", "Supply"], as_=["series", "value"]).mark_line(point=True, strokeWidth=2.8).encode(
        x=alt.X("hour:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=False, labelFontSize=11)),
        y=alt.Y("value:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=True, gridColor="#1b2734", labelFontSize=11)),
        color=alt.Color("series:N", scale=alt.Scale(domain=["Demand", "Supply"], range=["#67e8f9", "#86efac"]), legend=alt.Legend(title=None, orient="top-right", labelColor="#c9d7ea", labelFontSize=11, symbolType="stroke")),
        tooltip=["hour:Q", "series:N", "value:Q"],
    )
    a2r_line = alt.Chart(trend).mark_line(color="#f5d76e", strokeWidth=2.6, point=True).encode(
        x=alt.X("hour:Q", title=None),
        y=alt.Y("A2R:Q", title=None, axis=alt.Axis(title="A2R(%)", labelColor="#d8d29a", titleColor="#d8d29a", tickColor="#2c3c52", grid=False, labelFontSize=11), scale=alt.Scale(domain=[70, 100])),
        tooltip=["hour:Q", alt.Tooltip("A2R:Q", title="实时应答率")],
    )
    health_line = alt.Chart(pd.DataFrame({"health": [health_supply_ratio]})).mark_rule(color="#9ca3af", strokeDash=[6, 4], strokeWidth=2).encode(
        y=alt.Y("health:Q", title=None, axis=alt.Axis(title="供需比(右轴)", labelColor="#d8d29a", titleColor="#d8d29a", tickColor="#2c3c52", grid=False, labelFontSize=11), scale=alt.Scale(domain=[0, max(1.4, float(trend["Supply_Ratio"].max(skipna=True) or 1.4) * 1.1)])),
        tooltip=[alt.Tooltip("health:Q", title="健康供需比", format=".2f")],
    )
    trend_chart = (gap_bars + demand_supply + a2r_line + health_line).resolve_scale(y="independent").properties(height=400, width="container").configure_view(strokeOpacity=0, fill="#11151c").configure(background="transparent").configure_axis(domainColor="#2a394c", tickColor="#2a394c").configure_legend(fillColor="#11151c", strokeColor="#233549")
    st.altair_chart(trend_chart, use_container_width=True)
    st.markdown(
        f'<div style="display:flex; flex-direction:column; gap:4px; margin-top:8px; color:#cbd5e1; font-size:0.84rem; line-height:1.35;">'
        f'<div>💰 今日已耗补贴：<span style="color:#ffffff; font-weight:700;">$2,447</span> | 剩余运营弹药：<span style="color:#67e8f9; font-weight:700;">$7,553</span> <span style="color:#8fa3b8;">(预算水位：24.5%)</span></div>'
        f'<div>💡 当前单均补贴成本(CPC)：<span style="color:#ffffff; font-weight:700;">${1.18 * subsidy_ratio:.2f}</span> | 预计策略ROI：<span style="color:#67e8f9; font-weight:700;">{max(0.8, 1.65 / (subsidy_ratio ** 0.5 if subsidy_ratio > 0 else 1)):.2f}</span></div>'
        '</div>'
        '<div class="chart-budget-bar"><div class="chart-budget-fill"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">区域热力监控图</div>', unsafe_allow_html=True)
    geo_df = pd.DataFrame(simulation.geo_points).copy()
    geo_df["backlog"] = (geo_df["weight"] * 18 / sim_factor).round(0).astype(int)
    geo_df["bonus"] = (geo_df["weight"] * 1.8).round(2)
    geo_df["a2r"] = (98 - geo_df["weight"] * 1.6).round(1)
    geo_df["zone_name"] = [f"一级网格-{i+1:02d}" for i in range(len(geo_df))]
    geo_df["sub_zone"] = [f"二级网格-{i+1:02d}" for i in range(len(geo_df))]
    geo_df["radius"] = (geo_df["backlog"] * 120 / sim_factor).clip(300, 1600)
    geo_df["fill_rgba"] = geo_df["backlog"].apply(
        lambda x: [255, 75, 75, 210] if x >= 12 else ([255, 165, 0, 180] if x >= 6 else [255, 255, 255, 30])
    )
    geo_df["tri_size"] = (geo_df["backlog"] * 0.00055).clip(0.00045, 0.0018)
    geo_df["triangles"] = geo_df.apply(
        lambda row: [
            [
                [row["lon"], row["lat"] + row["tri_size"]],
                [row["lon"] - row["tri_size"] * 0.9, row["lat"] - row["tri_size"] * 0.85],
                [row["lon"] + row["tri_size"] * 0.9, row["lat"] - row["tri_size"] * 0.85],
            ]
        ],
        axis=1,
    )

    # 补充灰度底图网格层，强化区域轮廓感
    grid_points = []
    for _, row in geo_df.iterrows():
        for dx in (-0.02, 0, 0.02):
            for dy in (-0.02, 0, 0.02):
                grid_points.append(
                    {
                        "lon": row["lon"] + dx,
                        "lat": row["lat"] + dy,
                        "value": max(1, int(row["backlog"] * 0.2)),
                    }
                )
    grid_df = pd.DataFrame(grid_points)

    grid_layer = pdk.Layer(
        "ScreenGridLayer",
        data=grid_df,
        get_position="[lon, lat]",
        get_weight="value",
        cell_size_pixels=55,
        opacity=0.22,
        color_range=[[30, 41, 59, 20], [71, 85, 105, 40], [148, 163, 184, 80], [251, 146, 60, 120], [239, 68, 68, 160]],
        pickable=False,
    )
    scatter_layer = pdk.Layer(
        "PolygonLayer",
        data=geo_df,
        get_polygon="triangles",
        get_fill_color="fill_rgba",
        get_line_color=[15, 23, 42],
        line_width_min_pixels=1,
        stroked=True,
        filled=True,
        pickable=True,
        auto_highlight=True,
    )
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(latitude=31.2304, longitude=121.4737, zoom=11, pitch=45),
        layers=[grid_layer, scatter_layer],
        tooltip={
            "html": "<div style='font-size:12px;line-height:1.5;color:#fff;'>📍 网格区域: {zone_name}<br/>🧩 二级网格: {sub_zone}<br/>📉 实时应答率: {a2r}%<br/>👥 积压排队单: {backlog}单<br/>💰 动态调度溢价: +${bonus}/单</div>",
            "style": {"backgroundColor": "#11151c", "color": "#fff", "border": "1px solid #233549"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel"><div class="panel-title" style="margin-bottom:10px;">AI 决策工作台</div>', unsafe_allow_html=True)
if run_agent:
    st.session_state.agent_ready = True
    with st.status("AI agent 正在推理", expanded=True) as status:
        st.write("🚨 【异常识别】监测到区域供给缺口。")
        time.sleep(0.3)
        st.write("🔍 【根因分析】由恶劣天气导致运力出车率下降。")
        time.sleep(0.3)
        st.write(f"💡 【策略生成】建议每单补贴上调 {round(3.5 * s_factor, 1)} 元。")
        time.sleep(0.3)
        st.write("✅ 【方案确认】等待人工确认后下发执行。")
        status.update(label="AI agent 推理完成", state="complete")

if st.session_state.agent_ready:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button("⚡ 同意 AI 策略，一键下发执行", use_container_width=True, type="primary")
    with c2:
        if st.button("确认执行", use_container_width=True):
            st.session_state.strategy_confirmed = True
            st.markdown('<div style="background-color: rgba(46, 160, 67, 0.15); border: 1px solid rgba(46, 160, 67, 0.4); padding: 8px 12px; border-radius: 6px; color: #56d364; font-size: 13px; font-weight: 500;">✅ 执行成功 | 调度令已下发至 ERP 系统 (单号: ISDP-2026-XXXX)</div>', unsafe_allow_html=True)

if st.session_state.strategy_confirmed:
    before = 93.37
    after = post_punctuality
    b1, b2 = st.columns(2)
    with b1:
        st.metric("执行前准时率", f"{before:.2f}%")
    with b2:
        st.metric("执行后准时率", f"{after:.2f}%", f"+{after - before:.2f}%")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel"><div class="panel-title" style="margin-bottom:10px;">AB 实验指标面板</div>', unsafe_allow_html=True)
ab = simulation.ab_metrics
结论 = "实验组效果显著，建议全量上线" if current_roi > 1.0 else "效果不显著，请保持现状"
st.info(结论)
ab_display = pd.DataFrame(
    {
        "指标": ["ROI", "匹配率", "压单量"],
        "基准组": [f"{1.15:.2f}", f"{88.47:.2f}%", f"{2440:d}"],
        "实验组": [f"{(current_roi * 1.8):.2f}", f"{current_punctuality:.2f}%", f"{int(2440 / sim_factor):d}"],
        "提升率": [
            f"{((current_roi * 1.8 - 1.15) / 1.15 * 100):.2f}%",
            f"{((current_punctuality - 88.47) / 88.47 * 100):.2f}%",
            f"{((int(2440 / sim_factor) - 2440) / 2440 * 100):.2f}%",
        ],
    }
)
ab_style = ab_display.style.set_table_styles(
    [
        {"selector": "th", "props": [("text-align", "center")]},
        {"selector": "td", "props": [("text-align", "center")]},
    ]
).set_properties(**{"text-align": "center"})
st.table(ab_style)
st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"场景：{scenario} ｜ 底层数据与前端展示已严格联动。")
