# LangGraph 기반 State 정의
from typing import TypedDict, Dict


class MainState(TypedDict, total=False):
    # 입력 (레이어 1~3)
    layer1_stock: str
    layer2_buy_date: str
    layer2_sell_date: str
    layer3_decision_basis: str

    # N6 출력
    n6_stock_analysis: Dict[str, object]

    # N7 출력
    n7_news_analysis: Dict[str, object]

    # N8 출력 (손실 분석)
    n8_loss_analysis: Dict[str, object]

    # N9 출력 (학습 패턴 분석)
    learning_pattern_analysis: Dict[str, object]

    # N10 출력 (학습 튜터)
    n10_loss_review_report: Dict[str, object]

    # N4 출력 (채팅 진입)
    n4_chat_entry: Dict[str, object]
