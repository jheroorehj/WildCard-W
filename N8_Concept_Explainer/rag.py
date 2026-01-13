"""
N8 RAG (Retrieval-Augmented Generation) 모듈

경제/주식 용어 지식 베이스 검색 기능
"""

from typing import List, Dict, Any, Optional
import json
import os


class SimpleTermKnowledgeBase:
    """
    간단한 용어 지식 베이스 (인메모리)
    
    TODO: 향후 벡터 DB(Chroma, FAISS)로 교체
    """
    
    def __init__(self):
        self.terms: Dict[str, Dict[str, Any]] = {}
        self._load_default_terms()
    
    def _load_default_terms(self):
        """기본 용어 데이터 로드"""
        default_terms = [
            {
                "term": "볼린저 밴드",
                "keywords": ["볼린저", "밴드", "bollinger", "변동성", "표준편차"],
                "category": "기술적 지표",
                "short_definition": "주가의 변동 범위를 보여주는 지표",
                "detailed_explanation": "볼린저 밴드는 주가가 평균에서 얼마나 벗어났는지를 보여주는 지표입니다. 이동평균선을 중심으로 위아래로 띠(밴드)를 그려서, 주가가 이 범위를 벗어나면 과매수나 과매도 상태로 판단할 수 있습니다.",
                "example": "체온이 36.5도를 중심으로 ±1도 범위 내에 있으면 정상인 것처럼, 주가도 평균 가격 근처의 일정 범위 안에서 움직이는 게 정상입니다.",
                "related_terms": ["이동평균선", "RSI", "과매수", "과매도", "표준편차"]
            },
            {
                "term": "손절매",
                "keywords": ["손절", "손절매", "손실", "매도", "stop loss", "스톱로스"],
                "category": "리스크 관리",
                "short_definition": "손실을 더 키우지 않기 위해 미리 파는 것",
                "detailed_explanation": "손절매는 주식 가격이 떨어져서 손해를 보고 있을 때, 손실이 더 커지기 전에 미리 매도하는 전략입니다. 예를 들어 '10% 떨어지면 무조건 판다'는 규칙을 정해두고, 그 선을 넘으면 감정에 흔들리지 않고 바로 매도하는 것입니다.",
                "example": "물이 새는 배에서 더 많은 물이 들어오기 전에 배를 버리고 구명보트로 갈아타는 것과 같습니다.",
                "related_terms": ["손절선", "스톱로스", "리스크 관리", "물타기"]
            },
            {
                "term": "정보 검증",
                "keywords": ["정보", "검증", "확인", "출처", "신뢰도"],
                "category": "투자 원칙",
                "short_definition": "투자 정보의 신뢰성을 확인하는 과정",
                "detailed_explanation": "정보 검증은 투자 결정을 내리기 전에 받은 정보가 정확하고 신뢰할 만한지 확인하는 과정입니다. 지인 추천, 유튜브, SNS 등에서 얻은 정보는 출처를 확인하고, 공식 공시나 재무제표 같은 1차 자료와 비교해봐야 합니다. 잘못된 정보로 투자하면 큰 손실로 이어질 수 있습니다.",
                "example": "친구가 '이 식당 맛있다'고 해도, 직접 리뷰를 찾아보고 메뉴판을 확인한 뒤 가는 것처럼, 투자 정보도 여러 출처에서 교차 확인해야 합니다.",
                "related_terms": ["공시", "재무제표", "팩트 체크", "1차 자료", "소문"]
            },
            {
                "term": "RSI",
                "keywords": ["RSI", "상대강도지수", "과매수", "과매도", "모멘텀"],
                "category": "기술적 지표",
                "short_definition": "주가 상승/하락 강도를 측정하는 지표",
                "detailed_explanation": "RSI(Relative Strength Index)는 0~100 사이의 숫자로 주가가 얼마나 빠르게 오르고 내리는지를 보여줍니다. 70 이상이면 과매수(너무 많이 올라서 조정 가능), 30 이하면 과매도(너무 많이 떨어져서 반등 가능) 상태로 봅니다. 14일 기간을 주로 사용합니다.",
                "example": "자동차 속도계가 0~200km/h를 표시하는 것처럼, RSI는 주가의 '과열도'를 0~100으로 보여줍니다.",
                "related_terms": ["볼린저 밴드", "MACD", "과매수", "과매도", "모멘텀"]
            },
            {
                "term": "PER",
                "keywords": ["PER", "주가수익비율", "밸류에이션", "고평가", "저평가"],
                "category": "재무 지표",
                "short_definition": "주가가 기업 수익 대비 적정한지 보는 지표",
                "detailed_explanation": "PER(Price Earning Ratio)는 주가를 주당순이익으로 나눈 값입니다. PER이 10이면 '지금 주가로 10년치 수익을 내면 투자금을 회수한다'는 뜻입니다. 낮을수록 저평가, 높을수록 고평가로 볼 수 있지만, 산업마다 적정 PER이 다르므로 같은 업종끼리 비교해야 합니다.",
                "example": "집을 10억에 샀는데 월세가 100만원이면 전세금 회수에 83년(10억/100만원/12개월) 걸리는 것처럼, PER은 투자금 회수 기간을 보여줍니다.",
                "related_terms": ["PBR", "ROE", "EPS", "밸류에이션", "저평가"]
            },
            {
                "term": "분산투자",
                "keywords": ["분산", "포트폴리오", "달걀", "리스크", "다각화"],
                "category": "투자 전략",
                "short_definition": "여러 종목에 나눠서 투자하는 전략",
                "detailed_explanation": "분산투자는 모든 돈을 한 종목에 몰아넣지 않고, 여러 종목이나 자산에 나눠서 투자하는 것입니다. 한 종목이 크게 떨어져도 다른 종목이 버텨주면 전체 손실을 줄일 수 있습니다. '계란을 한 바구니에 담지 마라'는 격언이 대표적입니다.",
                "example": "시험 과목을 5개 다 공부하면 한 과목이 어려워도 다른 과목으로 만회할 수 있는 것처럼, 투자도 여러 종목에 분산하면 리스크를 줄일 수 있습니다.",
                "related_terms": ["포트폴리오", "리스크 관리", "자산 배분", "달걀 바구니"]
            }
        ]
        
        for term_data in default_terms:
            term_name = term_data["term"]
            self.terms[term_name.lower()] = term_data
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        용어 검색 (간단한 키워드 매칭)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 개수
        
        Returns:
            관련 용어 리스트
        """
        query_lower = query.lower()
        results = []
        
        for term_name, term_data in self.terms.items():
            # 용어명 직접 매칭
            if query_lower in term_name:
                results.append({"score": 1.0, "data": term_data})
                continue
            
            # 키워드 매칭
            keywords = term_data.get("keywords", [])
            for keyword in keywords:
                if query_lower in keyword.lower() or keyword.lower() in query_lower:
                    results.append({"score": 0.8, "data": term_data})
                    break
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return [r["data"] for r in results[:top_k]]
    
    def get_term(self, term: str) -> Optional[Dict[str, Any]]:
        """
        특정 용어 직접 조회
        
        Args:
            term: 용어명
        
        Returns:
            용어 데이터 또는 None
        """
        return self.terms.get(term.lower())
    
    def add_term(self, term_data: Dict[str, Any]):
        """
        새로운 용어 추가
        
        Args:
            term_data: 용어 데이터 딕셔너리
        """
        term_name = term_data.get("term", "")
        if term_name:
            self.terms[term_name.lower()] = term_data


# 전역 지식 베이스 인스턴스 (싱글톤 패턴)
_knowledge_base = None


def get_knowledge_base() -> SimpleTermKnowledgeBase:
    """지식 베이스 싱글톤 인스턴스 반환"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = SimpleTermKnowledgeBase()
    return _knowledge_base


def search_term_in_knowledge_base(term: str) -> str:
    """
    지식 베이스에서 용어 검색하여 컨텍스트 반환
    
    Args:
        term: 검색할 용어
    
    Returns:
        검색된 컨텍스트 문자열 (RAG용)
    """
    kb = get_knowledge_base()
    
    # 1. 정확한 용어 매칭 시도
    exact_match = kb.get_term(term)
    if exact_match:
        context = f"""
[지식 베이스 검색 결과]
용어: {exact_match['term']}
카테고리: {exact_match['category']}
정의: {exact_match['short_definition']}
상세 설명: {exact_match['detailed_explanation']}
예시: {exact_match['example']}
연관 용어: {', '.join(exact_match['related_terms'])}
"""
        return context.strip()
    
    # 2. 유사 용어 검색
    similar_terms = kb.search(term, top_k=2)
    if similar_terms:
        context_parts = ["[지식 베이스 유사 용어]"]
        for i, term_data in enumerate(similar_terms, 1):
            context_parts.append(f"\n{i}. {term_data['term']}: {term_data['short_definition']}")
        return "\n".join(context_parts)
    
    return ""
