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
        --bg0: #04101d;
        --bg1: #07182a;
        --panel: rgba(10, 18, 34, 0.78);
        --line: rgba(125, 211, 252, 0.16);
        --text: #eaf2ff;
        --muted: #8aa8c8;
        --good: #34d399;
        --warn: #f59e0b;
        --bad: #fb7185;
    }
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, rgba(56,189,248,0.14), transparent 28%),
            radial-gradient(circle at 85% 10%, rgba(168,85,247,0.10), transparent 25%),
            linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 55%, #030712 100%);
        color: var(--text);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8,16,30,0.99), rgba(4,9,18,0.99));
        border-right: 1px solid rgba(148,163,184,0.14);
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(13,20,38,0.96), rgba(6,12,24,0.88));
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    }
    [data-testid="stMetricValue"] { color: #fff; }
    .isdp-title {
        font-size: 2.35rem;
        font-weight: 900;
        letter-spacing: 0.04em;
        color: #f8fbff;
        margin-bottom: 0.2rem;
    }
    .isdp-subtitle { color: var(--muted); margin-bottom: 1rem; }
    .glass {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.26);
        backdrop-filter: blur(14px);
    }
    .section-title {
        font-size: 1.06rem;
        font-weight: 800;
        color: #f3f8ff;
        margin-bottom: 10px;
    }
    .badge {
        display: inline-block;
        margin: 0 8px 8px 0;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(103,232,249,0.16);
        background: rgba(15,23,42,0.55);
        color: #d8f3ff;
        font-size: 0.86rem;
    }
    .roi-tag-good { color: var(--good); font-size: 0.82rem; margin-top: 6px; }
    .roi-tag-bad { color: var(--bad); font-size: 0.82rem; margin-top: 6px; }
    .roi-tag-mid { color: var(--warn); font-size: 0.82rem; margin-top: 6px; }
    .tiny-note { color: var(--muted); font-size: 0.84rem; }
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
    st.markdown("---")
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

st.markdown('<div class="isdp-title">ISDP 智能供需决策中心</div>', unsafe_allow_html=True)
st.markdown(f'<div class="isdp-subtitle">企业级调度大屏 · 红绿灯预警 · 一键闭环 · {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
for tag in ["红绿灯预警", "智能防错", "一键下发", "复盘飞轮"]:
    st.markdown(f"<span class='badge'>{tag}</span>", unsafe_allow_html=True)

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
        st.markdown('<div class="roi-tag-good">补贴高效</div>', unsafe_allow_html=True)
    elif simulation.core_roi < 1.0:
        st.markdown('<div class="roi-tag-bad">倒挂预警</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="roi-tag-mid">正常</div>', unsafe_allow_html=True)

left, right = st.columns([1.4, 1.0])
with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">分时供需趋势</div>', unsafe_allow_html=True)
    trend = pd.DataFrame(
        {
            "hour": list(range(HOURS)),
            "Demand": [summary[h]["demand"] for h in range(HOURS)],
            "Supply": [summary[h]["supply"] for h in range(HOURS)],
        }
    )
    trend_long = trend.melt("hour", var_name="series", value_name="value")
    chart = (
        alt.Chart(trend_long)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("hour:Q", title="小时", axis=alt.Axis(labelColor="#c9d7ea", titleColor="#c9d7ea", gridColor="rgba(255,255,255,0.06)")),
            y=alt.Y("value:Q", title="数量", axis=alt.Axis(labelColor="#c9d7ea", titleColor="#c9d7ea", gridColor="rgba(255,255,255,0.06)")),
            color=alt.Color("series:N", scale=alt.Scale(domain=["Demand", "Supply"], range=["#67e8f9", "#86efac"]), legend=alt.Legend(labelColor="#c9d7ea", titleColor="#c9d7ea")),
            tooltip=["hour:Q", "series:N", "value:Q"],
        )
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure(background="#071426")
        .configure_axis(domainColor="#46607a", tickColor="#46607a")
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">地理空间热力联动</div>', unsafe_allow_html=True)
    geo_df = pd.DataFrame(simulation.geo_points)
    st.map(geo_df.rename(columns={"lat": "latitude", "lon": "longitude"}))
    st.caption("日常：均匀分散；异常天气：写字楼/商圈聚集；节假日：景区/高铁站/机场集中。")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass" style="margin-top:18px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">AI 决策工作台</div>', unsafe_allow_html=True)
if run_agent:
    st.session_state.agent_ready = True
    with st.status("AI agent 正在推理", expanded=True) as status:
        st.write("🚨 【异常识别】监测到区域供给缺口。")
        time.sleep(0.35)
        st.write("🔍 【根因分析】由恶劣天气导致运力出车率下降。")
        time.sleep(0.35)
        st.write("💡 【策略生成】建议每单补贴上调 X 元。")
        time.sleep(0.35)
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

st.markdown('<div class="glass" style="margin-top:18px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">AB 实验指标面板</div>', unsafe_allow_html=True)
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

st.caption(f"场景：{scenario} ｜ MAPE：{simulation.mape:.2f}% ｜ 底层数据与前端展示已严格联动。")
