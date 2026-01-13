from typing import Any, Dict


def node1_loss_input(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N1: 입력 단계. 실제 UI 입력을 그대로 전달하는 패스스루 노드.
    """
    return dict(state)
