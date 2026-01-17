# -*- coding: utf-8 -*-
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat
from core.db import build_chroma_where, query_chroma_collection
from langsmith.run_helpers import get_current_run_tree
from utils.json_parser import parse_json
from utils.safety import contains_advice
from utils.validator import validate_node8
from metrics.llm_judge import judge_consistency_sync
from metrics.models import METRIC_TARGETS
from .prompt import NODE8_LOSS_ANALYST_PROMPT


def _collect_rag_docs(result: Dict[str, Any]) -> list[str]:
    docs = result.get("documents")
    if not isinstance(docs, list) or not docs:
        return []
    first = docs[0]
    if not isinstance(first, list):
        return []
    return [item for item in first if isinstance(item, str) and item.strip()]


def _build_rag_context(ticker: str, buy_date: str, sell_date: str | None) -> str:
    where = build_chroma_where(ticker=ticker, start_date=buy_date, end_date=sell_date)
    query_text = f"{ticker} {buy_date} {sell_date or ''} loss cause market"
    sections = []
    for name in ("external_news", "stock_metrics", "internal_facts"):
        try:
            result = query_chroma_collection(name, query_text, top_k=3, where=where)
        except Exception:
            continue
        docs = _collect_rag_docs(result)
        if docs:
            sections.append(f"[{name}] " + " | ".join(docs))
    return "\n".join(sections)


def node8_loss_analyst(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N8: loss analyst.
    Uses N6/N7 outputs to derive loss causes and market context.
    """
    ticker = state.get("layer1_stock")
    buy_date = state.get("layer2_buy_date")
    sell_date = state.get("layer2_sell_date")
    rag_context = _build_rag_context(ticker or "", buy_date or "", sell_date)
    payload = {
        "ticker": ticker,
        "buy_date": buy_date,
        "sell_date": sell_date,
        "user_decision_basis": state.get("layer3_decision_basis"),
        "n6_stock_analysis": state.get("n6_stock_analysis"),
        "n7_news_analysis": state.get("n7_news_analysis"),
        "rag_context": rag_context,
    }

    llm = get_solar_chat()
    messages = [
        SystemMessage(content=NODE8_LOSS_ANALYST_PROMPT),
        HumanMessage(content=f"Build JSON using the following input.\n{payload}"),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        return _fallback(f"LLM call failed: {exc}")

    if contains_advice(raw):
        return _fallback("Blocked due to investment advice")

    parsed = parse_json(raw)
    if not isinstance(parsed, dict):
        return _fallback("JSON parse failed")

    if not validate_node8(parsed):
        return _fallback("Output schema validation failed")

    n8_eval = _evaluate_n8_metrics(parsed)
    n8_eval.update(_evaluate_n8_llm_metrics(parsed, state))
    parsed["n8_eval"] = n8_eval
    _record_n8_eval_to_langsmith(n8_eval)
    return parsed


def _fallback(reason: str) -> Dict[str, Any]:
    payload = {
        "n8_loss_cause_analysis": {
            "loss_check": f"분석 생성 실패. ({reason})",
            "loss_amount_pct": "N/A",
            "one_line_summary": "분석을 완료할 수 없습니다.",
            "root_causes": [
                {
                    "id": "RC001",
                    "category": "internal",
                    "subcategory": "judgment_error",
                    "title": "분석 불가",
                    "description": f"손실 원인 분석을 완료할 수 없습니다. 사유: {reason}",
                    "impact_score": 5,
                    "impact_level": "medium",
                    "evidence": [
                        {
                            "source": "n6",
                            "type": "price",
                            "data_point": "데이터 없음",
                            "interpretation": "분석에 필요한 데이터를 수집할 수 없습니다."
                        }
                    ],
                    "timeline_relevance": "throughout"
                },
                {
                    "id": "RC002",
                    "category": "external",
                    "subcategory": "unexpected_event",
                    "title": "데이터 부족",
                    "description": "충분한 시장 데이터를 확보하지 못했습니다.",
                    "impact_score": 5,
                    "impact_level": "medium",
                    "evidence": [
                        {
                            "source": "n7",
                            "type": "news",
                            "data_point": "데이터 없음",
                            "interpretation": "관련 뉴스 데이터를 수집할 수 없습니다."
                        }
                    ],
                    "timeline_relevance": "throughout"
                }
            ],
            "cause_breakdown": {
                "internal_ratio": 50,
                "external_ratio": 50
            },
            "detailed_explanation": f"손실 원인 분석을 완료할 수 없습니다. 사유: {reason}. 다시 시도해 주세요.",
            "confidence_level": "low",
        },
        "n8_market_context_analysis": {
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
    n8_eval = _evaluate_n8_metrics(payload)
    n8_eval.update(_evaluate_n8_llm_metrics(payload, {}))
    payload["n8_eval"] = n8_eval
    _record_n8_eval_to_langsmith(n8_eval)
    return payload


def _evaluate_n8_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    root_causes = []
    loss = data.get("n8_loss_cause_analysis")
    if isinstance(loss, dict):
        root_causes = loss.get("root_causes") if isinstance(loss.get("root_causes"), list) else []

    total_causes = len(root_causes)
    with_evidence = 0
    for cause in root_causes:
        evidence = cause.get("evidence") if isinstance(cause, dict) else None
        if isinstance(evidence, list) and evidence:
            with_evidence += 1

    evidence_coverage = (with_evidence / total_causes * 100) if total_causes else 0.0

    objective = {}
    n9_input = data.get("n9_input")
    if isinstance(n9_input, dict):
        objective = n9_input.get("objective_signals") if isinstance(n9_input.get("objective_signals"), dict) else {}

    tech = objective.get("technical_indicators") if isinstance(objective.get("technical_indicators"), list) else []
    news = objective.get("news_facts") if isinstance(objective.get("news_facts"), list) else []
    coverage_parts = int(bool(tech)) + int(bool(news))
    objective_signals_coverage = (coverage_parts / 2 * 100) if coverage_parts >= 0 else 0.0

    return {
        "schema_valid": validate_node8(data),
        "root_causes_count": total_causes,
        "evidence_coverage_pct": round(evidence_coverage, 2),
        "objective_signals_coverage_pct": round(objective_signals_coverage, 2),
        "has_technical_indicators": bool(tech),
        "has_news_facts": bool(news),
    }


def _evaluate_n8_llm_metrics(
    n8_data: Dict[str, Any],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    news_text = _build_news_text(state.get("n7_news_analysis") or {})
    ai_text = _build_n8_text(n8_data)
    if not news_text or not ai_text:
        return {"llm_fact_consistency_score": None}

    try:
        llm = get_solar_chat()
        score = judge_consistency_sync(llm, news_text, ai_text)
    except Exception:
        return {"llm_fact_consistency_score": None}

    target = METRIC_TARGETS.get("fact_consistency_score", 95.0)
    return {
        "llm_fact_consistency_score": round(score, 2),
        "llm_fact_consistency_passed": score >= target,
    }


def _build_news_text(n7_data: Dict[str, Any]) -> str:
    if not isinstance(n7_data, dict):
        return ""
    context = n7_data.get("news_context")
    if not isinstance(context, dict):
        return ""
    items = context.get("key_headlines")
    if not isinstance(items, list):
        return ""
    parts = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        line = " ".join(part for part in [title.strip(), snippet.strip()] if part)
        if line:
            parts.append(line)
    return "\n".join(parts).strip()


def _build_n8_text(n8_data: Dict[str, Any]) -> str:
    if not isinstance(n8_data, dict):
        return ""
    loss = n8_data.get("n8_loss_cause_analysis")
    if not isinstance(loss, dict):
        return ""
    parts = []
    summary = loss.get("one_line_summary")
    if isinstance(summary, str) and summary.strip():
        parts.append(summary.strip())
    root_causes = loss.get("root_causes")
    if isinstance(root_causes, list):
        for cause in root_causes[:3]:
            if not isinstance(cause, dict):
                continue
            desc = cause.get("description") or cause.get("title")
            if isinstance(desc, str) and desc.strip():
                parts.append(desc.strip())
    return "\n".join(parts).strip()


def _record_n8_eval_to_langsmith(n8_eval: Dict[str, Any]) -> None:
    """
    Attach N8 evaluation metrics to the current LangSmith run if tracing is enabled.
    """
    try:
        run = get_current_run_tree()
        if run:
            run.add_metadata({"n8_eval": n8_eval})
    except Exception:
        # Best-effort only; never fail N8 due to tracing
        return
