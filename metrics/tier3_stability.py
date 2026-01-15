"""
Tier 3: System Stability Metrics

기본적인 엔지니어링 완성도 지표:
- E2E Latency: 전체 워크플로우 완료 시간 (목표: < 15초)
- JSON Stability Rate: JSON 스키마 준수율 (목표: > 99%)
"""

from datetime import datetime
from typing import List, Dict, Any

from .models import METRIC_TARGETS


def measure_e2e_latency(
    start_time: datetime,
    end_time: datetime,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    E2E Latency 측정

    전체 워크플로우(검색-분석-생성) 완료 시간을 측정합니다.

    Args:
        start_time: 요청 시작 시간
        end_time: 요청 종료 시간
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    latency_seconds = (end_time - start_time).total_seconds()
    target = METRIC_TARGETS["e2e_latency"]

    return {
        "metric_name": "E2E Latency",
        "tier": "stability",
        "value": round(latency_seconds, 2),
        "target": target,
        "passed": latency_seconds < target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "unit": "seconds",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
    }


def measure_json_stability(
    validation_results: List[bool],
    request_id: str = ""
) -> Dict[str, Any]:
    """
    JSON Stability Rate 측정

    프론트엔드 연동을 위한 JSON 스키마 준수율을 측정합니다.

    Args:
        validation_results: 각 노드별 JSON 검증 결과 리스트
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    if not validation_results:
        return {
            "metric_name": "JSON Stability Rate",
            "tier": "stability",
            "value": 0.0,
            "target": METRIC_TARGETS["json_stability_rate"],
            "passed": False,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "metadata": {
                "total_validations": 0,
                "successful_validations": 0,
                "failed_validations": 0,
                "error": "No validation results provided"
            }
        }

    successful = sum(validation_results)
    total = len(validation_results)
    rate = (successful / total) * 100
    target = METRIC_TARGETS["json_stability_rate"]

    return {
        "metric_name": "JSON Stability Rate",
        "tier": "stability",
        "value": round(rate, 2),
        "target": target,
        "passed": rate >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "total_validations": total,
            "successful_validations": successful,
            "failed_validations": total - successful,
            "unit": "percent"
        }
    }


def measure_node_latencies(
    node_timings: Dict[str, float],
    request_id: str = ""
) -> Dict[str, Any]:
    """
    개별 노드 레이턴시 측정 (상세 분석용)

    Args:
        node_timings: 노드별 실행 시간 딕셔너리 (예: {"N6": 2.5, "N7": 3.1, ...})
        request_id: 요청 ID

    Returns:
        노드별 레이턴시 상세 정보
    """
    if not node_timings:
        return {
            "metric_name": "Node Latencies",
            "tier": "stability",
            "value": 0.0,
            "target": 0.0,
            "passed": True,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "metadata": {"error": "No node timings provided"}
        }

    total_latency = sum(node_timings.values())
    avg_latency = total_latency / len(node_timings)
    max_node = max(node_timings, key=node_timings.get)
    min_node = min(node_timings, key=node_timings.get)

    return {
        "metric_name": "Node Latencies",
        "tier": "stability",
        "value": round(total_latency, 2),
        "target": METRIC_TARGETS["e2e_latency"],
        "passed": total_latency < METRIC_TARGETS["e2e_latency"],
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "node_timings": {k: round(v, 2) for k, v in node_timings.items()},
            "average_latency": round(avg_latency, 2),
            "slowest_node": max_node,
            "slowest_latency": round(node_timings[max_node], 2),
            "fastest_node": min_node,
            "fastest_latency": round(node_timings[min_node], 2),
            "unit": "seconds"
        }
    }
