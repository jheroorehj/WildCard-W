from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat
from utils.json_parser import parse_json
from utils.validator import validate_action_missions, validate_if_then_plan, validate_learning_frame

from .prompt import NODE10_REPORT_PROMPT


# 편향별 If-Then 플랜 템플릿
IF_THEN_TEMPLATES = {
    "confirmation_bias": {
        "trigger_situation": "매수 버튼을 누르기 직전",
        "trigger_emotion": "확신이 들 때",
        "then_action": "검색창에 '[종목명] 리스크'를 검색한다",
        "commitment_phrase": "만약 매수 버튼을 누르려 할 때, 그때는 반드시 리스크 1개를 먼저 검색한다",
    },
    "loss_aversion": {
        "trigger_situation": "손실률이 -5%에 도달했을 때",
        "trigger_emotion": "불안할 때",
        "then_action": "매매 일지를 펼치고 원래 계획을 다시 읽는다",
        "commitment_phrase": "만약 손실률 -5%에 도달하면, 그때는 매매 일지를 먼저 확인한다",
    },
    "fomo": {
        "trigger_situation": "급등 뉴스를 발견했을 때",
        "trigger_emotion": "조급할 때",
        "then_action": "스마트폰에 24시간 타이머를 설정한다",
        "commitment_phrase": "만약 급등 종목을 발견하면, 그때는 24시간 타이머를 먼저 설정한다",
    },
    "herding_effect": {
        "trigger_situation": "'다들 산다'는 생각이 들 때",
        "trigger_emotion": "불안하거나 소외감을 느낄 때",
        "then_action": "메모장에 나만의 매수 이유 1문장을 적는다",
        "commitment_phrase": "만약 남들 따라 사고 싶을 때, 그때는 나만의 이유 1문장을 먼저 적는다",
    },
    "anchoring_effect": {
        "trigger_situation": "전고점 가격과 비교하고 있을 때",
        "trigger_emotion": "아쉬울 때",
        "then_action": "현재 기업의 PER, PBR을 검색해 확인한다",
        "commitment_phrase": "만약 전고점을 떠올리면, 그때는 현재 밸류에이션을 먼저 확인한다",
    },
    "overconfidence": {
        "trigger_situation": "'내 감이 맞다'는 생각이 들 때",
        "trigger_emotion": "자신감이 넘칠 때",
        "then_action": "최근 투자 1건의 결과를 기록에서 확인한다",
        "commitment_phrase": "만약 강한 확신이 들면, 그때는 최근 투자 기록을 먼저 확인한다",
    },
    "disposition_effect": {
        "trigger_situation": "수익 중인 종목을 빨리 팔고 싶을 때",
        "trigger_emotion": "불안할 때",
        "then_action": "원래 설정한 목표가를 확인한다",
        "commitment_phrase": "만약 익절하고 싶어지면, 그때는 원래 목표가를 먼저 확인한다",
    },
}

# 편향별 강점 매핑 (mistake_reframe용)
BIAS_STRENGTHS = {
    "confirmation_bias": "빠른 정보 반응력",
    "loss_aversion": "신중한 리스크 인식",
    "fomo": "시장 트렌드 감지력",
    "herding_effect": "정보 수집 적극성",
    "anchoring_effect": "과거 데이터 활용 능력",
    "overconfidence": "결단력 있는 실행력",
    "disposition_effect": "수익 실현에 대한 민감성",
}



def node10_learning_tutor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node10: N8/N9 결과를 기반으로 투자 학습 튜터 출력을 생성합니다.
    행동경제학 기반 넛지(If-Then 플랜, 프레이밍 효과)를 포함합니다.
    """
    # N9에서 받은 learning_pattern_analysis
    learning_pattern = state.get("learning_pattern_analysis", {})
    n8_loss_cause = state.get("n8_loss_cause_analysis", {})
    n9_input = state.get("n9_input", {})

    # === 토큰 최적화: 핵심 정보만 추출 (~300 tokens) ===
    optimized_payload = _extract_optimized_input(
        learning_pattern=learning_pattern,
        n8_loss_cause=n8_loss_cause,
        n9_input=n9_input,
        state=state,
    )

    llm = get_solar_chat()
    llm_with_config = llm.bind(max_tokens=4096)

    messages = [
        SystemMessage(content=NODE10_REPORT_PROMPT),
        HumanMessage(content=f"다음 핵심 정보를 기반으로 분석해주세요:\n{optimized_payload}"),
    ]

    try:
        response = llm_with_config.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        return {"n10_loss_review_report": _fallback(f"LLM 호출 실패: {exc}", learning_pattern, n8_loss_cause)}



    parsed = parse_json(raw)

    if not isinstance(parsed, dict):
        return {"n10_loss_review_report": _fallback("JSON 파싱 실패", learning_pattern, n8_loss_cause)}

    return {"n10_loss_review_report": _normalize(parsed, learning_pattern, n8_loss_cause)}


def _normalize(
    data: Dict[str, Any],
    learning_pattern: Dict[str, Any] = None,
    n8_loss_cause: Dict[str, Any] = None,
) -> Dict[str, Any]:
    tutor = data.get("learning_tutor")
    if isinstance(tutor, dict):
        return {"learning_tutor": _normalize_learning_tutor(tutor, learning_pattern, n8_loss_cause)}

    if _looks_like_tutor(data):
        return {"learning_tutor": _normalize_learning_tutor(data, learning_pattern, n8_loss_cause)}

    return {"learning_tutor": _normalize_learning_tutor({}, learning_pattern, n8_loss_cause)}




def _coerce_list(value: Any) -> List[str]:

    if isinstance(value, list):

        return [str(item) for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():

        return [value]

    return []





def _normalize_learning_tutor(
    value: Any,
    learning_pattern: Dict[str, Any] = None,
    n8_loss_cause: Dict[str, Any] = None,
) -> Dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    custom_path = value.get("custom_learning_path")
    if not isinstance(custom_path, dict):
        custom_path = {}
    advisor = value.get("investment_advisor")
    if not isinstance(advisor, dict):
        advisor = {}

    # === learning_frame 처리 (신규) ===
    learning_frame = value.get("learning_frame")
    if not validate_learning_frame(learning_frame):
        learning_frame = _generate_fallback_frame(learning_pattern, n8_loss_cause)

    # === action_missions 처리 (if_then_plan 포함) ===
    missions = value.get("action_missions", [])
    if not validate_action_missions(missions):
        missions = _generate_fallback_missions(learning_pattern)
    else:
        # LLM이 생성했지만 if_then_plan이 없는 미션에 폴백 추가
        missions = _ensure_if_then_plans(missions, learning_pattern)

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
        "learning_frame": learning_frame,
        "action_missions": missions,
        "uncertainty_level": value.get("uncertainty_level", "high"),
    }


def _fallback(
    reason: str,
    learning_pattern: Dict[str, Any] = None,
    n8_loss_cause: Dict[str, Any] = None,
) -> Dict[str, Any]:
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
            "learning_frame": _generate_fallback_frame(learning_pattern, n8_loss_cause),
            "action_missions": _generate_fallback_missions(learning_pattern),
            "uncertainty_level": "high",
        }
    }


def _generate_fallback_missions(learning_pattern: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    N9의 learning_pattern_analysis 기반으로 기본 미션 생성 (If-Then 플랜 포함)
    """
    if not learning_pattern:
        learning_pattern = {}

    # N9의 인지 편향 정보 추출
    cognitive = learning_pattern.get("cognitive_analysis", {})
    primary_bias = cognitive.get("primary_bias", {})
    bias_name = primary_bias.get("name", "확증 편향")
    bias_code = learning_pattern.get("investor_character", {}).get("behavioral_bias", "confirmation_bias")

    # 편향별 맞춤 미션 매핑 (난이도를 easy로 낮춤 - Small Win 원칙)
    mission_templates = {
        "confirmation_bias": {
            "title": "반대 의견 1개 찾기",
            "description": "매수하려는 종목의 부정적 의견을 딱 1개만 찾아보세요. 작은 시작이 습관을 바꿉니다.",
            "behavioral_target": "확증 편향 완화",
            "difficulty": "easy",
        },
        "herding_effect": {
            "title": "나만의 매수 이유 1문장 쓰기",
            "description": "'왜 이 종목인가?'에 대해 다른 사람 의견 없이 자신만의 이유를 1문장으로 적어보세요.",
            "behavioral_target": "군중 심리 완화",
            "difficulty": "easy",
        },
        "fomo": {
            "title": "24시간 타이머 설정하기",
            "description": "급등 종목 발견 시 바로 매수하지 말고 스마트폰에 24시간 타이머를 설정하세요.",
            "behavioral_target": "FOMO 완화",
            "difficulty": "easy",
        },
        "loss_aversion": {
            "title": "손절 기준 1개 적기",
            "description": "매수 전에 '이 가격까지 떨어지면 손절한다'는 기준 1개를 메모하세요.",
            "behavioral_target": "손실 회피 완화",
            "difficulty": "easy",
        },
        "anchoring_effect": {
            "title": "현재 PER 확인하기",
            "description": "전고점 가격 대신, 현재 기업의 PER(주가수익비율)을 검색해 확인해보세요.",
            "behavioral_target": "앵커링 효과 완화",
            "difficulty": "easy",
        },
        "overconfidence": {
            "title": "최근 투자 1건 복기하기",
            "description": "가장 최근 투자 결정 1개를 되돌아보고, 예상과 다른 점이 있었는지 확인하세요.",
            "behavioral_target": "자기과신 완화",
            "difficulty": "easy",
        },
        "disposition_effect": {
            "title": "원래 목표가 확인하기",
            "description": "익절하고 싶을 때, 처음 설정한 목표가를 메모에서 찾아 확인하세요.",
            "behavioral_target": "처분 효과 완화",
            "difficulty": "easy",
        },
    }

    # 해당 편향에 맞는 미션 선택 (기본값: 확증 편향)
    template = mission_templates.get(bias_code, mission_templates["confirmation_bias"])
    if_then = IF_THEN_TEMPLATES.get(bias_code, IF_THEN_TEMPLATES["confirmation_bias"])

    return [
        {
            "mission_id": "M001",
            "priority": 1,
            "title": template["title"],
            "description": template["description"],
            "behavioral_target": template["behavioral_target"],
            "expected_outcome": "투자 의사결정 품질 향상",
            "difficulty": template.get("difficulty", "easy"),
            "estimated_impact": "medium",
            "if_then_plan": if_then,
        }
    ]


def _generate_fallback_frame(
    learning_pattern: Dict[str, Any] = None,
    n8_loss_cause: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    N8 손실 원인 + N9 편향 기반으로 기본 learning_frame 생성
    """
    if not learning_pattern:
        learning_pattern = {}
    if not n8_loss_cause:
        n8_loss_cause = {}

    # N8에서 손실 정보 추출
    loss_pct = n8_loss_cause.get("loss_amount_pct", "손실")
    one_line_summary = n8_loss_cause.get("one_line_summary", "투자 경험")

    # N9에서 편향 정보 추출
    cognitive = learning_pattern.get("cognitive_analysis", {})
    primary_bias = cognitive.get("primary_bias", {})
    bias_name = primary_bias.get("name", "인지 편향")
    bias_code = learning_pattern.get("investor_character", {}).get("behavioral_bias", "confirmation_bias")

    # 편향별 강점 매핑
    strength = BIAS_STRENGTHS.get(bias_code, "정보 수집 능력")

    return {
        "loss_reframe": {
            "original": f"{loss_pct} 손실" if loss_pct else "손실 경험",
            "reframed": f"{loss_pct}의 수업료를 내고 '{bias_name}'이라는 중요한 교훈을 배웠습니다",
            "learning_value": "이 경험을 통해 향후 더 큰 손실을 예방하는 통찰을 얻었습니다",
        },
        "mistake_reframe": {
            "original": one_line_summary if one_line_summary else "투자 결정 과정",
            "reframed": f"'{strength}'이라는 강점이 있으나, 보완이 필요한 부분을 발견했습니다",
            "strength_focus": strength,
        },
        "progress_frame": {
            "message": "자신의 투자 패턴을 분석하고 인식한 것 자체가 성장입니다",
            "comparison_anchor": "대부분의 투자자는 자신의 편향을 인식하지 못합니다",
        },
    }


def _ensure_if_then_plans(
    missions: List[Dict[str, Any]],
    learning_pattern: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    LLM이 생성한 미션에 if_then_plan이 없는 경우 폴백 추가
    """
    if not learning_pattern:
        learning_pattern = {}

    bias_code = learning_pattern.get("investor_character", {}).get("behavioral_bias", "confirmation_bias")
    default_if_then = IF_THEN_TEMPLATES.get(bias_code, IF_THEN_TEMPLATES["confirmation_bias"])

    result = []
    for mission in missions:
        if not isinstance(mission, dict):
            continue
        # if_then_plan이 없거나 유효하지 않으면 폴백 추가
        if_then = mission.get("if_then_plan")
        if not validate_if_then_plan(if_then):
            mission = dict(mission)  # 복사본 생성
            mission["if_then_plan"] = default_if_then
        result.append(mission)

    return result


def _extract_optimized_input(
    learning_pattern: Dict[str, Any],
    n8_loss_cause: Dict[str, Any],
    n9_input: Dict[str, Any],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    토큰 최적화: N8/N9 결과에서 핵심 정보만 추출 (~300 tokens)
    """
    # N9에서 핵심 정보 추출
    cognitive = learning_pattern.get("cognitive_analysis", {})
    primary_bias = cognitive.get("primary_bias", {}).get("name", "")
    investor_character = learning_pattern.get("investor_character", {})

    # 취약 지표 추출 (점수 40 이하)
    profile_metrics = learning_pattern.get("profile_metrics", {})
    weak_metrics = [
        key for key, value in profile_metrics.items()
        if isinstance(value, dict) and value.get("score", 100) <= 40
    ]

    # 최상위 의사결정 문제
    decision_problems = learning_pattern.get("decision_problems", [])
    top_problem = decision_problems[0].get("problem_type", "") if decision_problems else ""

    # N8에서 핵심 정보 추출
    loss_summary = n8_loss_cause.get("one_line_summary", "")
    loss_amount_pct = n8_loss_cause.get("loss_amount_pct", "")

    # 투자 원인 (n9_input에서)
    investment_reason = n9_input.get("investment_reason", "")

    # 보유 상태 (state에서 추출 시도)
    position_status = "sold"  # 기본값
    stocks = state.get("stocks", [])
    if stocks and isinstance(stocks, list):
        first_stock = stocks[0] if stocks else {}
        if isinstance(first_stock, dict):
            status = first_stock.get("status", "sold")
            position_status = "holding" if status == "holding" else "sold"

    return {
        "primary_bias": primary_bias,
        "investor_character": investor_character.get("type", ""),
        "behavioral_bias_code": investor_character.get("behavioral_bias", "confirmation_bias"),
        "weak_metrics": weak_metrics,
        "top_decision_problem": top_problem,
        "loss_summary": loss_summary,
        "loss_amount_pct": loss_amount_pct,
        "position_status": position_status,
        "investment_reason": investment_reason[:200] if investment_reason else "",  # 200자 제한
    }


def _looks_like_tutor(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "custom_learning_path" in value:
        return True
    if "investment_advisor" in value:
        return True
    return False
