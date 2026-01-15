# LangGraph 기반 State 정의
from typing import TypedDict, Dict


class MainState(TypedDict, total=False):
    # N1: 입력 레이어
    layer1_stock: str
    layer2_buy_date: str
    layer2_sell_date: str
    layer3_decision_basis: str
    user_message: str
    trade_period: Dict[str, object]

    # N6: 기술분석
    n6_stock_analysis: Dict[str, object]

    # N7: 뉴스 요약/시장 상황
    n7_news_analysis: Dict[str, object]

    # N8: 손실 분석 + 시장상황 분석 + N9 입력 요약
    n8_loss_cause_analysis: Dict[str, object]
    n8_market_context_analysis: Dict[str, object]
    n9_input: Dict[str, object]

    # N9: 학습 패턴 분석
    learning_pattern_analysis: Dict[str, object]

    # N10: 최종 리포트
    n10_loss_review_report: Dict[str, object]

    # N4: 채팅 진입
    chat_entry: Dict[str, object]
