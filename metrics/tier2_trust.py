"""
Tier 2: Reliability & Trust Metrics

금융 도메인 특화 신뢰 지표:
- Zero-Anachronism Rate: 시점 오류 제로 (목표: 100%)
- Signal-to-Noise Ratio: 핵심 뉴스 비율 (목표: > 70%)
- Fact-Consistency Score: 팩트 정합성 (목표: > 95%)
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional

from .models import METRIC_TARGETS


def measure_zero_anachronism(
    news_dates: List[date],
    buy_date: date,
    sell_date: date,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Zero-Anachronism Rate 측정

    미래 시점의 정보가 과거 분석에 개입되는 'Look-ahead Bias'를 검증합니다.
    모든 뉴스가 매수일 ~ 매도일 범위 내에 있어야 합니다.

    Args:
        news_dates: 검색된 뉴스들의 날짜 리스트
        buy_date: 매수일
        sell_date: 매도일
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    if not news_dates:
        return {
            "metric_name": "Zero-Anachronism Rate",
            "tier": "trust",
            "value": 100.0,
            "target": METRIC_TARGETS["zero_anachronism_rate"],
            "passed": True,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "metadata": {
                "total_news": 0,
                "valid_news": 0,
                "invalid_news": 0,
                "note": "No news items to validate"
            }
        }

    valid_dates = []
    invalid_dates = []

    for news_date in news_dates:
        if buy_date <= news_date <= sell_date:
            valid_dates.append(news_date.isoformat() if hasattr(news_date, 'isoformat') else str(news_date))
        else:
            invalid_dates.append(news_date.isoformat() if hasattr(news_date, 'isoformat') else str(news_date))

    valid_count = len(valid_dates)
    total_count = len(news_dates)
    rate = (valid_count / total_count) * 100

    return {
        "metric_name": "Zero-Anachronism Rate",
        "tier": "trust",
        "value": round(rate, 2),
        "target": METRIC_TARGETS["zero_anachronism_rate"],
        "passed": rate == 100.0,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "total_news": total_count,
            "valid_news": valid_count,
            "invalid_news": total_count - valid_count,
            "buy_date": buy_date.isoformat() if hasattr(buy_date, 'isoformat') else str(buy_date),
            "sell_date": sell_date.isoformat() if hasattr(sell_date, 'isoformat') else str(sell_date),
            "invalid_dates": invalid_dates[:5],  # 최대 5개만 표시
            "unit": "percent"
        }
    }


def measure_signal_to_noise(
    news_items: List[Dict[str, Any]],
    llm_judge_results: List[bool],
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Signal-to-Noise Ratio 측정

    검색된 뉴스 중 주가 변동에 실질적 영향을 준 '핵심 뉴스(Signal)'의 비율을 측정합니다.

    Args:
        news_items: 뉴스 아이템 리스트
        llm_judge_results: LLM이 판단한 Signal 여부 리스트 (True=Signal, False=Noise)
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    if not llm_judge_results:
        return {
            "metric_name": "Signal-to-Noise Ratio",
            "tier": "trust",
            "value": 0.0,
            "target": METRIC_TARGETS["signal_to_noise_ratio"],
            "passed": False,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "metadata": {
                "signal_count": 0,
                "noise_count": 0,
                "total_count": 0,
                "error": "No LLM judge results provided"
            }
        }

    signal_count = sum(llm_judge_results)
    noise_count = len(llm_judge_results) - signal_count
    rate = (signal_count / len(llm_judge_results)) * 100
    target = METRIC_TARGETS["signal_to_noise_ratio"]

    # Signal로 판정된 뉴스 제목 추출
    signal_headlines = []
    noise_headlines = []
    for i, is_signal in enumerate(llm_judge_results):
        if i < len(news_items):
            headline = news_items[i].get("title", news_items[i].get("headline", f"News {i+1}"))
            if is_signal:
                signal_headlines.append(headline)
            else:
                noise_headlines.append(headline)

    return {
        "metric_name": "Signal-to-Noise Ratio",
        "tier": "trust",
        "value": round(rate, 2),
        "target": target,
        "passed": rate >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "signal_count": signal_count,
            "noise_count": noise_count,
            "total_count": len(llm_judge_results),
            "signal_headlines": signal_headlines[:3],  # 최대 3개
            "noise_headlines": noise_headlines[:3],    # 최대 3개
            "unit": "percent"
        }
    }


def measure_fact_consistency(
    faithfulness_score: float,
    original_sources: Optional[List[str]] = None,
    ai_claims: Optional[List[str]] = None,
    request_id: str = ""
) -> Dict[str, Any]:
    """
    Fact-Consistency Score 측정

    뉴스 원문(Fact)과 에이전트의 요약/판단이 모순되지 않는지 평가합니다.
    RAGAS Faithfulness 또는 LLM Judge를 통해 측정됩니다.

    Args:
        faithfulness_score: 팩트 정합성 점수 (0-100)
        original_sources: 원본 뉴스 소스 리스트 (선택)
        ai_claims: AI가 생성한 주장 리스트 (선택)
        request_id: 요청 ID

    Returns:
        메트릭 결과 딕셔너리
    """
    target = METRIC_TARGETS["fact_consistency_score"]

    return {
        "metric_name": "Fact-Consistency Score",
        "tier": "trust",
        "value": round(faithfulness_score, 2),
        "target": target,
        "passed": faithfulness_score >= target,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "metadata": {
            "evaluation_method": "ragas_faithfulness",
            "sources_count": len(original_sources) if original_sources else 0,
            "claims_count": len(ai_claims) if ai_claims else 0,
            "unit": "percent"
        }
    }


def parse_news_date(date_str: str) -> Optional[date]:
    """
    다양한 형식의 날짜 문자열을 date 객체로 변환

    Args:
        date_str: 날짜 문자열

    Returns:
        date 객체 또는 None
    """
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y.%m.%d",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    return None


def extract_news_dates(news_items: List[Dict[str, Any]]) -> List[date]:
    """
    뉴스 아이템 리스트에서 날짜 추출

    Args:
        news_items: 뉴스 아이템 리스트 (각 아이템에 'date' 또는 'published_date' 키 포함)

    Returns:
        날짜 리스트
    """
    dates = []
    for item in news_items:
        date_str = item.get("date") or item.get("published_date") or item.get("pub_date")
        if date_str:
            parsed = parse_news_date(str(date_str))
            if parsed:
                dates.append(parsed)
    return dates
