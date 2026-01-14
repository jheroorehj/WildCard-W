from typing import Any, Dict, List


REQUIRED_FIELDS = (
    "layer1_stock",
    "layer2_buy_date",
    "layer2_sell_date",
    "layer3_decision_basis",
)


def node1_input_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node1: 입력값을 통합 스키마 키로 정규화한다.
    """
    normalized = _normalize_payload(state)
    missing = _missing_required(normalized, REQUIRED_FIELDS)
    if missing:
        return {
            "n1_input_error": {
                "message": "missing required input",
                "fields": missing,
            }
        }

    # ???? ??? ?? ??? ?? ??
    return normalized


def _missing_required(state: Dict[str, Any], keys: List[str]) -> List[str]:
    missing = []
    for key in keys:
        value = state.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
    return missing


def _normalize_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    layer1_stock = _normalize_text(state.get("layer1_stock"))
    layer2_buy_date = _normalize_text(state.get("layer2_buy_date"))
    layer2_sell_date = _normalize_text(state.get("layer2_sell_date"))
    layer3_decision_basis = _normalize_text(state.get("layer3_decision_basis"))
    user_message = _normalize_text(state.get("user_message"))
    position_status = _normalize_text(state.get("position_status"))
    if not user_message:
        user_message = layer3_decision_basis
    if position_status not in ("holding", "sold"):
        position_status = ""

    return {
        # 종목명 또는 티커
        "layer1_stock": layer1_stock,
        # 매수 날짜(YYYY-MM-DD)
        "layer2_buy_date": layer2_buy_date,
        # 매도 날짜(YYYY-MM-DD)
        "layer2_sell_date": layer2_sell_date,
        # 의사결정 근거 요약
        "layer3_decision_basis": layer3_decision_basis,
        # 사용자 메시지(없으면 의사결정 근거 복사)
        "user_message": user_message,
        "trade_period": {
            # 매수 날짜(통합 기간 정보)
            "buy_date": layer2_buy_date,
            # 매도 날짜(통합 기간 정보)
            "sell_date": layer2_sell_date,
            # 보유 상태(holding|sold)
            "position_status": position_status,
        },
    }


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()
