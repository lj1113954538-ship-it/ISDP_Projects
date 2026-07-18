from __future__ import annotations

import time
from datetime import datetime

import pandas as pd
import streamlit as st

from isdp_data_simulator_validation import HOURS, SCENARIOS, build_grid_ids, simulate_business_scenario, summarize_by_hour


st.set_page_config(page_title="ISDP 智能决策中心", layout="wide")
st.markdown('<html lang="zh-CN" class="notranslate" translate="no"></html>', unsafe_allow_html=True)

CUSTOM_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #03101f 0%, #06182b 55%, #02060f 100%);
        color: #eaf2ff;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8,16,30,0.99), rgba(4,9,18,0.99));
    }
    .title { font-size: 2.2rem; font-weight: 900; color: #f8fbff; }
    .subtitle { color: #8fb3d9; margin-bottom: 1rem; }
    .glass {
        background: rgba(8,16,30,0.82);
        border: 1px solid rgba(125,211,252,0.16);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.26);
    }
    .hint-green { color: #86efac; font-size: 0.82rem; margin-top: 6px; }
    .hint-red { color: #fca5a5; font-size: 0.82rem; margin-top: 6px; }
    .badge {
        display:inline-block;
        margin: 0 8px 8px 0;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(103,232,249,0.16);
        background: rgba(15,23,42,0.55);
        color: #d8f3ff;
        font-size: 0.86rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

st.markdown('<div class="title">ISDP 智能供需决策中心</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">红绿灯式调度 · 一键闭环 · {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
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
    st.caption("补贴高效" if simulation.core_roi > 1.5 else "倒挂预警" if simulation.core_roi < 1.0 else "正常")

left, right = st.columns([1.35, 1.0])
with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("分时供需趋势")
    trend = pd.DataFrame({
        "hour": list(range(HOURS)),
        "Demand": [summary[h]["demand"] for h in range(HOURS)],
        "Supply": [summary[h]["supply"] for h in range(HOURS)],
    }).set_index("hour")
    st.line_chart(trend, height=320)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("地理空间热力联动")
    geo_df = pd.DataFrame(simulation.geo_points)
    st.map(geo_df.rename(columns={"lat": "latitude", "lon": "longitude"}))
    st.caption("日常：均匀分散；异常天气：写字楼/商圈聚集；节假日：景区/高铁站/机场集中。")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="glass" style="margin-top:18px;">', unsafe_allow_html=True)
st.subheader("AI 决策工作台")
if run_agent:
    st.session_state.agent_ready = True
    with st.status("AI agent 正在推理", expanded=True) as status:
        st.write("🚨 【异常识别】监测到区域供给缺口。")
        time.sleep(0.4)
        st.write("🔍 【根因分析】由恶劣天气导致运力出车率下降。")
        time.sleep(0.4)
        st.write("💡 【策略生成】建议每单补贴上调 X 元。")
        time.sleep(0.4)
        st.write("✅ 【方案确认】等待人工确认后下发执行。")
        status.update(label="AI agent 推理完成", state="complete")

if st.session_state.agent_ready:
    st.button("⚡ 同意 AI 策略，一键下发执行", use_container_width=True, type="primary")
    if st.button("确认执行", use_container_width=True):
        st.session_state.strategy_confirmed = True
        st.success("🎉 执行成功！调度令已流转至 ERP 系统，单号：ISDP-2026-XXXX")

if st.session_state.strategy_confirmed:
    before = simulation.before_after_punctuality["执行前"]
    after = simulation.before_after_punctuality["执行后"]
    c1, c2 = st.columns(2)
    with c1:
        st.metric("执行前准时率", f"{before:.2f}%")
    with c2:
        st.metric("执行后准时率", f"{after:.2f}%", f"+{after - before:.2f}%")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="glass" style="margin-top:18px;">', unsafe_allow_html=True)
st.subheader("AB 实验指标面板")
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
st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"场景：{scenario} ｜ MAPE：{simulation.mape:.2f}% ｜ 底层数据与前端展示已严格联动。")
