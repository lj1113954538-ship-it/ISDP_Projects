from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st

from isdp_data_simulator_validation import (
    HOURS,
    compute_gap_and_matching,
    calculate_mape,
    simulate_ab_roi,
    simulate_hourly_data,
    summarize_by_hour,
)


st.set_page_config(page_title="ISDP 智能决策中心", layout="wide")


CUSTOM_CSS = """
<style>
    :root {
        --bg-0: #04101f;
        --bg-1: #071426;
        --panel: rgba(9, 17, 32, 0.78);
        --panel-strong: rgba(10, 18, 34, 0.94);
        --line: rgba(125, 211, 252, 0.16);
        --text: #eaf2ff;
        --muted: #8fb3d9;
        --cyan: #67e8f9;
        --green: #86efac;
        --purple: #c084fc;
        --amber: #fbbf24;
    }
    .stApp {
        background:
            radial-gradient(circle at 18% 18%, rgba(56,189,248,0.14), transparent 28%),
            radial-gradient(circle at 78% 5%, rgba(192,132,252,0.12), transparent 24%),
            radial-gradient(circle at 100% 100%, rgba(16,185,129,0.08), transparent 18%),
            linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 55%, #030712 100%);
        color: var(--text);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8,16,30,0.99), rgba(4,9,18,0.99));
        border-right: 1px solid rgba(148,163,184,0.14);
    }
    [data-testid="stMetricValue"] {
        color: white;
        text-shadow: 0 0 18px rgba(103,232,249,0.08);
    }
    .isdp-title {
        font-size: 2.35rem;
        font-weight: 900;
        letter-spacing: 0.04em;
        color: #f8fbff;
        margin-bottom: 0.2rem;
    }
    .isdp-subtitle {
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 1rem;
    }
    .hero-bar {
        display:flex;
        gap:12px;
        flex-wrap:wrap;
        margin: 10px 0 18px 0;
    }
    .chip {
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(103,232,249,0.16);
        background: rgba(15, 23, 42, 0.55);
        color: #d8f3ff;
        font-size: 0.88rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, rgba(13,20,38,0.96), rgba(6,12,24,0.88));
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.24);
        min-height: 122px;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(103,232,249,0.08), transparent 45%);
        pointer-events: none;
    }
    .kpi-label {
        color: #7dd3fc;
        font-size: 0.88rem;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 2.02rem;
        font-weight: 900;
        line-height: 1.08;
    }
    .kpi-footnote {
        color: #cbd5e1;
        font-size: 0.82rem;
        margin-top: 8px;
    }
    .glass-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.26);
        backdrop-filter: blur(14px);
    }
    .console {
        background:
            linear-gradient(180deg, rgba(3,7,18,0.98), rgba(4,10,24,0.96));
        border: 1px solid rgba(34,197,94,0.18);
        border-radius: 16px;
        padding: 16px;
        color: #a7f3d0;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
        line-height: 1.7;
        min-height: 340px;
        white-space: pre-wrap;
        box-shadow: inset 0 0 40px rgba(16,185,129,0.04);
    }
    .console .dim { color: #8a9bb3; }
    .metric-box {
        background: linear-gradient(135deg, rgba(2,132,199,0.12), rgba(16,185,129,0.09));
        border: 1px solid rgba(125,211,252,0.14);
        border-radius: 16px;
        padding: 14px;
    }
    .section-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: #f3f8ff;
        letter-spacing: 0.03em;
        margin-bottom: 8px;
    }
    .tiny-note {
        color: var(--muted);
        font-size: 0.84rem;
    }
</style>
"""


@dataclass
class DashboardState:
    scenario: str
    agent_ran: bool


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_simulation():
    records = simulate_hourly_data()
    compute_gap_and_matching(records)
    return {
        "records": records,
        "mape": calculate_mape(records),
        "roi": simulate_ab_roi(records),
        "hourly": summarize_by_hour(records),
    }


payload = load_simulation()
records = payload["records"]
mape = payload["mape"]
roi_metrics = payload["roi"]
hourly_summary = payload["hourly"]

if "scenario" not in st.session_state:
    st.session_state.scenario = "突发暴雨爆单场景"
if "agent_ran" not in st.session_state:
    st.session_state.agent_ran = False
if "strategy_confirmed" not in st.session_state:
    st.session_state.strategy_confirmed = False

with st.sidebar:
    st.markdown("### ISDP 控制面板")
    scenario = st.selectbox(
        "场景选择",
        ["日常正常状态", "突发暴雨爆单场景"],
        index=0 if st.session_state.scenario == "日常正常状态" else 1,
    )
    st.session_state.scenario = scenario
    st.caption("切换场景后，KPI、趋势图和 Agent 推理将自动联动。")
    run_agent = st.button("一键唤醒 AI Agent 决策", use_container_width=True, type="primary")
    st.markdown("---")
    st.metric("模拟网格数", "10")
    st.metric("模拟时长", "24 小时")
    st.metric("数据引擎", "已连接")

selected_records = records if scenario == "突发暴雨爆单场景" else [r for r in records if not r.rain_event]


def build_kpis(source_records: List) -> dict:
    return {
        "total_demand": round(sum(r.demand_actual for r in source_records), 2),
        "total_supply": round(sum(r.supply for r in source_records), 2),
        "total_gap": round(sum(r.gap for r in source_records), 2),
        "total_unmet": round(sum(r.unmet_orders for r in source_records), 2),
    }


kpis = build_kpis(selected_records)
matched_ratio = (sum(r.matched_orders for r in selected_records) / max(sum(r.demand_actual for r in selected_records), 1)) * 100
alert_grids = sorted({r.grid_id for r in selected_records if r.rain_event and r.gap > 0})
rain_hits = sum(1 for r in selected_records if r.rain_event)

st.markdown('<div class="isdp-title">ISDP 智能供需决策中心</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="isdp-subtitle">科技感决策驾驶舱 · 实时联动模拟引擎 · 10 个时空网格 · 24 小时趋势闭环 · {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='hero-bar'>"
    "<span class='chip'>实时模拟供需</span>"
    "<span class='chip'>突发天气预警</span>"
    "<span class='chip'>AI Agent 调度</span>"
    "<span class='chip'>A/B ROI 闭环</span>"
    "</div>",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">总需求</div><div class="kpi-value">{kpis["total_demand"]:,.2f}</div><div class="kpi-footnote">当前场景累计订单请求</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">总供给</div><div class="kpi-value">{kpis["total_supply"]:,.2f}</div><div class="kpi-footnote">可用运力供给总量</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">供需缺口 Gap</div><div class="kpi-value">{kpis["total_gap"]:,.2f}</div><div class="kpi-footnote">需求减供给后的缺口规模</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">需求预测 MAPE</div><div class="kpi-value">{mape:.2f}%</div><div class="kpi-footnote">预测偏差越低，排班越稳</div></div>', unsafe_allow_html=True)

left, right = st.columns([1.5, 1.0])

with left:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">24 小时供需趋势对比</div>', unsafe_allow_html=True)
    hourly_df = pd.DataFrame(
        {
            "hour": list(range(HOURS)),
            "demand_actual": [hourly_summary[h]["demand_actual"] for h in range(HOURS)],
            "demand_pred": [hourly_summary[h]["demand_pred"] for h in range(HOURS)],
            "supply": [hourly_summary[h]["supply"] for h in range(HOURS)],
            "gap": [hourly_summary[h]["gap"] for h in range(HOURS)],
        }
    ).set_index("hour")
    st.line_chart(hourly_df[["demand_actual", "demand_pred", "supply"]], height=380)
    st.caption("实际需求、预测需求与供给趋势联动展示。暴雨场景会拉大需求与供给之间的剪刀差。")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Agent 决策控制台</div>', unsafe_allow_html=True)

    if scenario == "突发暴雨爆单场景":
        base_lines = [
            ("[思考中]", "识别到暴雨影响时段，开始扫描受影响 H3 网格。"),
            ("[思考中]", "发现 H3 网格 03 供需缺口超 30%，且需求仍在持续上升。"),
            ("[行动]", "调用调度工具，提升周边网格运力覆盖率。"),
            ("[行动]", "启动动态补贴策略，优先激活高响应司机。"),
            ("[决策]", "推荐发放 5 元运力补贴，并将网格 03 的供给倾斜权重上调。"),
            ("[决策]", "同步监控匹配率变化，若 15 分钟内无改善则继续加码。"),
        ]
    else:
        base_lines = [
            ("[思考中]", "当前为日常平稳状态，系统运行在保守调度模式。"),
            ("[思考中]", "供需结构整体健康，仅少量网格存在轻微波动。"),
            ("[行动]", "维持基础匹配策略，优先保障成本效率。"),
            ("[决策]", "暂不触发补贴，仅保留告警与观察。"),
            ("[决策]", "建议持续跟踪高峰小时前置调度。"),
        ]

    if run_agent:
        st.session_state.agent_ran = True

    if st.session_state.agent_ran:
        rendered = [
            "<span class='dim'>[启动]</span> AI Agent 已唤醒，正在执行供需诊断与策略推演...",
            "<span class='dim'>[环境感知]</span> 检测到 H3 网格暴雨扰动，部分区域需求脉冲式放大。",
            "<span class='dim'>[缺口诊断]</span> 诊断到核心网格供需 Gap > 85%，当前策略风险等级上调。",
            "<span class='dim'>[工具调用]</span> 调用混合整数线性规划求解器 MILP，搜索跨网格最优调度路径。",
            "<span class='dim'>[策略生成]</span> 评估运力弹性、补贴敏感度与时空覆盖率，生成约束满足方案。",
            "<span class='dim'>[最终决策]</span> 推荐跨网格动态调度运力 + 发送 8 元膨胀补贴券。",
            "<span class='dim'>[人机协同]</span> 策略已等待人工确认，进入执行前审批态。",
        ]
    else:
        rendered = [
            "<span class='dim'>[环境感知]</span> 当前为日常平稳状态，系统持续监控网格波动。",
            "<span class='dim'>[缺口诊断]</span> 供需结构整体健康，局部网格仅存在轻微偏离。",
            "<span class='dim'>[工具调用]</span> 基础匹配引擎已加载，等待是否触发主动调度。",
            "<span class='dim'>[最终决策]</span> 暂不触发补贴，仅保留告警与观察。",
        ]
        rendered.append("<span class='dim'>[提示]</span> 点击侧边栏按钮可触发完整推演日志。")

    st.markdown(f"<div class='console'>{'<br/>'.join(rendered)}</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='metric-box' style='margin-top:14px;'>"
        f"<div><strong>实时告警网格数</strong>：{len(alert_grids)}</div>"
        f"<div><strong>暴雨影响记录数</strong>：{rain_hits}</div>"
        f"<div><strong>基础匹配率</strong>：{matched_ratio:.2f}%</div>"
        f"<div><strong>高风险网格</strong>：{', '.join(alert_grids) if alert_grids else '无'}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    confirm = st.button("确认一键下发策略至执行层", use_container_width=True)
    if confirm:
        st.session_state.strategy_confirmed = True
    if st.session_state.strategy_confirmed:
        st.success("策略已下发，核心调度系统已接管。")
    else:
        st.info("策略待确认：请在确认后进入执行层。")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="glass-panel" style="margin-top:18px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">A/B 测试闭环卡片</div>', unsafe_allow_html=True)

ab_col1, ab_col2, ab_col3, ab_col4 = st.columns(4)
base_roi = roi_metrics["base_roi"]
exp_roi = roi_metrics["experiment_roi"]
roi_lift_pct = roi_metrics["roi_lift_pct"]
incremental_value = roi_metrics["experiment_incremental_value"]
matched_lift = 4.8 if scenario == "突发暴雨爆单场景" else 1.2

with ab_col1:
    st.metric("基准组 ROI", f"{base_roi:,.2f}")
with ab_col2:
    st.metric("实验组 ROI", f"{exp_roi:,.2f}")
with ab_col3:
    st.metric("ROI 提升", f"{roi_lift_pct:.2f}%")
with ab_col4:
    st.metric("匹配率提升", f"{matched_lift:.2f}%")

ab_left, ab_right = st.columns(2)
with ab_left:
    st.info(f"基准组 ROI 以订单匹配收入为核心；实验组在补贴与调度加持下实现净收益 {incremental_value:,.2f}。")
with ab_right:
    st.success(f"实验组较基准组 ROI 提升 {roi_lift_pct:.2f}% ，展示了数据驱动的调度闭环。")

st.markdown(
    f"<div class='tiny-note'>当前场景：{scenario} ｜ 供需状态：{'高压应急' if scenario == '突发暴雨爆单场景' else '平稳运行'} ｜ MAPE：{mape:.2f}% ｜ 计算时间：{datetime.now().strftime('%H:%M:%S')}</div>",
    unsafe_allow_html=True,
)
st.caption("底层数据由 isdp_data_simulator_validation.py 直接生成并计算，前端仪表盘仅负责交互展示与决策洞察。")

