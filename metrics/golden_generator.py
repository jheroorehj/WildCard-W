"""
Golden Dataset Generator

반자동 Golden Dataset 생성을 위한 모듈
LLM이 초안을 생성하고 사용자가 검토하는 방식
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import GoldenTestCase, GoldenDataset


# Golden Dataset 저장 경로
GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"


# ============================================
# Golden Dataset 생성 프롬프트
# ============================================
GOLDEN_GENERATION_PROMPT = """당신은 투자 손실 분석 AI 테스트 전문가입니다.
AI 시스템의 '편향 교정 능력'을 테스트하기 위한 Golden Dataset 케이스를 생성해주세요.

## 시나리오 유형: {scenario_type}

### 시나리오 설명
{scenario_description}

## 생성 지침

1. **실제 있을 법한 상황**을 설정하세요
2. **사용자 믿음과 실제 원인의 차이**를 명확히 하세요
3. **검증 가능한 증거**를 포함하세요
4. **한국 주식 시장** 상황을 반영하세요

## 출력 형식 (JSON)

```json
{{
  "id": "TC{case_number:03d}",
  "scenario": "{scenario_type}",
  "description": "시나리오에 대한 한 줄 설명",
  "input": {{
    "layer1_stock": "종목명 (예: 삼성전자, 카카오)",
    "layer2_buy_date": "YYYY-MM-DD",
    "layer2_sell_date": "YYYY-MM-DD",
    "layer3_decision_basis": "사용자가 생각하는 손실 원인 (틀린 믿음)"
  }},
  "ground_truth": {{
    "actual_cause": "실제 손실의 근본 원인",
    "category": "internal 또는 external",
    "subcategory": "세부 카테고리",
    "key_evidence": "핵심 증거 (뉴스, 지표 등)"
  }},
  "user_belief_correct": false,
  "expected_blind_spot_score": 1.0
}}
```

JSON만 출력하세요:"""


# 시나리오 유형별 설명
SCENARIO_DESCRIPTIONS = {
    "hidden_truth": """
**The Hidden Truth (정보 비대칭 해소)**
- 사용자가 "시장 전체가 안 좋아서" 또는 "운이 없어서"라고 생각하지만
- 실제로는 해당 기업의 개별 악재 (실적 쇼크, 경영진 이슈, 소송 등)가 원인
- AI가 사용자의 '시장 탓' 믿음을 '개별 악재'로 교정해야 함
""",
    "time_traveler": """
**The Time Traveler (시점 오류 방지)**
- 매도 시점 이후에 발표된 정보를 원인으로 착각하는 경우
- 예: 2024년 1월 매도했는데, 2024년 2월 발표된 실적을 원인으로 생각
- AI가 시점 필터링을 통해 올바른 시점의 정보만 분석해야 함
""",
    "confirmation_bias": """
**Confirmation Bias (확증 편향)**
- 사용자의 믿음이 부분적으로 맞지만, 더 중요한 원인을 놓치고 있는 경우
- 예: "금리 인상 때문"이라고 생각하지만, 실제로는 동종업계 대비 실적 부진이 더 큰 원인
- AI가 사용자 믿음을 인정하면서도 추가 인사이트를 제공해야 함
""",
    "external_shock": """
**External Shock (외부 충격)**
- 예측 불가능한 외부 요인 (지정학적 리스크, 팬데믹, 자연재해 등)이 원인
- 사용자가 내부 요인을 탓하지만 실제로는 외부 요인이 주요 원인
- AI가 '통제 가능/불가능' 요인을 구분해줘야 함
""",
    "technical_miss": """
**Technical Miss (기술적 분석 실패)**
- 사용자가 기본적 분석에만 의존했지만, 기술적 지표가 명확한 위험 신호를 보냈던 경우
- 예: RSI 과매수, 이동평균 데드크로스 등을 무시
- AI가 기술적 분석의 중요성을 인식시켜야 함
""",
    "herd_behavior": """
**Herd Behavior (군중 심리)**
- 사용자가 "다들 산다고 해서" 매수했다가 손실
- 실제로는 이미 고점에서 매수한 전형적인 FOMO 사례
- AI가 군중 심리의 위험성을 지적해야 함
"""
}


async def generate_golden_case(
    llm,
    scenario_type: str,
    case_number: int
) -> Optional[GoldenTestCase]:
    """
    단일 Golden Dataset 케이스 생성

    Args:
        llm: LLM 인스턴스
        scenario_type: 시나리오 유형
        case_number: 케이스 번호

    Returns:
        생성된 테스트 케이스 또는 None
    """
    description = SCENARIO_DESCRIPTIONS.get(
        scenario_type,
        SCENARIO_DESCRIPTIONS["hidden_truth"]
    )

    prompt = GOLDEN_GENERATION_PROMPT.format(
        scenario_type=scenario_type,
        scenario_description=description,
        case_number=case_number
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content

        # JSON 추출
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            case = json.loads(json_str)
            case["id"] = f"TC{case_number:03d}"
            return case
    except json.JSONDecodeError:
        pass
    except Exception:
        pass

    return None


async def generate_golden_dataset(
    llm,
    count: int = 12,
    scenarios: Optional[List[str]] = None
) -> GoldenDataset:
    """
    Golden Dataset 전체 생성

    Args:
        llm: LLM 인스턴스
        count: 생성할 케이스 수
        scenarios: 사용할 시나리오 유형 리스트 (None이면 모든 유형 사용)

    Returns:
        생성된 Golden Dataset
    """
    if scenarios is None:
        scenarios = list(SCENARIO_DESCRIPTIONS.keys())

    cases: List[GoldenTestCase] = []
    case_number = 1

    # 각 시나리오 유형별로 균등하게 생성
    cases_per_scenario = max(1, count // len(scenarios))

    for scenario in scenarios:
        for _ in range(cases_per_scenario):
            if len(cases) >= count:
                break

            case = await generate_golden_case(llm, scenario, case_number)
            if case:
                cases.append(case)
                case_number += 1

    return {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "test_cases": cases
    }


def save_golden_dataset(dataset: GoldenDataset, filepath: Optional[Path] = None) -> Path:
    """
    Golden Dataset을 파일로 저장

    Args:
        dataset: 저장할 데이터셋
        filepath: 저장 경로 (None이면 기본 경로 사용)

    Returns:
        저장된 파일 경로
    """
    if filepath is None:
        filepath = GOLDEN_DATASET_PATH

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    return filepath


def load_golden_dataset(filepath: Optional[Path] = None) -> Optional[GoldenDataset]:
    """
    Golden Dataset 로드

    Args:
        filepath: 파일 경로 (None이면 기본 경로 사용)

    Returns:
        로드된 데이터셋 또는 None
    """
    if filepath is None:
        filepath = GOLDEN_DATASET_PATH

    if not filepath.exists():
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_golden_dataset() -> GoldenDataset:
    """
    기본 Golden Dataset 반환 (수동 작성된 케이스)

    Returns:
        기본 Golden Dataset
    """
    return {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "test_cases": [
            {
                "id": "TC001",
                "scenario": "hidden_truth",
                "description": "시장 탓이라 생각했지만 실제로는 CEO 횡령 뉴스가 원인",
                "input": {
                    "layer1_stock": "삼성전자",
                    "layer2_buy_date": "2024-01-15",
                    "layer2_sell_date": "2024-02-15",
                    "layer3_decision_basis": "시장 전체가 하락해서 같이 떨어진 것 같다. 코스피도 많이 빠졌으니까."
                },
                "ground_truth": {
                    "actual_cause": "반도체 수요 둔화에 대한 우려와 경쟁사 대비 실적 전망 하향",
                    "category": "external",
                    "subcategory": "market_condition",
                    "key_evidence": "글로벌 반도체 수요 감소 뉴스, 애널리스트 목표가 하향 조정"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 1.0
            },
            {
                "id": "TC002",
                "scenario": "time_traveler",
                "description": "매도 후 발표된 실적을 원인으로 착각",
                "input": {
                    "layer1_stock": "카카오",
                    "layer2_buy_date": "2023-10-01",
                    "layer2_sell_date": "2023-12-15",
                    "layer3_decision_basis": "4분기 실적이 안 좋아서 떨어진 것 같다"
                },
                "ground_truth": {
                    "actual_cause": "매도 시점 기준으로는 규제 리스크와 광고 수익 감소 우려가 주요 원인",
                    "category": "external",
                    "subcategory": "regulatory_risk",
                    "key_evidence": "공정위 조사 뉴스, 광고 시장 둔화 보도 (12월 이전 기사)"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 1.0
            },
            {
                "id": "TC003",
                "scenario": "confirmation_bias",
                "description": "금리 탓이라 생각했지만 더 중요한 원인 존재",
                "input": {
                    "layer1_stock": "네이버",
                    "layer2_buy_date": "2024-03-01",
                    "layer2_sell_date": "2024-04-15",
                    "layer3_decision_basis": "금리가 계속 높아서 성장주가 다 힘든 것 같다"
                },
                "ground_truth": {
                    "actual_cause": "금리 영향도 있지만, 검색 점유율 하락과 AI 경쟁 심화가 더 큰 요인",
                    "category": "internal",
                    "subcategory": "competitive_pressure",
                    "key_evidence": "검색 시장 점유율 데이터, AI 서비스 경쟁 관련 뉴스"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 0.5
            },
            {
                "id": "TC004",
                "scenario": "external_shock",
                "description": "내부 문제라 생각했지만 외부 충격이 원인",
                "input": {
                    "layer1_stock": "현대차",
                    "layer2_buy_date": "2024-02-01",
                    "layer2_sell_date": "2024-03-01",
                    "layer3_decision_basis": "전기차 판매가 기대만큼 안 나온 것 같다. 회사 실력 문제"
                },
                "ground_truth": {
                    "actual_cause": "중동 지정학적 리스크로 인한 물류비 상승과 원자재 가격 급등",
                    "category": "external",
                    "subcategory": "geopolitical_risk",
                    "key_evidence": "홍해 사태 관련 뉴스, 해운비 상승 보도"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 1.0
            },
            {
                "id": "TC005",
                "scenario": "technical_miss",
                "description": "기술적 지표를 무시하고 매수",
                "input": {
                    "layer1_stock": "SK하이닉스",
                    "layer2_buy_date": "2024-01-20",
                    "layer2_sell_date": "2024-02-20",
                    "layer3_decision_basis": "AI 반도체 수요가 늘어날 것 같아서 샀는데 왜 떨어졌는지 모르겠다"
                },
                "ground_truth": {
                    "actual_cause": "매수 시점에 RSI가 80 이상으로 과매수 상태였고, 단기 차익실현 매물 출회",
                    "category": "internal",
                    "subcategory": "judgment_error",
                    "key_evidence": "RSI 과매수 신호, 외국인 순매도 전환 데이터"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 1.0
            },
            {
                "id": "TC006",
                "scenario": "herd_behavior",
                "description": "군중 심리에 휩쓸려 고점 매수",
                "input": {
                    "layer1_stock": "에코프로",
                    "layer2_buy_date": "2023-07-15",
                    "layer2_sell_date": "2023-09-15",
                    "layer3_decision_basis": "다들 이차전지 좋다고 해서 샀는데 갑자기 분위기가 바뀌었다"
                },
                "ground_truth": {
                    "actual_cause": "이미 밸류에이션이 과도하게 높은 상태에서 매수, 전형적인 FOMO 매수",
                    "category": "internal",
                    "subcategory": "behavioral_bias",
                    "key_evidence": "PER 200배 이상, 기관 순매도 지속"
                },
                "user_belief_correct": False,
                "expected_blind_spot_score": 1.0
            }
        ]
    }


def add_manual_case(
    case: GoldenTestCase,
    filepath: Optional[Path] = None
) -> GoldenDataset:
    """
    수동으로 작성한 케이스 추가

    Args:
        case: 추가할 테스트 케이스
        filepath: 파일 경로

    Returns:
        업데이트된 데이터셋
    """
    dataset = load_golden_dataset(filepath)
    if dataset is None:
        dataset = get_default_golden_dataset()

    # 새 ID 부여
    existing_ids = [c["id"] for c in dataset["test_cases"]]
    max_num = max([int(id[2:]) for id in existing_ids] + [0])
    case["id"] = f"TC{max_num + 1:03d}"

    dataset["test_cases"].append(case)
    save_golden_dataset(dataset, filepath)

    return dataset
