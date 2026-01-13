from typing import Any, Dict

from N10_Report_Writer.n10 import node10_loss_review_report


def node10_learning_tutor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N10: 투자 학습 튜터 래퍼
    """
    return node10_loss_review_report(state)
