"""ISDP 核心数据模拟引擎（红绿灯式调度版）

目标
- 面向一线业务调度人员
- 强调直观视觉、智能防错、一键闭环
- 严格联动三类业务场景
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

SEED = 42
HOURS = 24
GRID_COUNT = 10

SCENARIOS = {
    "日常正常状态": {
        "demand_multiplier": 1.0,
        "supply_multiplier": 1.0,
        "subsidy_multiplier": 1.0,
        "punctuality_base": 0.95,
        "roi_target": (1.2, 1.5),
    },
    "异常天气状态": {
        "demand_multiplier": 3.0,
        "supply_multiplier": 0.6,
        "subsidy_multiplier": 3.0,
        "punctuality_base": 0.74,
        "roi_target": (0.55, 0.65),
    },
    "传统节假日": {
        "demand_multiplier": 1.7,
        "supply_multiplier": 1.08,
        "subsidy_multiplier": 0.72,
        "punctuality_base": 0.97,
        "roi_target": (2.0, 2.4),
    },
}


@dataclass
class HourlyRecord:
    grid_id: str
    hour: int
    scenario: str
    demand: int
    supply: int
    matched: int
    backlog: int
    on_time: int
    subsidy: float
    supply_hours: float
    demand_pred: int
    latitude: float
    longitude: float
    zone: str


@dataclass
class ScenarioSimulation:
    scenario: str
    records: List[HourlyRecord]
    total_demand: int
    total_supply: int
    total_matched: int
    backlog: int
    punctuality_rate: float
    subsidy_amount: float
    supply_hours_increment: float
    core_roi: float
    mape: float
    ab_metrics: Dict[str, Dict[str, float]]
    emergency_strategies: List[str]
    geo_points: List[Dict[str, float]]
    before_after_punctuality: Dict[str, float]


def build_grid_ids(count: int = GRID_COUNT) -> List[str]:
    return [f"H3-{i:02d}" for i in range(count)]


def build_grid_coords() -> Dict[str, tuple[float, float]]:
    base_lat, base_lon = 31.2304, 121.4737
    coords = {}
    for idx, grid_id in enumerate(build_grid_ids()):
        lat = base_lat + (idx % 5) * 0.04 + (idx // 5) * 0.02
        lon = base_lon + (idx % 5) * 0.05 - (idx // 5) * 0.025
        coords[grid_id] = (round(lat, 5), round(lon, 5))
    return coords


def build_geo_points(scenario: str) -> List[Dict[str, float]]:
    rng = random.Random(SEED + len(scenario))
    if scenario == "异常天气状态":
        base = [
            (31.23, 121.48, 9.8),
            (31.24, 121.49, 9.6),
            (31.22, 121.47, 9.9),
            (31.245, 121.495, 9.7),
            (31.235, 121.485, 9.5),
            (31.205, 121.455, 5.0),
            (31.195, 121.445, 4.6),
            (31.255, 121.505, 9.2),
        ]
        return [{"lat": lat, "lon": lon, "weight": weight + rng.uniform(-0.2, 0.2)} for lat, lon, weight in base]
    if scenario == "传统节假日":
        base = [
            (31.17, 121.49, 9.8),
            (31.15, 121.51, 9.7),
            (31.20, 121.46, 9.5),
            (31.18, 121.47, 9.3),
            (31.21, 121.52, 9.4),
            (31.26, 121.43, 8.8),
            (31.27, 121.44, 8.9),
            (31.16, 121.50, 9.1),
        ]
        return [{"lat": lat, "lon": lon, "weight": weight + rng.uniform(-0.2, 0.2)} for lat, lon, weight in base]
    base = [
        (31.21, 121.45, 6.2),
        (31.23, 121.47, 6.8),
        (31.25, 121.49, 6.4),
        (31.19, 121.46, 6.0),
        (31.22, 121.51, 6.5),
        (31.24, 121.43, 6.1),
        (31.20, 121.50, 6.3),
        (31.26, 121.47, 6.7),
    ]
    return [{"lat": lat, "lon": lon, "weight": weight + rng.uniform(-0.15, 0.15)} for lat, lon, weight in base]


def _hour_profile(hour: int) -> float:
    angle = 2 * math.pi * hour / 24
    return 1.0 + 0.16 * math.sin(angle - 0.7) + 0.06 * math.cos(angle * 2)


def _zone_for_idx(idx: int, scenario: str) -> str:
    if scenario == "异常天气状态":
        return ["写字楼", "商圈", "写字楼", "商圈", "写字楼", "住宅区", "住宅区", "商圈", "写字楼", "商圈"][idx]
    if scenario == "传统节假日":
        return ["景区", "高铁站", "机场", "景区", "高铁站", "机场", "景区", "高铁站", "机场", "景区"][idx]
    return ["住宅区", "商圈", "写字楼", "社区", "园区", "商圈", "住宅区", "社区", "园区", "写字楼"][idx]


def _simulate_records(scenario: str) -> List[HourlyRecord]:
    cfg = SCENARIOS[scenario]
    rng = random.Random(SEED + abs(hash(scenario)) % 1000)
    coords = build_grid_coords()
    records: List[HourlyRecord] = []

    for hour in range(HOURS):
        for idx, grid_id in enumerate(build_grid_ids()):
            profile = _hour_profile(hour)
            demand = int(round((68 + idx * 4 + hour % 5) * profile + rng.normalvariate(0, 2.4)))
            supply = int(round((66 + idx * 3 + (hour % 4)) * (1.0 + 0.08 * math.cos(2 * math.pi * hour / 24)) + rng.normalvariate(0, 1.8)))
            demand = max(8, int(round(demand * cfg["demand_multiplier"])))
            supply = max(5, int(round(supply * cfg["supply_multiplier"])))

            if scenario == "异常天气状态":
                if hour in range(8, 20) and idx in {1, 2, 3, 5, 7}:
                    demand = int(round(demand * 1.08))
                    supply = int(round(supply * 0.88))
            elif scenario == "传统节假日":
                if hour in {10, 11, 12, 17, 18, 19}:
                    demand = int(round(demand * 1.14))
                    supply = int(round(supply * 1.04))

            demand_pred = max(1, int(round(demand * (0.94 + rng.uniform(-0.02, 0.02)))))
            matched = min(demand, supply)
            backlog = max(demand - supply, 0)
            punctuality = max(0.45, min(0.99, cfg["punctuality_base"] - backlog / max(demand, 1) * 0.16 + rng.uniform(-0.008, 0.008)))
            on_time = int(round(matched * punctuality))
            subsidy = float(backlog) * cfg["subsidy_multiplier"] * (1.0 + 0.03 * (hour in {8, 17, 18}))
            supply_hours = float(supply) * (1.0 + 0.08 * punctuality)
            lat, lon = coords[grid_id]
            records.append(
                HourlyRecord(
                    grid_id=grid_id,
                    hour=hour,
                    scenario=scenario,
                    demand=demand,
                    supply=supply,
                    matched=matched,
                    backlog=backlog,
                    on_time=on_time,
                    subsidy=round(subsidy, 2),
                    supply_hours=round(supply_hours, 2),
                    demand_pred=demand_pred,
                    latitude=lat,
                    longitude=lon,
                    zone=_zone_for_idx(idx, scenario),
                )
            )
    return records


def _mape(records: List[HourlyRecord]) -> float:
    err = [abs(r.demand - r.demand_pred) / r.demand for r in records if r.demand > 0]
    return round(sum(err) / len(err) * 100, 2) if err else 0.0


def _ab_metrics(records: List[HourlyRecord], scenario: str, subsidy_amount: float, matched_rate: float) -> Dict[str, Dict[str, float]]:
    base_matched = sum(r.matched for r in records)
    base_backlog = sum(r.backlog for r in records)
    base_supply_hours = sum(r.supply_hours for r in records)
    if scenario == "异常天气状态":
        exp_supply_hours = base_supply_hours * 0.94 + base_matched * 0.05
        exp_subsidy = subsidy_amount * 1.18
    elif scenario == "传统节假日":
        exp_supply_hours = base_supply_hours * 1.12 + base_matched * 0.08
        exp_subsidy = subsidy_amount * 0.74
    else:
        exp_supply_hours = base_supply_hours * 1.06 + base_matched * 0.04
        exp_subsidy = subsidy_amount * 0.92
    base_roi = round(base_supply_hours / max(subsidy_amount, 1.0), 2)
    exp_roi = round(exp_supply_hours / max(exp_subsidy, 1.0), 2)
    base_match_rate = round(matched_rate * 100, 2)
    exp_match_rate = round(min(99.99, base_match_rate * (1.05 if scenario != "异常天气状态" else 1.03)), 2)
    exp_backlog = int(round(base_backlog * (0.84 if scenario == "异常天气状态" else 0.72 if scenario == "传统节假日" else 0.9)))
    return {
        "基准组": {"roi": base_roi, "match_rate": base_match_rate, "backlog": float(base_backlog)},
        "实验组": {"roi": exp_roi, "match_rate": exp_match_rate, "backlog": float(exp_backlog)},
        "提升率": {
            "roi": round((exp_roi - base_roi) / max(base_roi, 0.01) * 100, 2),
            "match_rate": round((exp_match_rate - base_match_rate) / max(base_match_rate, 0.01) * 100, 2),
            "backlog": round((base_backlog - exp_backlog) / max(base_backlog, 1) * 100, 2),
        },
    }


def _emergency_strategies() -> List[str]:
    return [
        "策略 A：跨网格动态调度运力，优先向高缺口区域倾斜。",
        "策略 B：发放 8 元膨胀补贴券，锁定高响应司机。",
        "策略 C：缩短派单半径，叠加人工值守。",
    ]


def simulate_business_scenario(scenario: str) -> ScenarioSimulation:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    records = _simulate_records(scenario)
    total_demand = sum(r.demand for r in records)
    total_supply = sum(r.supply for r in records)
    total_matched = sum(r.matched for r in records)
    backlog = sum(r.backlog for r in records)
    punctuality_rate = round(sum(r.on_time for r in records) / max(total_matched, 1) * 100, 2)
    subsidy_amount = round(sum(r.subsidy for r in records), 2)
    supply_hours_increment = round(sum(r.supply_hours for r in records) - total_supply, 2)
    core_roi = round(supply_hours_increment / max(subsidy_amount, 1.0), 2)
    mape = _mape(records)
    matched_rate = total_matched / max(total_demand, 1)
    ab_metrics = _ab_metrics(records, scenario, subsidy_amount, matched_rate)
    emergency_strategies = _emergency_strategies() if scenario == "异常天气状态" else []
    geo_points = build_geo_points(scenario)
    before_after_punctuality = {
        "执行前": punctuality_rate,
        "执行后": round(min(99.99, punctuality_rate + (6.5 if scenario == "异常天气状态" else 2.8 if scenario == "传统节假日" else 1.8)), 2),
    }
    return ScenarioSimulation(
        scenario=scenario,
        records=records,
        total_demand=total_demand,
        total_supply=total_supply,
        total_matched=total_matched,
        backlog=backlog,
        punctuality_rate=punctuality_rate,
        subsidy_amount=subsidy_amount,
        supply_hours_increment=supply_hours_increment,
        core_roi=core_roi,
        mape=mape,
        ab_metrics=ab_metrics,
        emergency_strategies=emergency_strategies,
        geo_points=geo_points,
        before_after_punctuality=before_after_punctuality,
    )


def summarize_by_hour(records: List[HourlyRecord]) -> Dict[int, Dict[str, float]]:
    summary: Dict[int, Dict[str, float]] = {}
    for hour in range(HOURS):
        subset = [r for r in records if r.hour == hour]
        summary[hour] = {
            "demand": float(sum(r.demand for r in subset)),
            "supply": float(sum(r.supply for r in subset)),
            "matched": float(sum(r.matched for r in subset)),
            "backlog": float(sum(r.backlog for r in subset)),
            "on_time_rate": round(sum(r.on_time for r in subset) / max(sum(r.matched for r in subset), 1) * 100, 2),
        }
    return summary


def scenario_report(simulation: ScenarioSimulation) -> None:
    print("=" * 72)
    print("ISDP 核心数据模拟引擎")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"场景: {simulation.scenario}")
    print(f"总需求: {simulation.total_demand}")
    print(f"总供给: {simulation.total_supply}")
    print(f"相对准时率: {simulation.punctuality_rate:.2f}%")
    print(f"补贴金额: {simulation.subsidy_amount:.0f}")
    print(f"核心 ROI: {simulation.core_roi:.2f}")
    print(f"MAPE: {simulation.mape:.2f}%")
    print("A/B 指标:")
    for k, v in simulation.ab_metrics.items():
        print(f"- {k}: {v}")
    print("=" * 72)


if __name__ == "__main__":
    scenario_report(simulate_business_scenario("异常天气状态"))
