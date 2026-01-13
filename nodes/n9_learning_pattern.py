from typing import Any, Dict

from N9_Fallback_Handler.n9 import node9_fallback_handler


def node9_learning_pattern(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N9: 학습 패턴 분석 래퍼
    """
    return node9_fallback_handler(state)
