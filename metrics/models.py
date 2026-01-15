"""
Metrics Data Models

METRIC_GUIDE_V2.md 기반 3-Tier 평가 체계 데이터 모델 정의
"""

from typing import TypedDict, Dict, Any, List, Optional
from enum import Enum


class MetricTier(str, Enum):
    """평가 지표 계층"""
    IMPACT = "impact"       # Tier 1: Business Impact
    TRUST = "trust"         # Tier 2: Reliability & Trust
    STABILITY = "stability" # Tier 3: System Stability


class MetricResult(TypedDict):
    """개별 메트릭 측정 결과"""
    metric_name: str        # 메트릭 이름 (예: "E2E Latency")
    tier: str               # 소속 Tier ("impact", "trust", "stability")
    value: float            # 측정값
    target: float           # 목표치
    passed: bool            # 목표 달성 여부
    timestamp: str          # 측정 시간 (ISO format)
    request_id: str         # 요청 ID
    metadata: Dict[str, Any]  # 추가 메타데이터


class EvaluationReport(TypedDict):
    """전체 평가 리포트"""
    request_id: str                    # 요청 ID
    timestamp: str                     # 평가 시간
    metrics: List[MetricResult]        # 개별 메트릭 결과 리스트
    summary: Dict[str, float]          # Tier별 통과율 요약


class GoldenTestCase(TypedDict):
    """Golden Dataset 테스트 케이스"""
    id: str                            # 테스트 케이스 ID (예: "TC001")
    scenario: str                      # 시나리오 유형
    description: str                   # 시나리오 설명
    input: Dict[str, str]              # 입력 데이터 (layer1_stock, layer2_buy_date, etc.)
    ground_truth: Dict[str, Any]       # 정답 데이터
    user_belief_correct: bool          # 사용자 믿음의 정확성
    expected_blind_spot_score: float   # 예상 Blind Spot 점수


class GoldenDataset(TypedDict):
    """Golden Dataset 전체 구조"""
    version: str
    test_cases: List[GoldenTestCase]


# 메트릭별 목표치 상수
METRIC_TARGETS = {
    # Tier 1: Impact
    "blind_spot_detection_rate": 0.40,      # > 40%
    "time_to_insight_efficiency": 99.0,      # > 99%
    "actionability_score": 4.2,              # > 4.2 (5점 만점)

    # Tier 2: Trust
    "zero_anachronism_rate": 100.0,          # 100%
    "signal_to_noise_ratio": 70.0,           # > 70%
    "fact_consistency_score": 95.0,          # > 95%

    # Tier 3: Stability
    "e2e_latency": 15.0,                     # < 15초
    "json_stability_rate": 99.0,             # > 99%
}

# 인간 기준선 상수
HUMAN_BASELINE = {
    "avg_analysis_time_seconds": 30 * 60,    # 30분
}
