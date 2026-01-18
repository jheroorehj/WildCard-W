from typing import Any, Dict, List



from langchain_core.messages import HumanMessage, SystemMessage



from core.llm import get_solar_chat, invoke_with_usage

from utils.json_parser import parse_json



from .prompt import NODE10_REPORT_PROMPT





def node10_learning_tutor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node10: N8/N9 결과를 기반으로 투자 학습 튜터 출력을 생성합니다.
    """
    payload = {
        "n8_loss_cause_analysis": state.get("n8_loss_cause_analysis"),
        "n8_market_context_analysis": state.get("n8_market_context_analysis"),
        "n9_input": state.get("n9_input"),
        "learning_pattern_analysis": state.get("learning_pattern_analysis"),
    }


    llm = get_solar_chat()

    messages = [

        SystemMessage(content=NODE10_REPORT_PROMPT),

        HumanMessage(content=f"Write the report using this input:\n{payload}"),

    ]



    llm_usage = None
    try:
        raw, llm_usage = invoke_with_usage(llm, messages)
    except Exception as exc:
        return {"n10_loss_review_report": _fallback(f"LLM 호출 실패: {exc}")}



    parsed = parse_json(raw)

    if not isinstance(parsed, dict):

        return {"n10_loss_review_report": _fallback("JSON 파싱 실패")}



    normalized = _normalize(parsed)
    if llm_usage:
        normalized["llm_usage"] = llm_usage
    return {"n10_loss_review_report": normalized}


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    tutor = data.get("learning_tutor")
    if isinstance(tutor, dict):
        return {"learning_tutor": _normalize_learning_tutor(tutor)}

    if _looks_like_tutor(data):
        return {"learning_tutor": _normalize_learning_tutor(data)}

    return {"learning_tutor": _normalize_learning_tutor({})}




def _coerce_list(value: Any) -> List[str]:

    if isinstance(value, list):

        return [str(item) for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():

        return [value]

    return []





def _normalize_learning_tutor(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    custom_path = value.get("custom_learning_path")
    if not isinstance(custom_path, dict):
        custom_path = {}
    advisor = value.get("investment_advisor")
    if not isinstance(advisor, dict):
        advisor = {}
    return {
        "custom_learning_path": {
            "path_summary": str(custom_path.get("path_summary", "")),
            "learning_materials": _coerce_list(custom_path.get("learning_materials")),
            "practice_steps": _coerce_list(custom_path.get("practice_steps")),
            "recommended_topics": _coerce_list(custom_path.get("recommended_topics")),
        },
        "investment_advisor": {
            "advisor_message": str(advisor.get("advisor_message", "")),
            "recommended_questions": _coerce_list(advisor.get("recommended_questions")),
        },
        "uncertainty_level": value.get("uncertainty_level", "high"),
    }


def _fallback(reason: str) -> Dict[str, Any]:
    return {
        "learning_tutor": {
            "custom_learning_path": {
                "path_summary": "학습 경로를 생성하지 못했습니다.",
                "learning_materials": [],
                "practice_steps": [],
                "recommended_topics": [],
            },
            "investment_advisor": {
                "advisor_message": f"튜터 메시지를 생성하지 못했습니다. ({reason})",
                "recommended_questions": [],
            },
            "uncertainty_level": "high",
        }
    }


def _looks_like_tutor(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "custom_learning_path" in value:
        return True
    if "investment_advisor" in value:
        return True
    return False
