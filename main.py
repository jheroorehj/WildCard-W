from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Set

from N3_Loss_Analyzer.n3 import node3_loss_analyzer

REQUIRED_KEYS: Set[str] = {
    "layer1_stock",
    "layer2_buy_date",
    "layer2_sell_date",
    "layer3_decision_basis",
}


def load_state_from_stdin() -> Dict[str, str]:
    if sys.stdin.isatty():
        print("JSON 한 줄 입력 후 Enter를 눌러주세요.")
        raw = input().strip()
    else:
        raw = sys.stdin.read().strip()

    if not raw:
        raise ValueError("입력이 비었습니다. JSON 객체를 입력해주세요.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"입력된 JSON이 올바르지 않습니다: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("입력 JSON은 객체여야 합니다.")
    return data


def load_state_from_file(path: str) -> Dict[str, str]:
    raw = Path(path).read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("JSON 파일이 비었습니다.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"파일의 JSON이 올바르지 않습니다: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON 파일은 객체여야 합니다.")
    return data


def validate_state(data: Dict[str, str]) -> Dict[str, str]:
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(f"필수 키가 없습니다: {', '.join(missing)}")

    unknown = [key for key in data.keys() if key not in REQUIRED_KEYS]
    if unknown:
        raise ValueError(f"허용되지 않은 키가 있습니다: {', '.join(unknown)}")

    for key in REQUIRED_KEYS:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} 값은 비어있지 않은 문자열이어야 합니다.")

    return data


def main() -> None:
    if len(sys.argv) > 1:
        state = load_state_from_file(sys.argv[1])
    else:
        # Default sample input for quick local runs when no args/stdin are provided.
        if sys.stdin.isatty():
            state = {
                "layer1_stock": "AAPL",
                "layer2_buy_date": "2024-03-12",
                "layer2_sell_date": "2024-04-18",
                "layer3_decision_basis": (
                    "earnings 기대감으로 매수했지만 실적 발표 후 가이던스가 약했고 "
                    "하락 추세 전환으로 손절"
                ),
            }
        else:
            state = load_state_from_stdin()

    state = validate_state(state)
    result = node3_loss_analyzer(state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
