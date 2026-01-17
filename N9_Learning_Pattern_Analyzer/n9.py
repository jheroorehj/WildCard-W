from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat
from .prompt import NODE9_SYSTEM_PROMPT
from utils.json_parser import parse_json
from utils.validator import validate_node9


def node9_learning_pattern_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node9: 학습 패턴 분석
    """
    llm = get_solar_chat()

    n9_input = state.get("n9_input")
    if not isinstance(n9_input, dict):
        n9_input = {}

    payload = {
        "investment_reason": n9_input.get("investment_reason")
        or state.get("layer3_decision_basis"),
        "loss_cause_summary": n9_input.get("loss_cause_summary", ""),
        "loss_cause_details": n9_input.get("loss_cause_details", []),
        "objective_signals": n9_input.get("objective_signals", {}),
        "uncertainty_level": n9_input.get("uncertainty_level", "high"),
    }

    messages = [
        SystemMessage(content=NODE9_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                "아래 입력을 바탕으로 학습 패턴 분석을 작성해 주세요.\n"
                "출력은 JSON만 반환하세요.\n"
                f"{payload}"
            )
        ),
    ]

    response = llm.invoke(messages)
    raw = response.content if isinstance(response.content, str) else str(response.content)

    parsed = parse_json(raw)
    if not isinstance(parsed, dict):
        return _fallback()

    if not validate_node9(parsed):
        return _fallback()

    return parsed


def _fallback() -> Dict[str, Any]:
    return {
        "learning_pattern_analysis": {
            "pattern_summary": "투자 판단 패턴을 요약할 정보가 부족합니다.",
            "pattern_strengths": ["핵심 투자 근거를 정리하려는 시도가 있습니다."],
            "pattern_weaknesses": ["검증 정보가 부족해 판단이 흔들릴 수 있습니다."],
            "learning_recommendation": {
                "focus_area": "정보 검증과 객관 지표 확인",
                "learning_reason": "근거 부족으로 판단 오류가 발생할 수 있습니다.",
                "learning_steps": [
                    "핵심 근거를 1~2개로 정리",
                    "객관 지표와 뉴스 사실을 확인",
                    "결정 근거를 기록하고 재점검",
                ],
                "recommended_topics": ["정보 검증", "기술적 지표 기초", "리스크 관리"],
            },
            "uncertainty_level": "high",
        }
    }
