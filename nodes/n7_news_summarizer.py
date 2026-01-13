from typing import Any, Dict

from N7_News_Summarizer.n7 import node7_news_summarizer


def node7_news_summarizer_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N7: 뉴스/시장 요약 래퍼
    """
    return node7_news_summarizer(state)
