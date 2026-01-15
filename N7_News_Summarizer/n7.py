# -*- coding: utf-8 -*-
from typing import Any, Dict
import json

from core.llm import get_solar_chat, get_upstage_embeddings
from .prompt import NODE7_SUMMARY_PROMPT
from .search_tool import search_news_with_serper
from metrics.tier2_trust import parse_news_date
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


def _clamp01(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _calc_zero_anachronism(
    news_results: list, buy_date: str | None, sell_date: str | None
) -> float:
    if not news_results:
        return 0.0
    start = parse_news_date(buy_date or "")
    end = parse_news_date(sell_date or "") if sell_date else None
    if not start:
        return 0.0
    valid = 0
    for item in news_results:
        parsed = parse_news_date(item.get("date", ""))
        if not parsed:
            continue
        if parsed >= start and (end is None or parsed <= end):
            valid += 1
    return round(valid / len(news_results) * 100, 1)


def _judge_n7_quality(
    llm: Any,
    ticker: str,
    user_reason: str,
    news_items: list,
    analysis_json: Dict[str, Any],
) -> Dict[str, Any]:
    payload = {
        "ticker": ticker,
        "user_reason": user_reason,
        "news_items": news_items,
        "summary": analysis_json.get("summary"),
        "news_summaries": analysis_json.get("news_summaries"),
        "fact_check": analysis_json.get("fact_check"),
    }
    prompt = (
        "You are a strict evaluator for financial news summaries.\n"
        "Score the following:\n"
        "1) relevance per item (0~1) to the ticker and user_reason\n"
        "2) faithfulness of the summary to snippets (0~1)\n"
        "3) signal per item (1/0): earnings, guidance, macro, regulatory, risk events\n"
        "4) coverage topics (short labels), unique_count, and score (unique_count/total)\n"
        "Return JSON exactly with keys:\n"
        "relevance.per_item, relevance.avg, faithfulness, signal.per_item, signal.ratio, "
        "coverage.topics, coverage.unique_count, coverage.score, notes\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        response = llm.invoke(prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Judge output is not a dict.")
    except Exception as exc:
        print(f"[WARNING] N7 judge failed: {exc}")
        parsed = {
            "relevance": {"per_item": [], "avg": 0.0},
            "faithfulness": 0.0,
            "signal": {"per_item": [], "ratio": 0.0},
            "coverage": {"topics": [], "unique_count": 0, "score": 0.0},
            "notes": "judge_failed",
        }

    total = max(1, len(news_items))
    rel = parsed.get("relevance", {})
    sig = parsed.get("signal", {})
    cov = parsed.get("coverage", {})

    rel_per = rel.get("per_item") if isinstance(rel, dict) else []
    sig_per = sig.get("per_item") if isinstance(sig, dict) else []

    rel_avg = _clamp01(rel.get("avg") if isinstance(rel, dict) else 0.0)
    faith = _clamp01(parsed.get("faithfulness", 0.0))
    sig_ratio = _clamp01(sig.get("ratio") if isinstance(sig, dict) else 0.0)
    cov_score = _clamp01(cov.get("score") if isinstance(cov, dict) else 0.0)

    if rel_per and len(rel_per) != len(news_items):
        rel_avg = _clamp01(sum(_clamp01(x) for x in rel_per) / len(rel_per))
    if sig_per and len(sig_per) != len(news_items):
        sig_ratio = _clamp01(sum(1 for x in sig_per if int(x) == 1) / len(sig_per))
    if isinstance(cov, dict) and "unique_count" in cov:
        try:
            cov_score = _clamp01(float(cov.get("unique_count", 0)) / total)
        except (TypeError, ValueError):
            cov_score = 0.0

    return {
        "relevance_rate": round(rel_avg * 100, 1),
        "faithfulness": round(faith * 100, 1),
        "signal_to_noise": round(sig_ratio * 100, 1),
        "coverage": round(cov_score * 100, 1),
        "judge_raw": parsed,
    }


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
            run.add_metadata(
                {
                    "n7_zero_anachronism": 0.0,
                    "n7_relevance_rate": 0.0,
                    "n7_faithfulness": 0.0,
                    "n7_signal_to_noise": 0.0,
                    "n7_coverage": 0.0,
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
    )

    try:
        response = llm.invoke(prompt)
        content = response.content.replace("```json", "").replace("```", "").strip()
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

    zero_anachronism = _calc_zero_anachronism(news_results, buy_date, sell_date)
    judge_metrics = _judge_n7_quality(llm, ticker, user_reason, news_results[:3], analysis_json)
    if run:
        run.add_metadata(
            {
                "n7_zero_anachronism": zero_anachronism,
                "n7_relevance_rate": judge_metrics.get("relevance_rate", 0.0),
                "n7_faithfulness": judge_metrics.get("faithfulness", 0.0),
                "n7_signal_to_noise": judge_metrics.get("signal_to_noise", 0.0),
                "n7_coverage": judge_metrics.get("coverage", 0.0),
            }
        )
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
