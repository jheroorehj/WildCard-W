import re
from typing import List

_ADVICE_PATTERNS: List[str] = [
    r"조언",
    r"추천",
    r"(매수|매도|투자)\s*(하세요|해라|하는게|하는 것이)",
    r"(사라|팔아라|사세요|파세요)",
    r"(수익|손실)\s*(전망|예측)",
    r"(목표가|손절|익절)",
]


def contains_advice(text: str) -> bool:
    """
    Node3 응답에 '조언/추천/투자' 등 행동 제안이 있으면 True를 반환합니다.
    """
    if not text:
        return False

    for pattern in _ADVICE_PATTERNS:
        if re.search(pattern, text):
            return True

    return False
