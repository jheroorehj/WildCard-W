# WildCard-W AI 에이전트 평가 매트릭 및 검증 가이드라인 (V2)

**Version:** 2.0 (Judge-Oriented Update)
**Description:** 본 문서는 투자 손실 원인 분석 에이전트 **WildCard-W**의 성능을 정의합니다. 단순한 시스템 운영 안정성을 넘어, **사용자의 편향(Bias)을 교정**하고 **인간 대비 압도적인 분석 효율**을 제공하는지 증명하는 데 초점을 맞춥니다.

---

## 1. 핵심 평가 매트릭 (Key Evaluation Metrics)

평가 지표를 심사위원 설득 논리에 맞춰 **Impact (가치)**, **Trust (신뢰)**, **Stability (안정성)**의 3계층으로 재구성했습니다.

### **Tier 1: Business Impact (심사위원 설득을 위한 핵심 가치 지표)**
*"이 서비스가 왜 필요한가? 인간보다 무엇이 더 뛰어난가?"*

| 매트릭 명 (Metric Name) | 정의 및 목적 (Definition) | 측정 공식/방법 (Measurement Method) | 목표치 (Target) |
|:---:|:---|:---|:---:|
| **Blind Spot Detection Rate**<br>*(편향 교정률)* | 사용자가 인지하지 못한(또는 잘못 알고 있는) 손실의 '진짜 원인'을 찾아낸 비율.<br>*(단순 공감이 아닌 통찰력 제공 여부)* | `Count(AI_Cause != User_Belief) / Total_Cases`<br>*(Golden Dataset 정답지 비교)* | **> 40%** |
| **Time-to-Insight Efficiency**<br>*(분석 효율성)* | 인간이 직접 뉴스/공시를 분석할 때 대비 시간을 얼마나 단축시켰는지에 대한 효율성 지표. | `(Human_Avg_Time(30m) - AI_Latency) / Human_Avg_Time * 100` | **> 99%**<br>(15초 이내) |
| **Actionability Score**<br>*(실행 가능성)* | 분석 결과가 단순한 현상 설명이 아니라, '다음 행동'으로 이어질 수 있는 구체적인 지침을 포함하는지 평가. | **LLM-as-a-Judge:**<br>제안된 학습/행동의 구체성을 1-5점 척도로 평가 | **> 4.2** |

### **Tier 2: Reliability & Trust (금융 도메인 특화 신뢰 지표)**
*"AI의 분석을 믿고 내 돈을 맡길 수 있는가?"*

| 매트릭 명 (Metric Name) | 정의 및 목적 (Definition) | 측정 공식/방법 (Measurement Method) | 목표치 (Target) |
|:---:|:---|:---|:---:|
| **Zero-Anachronism Rate**<br>*(시점 오류 제로)* | **[Hard Constraint]** 미래 시점의 정보가 과거 분석에 개입되는 '룩어헤드 편향(Look-ahead Bias)'이 0%임을 보증. | `(Valid_Date_News / Total_Retrieved_News) * 100`<br>*(매수/매도일 기준 엄격한 필터링)* | **100%** |
| **Signal-to-Noise Ratio**<br>*(신호 대 잡음비)* | 검색된 뉴스 중 주가 변동에 실질적 영향을 준 '핵심 뉴스(Signal)'의 비율.<br>*(금융 데이터의 노이즈 제거 능력)* | `Count(High_Impact_News) / Total_Retrieved_News`<br>*(LLM 판별: 주가 영향도 유무)* | **> 70%** |
| **Fact-Consistency Score**<br>*(팩트 정합성)* | 뉴스 원문(Fact)과 에이전트의 요약/판단이 모순되지 않는지 종합 평가.<br>*(Hallucination 방지)* | **RAGAS (Faithfulness) & LLM Judge**<br>원문 지지율 측정 | **> 95%** |

### **Tier 3: System Stability (기본적인 엔지니어링 완성도)**
*"서비스가 중단 없이 매끄럽게 돌아가는가?"*

| 매트릭 명 (Metric Name) | 정의 및 목적 (Definition) | 측정 공식/방법 (Measurement Method) | 목표치 (Target) |
|:---:|:---|:---|:---:|
| **E2E Latency** | 전체 워크플로우(검색-분석-생성) 완료 시간 | `Timestamp(End) - Timestamp(Start)` | **< 15s (P95)** |
| **JSON Stability Rate** | 프론트엔드 연동을 위한 JSON 스키마 준수율 | `100 - Parsing_Error_Rate` | **> 99%** |

---

## 2. 고도화된 검증 방법론 (Advanced Validation)

### A. Blind Spot Detection (맹점 발견) 검증 로직

단순히 정답을 맞혔느냐가 아니라, **"사용자의 잘못된 믿음을 지적하고 교정했는가"**를 측정하여 서비스의 차별점을 증명합니다.

```python
# Pseudo-code for Blind Spot Evaluation
def evaluate_blind_spot(user_belief, ai_conclusion, ground_truth):
    """
    Case 1: AI가 정답이고, 사용자 믿음이 틀렸을 때 -> Insight (성공)
    Case 2: AI가 정답이고, 사용자 믿음도 맞았을 때 -> Confirmation (중립)
    Case 3: AI가 틀렸을 때 -> Failure (실패)
    """
    is_ai_correct = compare_similarity(ai_conclusion, ground_truth) > 0.9
    is_user_biased = compare_similarity(user_belief, ground_truth) < 0.5

    if is_ai_correct and is_user_biased:
        return 1.0  # Blind Spot Detected (High Value)
    elif is_ai_correct and not is_user_biased:
        return 0.5  # Simple Assistant
    else:
        return 0.0
```

### B. Signal-to-Noise Ratio (SNR) 측정

금융 뉴스는 "단순 시황 중계(Noise)"가 80% 이상입니다. 이를 거르고 "이슈(Signal)"만 잡았는지 확인합니다.

**Method:** 검색된 Top-K 뉴스 청크 각각에 대해 LLM에게 질문

**Prompt:** "이 뉴스가 해당 날짜의 주가 등락 원인이 될 수 있는 결정적 사건(Event)입니까?" (Yes/No)

**Formula:** Yes 응답 수 / 전체 검색된 청크 수

---

## 3. 검증 시나리오 (Golden Dataset) - Showcase

심사위원에게 보여줄 대표적인 "AI가 사람을 이기는 순간" 시나리오입니다.

### Scenario A: "The Hidden Truth" (정보 비대칭 해소)

**상황:** 사용자는 단순히 "시장 분위기가 안 좋아서(Macro) 떨어졌다"고 믿고 분석 요청.

**AI 발견 (Blind Spot):** 시장 지수는 상승했으나, 해당 기업의 **CEO 횡령 뉴스(Governance Issue)**가 당일 장 마감 직전 보도되었음을 찾아냄.

**평가 포인트:** 사용자의 '시장 탓' 믿음을 '개별 악재'로 교정 → Insight Score 획득.

### Scenario B: "The Time Traveler" (시점 오류 방지 증명)

**상황:** 2022년 12월의 손실 분석 요청. (당시엔 실적 발표 전)

**일반 챗봇 오류:** 2023년 1월에 발표된 "실적 쇼크" 뉴스를 가져와서 분석하는 '미래 정보 참조' 오류 범함.

**WildCard-W:** 매수~매도 기간(Window) 필터링을 통해 2023년 뉴스를 **완벽히 차단(Block)**하고, 당시의 뉴스만으로 분석.

**평가 포인트:** Zero-Anachronism 100% 달성.

---

## 4. 정성적 평가 (Qualitative Evaluation)

정량적 지표를 보완하기 위해, 베타 테스터(또는 모의 투자자) 대상 설문 결과를 매트릭에 포함합니다.

| 평가 지표 | 정의 | 목표치 |
|:---:|:---|:---:|
| **Trust Score (신뢰도)** | "이 분석 결과를 보고 실제 매매 전략을 수정하시겠습니까?" (Yes/No 비율) | **> 80%** |
| **Clarity Score (명확성)** | "AI가 제시한 원인이 금융 지식이 부족해도 이해하기 쉬운가?" (1-5점) | **> 4.0** |