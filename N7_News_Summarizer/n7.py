# -*- coding: utf-8 -*-
from typing import Any, Dict
import json
import os

from core.llm import get_solar_chat, get_upstage_embeddings, invoke_with_usage
from core.db import build_chroma_where, query_chroma_collection
from .prompt import NODE7_SUMMARY_PROMPT
from .search_tool import search_news_with_serper
from .metrics import evaluate_n7_metrics, persist_n7_metrics
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

# Repository imports - optional (will be used when available)
try:
    from repository.rdb_repo import RDBRepository
    from repository.vector.vector_repo import ChromaDBRepository
    HAS_REPOSITORY = True
except ImportError:
    HAS_REPOSITORY = False
    print("[WARNING] Repository modules not found. Database features will be disabled.")


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
    query_text = f"{ticker} {buy_date} {sell_date or ''} market news"
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


@traceable(name="N7_News_Summarizer")
def node7_news_summarizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N7 에이전트: 뉴스 및 시황 분석 노드
    1. N3 분석 결과에서 검색 키워드 추출
    2. Serper API로 뉴스 검색
    3. 검색 결과를 ChromaDB에 저장 (RAG 대비)
    4. LLM을 사용하여 팩트 체크 및 시황 요약 수행
    5. 분석 결과를 Supabase에 저장
    """

    ticker = state.get("layer1_stock", "Unknown")
    buy_date = state.get("layer2_buy_date", "Unknown")
    sell_date = state.get("layer2_sell_date") or None
    user_reason = state.get("layer3_decision_basis", "판단 근거 없음")

    search_query = (
        f"{ticker} 주가 OR {ticker} 실적 OR {ticker} 공시 OR {ticker} 가이던스 OR "
        f'{ticker} "stock price" OR {ticker} earnings OR {ticker} filing OR {ticker} guidance'
    )

    run = get_current_run_tree()
    metrics_enabled = os.getenv("N7_METRICS_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    if run:
        run.add_metadata(
            {
                "ticker": ticker,
                "buy_date": buy_date,
                "sell_date": sell_date,
                "user_reason": user_reason,
            }
        )

    print(f"[*] N7 searching for: {search_query} around {buy_date}")

    news_results = search_news_with_serper(
        search_query,
        date_range=buy_date,
        end_date=sell_date,
        num_results=3,
    )
    if run:
        run.add_metadata(
            {
                "news_count": len(news_results) if news_results else 0,
                "query": search_query,
                "fallback_used": False,
            }
        )
    if not news_results:
        fallback_query = f"{ticker} 실적 OR 가이던스 OR 리스크 OR 악재 OR 호재"
        print(f"[INFO] N7 fallback search (en/us): {fallback_query} around {buy_date}")
        news_results = search_news_with_serper(
            fallback_query,
            date_range=buy_date,
            end_date=sell_date,
            num_results=3,
            gl="us",
            hl="en",
        )
        if run:
            run.add_metadata({"fallback_used": True, "fallback_query": fallback_query})
    if not news_results:
        print("[WARNING] N7 no news results after fallback search.")
        empty_context = {
            "ticker": ticker,
            "period": {"buy_date": buy_date, "sell_date": state.get("layer2_sell_date")},
            "summary": "관련 뉴스 검색 결과가 없습니다.",
            "market_sentiment": {
                "index": 50,
                "label": "neutral",
                "description": "데이터 부재로 인해 객관적인 시장 심리 판단 불가.",
            },
            "key_headlines": [],
            "news_summaries": [
                {
                    "title": "정보 없음",
                    "source": "N/A",
                    "date": "N/A",
                    "link": "N/A",
                    "summary": "분석 가능한 뉴스 데이터 미제공.",
                }
            ],
            "fact_check": {
                "user_belief": user_reason,
                "actual_fact": "제공된 뉴스 항목 없음.",
                "verdict": "unknown",
            },
            "uncertainty_level": "high",
        }
        if run:
            if metrics_enabled:
                run.add_metadata(
                    {
                        "n7_metrics_summary": {"passed": 0, "total": 5, "score": 0.0},
                    }
                )
            run.add_outputs({"n7_news_analysis": {"news_context": empty_context}})
        return {"n7_news_analysis": {"news_context": empty_context}}
    news_items = [
        {
            "title": n.get("title", ""),
            "source": n.get("source", ""),
            "date": n.get("date", ""),
            "snippet": n.get("snippet", ""),
            "link": n.get("link", ""),
        }
        for n in news_results[:3]
    ]
    rag_context = _build_rag_context(ticker, buy_date, sell_date)

    # ChromaDB 저장 (선택적)
    if HAS_REPOSITORY:
        try:
            v_repo = ChromaDBRepository(collection_name="news_context")
            docs = [f"[{n['source']}] {n['title']}: {n['snippet']}" for n in news_results]
            metadatas = [{"url": n["link"], "date": n["date"]} for n in news_results]

            print(f"[DEBUG] Docs to embed: {len(docs)}")

            # Upstage Embedding 적용
            embedding_model = get_upstage_embeddings()
            embeddings = embedding_model.embed_documents(docs)

            print(f"[DEBUG] Generated embeddings: {len(embeddings)}")

            v_repo.add_documents(
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            print(f"[*] Saved {len(docs)} news items to ChromaDB.")
        except Exception as e:
            print(f"[WARNING] Failed to save news to VectorDB: {e}")
    else:
        print("[INFO] Skipping ChromaDB storage (repository module not available)")


    llm = get_solar_chat()
    news_payload = json.dumps(news_items, ensure_ascii=False)

    prompt = NODE7_SUMMARY_PROMPT.format(
        ticker=ticker,
        buy_date=buy_date,
        sell_date=sell_date or "Unknown",
        user_reason=user_reason,
        news_items=news_payload,
        rag_context=rag_context,
    )

    llm_usage = None
    try:
        content, llm_usage = invoke_with_usage(llm, prompt)
        content = content.replace("```json", "").replace("```", "").strip()
        analysis_json = json.loads(content)
    except Exception as e:
        print(f"[ERROR] LLM analysis failed: {e}")
        analysis_json = {
            "summary": "분석 실패",
            "market_sentiment": {"index": 50, "label": "unknown", "description": ""},
            "fact_check": {"user_belief": user_reason, "actual_fact": "분석 오류", "verdict": "unknown"},
        }

    fallback_news_summaries = [
        {
            "title": n.get("title", ""),
            "source": n.get("source", ""),
            "date": n.get("date", ""),
            "link": n.get("link", ""),
            "summary": n.get("snippet", "") or "",
        }
        for n in news_results[:3]
    ]
    news_summaries = analysis_json.get("news_summaries")
    if not isinstance(news_summaries, list) or not news_summaries:
        news_summaries = fallback_news_summaries

    output_data = {
        "ticker": ticker,
        "period": {"buy_date": buy_date, "sell_date": state.get("layer2_sell_date")},
        "summary": analysis_json.get("summary"),
        "market_sentiment": analysis_json.get("market_sentiment"),
        "key_headlines": news_results[:3],
        "news_summaries": news_summaries,
        "fact_check": analysis_json.get("fact_check"),
        "uncertainty_level": "low",
    }
    if llm_usage:
        output_data["llm_usage"] = llm_usage

    if metrics_enabled:
        report = evaluate_n7_metrics(
            llm=llm,
            ticker=ticker,
            user_reason=user_reason,
            news_results=news_results,
            analysis_json=analysis_json,
            buy_date=buy_date,
            sell_date=sell_date,
        )
        output_data["metrics_summary"] = report.get("summary", {})
        try:
            persist_n7_metrics(report, state.get("request_id"))
        except Exception as exc:
            output_data["metrics_summary"] = {"error": f"persist_failed: {exc}"}

        if run:
            run.add_metadata({"n7_metrics_summary": report.get("summary", {})})
            run.add_outputs({"n7_news_analysis": {"news_context": output_data}})
    elif run:
        run.add_outputs({"n7_news_analysis": {"news_context": output_data}})

    # Supabase 저장 (선택적)
    if HAS_REPOSITORY:
        try:
            case_id = state.get("case_id")
            if case_id:
                r_repo = RDBRepository()
                r_repo.save_market_context(case_id, output_data)
                print(f"[*] N7 results saved to Supabase for case: {case_id}")
        except Exception as e:
            print(f"[WARNING] Failed to save N7 results to Supabase: {e}")
    else:
        print("[INFO] Skipping Supabase storage (repository module not available)")

    return {"n7_news_analysis": {"news_context": output_data}}
