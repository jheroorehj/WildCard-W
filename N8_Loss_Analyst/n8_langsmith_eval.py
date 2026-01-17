from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict

from langsmith import Client
from langsmith.evaluation import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from N8_Loss_Analyst.n8 import node8_loss_analyst


def _coerce_nested(payload: Any, key: str) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get(key), dict):
        return payload.get(key)
    return payload


def predict(inputs: Dict[str, Any]) -> Dict[str, Any]:
    n6_payload = _coerce_nested(inputs.get("n6_stock_analysis"), "n6_stock_analysis")
    n7_payload = _coerce_nested(inputs.get("n7_news_analysis"), "n7_news_analysis")
    state = {
        "layer1_stock": inputs.get("layer1_stock") or inputs.get("ticker") or "",
        "layer2_buy_date": inputs.get("layer2_buy_date") or inputs.get("buy_date") or "",
        "layer2_sell_date": inputs.get("layer2_sell_date") or inputs.get("sell_date"),
        "layer3_decision_basis": inputs.get("layer3_decision_basis")
        or inputs.get("user_decision_basis")
        or "",
        "n6_stock_analysis": n6_payload,
        "n7_news_analysis": n7_payload,
    }
    return node8_loss_analyst(state)


def n8_eval_evaluator(run, example) -> Dict[str, Any]:
    output = run.outputs or {}
    n8_eval = output.get("n8_eval", {})
    if not isinstance(n8_eval, dict):
        return {"key": "n8_eval", "score": 0, "comment": "missing n8_eval"}

    schema_valid = 1.0 if n8_eval.get("schema_valid") else 0.0
    evidence = _pct_score(n8_eval.get("evidence_coverage_pct"))
    objective = _pct_score(n8_eval.get("objective_signals_coverage_pct"))
    root_causes = _count_score(n8_eval.get("root_causes_count"))
    llm_fact = _pct_score(n8_eval.get("llm_fact_consistency_score"))

    score = round((schema_valid + evidence + objective + root_causes + llm_fact) * 2, 2)
    comment = (
        f"schema={schema_valid}, evidence={evidence}, objective={objective}, "
        f"root_causes={root_causes}, llm_fact={llm_fact}"
    )
    return {"key": "n8_eval", "score": score, "comment": comment}


def _pct_score(value: Any) -> float:
    try:
        return max(min(float(value), 100.0), 0.0) / 100.0
    except (TypeError, ValueError):
        return 0.0


def _count_score(value: Any) -> float:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0.0
    return min(count, 3) / 3


def main() -> None:
    client = Client()
    dataset_name = "n8_loss_cause_eval_v1"

    evaluate(
        predict,
        data=dataset_name,
        evaluators=[n8_eval_evaluator],
        experiment_prefix="n8-eval",
        client=client,
    )


if __name__ == "__main__":
    main()
