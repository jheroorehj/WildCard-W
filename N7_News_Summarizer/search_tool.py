import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv 

def search_news_with_serper(
    query: str,
    date_range: str = None,
    end_date: str = None,
    num_results: int = 5,
    gl: str | None = None,
    hl: str | None = None,
    date_window_days: int = 14,
) -> List[Dict[str, Any]]:
    """
    Serper API(Google Search)를 사용하여 뉴스를 검색합니다.
    :param query: 검색어 (예: 'NVDA earnings OR NVDA filing')
    :param date_range: 기준 날짜 (YYYY-MM-DD) 또는 기간 문자열
    :param end_date: 종료 날짜 (YYYY-MM-DD, 선택)
    :param num_results: 가져올 뉴스 개수
    :param gl: 지역 코드 (기본: env SERPER_GL 또는 kr)
    :param hl: 언어 코드 (기본: env SERPER_HL 또는 ko)
    :param date_window_days: 기준 날짜에서 앞뒤로 확장할 일수
    :return: 정제된 뉴스 리스트 [{'title': ..., 'link': ..., 'date': ..., 'snippet': ...}]
    """
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("[WARNING] SERPER_API_KEY is missing. Returning mock data.")
        return _get_mock_news_data(query)

    url = "https://google.serper.dev/news"
    gl = gl or os.getenv("SERPER_GL", "kr")
    hl = hl or os.getenv("SERPER_HL", "ko")
    
    # Serper는 'q' 파라미터에 날짜 조건을 직접 넣는 방식이 더 안정적임
    # 예: "NVDA news after:2024-03-01 before:2024-03-31"
    final_query = f"{query}"
    if date_range:
        date_range = str(date_range).strip()
        end_date = str(end_date).strip() if end_date else ""
        try:
            base_start = datetime.strptime(date_range, "%Y-%m-%d")
            start = (base_start - timedelta(days=date_window_days)).strftime("%Y-%m-%d")
            if end_date:
                base_end = datetime.strptime(end_date, "%Y-%m-%d")
                end = base_end.strftime("%Y-%m-%d")
            else:
                end = (base_start + timedelta(days=date_window_days)).strftime("%Y-%m-%d")
            final_query += f" after:{start} before:{end}"
        except ValueError:
            final_query += f" {date_range}"

    payload = json.dumps({
        "q": final_query,
        "num": num_results,
        "gl": gl, # 지역
        "hl": hl  # 언어
    })
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        result = response.json()
        
        news_list = []
        if "news" in result:
            for item in result["news"]:
                news_list.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "date": item.get("date", "Unknown date"),
                    "source": item.get("source"),
                    "snippet": item.get("snippet", "")
                })
        return news_list

    except Exception as e:
        print(f"[ERROR] Serper API request failed: {e}")
        return []

def _get_mock_news_data(query: str) -> List[Dict[str, Any]]:
    """API 키가 없을 때 테스트용 가짜 데이터 반환"""
    return [
        {
            "title": f"[Mock] {query} 관련 주요 뉴스 1",
            "link": "https://example.com/news1",
            "date": "2024-03-08",
            "source": "MockDaily",
            "snippet": "이것은 테스트용 뉴스 요약입니다. 실제 API 연동이 필요합니다."
        },
        {
            "title": f"[Mock] {query} 시장 반응 분석",
            "link": "https://example.com/news2",
            "date": "2024-03-09",
            "source": "MockTimes",
            "snippet": "시장 전문가들은 해당 이슈에 대해 부정적인 견해를 보였습니다."
        }
    ]