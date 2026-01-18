from __future__ import annotations

import asyncio
import json
from datetime import datetime, date
from typing import Any, Dict, List, Tuple, Optional
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from N9_Learning_Pattern_Analyzer.n9 import node9_learning_pattern_analyzer
from workflow.graph import build_graph
from app.service.embedding_service import EmbeddingService
from core.db import get_chroma_collection, get_supabase_client
from core.llm import get_solar_chat
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from utils.json_parser import parse_json
from app.quiz_prompt import QUIZ_SYSTEM_PROMPT

# Metrics imports
from metrics.evaluator import MetricsEvaluator, evaluate_basic_metrics
from metrics.storage import load_metrics_json, get_metrics_summary, load_metrics_history
from metrics.tier2_trust import parse_news_date


class AnalyzeRequest(BaseModel):
    layer1_stock: str
    layer2_buy_date: str
    layer2_sell_date: str
    layer3_decision_basis: str
    position_status: str | None = None
    user_message: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    history: List[ChatMessage] = []
    message: str


class QuizRequest(BaseModel):
    learning_pattern_analysis: Dict[str, Any]


app = FastAPI(title="WildCard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_embedding_service: EmbeddingService | None = None
_graph = build_graph()


def _get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_usage(usage: Dict[str, Any]) -> Dict[str, int]:
    prompt = _to_int(usage.get("prompt_tokens") or usage.get("input_tokens"))
    completion = _to_int(usage.get("completion_tokens") or usage.get("output_tokens"))
    total = _to_int(usage.get("total_tokens") or usage.get("total"))
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    normalized: Dict[str, int] = {}
    if prompt is not None:
        normalized["prompt_tokens"] = prompt
    if completion is not None:
        normalized["completion_tokens"] = completion
    if total is not None:
        normalized["total_tokens"] = total
    return normalized


def _collect_token_usage(result: Dict[str, Any]) -> Dict[str, Any]:
    usages: Dict[str, Dict[str, int]] = {}
    n6_usage = (
        result.get("n6_stock_analysis", {})
        .get("stock_analysis", {})
        .get("llm_usage")
    )
    if isinstance(n6_usage, dict):
        usages["n6"] = _normalize_usage(n6_usage)
    n7_usage = (
        result.get("n7_news_analysis", {})
        .get("news_context", {})
        .get("llm_usage")
    )
    if isinstance(n7_usage, dict):
        usages["n7"] = _normalize_usage(n7_usage)
    n8_usage = result.get("n8_llm_usage")
    if isinstance(n8_usage, dict):
        usages["n8"] = _normalize_usage(n8_usage)
    n9_usage = result.get("n9_llm_usage")
    if isinstance(n9_usage, dict):
        usages["n9"] = _normalize_usage(n9_usage)
    n10_usage = result.get("n10_loss_review_report", {}).get("llm_usage")
    if isinstance(n10_usage, dict):
        usages["n10"] = _normalize_usage(n10_usage)

    if not usages:
        return {}

    total_prompt = sum(item.get("prompt_tokens", 0) for item in usages.values())
    total_completion = sum(item.get("completion_tokens", 0) for item in usages.values())
    total_tokens = sum(item.get("total_tokens", 0) for item in usages.values())
    totals = {
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
        "total_tokens": total_tokens,
    }

    return {"total": totals, "per_node": usages}


def _save_to_supabase(request_id: str, state: Dict[str, Any], results: Dict[str, Any]) -> None:
    try:
        db = get_supabase_client()
        request_payload = {
            "id": request_id,
            "layer1_stock": state.get("layer1_stock"),
            "layer2_buy_date": state.get("layer2_buy_date"),
            "layer2_sell_date": state.get("layer2_sell_date"),
            "layer3_decision_basis": state.get("layer3_decision_basis"),
            "user_message": state.get("user_message"),
            "raw_input": state,
        }
        db.table("analysis_requests").insert(request_payload).execute()

        result_rows = []
        for node_key in ("n6", "n7", "n8", "n9", "n10"):
            node_result = results.get(node_key)
            if node_result is None:
                continue
            result_rows.append(
                {"request_id": request_id, "node": node_key, "result": node_result}
            )
        if result_rows:
            db.table("analysis_results").insert(result_rows).execute()
    except Exception as exc:
        print(f"[WARNING] Supabase save failed: {exc}")


def _save_to_chroma(request_id: str, state: Dict[str, Any], results: Dict[str, Any]) -> None:
    try:
        embeddings = _get_embedding_service()
        external_news_collection = get_chroma_collection("external_news")
        stock_metrics_collection = get_chroma_collection("stock_metrics")
        internal_facts_collection = get_chroma_collection("internal_facts")

        def _add_docs(collection, docs: List[str], ids: List[str], metas: List[Dict[str, Any]]) -> None:
            if not docs:
                return
            vectors = embeddings.create_embeddings(docs)
            collection.add(ids=ids, documents=docs, embeddings=vectors, metadatas=metas)

        # N7 뉴스 요약/헤드라인 저장 (RAG 대비)
        n7_payload = results.get("n7") or {}
        n7_context: Dict[str, Any] = {}
        if isinstance(n7_payload, dict):
            if isinstance(n7_payload.get("news_context"), dict):
                n7_context = n7_payload.get("news_context", {})
            elif isinstance(n7_payload.get("n7_news_analysis"), dict):
                n7_context = n7_payload.get("n7_news_analysis", {}).get("news_context", {})
        ticker = n7_context.get("ticker") or state.get("layer1_stock")
        news_items = []
        for item in (n7_context.get("news_summaries") or []):
            if not isinstance(item, dict):
                continue
            news_items.append(
                {
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "date": item.get("date"),
                    "source": item.get("source"),
                    "link": item.get("link"),
                }
            )
        for item in (n7_context.get("key_headlines") or []):
            if not isinstance(item, dict):
                continue
            news_items.append(
                {
                    "title": item.get("title"),
                    "summary": item.get("snippet"),
                    "date": item.get("date"),
                    "source": item.get("source"),
                    "link": item.get("link"),
                }
            )

        external_docs = []
        external_ids = []
        external_meta = []
        for idx, item in enumerate(news_items):
            title = item.get("title") or ""
            summary = item.get("summary") or ""
            if not title and not summary:
                continue
            text = f"{title}\n{summary}".strip()
            external_docs.append(text)
            external_ids.append(f"{request_id}:news:{idx}")
            external_meta.append(
                {
                    "request_id": request_id,
                    "ticker": ticker,
                    "date": item.get("date"),
                    "source": item.get("source"),
                    "link": item.get("link"),
                }
            )
        _add_docs(external_news_collection, external_docs, external_ids, external_meta)

        # N6 핵심 지표 요약 저장 (RAG 대비)
        n6_payload = results.get("n6") or {}
        stock_analysis: Dict[str, Any] = {}
        if isinstance(n6_payload, dict):
            if isinstance(n6_payload.get("stock_analysis"), dict):
                stock_analysis = n6_payload.get("stock_analysis", {})
            elif isinstance(n6_payload.get("n6_stock_analysis"), dict):
                stock_analysis = n6_payload.get("n6_stock_analysis", {}).get("stock_analysis", {})
        if isinstance(stock_analysis, dict) and stock_analysis:
            period = stock_analysis.get("period", {})
            price_move = stock_analysis.get("price_move", {})
            trend = stock_analysis.get("trend")
            indicators = stock_analysis.get("indicators") or []
            indicator_text = "; ".join(
                f"{i.get('name')}={i.get('value')}" for i in indicators if isinstance(i, dict)
            )
            summary_text = (
                f"ticker={stock_analysis.get('ticker')}, "
                f"pct_change={price_move.get('pct_change')}, "
                f"trend={trend}, "
                f"indicators={indicator_text}"
            )
            _add_docs(
                stock_metrics_collection,
                [summary_text],
                [f"{request_id}:stock_metrics:0"],
                [
                    {
                        "request_id": request_id,
                        "ticker": stock_analysis.get("ticker") or ticker,
                        "buy_date": period.get("buy_date"),
                        "sell_date": period.get("sell_date"),
                    }
                ],
            )

        # 내부 fact 저장 (검증된 구조 데이터 기반)
        internal_docs = []
        internal_ids = []
        internal_meta = []
        for idx, item in enumerate(news_items):
            title = item.get("title") or ""
            if not title:
                continue
            internal_docs.append(title)
            internal_ids.append(f"{request_id}:fact:news:{idx}")
            internal_meta.append(
                {
                    "request_id": request_id,
                    "ticker": ticker,
                    "date": item.get("date"),
                    "source": item.get("source") or "news",
                    "topic": "news",
                }
            )
        if isinstance(stock_analysis, dict) and stock_analysis:
            fact_text = (
                f"{stock_analysis.get('ticker')} pct_change={price_move.get('pct_change')}, "
                f"trend={trend}"
            )
            internal_docs.append(fact_text)
            internal_ids.append(f"{request_id}:fact:stock:0")
            internal_meta.append(
                {
                    "request_id": request_id,
                    "ticker": stock_analysis.get("ticker") or ticker,
                    "date": period.get("sell_date") or period.get("buy_date"),
                    "source": "indicator",
                    "topic": "stock_metrics",
                }
            )
        _add_docs(internal_facts_collection, internal_docs, internal_ids, internal_meta)
    except Exception as exc:
        print(f"[WARNING] Chroma save failed: {exc}")


@app.get("/v1/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


async def _run_node(name: str, fn: Any, state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(fn, dict(state))
    except Exception as exc:
        return {f"{name}_error": str(exc)}


@app.post("/v1/analyze")
async def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    # 분석 시작 시간 기록
    start_time = datetime.now()

    if hasattr(req, "model_dump"):
        state: Dict[str, Any] = req.model_dump()
    else:
        state = req.dict()
    if not state.get("user_message"):
        state["user_message"] = state.get("layer3_decision_basis", "")
    if state.get("position_status") == "holding" and not state.get("layer2_sell_date"):
        state["layer2_sell_date"] = datetime.utcnow().date().isoformat()

    result = await asyncio.to_thread(_graph.invoke, state)

    # 분석 종료 시간 기록
    end_time = datetime.now()

    request_id = str(uuid4())
    merged: Dict[str, Any] = {"request_id": request_id, **result}

    n8_result = {
        "n8_loss_cause_analysis": result.get("n8_loss_cause_analysis"),
        "n8_market_context_analysis": result.get("n8_market_context_analysis"),
        "n9_input": result.get("n9_input"),
    }

    node_results: Dict[str, Any] = {
        "n6": result.get("n6_stock_analysis"),
        "n7": result.get("n7_news_analysis"),
        "n8": n8_result,
        "n9": result.get("learning_pattern_analysis"),
        "n10": result.get("n10_loss_review_report"),
    }

    await asyncio.to_thread(_save_to_supabase, request_id, state, node_results)
    await asyncio.to_thread(_save_to_chroma, request_id, state, node_results)

    # 메트릭 평가 실행
    metrics_report = await _evaluate_metrics(
        request_id=request_id,
        start_time=start_time,
        end_time=end_time,
        state=state,
        result=result
    )

    # 결과에 메트릭 요약 추가
    if metrics_report:
        merged["metrics_summary"] = metrics_report.get("summary", {})

    token_usage = _collect_token_usage(result)
    if token_usage:
        merged["token_usage"] = token_usage

    return merged


@app.post("/v1/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    context = "\n".join([f"{m.role}: {m.content}" for m in req.history][-10:])
    state = {"user_message": req.message, "context": context}
    result = node9_learning_pattern_analyzer(state)

    llm = get_solar_chat()
    messages: List[Any] = [
        SystemMessage(
            content=(
                "You are an investment learning assistant. "
                "Answer the user's question in Korean in about two sentences. "
                "Keep it concise and avoid buy/sell recommendations."
            )
        )
    ]
    for item in req.history[-10:]:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    messages.append(HumanMessage(content=req.message))

    try:
        response = llm.invoke(messages)
        message = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        message = f"답변을 생성하지 못했습니다. ({exc})"

    return {"message": message, "raw": result}


@app.post("/v1/quiz")
async def quiz(req: QuizRequest) -> Dict[str, Any]:
    payload = {
        "learning_pattern_analysis": req.learning_pattern_analysis,
    }
    llm = get_solar_chat()
    messages = [
        SystemMessage(content=QUIZ_SYSTEM_PROMPT),
        HumanMessage(content=f"입력을 기반으로 JSON만 출력하세요.\n{payload}"),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        return _fallback_quiz(f"LLM 호출 실패: {exc}")

    parsed = parse_json(raw)
    if not isinstance(parsed, dict):
        return _fallback_quiz("JSON 파싱 실패")

    if not _is_valid_quiz(parsed):
        return _fallback_quiz("출력 스키마 검증 실패")

    return parsed


def _fallback_quiz(reason: str) -> Dict[str, Any]:
    return {
        "quiz_set": {
            "quiz_purpose": f"학습 점검 (오류: {reason})",
            "quizzes": [
                {
                    "quiz_id": "Q1",
                    "quiz_type": "multiple_choice",
                    "question": "가장 중요한 손실 원인은 무엇이었나요?",
                    "options": [{"text": "정보 검증 부족"}, {"text": "과도한 자신감"}, {"text": "추세 오판"}, {"text": "손절 규칙 부재"}],
                    "has_fixed_answer": True,
                    "correct_answer_index": 0,
                },
                {
                    "quiz_id": "Q2",
                    "quiz_type": "multiple_choice",
                    "question": "시장 상황에서 가장 영향이 컸던 요소는 무엇이었나요?",
                    "options": [{"text": "금리 변화"}, {"text": "뉴스 충격"}, {"text": "수급 변화"}, {"text": "변동성 급등"}],
                    "has_fixed_answer": True,
                    "correct_answer_index": 0,
                },
                {
                    "quiz_id": "Q3",
                    "quiz_type": "reflection",
                    "question": "다음 거래에서 우선 보완할 행동은 무엇인가요?",
                    "options": [
                        {"text": "진입/청산 기준 정리", "solution": "사전에 체크리스트를 만들고 진입·청산 기준을 문서화하세요."},
                        {"text": "리스크 한도 설정", "solution": "포지션별 최대 손실 범위를 정하고 즉시 적용하세요."},
                        {"text": "외부 신호 확인", "solution": "뉴스/거시 지표로 자신의 판단을 교차 검증하세요."},
                        {"text": "기록과 복기 강화", "solution": "매매 후 기록을 남기고 반복 패턴을 찾아보세요."},
                    ],
                    "has_fixed_answer": False,
                    "solution_required": True,
                },
            ],
        }
    }


def _is_valid_quiz(data: Dict[str, Any]) -> bool:
    quiz_set = data.get("quiz_set")
    if not isinstance(quiz_set, dict):
        return False
    quizzes = quiz_set.get("quizzes")
    if not isinstance(quizzes, list) or len(quizzes) != 3:
        return False
    for quiz in quizzes:
        if not isinstance(quiz, dict):
            return False
        if not isinstance(quiz.get("quiz_id"), str):
            return False
        if quiz.get("quiz_type") not in ("multiple_choice", "reflection"):
            return False
        if not isinstance(quiz.get("question"), str):
            return False
        options = quiz.get("options")
        if not isinstance(options, list) or len(options) != 4:
            return False
        for option in options:
            if not isinstance(option, dict):
                return False
            if not isinstance(option.get("text"), str):
                return False
            if quiz.get("quiz_type") == "reflection":
                if not isinstance(option.get("solution"), str):
                    return False
        if not isinstance(quiz.get("has_fixed_answer"), bool):
            return False
    return True


# ============================================
# Metrics Evaluation Functions & Endpoints
# ============================================

async def _evaluate_metrics(
    request_id: str,
    start_time: datetime,
    end_time: datetime,
    state: Dict[str, Any],
    result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    분석 결과에 대한 메트릭 평가 실행

    LLM이 필요한 메트릭은 별도 호출 없이 기본 메트릭만 평가합니다.
    전체 메트릭은 /v1/metrics/evaluate 엔드포인트로 별도 요청 가능합니다.
    """
    try:
        # 뉴스 데이터 추출
        news_analysis = result.get("n7_news_analysis", {})
        news_context = news_analysis.get("news_context", {})
        key_headlines = news_context.get("key_headlines", [])

        # 날짜 파싱
        buy_date = parse_news_date(state.get("layer2_buy_date", ""))
        sell_date = parse_news_date(state.get("layer2_sell_date", ""))

        # 뉴스 날짜 추출
        news_dates = []
        for headline in key_headlines:
            date_str = headline.get("date", "")
            if date_str:
                parsed = parse_news_date(date_str)
                if parsed:
                    news_dates.append(parsed)

        # JSON 검증 결과 (모든 노드가 결과를 반환했는지)
        validation_results = [
            result.get("n6_stock_analysis") is not None,
            result.get("n7_news_analysis") is not None,
            result.get("n8_loss_cause_analysis") is not None,
            result.get("learning_pattern_analysis") is not None,
            result.get("n10_loss_review_report") is not None,
        ]

        # 기본 메트릭 평가 (LLM 없이 측정 가능한 것들)
        if buy_date and sell_date:
            metrics = evaluate_basic_metrics(
                start_time=start_time,
                end_time=end_time,
                validation_results=validation_results,
                news_dates=news_dates,
                buy_date=buy_date,
                sell_date=sell_date,
                request_id=request_id
            )

            # 요약 생성
            summary = {}
            for tier in ["impact", "trust", "stability"]:
                tier_metrics = [m for m in metrics if m.get("tier") == tier]
                if tier_metrics:
                    passed = sum(1 for m in tier_metrics if m.get("passed", False))
                    summary[tier] = round(passed / len(tier_metrics) * 100, 1)

            total_passed = sum(1 for m in metrics if m.get("passed", False))
            summary["overall"] = round(total_passed / len(metrics) * 100, 1) if metrics else 0

            return {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "summary": summary
            }
    except Exception as exc:
        print(f"[WARNING] Metrics evaluation failed: {exc}")

    return None


@app.get("/v1/metrics/{request_id}")
async def get_metrics(request_id: str) -> Dict[str, Any]:
    """
    특정 요청의 메트릭 결과 조회
    """
    report = load_metrics_json(request_id)
    if report is None:
        return {"error": f"Metrics not found for request_id: {request_id}"}
    return report


@app.get("/v1/metrics")
async def get_all_metrics(
    limit: int = Query(default=100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    전체 메트릭 이력 조회
    """
    history = load_metrics_history(limit=limit)
    return {
        "count": len(history),
        "metrics": history
    }


@app.get("/v1/metrics/summary")
async def metrics_summary() -> Dict[str, Any]:
    """
    전체 메트릭 통계 요약

    Returns:
        Tier별 통과율 및 메트릭별 상세 통계
    """
    return get_metrics_summary()


@app.post("/v1/metrics/evaluate")
async def evaluate_metrics_full(req: AnalyzeRequest) -> Dict[str, Any]:
    """
    LLM Judge를 포함한 전체 메트릭 평가

    분석 실행 후 모든 Tier의 메트릭을 평가합니다.
    LLM 호출이 포함되어 있어 시간이 더 소요됩니다.
    """
    start_time = datetime.now()

    if hasattr(req, "model_dump"):
        state: Dict[str, Any] = req.model_dump()
    else:
        state = req.dict()
    if not state.get("user_message"):
        state["user_message"] = state.get("layer3_decision_basis", "")
    if state.get("position_status") == "holding" and not state.get("layer2_sell_date"):
        state["layer2_sell_date"] = datetime.utcnow().date().isoformat()

    # 분석 실행
    result = await asyncio.to_thread(_graph.invoke, state)
    end_time = datetime.now()

    request_id = str(uuid4())

    # 뉴스 데이터 준비
    news_analysis = result.get("n7_news_analysis", {})
    news_context = news_analysis.get("news_context", {})

    news_data = {
        "ticker": news_context.get("ticker", state.get("layer1_stock", "")),
        "buy_date": state.get("layer2_buy_date"),
        "sell_date": state.get("layer2_sell_date"),
        "items": news_context.get("key_headlines", []),
        "dates": [],
    }

    # 검증 결과
    validation_results = [
        result.get("n6_stock_analysis") is not None,
        result.get("n7_news_analysis") is not None,
        result.get("n8_loss_cause_analysis") is not None,
        result.get("learning_pattern_analysis") is not None,
        result.get("n10_loss_review_report") is not None,
    ]

    # LLM을 사용한 전체 메트릭 평가
    try:
        llm = get_solar_chat()
        evaluator = MetricsEvaluator(llm=llm)

        report = await evaluator.evaluate_all(
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            validation_results=validation_results,
            news_data=news_data,
            analysis_result=result,
            golden_truth=None,  # Golden Dataset은 별도 테스트에서 사용
            save_results=True
        )

        return {
            "request_id": request_id,
            "analysis_result": result,
            "metrics_report": report
        }
    except Exception as exc:
        return {
            "request_id": request_id,
            "error": f"Full metrics evaluation failed: {exc}",
            "analysis_result": result
        }
