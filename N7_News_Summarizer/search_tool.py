import os
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv 

def search_news_with_serper(query: str, date_range: str = None, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Serper API(Google Search)를 사용하여 뉴스를 검색합니다.
    :param query: 검색어 (예: 'NVDA 악재')
    :param date_range: 검색 기간 (예: 'w' (지난주), 'm' (지난달) 또는 특정 날짜 범위 문자열)
    :param num_results: 가져올 뉴스 개수
    :return: 정제된 뉴스 리스트 [{'title': ..., 'link': ..., 'date': ..., 'snippet': ...}]
    """
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("[WARNING] SERPER_API_KEY is missing. Returning mock data.")
        return _get_mock_news_data(query)

    url = "https://google.serper.dev/news"
    
    # Serper는 'q' 파라미터에 날짜 등을 자연어로 섞어 쓰는 것이 효과적일 수 있음
    # 예: "NVDA bad news 2024-03-08"
    final_query = f"{query}"
    if date_range:
        final_query += f" {date_range}"

    payload = json.dumps({
        "q": final_query,
        "num": num_results,
        "gl": "kr", # 지역: 한국
        "hl": "ko"  # 언어: 한국어
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
