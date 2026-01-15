"""
Tier 1: Business Impact Metrics

심사위원 설득을 위한 핵심 가치 지표:
- Blind Spot Detection Rate: 편향 교정률 (목표: > 40%)
- Time-to-Insight Efficiency: 분석 효율성 (목표: > 99%)
- Actionability Score: 실행 가능성 (목표: > 4.2)
"""

from datetime import datetime
from typing import Dict, Any, Optional

from .models import METRIC_TARGETS, HUMAN_BASELINE


def measure_time_efficiency(
    ai_latency_seconds: float,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Time-to-Insight Efficiency 측정

    인간이 직접 뉴스/공시를 분석할 때 대비 AI가 시간을 얼마나 단축시켰는지 측정합니다.
    공식: (Human_Avg_Time - AI_Latency) / Human_Avg_Time * 100

    Args:
        ai_latency_seconds: AI 분석 소요 시간 (초)
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    human_baseline = HUMAN_BASELINE["avg_analysis_time_seconds"]  # 30분 = 1800초
    efficiency = ((human_baseline - ai_latency_seconds) / human_baseline) * 100
    target = METRIC_TARGETS["time_to_insight_efficiency"]

    # 효율성이 100%를 넘을 수는 없음 (음수 레이턴시 불가)
    efficiency = min(efficiency, 100.0)

    return {
        "metric_name": "Time-to-Insight Efficiency",
        "tier": "impact",
        "value": round(efficiency, 2),
        "target": target,
        "passed": efficiency >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "ai_latency_seconds": round(ai_latency_seconds, 2),
            "human_baseline_seconds": human_baseline,
            "human_baseline_minutes": human_baseline / 60,
            "time_saved_seconds": round(human_baseline - ai_latency_seconds, 2),
            "time_saved_minutes": round((human_baseline - ai_latency_seconds) / 60, 2),
            "unit": "percent"
        }
    }


def evaluate_blind_spot(
    user_belief_similarity: float,
    ai_conclusion_similarity: float,
    user_belief: Optional[str] = None,
    ai_conclusion: Optional[str] = None,
    ground_truth: Optional[str] = None,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Blind Spot Detection Rate 측정

    사용자가 인지하지 못한(또는 잘못 알고 있는) 손실의 '진짜 원인'을
    AI가 찾아낸 비율을 측정합니다.

    평가 로직:
    - Case 1: AI가 정답이고, 사용자 믿음이 틀렸을 때 → Insight (1.0점)
    - Case 2: AI가 정답이고, 사용자 믿음도 맞았을 때 → Confirmation (0.5점)
    - Case 3: AI가 틀렸을 때 → Failure (0.0점)

    Args:
        user_belief_similarity: 사용자 믿음과 정답 간 유사도 (0-1)
        ai_conclusion_similarity: AI 결론과 정답 간 유사도 (0-1)
        user_belief: 사용자 믿음 텍스트 (선택)
        ai_conclusion: AI 결론 텍스트 (선택)
        ground_truth: 정답 텍스트 (선택)
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    # AI 정답 여부 (유사도 0.9 이상)
    is_ai_correct = ai_conclusion_similarity > 0.9
    # 사용자 편향 여부 (유사도 0.5 미만)
    is_user_biased = user_belief_similarity < 0.5

    if is_ai_correct and is_user_biased:
        score = 1.0
        label = "insight"
        description = "AI가 사용자의 맹점을 발견하고 교정함"
    elif is_ai_correct and not is_user_biased:
        score = 0.5
        label = "confirmation"
        description = "AI가 사용자의 올바른 판단을 확인함"
    else:
        score = 0.0
        label = "failure"
        description = "AI가 정답을 찾지 못함"

    target = METRIC_TARGETS["blind_spot_detection_rate"]

    return {
        "metric_name": "Blind Spot Detection",
        "tier": "impact",
        "value": score,
        "target": target,
        "passed": score >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "label": label,
            "description": description,
            "user_belief_similarity": round(user_belief_similarity, 3),
            "ai_conclusion_similarity": round(ai_conclusion_similarity, 3),
            "is_ai_correct": is_ai_correct,
            "is_user_biased": is_user_biased,
            "user_belief": user_belief[:100] if user_belief else None,  # 최대 100자
            "ai_conclusion": ai_conclusion[:100] if ai_conclusion else None,
            "ground_truth": ground_truth[:100] if ground_truth else None,
        }
    }


def measure_actionability(
    llm_score: float,
    learning_recommendation: Optional[Dict[str, Any]] = None,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Actionability Score 측정

    분석 결과가 단순한 현상 설명이 아니라,
    '다음 행동'으로 이어질 수 있는 구체적인 지침을 포함하는지 평가합니다.

    LLM-as-a-Judge가 1-5점 척도로 평가합니다:
    - 1점: 매우 추상적이고 막연한 조언
    - 2점: 방향은 있으나 구체성 부족
    - 3점: 실행 가능하나 단계가 불명확
    - 4점: 구체적이고 단계별 안내 포함
    - 5점: 즉시 실행 가능한 상세 지침

    Args:
        llm_score: LLM이 평가한 점수 (1-5)
        learning_recommendation: 평가 대상 학습 추천 내용 (선택)
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    target = METRIC_TARGETS["actionability_score"]

    # 점수 범위 검증
    llm_score = max(1.0, min(5.0, llm_score))

    # 점수별 레이블
    score_labels = {
        1: "very_abstract",
        2: "somewhat_vague",
        3: "moderately_actionable",
        4: "concrete",
        5: "highly_actionable"
    }
    label = score_labels.get(int(round(llm_score)), "unknown")

    return {
        "metric_name": "Actionability Score",
        "tier": "impact",
        "value": round(llm_score, 2),
        "target": target,
        "passed": llm_score >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "scale": "1-5",
            "label": label,
            "evaluation_method": "llm_judge",
            "has_learning_steps": bool(
                learning_recommendation and
                learning_recommendation.get("learning_steps")
            ),
            "has_recommended_topics": bool(
                learning_recommendation and
                learning_recommendation.get("recommended_topics")
            ),
            "has_focus_area": bool(
                learning_recommendation and
                learning_recommendation.get("focus_area")
            ),
        }
    }


def calculate_aggregate_blind_spot_rate(
    individual_scores: list[float]
) -> Dict[str, Any]:
    """
    전체 테스트 케이스에 대한 Blind Spot Detection Rate 집계

    Args:
        individual_scores: 개별 테스트 케이스별 Blind Spot 점수 리스트

    Returns:
        집계된 메트릭 결과
    """
    if not individual_scores:
        return {
            "metric_name": "Blind Spot Detection Rate (Aggregate)",
            "tier": "impact",
            "value": 0.0,
            "target": METRIC_TARGETS["blind_spot_detection_rate"],
            "passed": False,
            "timestamp": datetime.now().isoformat(),
            "request_id": "aggregate",
            "metadata": {"error": "No scores to aggregate"}
        }

    # Insight (1.0) 비율 계산
    insight_count = sum(1 for s in individual_scores if s == 1.0)
    rate = (insight_count / len(individual_scores)) * 100
    target = METRIC_TARGETS["blind_spot_detection_rate"] * 100  # 40%

    return {
        "metric_name": "Blind Spot Detection Rate (Aggregate)",
        "tier": "impact",
        "value": round(rate, 2),
        "target": target,
        "passed": rate >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": "aggregate",
        "metadata": {
            "total_cases": len(individual_scores),
            "insight_count": insight_count,
            "confirmation_count": sum(1 for s in individual_scores if s == 0.5),
            "failure_count": sum(1 for s in individual_scores if s == 0.0),
            "unit": "percent"
        }
    }
