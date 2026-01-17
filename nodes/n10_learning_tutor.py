from typing import Any, Dict

from N10_Learning_Tutor.n10 import node10_learning_tutor as _node10_learning_tutor


def node10_learning_tutor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N10: 투자 학습 튜터 래퍼
    """
    return _node10_learning_tutor(state)
