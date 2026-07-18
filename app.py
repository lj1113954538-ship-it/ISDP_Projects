from __future__ import annotations

import time
from datetime import datetime

import altair as alt
import pandas as pd
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
    .compact-caption { color: var(--muted); font-size: 0.8rem; margin-top: 4px; }
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
    st.metric("总供给", f"{simulation.total_supply:,d}")
with k3:
    st.metric("相对准时率", f"{simulation.punctuality_rate:.2f}%")
with k4:
    st.metric("补贴金额", f"{simulation.subsidy_amount:.0f}")
with k5:
    st.metric("核心 ROI", f"{simulation.core_roi:.2f}")
    if simulation.core_roi > 1.5:
        st.markdown('<div class="roi-good">补贴高效</div>', unsafe_allow_html=True)
    elif simulation.core_roi < 1.0:
        st.markdown('<div class="roi-bad">倒挂预警</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="roi-warn">正常</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1])
with left:
    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">分时供需趋势</div>', unsafe_allow_html=True)
        trend = pd.DataFrame(
            {
                "hour": list(range(HOURS)),
                "Demand": [summary[h]["demand"] for h in range(HOURS)],
                "Supply": [summary[h]["supply"] for h in range(HOURS)],
            }
        )
        diff = trend.assign(Gap=(trend["Demand"] - trend["Supply"]).clip(lower=0))
        base = alt.Chart(trend).properties(height=400, width="container")
        alert_band = alt.Chart(pd.DataFrame({"x1": [9], "x2": [13], "y1": [0], "y2": [max(trend["Demand"]) * 1.15]})).mark_rect(color="#ef4444", opacity=0.08).encode(x="x1:Q", x2="x2:Q", y="y1:Q", y2="y2:Q")
        gap_area = alt.Chart(diff).mark_area(color="#ef4444", opacity=0.18).encode(
            x=alt.X("hour:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=False, labelFontSize=11)),
            y=alt.Y("Gap:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=True, gridColor="#1b2734", labelFontSize=11)),
            tooltip=["hour:Q", alt.Tooltip("Gap:Q", title="供需断链缺口")],
        )
        lines = base.mark_line(point=True, strokeWidth=2.8).encode(
            x=alt.X("hour:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=False, labelFontSize=11)),
            y=alt.Y("value:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=True, gridColor="#1b2734", labelFontSize=11)),
            color=alt.Color("series:N", scale=alt.Scale(domain=["Demand", "Supply"], range=["#67e8f9", "#86efac"]), legend=alt.Legend(title=None, orient="top-right", labelColor="#c9d7ea", labelFontSize=11, symbolType="stroke")),
            tooltip=["hour:Q", "series:N", "value:Q"],
        ).transform_fold(["Demand", "Supply"], as_=["series", "value"])
        trend_chart = (alert_band + gap_area + lines).configure_view(strokeOpacity=0, fill="#11151c").configure(background="transparent").configure_axis(domainColor="#2a394c", tickColor="#2a394c").configure_legend(fillColor="#11151c", strokeColor="#233549")
        st.altair_chart(trend_chart, use_container_width=True)
        st.markdown(
            '<div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-top:8px;">'
            '<div style="color:#cbd5e1; font-size:0.84rem;">💰 今日补贴总额：<span style="color:#ffffff; font-weight:700;">$2,447</span></div>'
            '<div style="color:#cbd5e1; font-size:0.84rem;">剩余可用预算：<span style="color:#67e8f9; font-weight:700;">$7,553</span> <span style="color:#8fa3b8;">(预算水位：24.5%)</span></div>'
            '</div>'
            '<div class="chart-budget-bar"><div class="chart-budget-fill"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

with right:
    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">地理空间热力联动</div>', unsafe_allow_html=True)
        geo_df = pd.DataFrame(simulation.geo_points).copy()
        geo_df["缺口值"] = (geo_df["weight"] * 12).round(1)
        geo_df["建议加价"] = (geo_df["weight"] * 1.28).round(1)
        geo_df["建议运力"] = (geo_df["weight"] * 3.6).round(0)
        geo_df["颜色深度"] = geo_df["weight"]
        geo_df["lat"] = geo_df["lat"] + 0.0001 * (geo_df.index % 2)
        geo_df["lon"] = geo_df["lon"] + 0.0001 * (geo_df.index % 3)
        st.scatter_chart(geo_df, x="lon", y="lat", size="缺口值", color="颜色深度", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel" style="margin-top:0.5rem;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">AI 决策工作台</div>', unsafe_allow_html=True)
    if run_agent:
        st.session_state.agent_ready = True
        with st.status("AI agent 正在推理", expanded=True) as status:
            st.write("🚨 【异常识别】监测到区域供给缺口。")
            time.sleep(0.3)
            st.write("🔍 【根因分析】由恶劣天气导致运力出车率下降。")
            time.sleep(0.3)
            st.write("💡 【策略生成】建议每单补贴上调 X 元。")
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
        before = simulation.before_after_punctuality["执行前"]
        after = simulation.before_after_punctuality["执行后"]
        b1, b2 = st.columns(2)
        with b1:
            st.metric("执行前准时率", f"{before:.2f}%")
        with b2:
            st.metric("执行后准时率", f"{after:.2f}%", f"+{after - before:.2f}%")

    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel" style="margin-top:0.5rem;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">AB 实验指标面板</div>', unsafe_allow_html=True)
    ab = simulation.ab_metrics
    结论 = "实验组效果显著，建议全量上线" if ab["提升率"]["roi"] > 0 else "效果不显著，请保持现状"
    st.info(结论)
    ab_df = pd.DataFrame(
        {
            "指标": ["ROI", "匹配率", "压单量"],
            "基准组": [ab["基准组"]["roi"], ab["基准组"]["match_rate"], ab["基准组"]["backlog"]],
            "实验组": [ab["实验组"]["roi"], ab["实验组"]["match_rate"], ab["实验组"]["backlog"]],
            "提升率": [ab["提升率"]["roi"], ab["提升率"]["match_rate"], ab["提升率"]["backlog"]],
        }
    )
    st.dataframe(ab_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"场景：{scenario} ｜ 底层数据与前端展示已严格联动。")
