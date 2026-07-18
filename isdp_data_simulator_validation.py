"""ISDP 核心数据模拟引擎

功能
- 模拟 10 个 H3 风格时空网格，24 小时动态订单需求与可用运力供给
- 随机生成突发暴雨爆单场景：需求暴增、供给下降
- 计算供需缺口（Gap），运行基础匹配策略，并输出预测 MAPE
- 自动输出 A/B 测试 ROI 对比（实验组 vs 基准组）

说明
- 这是一个可直接运行的 Demo 级模拟器，用于演示智能供需决策系统（ISDP）的核心闭环
- 为避免外部依赖，H3 网格使用 H3 风格字符串进行模拟，不依赖第三方库
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple


SEED = 42
GRID_COUNT = 10
HOURS = 24
BASE_DEMAND_LEVEL = 80
BASE_SUPPLY_LEVEL = 78
RAIN_EVENT_DURATION = 4
RAIN_DEMAND_BOOST = 1.75
RAIN_SUPPLY_DROP = 0.55


@dataclass
class HourlyRecord:
    grid_id: str
    hour: int
    demand_actual: float
    demand_pred: float
    supply: float
    rain_event: bool
    gap: float = 0.0
    matched_orders: float = 0.0
    unmet_orders: float = 0.0
    revenue_base: float = 0.0
    revenue_experiment: float = 0.0
    cost_experiment: float = 0.0


def build_grid_ids(count: int) -> List[str]:
    return [f"h3_sim_{i:02d}" for i in range(count)]


def generate_base_profiles(grid_ids: List[str]) -> Dict[str, Dict[str, float]]:
    profiles = {}
    for idx, grid_id in enumerate(grid_ids):
        demand_amp = 0.18 + idx * 0.012
        supply_amp = 0.12 + idx * 0.009
        phase_shift = (idx % 5) * 0.6
        base_demand = BASE_DEMAND_LEVEL + idx * 4
        base_supply = BASE_SUPPLY_LEVEL + idx * 3
        profiles[grid_id] = {
            "demand_amp": demand_amp,
            "supply_amp": supply_amp,
            "phase_shift": phase_shift,
            "base_demand": base_demand,
            "base_supply": base_supply,
        }
    return profiles


def pick_rain_event(rng: random.Random) -> Tuple[int, List[int], str]:
    start_hour = rng.randint(8, 18)
    duration = RAIN_EVENT_DURATION
    affected_hours = list(range(start_hour, min(start_hour + duration, HOURS)))
    affected_grids = rng.sample(build_grid_ids(GRID_COUNT), k=4)
    return start_hour, affected_hours, ",".join(affected_grids)


def is_affected(grid_id: str, affected_grids_csv: str) -> bool:
    return grid_id in affected_grids_csv.split(",")


def simulate_hourly_data() -> List[HourlyRecord]:
    rng = random.Random(SEED)
    grid_ids = build_grid_ids(GRID_COUNT)
    profiles = generate_base_profiles(grid_ids)
    rain_start_hour, rain_hours, affected_grids_csv = pick_rain_event(rng)

    records: List[HourlyRecord] = []
    for hour in range(HOURS):
        hour_angle = 2 * math.pi * hour / 24
        rush_boost = 1.22 if hour in (7, 8, 17, 18) else 1.0
        for grid_id in grid_ids:
            profile = profiles[grid_id]
            demand_seasonality = 1 + profile["demand_amp"] * math.sin(hour_angle - profile["phase_shift"])
            supply_seasonality = 1 + profile["supply_amp"] * math.cos(hour_angle - profile["phase_shift"])

            noise_demand = rng.normalvariate(0, 4)
            noise_supply = rng.normalvariate(0, 3)

            demand_pred = max(5, profile["base_demand"] * demand_seasonality * rush_boost + noise_demand)
            demand_actual = demand_pred * rng.uniform(0.92, 1.08)
            supply = max(0, profile["base_supply"] * supply_seasonality + noise_supply)

            rain_event = hour in rain_hours and is_affected(grid_id, affected_grids_csv)
            if rain_event:
                demand_actual *= RAIN_DEMAND_BOOST
                demand_pred *= 1.18
                supply *= RAIN_SUPPLY_DROP

            records.append(
                HourlyRecord(
                    grid_id=grid_id,
                    hour=hour,
                    demand_actual=round(demand_actual, 2),
                    demand_pred=round(demand_pred, 2),
                    supply=round(supply, 2),
                    rain_event=rain_event,
                )
            )
    return records


def compute_gap_and_matching(records: List[HourlyRecord]) -> None:
    for record in records:
        record.gap = round(record.demand_actual - record.supply, 2)
        record.matched_orders = round(min(record.demand_actual, record.supply), 2)
        record.unmet_orders = round(max(record.demand_actual - record.supply, 0), 2)


def calculate_mape(records: List[HourlyRecord]) -> float:
    ape_sum = 0.0
    valid_count = 0
    for record in records:
        if record.demand_actual > 0:
            ape_sum += abs(record.demand_actual - record.demand_pred) / record.demand_actual
            valid_count += 1
    return round(ape_sum / valid_count * 100, 2) if valid_count else 0.0


def simulate_ab_roi(records: List[HourlyRecord]) -> Dict[str, float]:
    total_base_revenue = 0.0
    total_exp_revenue = 0.0
    total_exp_cost = 0.0

    for record in records:
        base_matched = min(record.demand_actual, record.supply)
        exp_supply_boost = record.supply * (1.12 if record.rain_event else 1.03)
        exp_matched = min(record.demand_actual, exp_supply_boost)

        base_revenue = base_matched * 18.0
        exp_revenue = exp_matched * 18.8
        exp_cost = max(0.0, exp_supply_boost - record.supply) * 6.0 + (1.5 if record.rain_event else 0.6)

        record.revenue_base = round(base_revenue, 2)
        record.revenue_experiment = round(exp_revenue, 2)
        record.cost_experiment = round(exp_cost, 2)

        total_base_revenue += base_revenue
        total_exp_revenue += exp_revenue
        total_exp_cost += exp_cost

    base_roi = total_base_revenue
    exp_roi = total_exp_revenue - total_exp_cost
    roi_lift = (exp_roi - base_roi) / base_roi * 100 if base_roi > 0 else 0.0

    return {
        "base_roi": round(base_roi, 2),
        "experiment_roi": round(exp_roi, 2),
        "roi_lift_pct": round(roi_lift, 2),
        "experiment_incremental_value": round(exp_roi - base_roi, 2),
    }


def summarize_by_hour(records: List[HourlyRecord]) -> Dict[int, Dict[str, float]]:
    summary: Dict[int, Dict[str, float]] = {}
    for hour in range(HOURS):
        subset = [r for r in records if r.hour == hour]
        summary[hour] = {
            "demand_actual": round(sum(r.demand_actual for r in subset), 2),
            "demand_pred": round(sum(r.demand_pred for r in subset), 2),
            "supply": round(sum(r.supply for r in subset), 2),
            "gap": round(sum(r.gap for r in subset), 2),
            "unmet": round(sum(r.unmet_orders for r in subset), 2),
            "rain_affected": sum(1 for r in subset if r.rain_event),
        }
    return summary


def print_report(records: List[HourlyRecord], mape: float, roi_metrics: Dict[str, float]) -> None:
    hour_summary = summarize_by_hour(records)
    total_demand = round(sum(r.demand_actual for r in records), 2)
    total_supply = round(sum(r.supply for r in records), 2)
    total_gap = round(sum(r.gap for r in records), 2)
    total_unmet = round(sum(r.unmet_orders for r in records), 2)
    rain_records = [r for r in records if r.rain_event]

    print("=" * 72)
    print("ISDP 核心数据模拟引擎 Demo")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模拟网格数: {GRID_COUNT} | 模拟小时数: {HOURS}")
    print("=" * 72)
    print(f"总需求量: {total_demand}")
    print(f"总供给量: {total_supply}")
    print(f"总供需缺口 Gap: {total_gap}")
    print(f"总未满足订单: {total_unmet}")
    print(f"需求预测 MAPE: {mape}%")
    print("=" * 72)
    print("A/B 测试 ROI 对比")
    print(f"基准组 ROI: {roi_metrics['base_roi']}")
    print(f"实验组 ROI: {roi_metrics['experiment_roi']}")
    print(f"ROI 提升: {roi_metrics['roi_lift_pct']}%")
    print(f"实验组增量收益: {roi_metrics['experiment_incremental_value']}")
    print("=" * 72)

    if rain_records:
        sample = rain_records[0]
        print("突发暴雨场景已触发")
        print(
            f"示例网格: {sample.grid_id} | 小时: {sample.hour} | 需求: {sample.demand_actual} | 供给: {sample.supply} | Gap: {sample.gap}"
        )
    print("=" * 72)
    print("基础匹配策略摘要（前 6 个小时）")
    for hour in range(6):
        h = hour_summary[hour]
        print(
            f"Hour {hour:02d} | 需求 {h['demand_actual']:.2f} | 供给 {h['supply']:.2f} | Gap {h['gap']:.2f} | 未满足 {h['unmet']:.2f} | 暴雨网格数 {h['rain_affected']}"
        )
    print("=" * 72)


def main() -> None:
    records = simulate_hourly_data()
    compute_gap_and_matching(records)
    mape = calculate_mape(records)
    roi_metrics = simulate_ab_roi(records)
    print_report(records, mape, roi_metrics)


if __name__ == "__main__":
    main()
