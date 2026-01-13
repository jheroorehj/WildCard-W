# LangGraph 기반 State 정의
from typing import TypedDict, Dict


class MainState(TypedDict, total=False):
    # 입력 (레이어 1~3)
    layer1_stock: str
    layer2_buy_date: str
    layer2_sell_date: str
    layer3_decision_basis: str

    # Node3 출력
    n3_loss_diagnosis: Dict[str, object]

    # Node6 출력
    n6_stock_analysis: Dict[str, object]

    # Node7 출력
    n7_news_analysis: Dict[str, object]

    # Node8 출력
    n8_loss_analysis: Dict[str, object]

    # Node9 출력
    n9_fallback_response: Dict[str, object]

    # Node10 출력
    n10_loss_review_report: Dict[str, object]
