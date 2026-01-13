# -*- coding: utf-8 -*-
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat
from utils.json_parser import parse_json
from utils.safety import contains_advice
from utils.validator import validate_node8
from .prompt import NODE8_LOSS_ANALYST_PROMPT


def node8_loss_analyst(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N8: ?? ???
    N6/N7 ??? ??? ?? ??? ?? ??? ??? ????.
    """
    payload = {
        "ticker": state.get("layer1_stock"),
        "buy_date": state.get("layer2_buy_date"),
        "sell_date": state.get("layer2_sell_date"),
        "user_decision_basis": state.get("layer3_decision_basis"),
        "n6_stock_analysis": state.get("n6_stock_analysis"),
        "n7_news_analysis": state.get("n7_news_analysis"),
    }

    llm = get_solar_chat()
    messages = [
        SystemMessage(content=NODE8_LOSS_ANALYST_PROMPT),
        HumanMessage(content=f"?? ??? ???? JSON? ?????:\n{payload}"),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        return {"n8_loss_analysis": _fallback(f"LLM ?? ??: {exc}")}

    if contains_advice(raw):
        return {"n8_loss_analysis": _fallback("?? ?? ???? ???")}

    parsed = parse_json(raw)
    if not isinstance(parsed, dict):
        return {"n8_loss_analysis": _fallback("JSON ?? ??")}

    if not validate_node8(parsed):
        return {"n8_loss_analysis": _fallback("?? ??? ?? ??")}

    return {"n8_loss_analysis": parsed}


def _fallback(reason: str) -> Dict[str, Any]:
    return {
        "loss_cause_analysis": {
            "loss_check": f"?? ?? ??? ???? ?????. ({reason})",
            "root_causes": [],
            "one_line_summary": "",
            "detailed_explanation": "",
        },
        "market_context_analysis": {
            "news_at_loss_time": [],
            "market_situation_analysis": "",
            "related_news": [],
        },
        "n9_input": {
            "investment_reason": "",
            "loss_cause_summary": "",
            "loss_cause_details": [],
            "objective_signals": {
                "price_trend": "sideways",
                "volatility_level": "medium",
                "technical_indicators": [],
                "news_facts": [],
            },
            "uncertainty_level": "high",
        },
    }
