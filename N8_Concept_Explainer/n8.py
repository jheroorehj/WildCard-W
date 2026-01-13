from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat
from .prompt import NODE8_SYSTEM_PROMPT
from utils.json_parser import parse_json
from utils.safety import contains_advice


def node8_concept_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node8: 학습 가이드만 제공 (용어 설명 기능 제거)

    입력:
    - investment_pattern: 사용자 투자 패턴
    - loss_causes: 손실 원인 리스트 (선택)
    - context: 추가 맥락 (선택)

    출력:
    - n8_concept_explanation.learning_guide
    """
    return provide_learning_guide(state)


def provide_learning_guide(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    학습 가이드 생성
    """
    llm = get_solar_chat()

    investment_pattern = state.get("investment_pattern") or state.get("layer3_decision_basis")
    loss_causes = state.get("loss_causes", [])
    context = state.get("context", "")

    if not investment_pattern:
        return {"n8_concept_explanation": fallback_result_learning("투자 패턴 정보가 없습니다.")}

    payload = {
        "mode": "learning",
        "investment_pattern": investment_pattern,
        "loss_causes": loss_causes,
        "context": context,
        "n6_stock_analysis": state.get("n6_stock_analysis"),
    }

    messages = [
        SystemMessage(content=NODE8_SYSTEM_PROMPT),
        HumanMessage(content=f"다음 입력으로 학습 가이드를 생성해 주세요.\n{payload}"),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content

        if contains_investment_advice(raw):
            return {"n8_concept_explanation": fallback_result_learning("투자 조언 감지")}

        parsed = parse_json(raw)
        if not parsed:
            return {"n8_concept_explanation": fallback_result_learning("JSON 파싱 실패")}

        if "learning_guide" in parsed:
            return {
                "n8_concept_explanation": {
                    "mode": "learning",
                    "learning_guide": parsed["learning_guide"],
                }
            }

        return {"n8_concept_explanation": fallback_result_learning("learning_guide 없음")}

    except Exception as exc:
        return {"n8_concept_explanation": fallback_result_learning(f"오류: {exc}")}


def fallback_result_learning(reason: str) -> Dict[str, Any]:
    return {
        "mode": "learning",
        "learning_guide": {
            "weakness_summary": "학습 가이드를 생성하지 못했습니다.",
            "weakness_detailed": reason,
            "learning_path_summary": "기본 투자 지식부터 차근히 학습하세요.",
            "learning_path_detailed": {
                "step1": "투자 기초 개념 학습",
                "step2": "기술적 분석 기본 이해",
                "step3": "리스크 관리 원칙 정리",
            },
            "recommended_topics": ["투자 기초", "기술적 분석", "리스크 관리"],
            "estimated_difficulty": "보통",
            "uncertainty_level": "high",
        },
    }
