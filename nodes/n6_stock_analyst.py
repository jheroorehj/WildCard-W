from typing import Any, Dict

from N6_Stock_Analyst.n6 import node6_stock_analyst


def node6_stock_analyst_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N6: 주가/지표 분석 래퍼
    """
    return node6_stock_analyst(state)
