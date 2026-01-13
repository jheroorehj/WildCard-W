import json
import re
from typing import Any, Dict, Optional


def parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    LLM 출력에서 JSON만 안전하게 파싱
    우선순위:
    1) ```json ... ``` 코드 블록
    2) 가장 바깥 { ... } 영역
    3) raw JSON 파싱 시도
    """
    if not text:
        return None

    try:
        # 1. ```json ... ``` 블록
        block = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if block:
            return json.loads(block.group(1))

        # 2. 가장 바깥 JSON 객체
        brace = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace:
            return json.loads(brace.group(1))

        # 3. raw JSON 파싱 시도
        return json.loads(text)

    except Exception:
        return None
