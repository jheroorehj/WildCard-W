"""
LLM-as-a-Judge Module

LLM을 활용한 메트릭 평가 프롬프트 및 함수 정의
- Signal-to-Noise Ratio 판정
- Actionability Score 평가
- Fact-Consistency Score 평가
- Semantic Similarity 계산
"""

from typing import Optional, List, Tuple
import re


# ============================================
# Signal-to-Noise Ratio 판정 프롬프트
# ============================================
SNR_PROMPT = """당신은 금융 뉴스 분석 전문가입니다.
다음 뉴스가 해당 종목의 주가 변동에 실질적 영향을 줄 수 있는 결정적 사건(Signal)인지 판단해주세요.

## 판단 기준

**Signal (주가에 영향을 주는 뉴스):**
- 실적 발표 및 어닝 서프라이즈/쇼크
- 인수합병(M&A) 관련 뉴스
- 규제 변화 및 정부 정책
- 경영진 이슈 (CEO 교체, 횡령, 스캔들 등)
- 신제품 출시 또는 대형 계약 체결
- 대규모 투자 유치 또는 자본 변동
- 소송 및 법적 분쟁
- 산업 구조 변화 관련 뉴스

**Noise (주가에 영향이 적은 뉴스):**
- 단순 시황 중계 ("오늘 코스피 상승...")
- 일반적인 시장 논평
- 이미 알려진 정보의 반복
- 추측성 기사 ("~할 것으로 전망")
- 광고성/홍보성 기사

## 분석 대상

종목: {ticker}
날짜: {date}
뉴스 제목: {title}
뉴스 내용:
{news_content}

## 응답 형식

반드시 다음 형식으로만 응답하세요:
판정: [Signal 또는 Noise]
근거: [한 줄로 간단히]"""


SNR_PROMPT_SIMPLE = """다음 뉴스가 {ticker} 종목의 주가에 실질적 영향을 줄 수 있는 결정적 사건인지 판단하세요.

뉴스: {news_content}

Signal(주가 영향 있음) 또는 Noise(주가 영향 없음) 중 하나만 답하세요:"""


# ============================================
# Actionability Score 평가 프롬프트
# ============================================
ACTIONABILITY_PROMPT = """당신은 투자 교육 전문가입니다.
다음 '학습 제안'이 얼마나 구체적이고 실행 가능한지 1-5점 척도로 평가해주세요.

## 평가 기준

1점: 매우 추상적이고 막연한 조언
   - 예: "투자 공부를 더 하세요", "시장을 더 잘 파악하세요"

2점: 방향은 있으나 구체성 부족
   - 예: "기술적 분석을 배우세요", "뉴스를 더 주의깊게 보세요"

3점: 실행 가능하나 단계가 불명확
   - 예: "RSI 지표를 활용해보세요", "손절 기준을 정하세요"

4점: 구체적이고 단계별 안내 포함
   - 예: "RSI가 30 이하일 때 매수 신호로 활용하되, 거래량도 함께 확인하세요"

5점: 즉시 실행 가능한 상세 지침
   - 예: 구체적인 학습 자료 추천, 단계별 실습 방법, 체크리스트 제공

## 평가 대상

{learning_recommendation}

## 응답 형식

반드시 숫자 하나만 응답하세요 (1, 2, 3, 4, 또는 5):"""


# ============================================
# Fact-Consistency Score 평가 프롬프트
# ============================================
CONSISTENCY_PROMPT = """당신은 팩트체크 전문가입니다.
AI의 분석 결과가 원본 뉴스 내용과 일치하는지 평가해주세요.

## 평가 기준

- 사실 왜곡 여부: AI가 원본에 없는 사실을 추가했는가?
- 과장/축소 여부: AI가 원본의 내용을 과장하거나 축소했는가?
- 환각(Hallucination) 여부: AI가 존재하지 않는 내용을 만들어냈는가?
- 인용 정확성: AI가 원본의 숫자, 날짜, 이름 등을 정확히 인용했는가?

## 원본 뉴스

{original_news}

## AI 분석 결과

{ai_analysis}

## 응답 형식

일관성 점수를 0-100 사이의 숫자로만 응답하세요:
- 100: 완벽하게 일치, 어떠한 왜곡도 없음
- 80-99: 대체로 일치, 사소한 해석 차이만 있음
- 60-79: 일부 불일치, 약간의 과장이나 축소가 있음
- 40-59: 상당한 불일치, 명확한 왜곡이 있음
- 0-39: 심각한 불일치, 환각이 포함됨

점수:"""


# ============================================
# Semantic Similarity 평가 프롬프트
# ============================================
SIMILARITY_PROMPT = """두 텍스트의 의미적 유사도를 0.0에서 1.0 사이의 숫자로 평가하세요.

## 평가 기준

- 1.0: 완전히 동일한 의미
- 0.8-0.9: 매우 유사한 의미 (같은 결론, 약간 다른 표현)
- 0.6-0.7: 유사한 의미 (관련된 내용이지만 세부사항 차이)
- 0.4-0.5: 부분적으로 관련됨
- 0.2-0.3: 약간 관련됨
- 0.0-0.1: 관련 없거나 반대 의미

## 텍스트 A (기준)

{text_a}

## 텍스트 B (비교 대상)

{text_b}

## 응답 형식

0.0에서 1.0 사이의 숫자만 응답하세요:"""


# ============================================
# LLM Judge 함수들
# ============================================
async def judge_signal_or_noise(
    llm,
    ticker: str,
    date: str,
    news_content: str,
    title: str = ""
) -> Tuple[bool, str]:
    """
    뉴스가 Signal인지 Noise인지 LLM으로 판정

    Args:
        llm: LLM 인스턴스 (langchain ChatModel)
        ticker: 종목 티커
        date: 뉴스 날짜
        news_content: 뉴스 내용
        title: 뉴스 제목

    Returns:
        (is_signal, reason) 튜플
    """
    prompt = SNR_PROMPT.format(
        ticker=ticker,
        date=date,
        title=title,
        news_content=news_content[:500]  # 최대 500자
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.lower()

        is_signal = "signal" in content and "noise" not in content.split("signal")[0]

        # 근거 추출
        reason = ""
        if "근거:" in response.content:
            reason = response.content.split("근거:")[-1].strip()

        return is_signal, reason
    except Exception as e:
        return False, f"Error: {str(e)}"


async def judge_actionability(
    llm,
    learning_recommendation: str
) -> float:
    """
    학습 제안의 실행 가능성 점수 평가

    Args:
        llm: LLM 인스턴스
        learning_recommendation: 학습 제안 텍스트

    Returns:
        1-5 사이의 점수
    """
    prompt = ACTIONABILITY_PROMPT.format(
        learning_recommendation=learning_recommendation[:1000]  # 최대 1000자
    )

    try:
        response = await llm.ainvoke(prompt)
        # 숫자만 추출
        numbers = re.findall(r'[1-5]', response.content)
        if numbers:
            return float(numbers[0])
        return 3.0  # 기본값
    except Exception:
        return 3.0


async def judge_consistency(
    llm,
    original_news: str,
    ai_analysis: str
) -> float:
    """
    AI 분석의 팩트 정합성 평가

    Args:
        llm: LLM 인스턴스
        original_news: 원본 뉴스 내용
        ai_analysis: AI 분석 결과

    Returns:
        0-100 사이의 점수
    """
    prompt = CONSISTENCY_PROMPT.format(
        original_news=original_news[:1000],
        ai_analysis=ai_analysis[:1000]
    )

    try:
        response = await llm.ainvoke(prompt)
        # 숫자 추출
        numbers = re.findall(r'\d+(?:\.\d+)?', response.content)
        if numbers:
            score = float(numbers[-1])  # 마지막 숫자 사용
            return min(100.0, max(0.0, score))
        return 80.0  # 기본값
    except Exception:
        return 80.0


async def calculate_semantic_similarity(
    llm,
    text_a: str,
    text_b: str
) -> float:
    """
    두 텍스트의 의미적 유사도 계산

    Args:
        llm: LLM 인스턴스
        text_a: 기준 텍스트
        text_b: 비교 대상 텍스트

    Returns:
        0.0-1.0 사이의 유사도
    """
    prompt = SIMILARITY_PROMPT.format(
        text_a=text_a[:500],
        text_b=text_b[:500]
    )

    try:
        response = await llm.ainvoke(prompt)
        # 0.0-1.0 사이 숫자 추출
        numbers = re.findall(r'0?\.\d+|1\.0|0|1', response.content)
        if numbers:
            similarity = float(numbers[0])
            return min(1.0, max(0.0, similarity))
        return 0.5  # 기본값
    except Exception:
        return 0.5


# ============================================
# 동기 버전 함수들 (테스트/디버깅용)
# ============================================
def judge_signal_or_noise_sync(
    llm,
    ticker: str,
    date: str,
    news_content: str,
    title: str = ""
) -> Tuple[bool, str]:
    """Signal/Noise 판정 동기 버전"""
    prompt = SNR_PROMPT_SIMPLE.format(
        ticker=ticker,
        news_content=news_content[:300]
    )

    try:
        response = llm.invoke(prompt)
        is_signal = "signal" in response.content.lower()
        return is_signal, ""
    except Exception as e:
        return False, f"Error: {str(e)}"


def judge_actionability_sync(llm, learning_recommendation: str) -> float:
    """Actionability 평가 동기 버전"""
    prompt = ACTIONABILITY_PROMPT.format(
        learning_recommendation=learning_recommendation[:1000]
    )

    try:
        response = llm.invoke(prompt)
        numbers = re.findall(r'[1-5]', response.content)
        if numbers:
            return float(numbers[0])
        return 3.0
    except Exception:
        return 3.0


def judge_consistency_sync(llm, original_news: str, ai_analysis: str) -> float:
    """Consistency 평가 동기 버전"""
    prompt = CONSISTENCY_PROMPT.format(
        original_news=original_news[:1000],
        ai_analysis=ai_analysis[:1000]
    )

    try:
        response = llm.invoke(prompt)
        numbers = re.findall(r'\d+(?:\.\d+)?', response.content)
        if numbers:
            score = float(numbers[-1])
            return min(100.0, max(0.0, score))
        return 80.0
    except Exception:
        return 80.0
