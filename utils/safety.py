import re
from typing import List

_STRONG_ADVICE_PATTERNS: List[str] = [
    r"(매수|매도|투자)\s*(하세요|해라|하는게|하는 것이|하는\s*편)",
    r"(사라|팔아라|사세요|파세요)",
    r"(수익|손실)\s*(전망|예측)",
    r"(목표가|손절|익절)",
    r"(진입|청산)\s*(하세요|해라|하라)",
]

_SOFT_ADVICE_TERMS: List[str] = [
    r"조언",
    r"권고",
]

_NEGATION_HINTS: List[str] = [
    r"아닙니다",
    r"아니다",
    r"하지\s*않",
    r"금지",
    r"권하지\s*않",
    r"추천하지\s*않",
]


def contains_advice(text: str) -> bool:
    """
    Node3 응답에 '조언/추천/투자' 등 행동 제안이 있으면 True를 반환합니다.
    """

    if not text:
        return False

    for pattern in _STRONG_ADVICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            snippet = text[max(0, match.start() - 12):match.end() + 12]
            if any(re.search(neg, snippet) for neg in _NEGATION_HINTS):
                continue
            return True

    for term in _SOFT_ADVICE_TERMS:
        if re.search(term, text):
            # Allow if the sentence explicitly negates advice.
            window = re.search(term, text)
            if window:
                snippet = text[max(0, window.start() - 12):window.end() + 12]
                if any(re.search(neg, snippet) for neg in _NEGATION_HINTS):
                    continue
            return True

    return False
