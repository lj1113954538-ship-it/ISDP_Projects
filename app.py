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
        f'<div style="text-align:right; color:#8b949e; font-size:0.82rem; line-height:1.3;">数据更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>核心模式：一键闭环管控</div>',
        unsafe_allow_html=True,
    )

badge_cols = st.columns(4)
with badge_cols[0]:
    st.markdown(
        "<div class='badge' style='width:100%; justify-content:flex-start;'><span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444,0 0 14px #ef4444;animation:pulse 1.8s infinite;margin-right:8px;'></span>红绿灯预警</div>",
        unsafe_allow_html=True,
    )
with badge_cols[1]:
    st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>智能防错</div>", unsafe_allow_html=True)
with badge_cols[2]:
    st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>一键下发</div>", unsafe_allow_html=True)
with badge_cols[3]:
    st.markdown("<div class='badge' style='width:100%; justify-content:flex-start;'>复盘飞轮</div>", unsafe_allow_html=True)

status_cols = st.columns([1.7, 1.0], vertical_alignment="center")
with status_cols[0]:
    st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)
with status_cols[1]:
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
        ).melt("hour", var_name="series", value_name="value")
        trend_chart = (
            alt.Chart(trend)
            .mark_line(point=True, strokeWidth=2.8)
            .encode(
                x=alt.X("hour:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=False, labelFontSize=11)),
                y=alt.Y("value:Q", title=None, axis=alt.Axis(labelColor="#b9c9da", tickColor="#2c3c52", grid=True, gridColor="#1b2734", labelFontSize=11)),
                color=alt.Color("series:N", scale=alt.Scale(domain=["Demand", "Supply"], range=["#67e8f9", "#86efac"]), legend=alt.Legend(title=None, orient="top", labelColor="#c9d7ea", labelFontSize=11)),
                tooltip=["hour:Q", "series:N", "value:Q"],
            )
            .properties(height=320, width="container")
            .configure_view(strokeOpacity=0, fill="#11151c")
            .configure(background="transparent")
            .configure_axis(domainColor="#2a394c", tickColor="#2a394c")
            .configure_legend(fillColor="#11151c", strokeColor="#233549")
        )
        st.altair_chart(trend_chart, use_container_width=True)
        st.markdown('<div class="panel-note">按小时展示 Demand vs Supply，统一暗色背景避免白色斑块。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with right:
    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">地理空间热力联动</div>', unsafe_allow_html=True)
        geo_df = pd.DataFrame(simulation.geo_points)
        st.map(geo_df.rename(columns={"lat": "latitude", "lon": "longitude"}))
        st.markdown('<div class="panel-note">日常：均匀分散；异常天气：写字楼/商圈聚集；节假日：景区/高铁站/机场集中。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
            st.success("🎉 执行成功！调度令已流转至 ERP 系统，单号：ISDP-2026-XXXX")

if st.session_state.strategy_confirmed:
    before = simulation.before_after_punctuality["执行前"]
    after = simulation.before_after_punctuality["执行后"]
    b1, b2 = st.columns(2)
    with b1:
        st.metric("执行前准时率", f"{before:.2f}%")
    with b2:
        st.metric("执行后准时率", f"{after:.2f}%", f"+{after - before:.2f}%")

st.markdown('</div>', unsafe_allow_html=True)

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
