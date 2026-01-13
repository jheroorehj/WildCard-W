# -*- coding: utf-8 -*-
from typing import Any, Dict
import json

from core.llm import get_solar_chat, get_upstage_embeddings
from .search_tool import search_news_with_serper

# Repository imports - optional (will be used when available)
try:
    from repository.rdb_repo import RDBRepository
    from repository.vector.vector_repo import ChromaDBRepository
    HAS_REPOSITORY = True
except ImportError:
    HAS_REPOSITORY = False
    print("[WARNING] Repository modules not found. Database features will be disabled.")


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
    user_reason = state.get("layer3_decision_basis", "판단 근거 없음")

    n3_analysis = state.get("n3_loss_analysis", {})
    loss_factors = n3_analysis.get("loss_factors", [])

    search_query = f"{ticker} 악재"
    for factor in loss_factors:
        if factor.get("type") == "information_bias":
            missing_check_hint = factor.get("evidence", {}).get("missing_check", "")
            if missing_check_hint:
                search_query = f"{ticker} {missing_check_hint}"
            break

    print(f"[*] N7 searching for: {search_query} around {buy_date}")

    news_results = search_news_with_serper(search_query, date_range=buy_date, num_results=3)
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

    prompt = f"""
당신은 시장 뉴스 분석가입니다. 사용자의 믿음과 현재 뉴스를 비교해 뉴스 항목을 요약하세요.

입력:
- ticker: {ticker}
- buy_date: {buy_date}
- user_reason: {user_reason}
- news_items: {news_payload}

출력은 JSON만 포함하세요. 다음을 반드시 포함:
1) summary: 전체 시장/뉴스 요약(간단)
2) market_sentiment: index 0-100, label (fear|neutral|greed), description
3) fact_check: user_belief, actual_fact, verdict (mismatch|match|biased)
4) news_summaries: 3개 항목 리스트 (title, source, date, link, summary)

규칙:
- 각 뉴스 요약은 2~3문장으로, 조금 구체적으로 작성(일반론 금지).
- 중립 톤 유지. 투자 조언 금지.
- 뉴스에 정보가 부족하면 그 사실을 요약에 간단히 언급.
""".strip()

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
