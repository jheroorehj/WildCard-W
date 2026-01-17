from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from dotenv import load_dotenv
from langsmith import Client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env.local")


def _build_input_payload(inputs: Dict[str, Any]) -> Dict[str, Any]:
    state = inputs.get("state") if isinstance(inputs.get("state"), dict) else inputs
    return {
        "ticker": state.get("layer1_stock") or state.get("ticker"),
        "buy_date": state.get("layer2_buy_date") or state.get("buy_date"),
        "sell_date": state.get("layer2_sell_date") or state.get("sell_date"),
        "user_decision_basis": state.get("layer3_decision_basis")
        or state.get("user_decision_basis"),
        "n6_stock_analysis": state.get("n6_stock_analysis"),
        "n7_news_analysis": state.get("n7_news_analysis"),
    }


def _clean_output(outputs: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(outputs)
    cleaned.pop("n8_eval", None)
    return cleaned


def _valid_output(outputs: Dict[str, Any]) -> bool:
    return (
        isinstance(outputs, dict)
        and isinstance(outputs.get("n8_loss_cause_analysis"), dict)
        and isinstance(outputs.get("n9_input"), dict)
    )


def _iter_candidate_runs(client: Client, project: Optional[str], limit: int) -> Iterable[Any]:
    fetch = max(limit * 5, 10)
    return client.list_runs(project_name=project, limit=fetch)


def _seen_runs_path() -> Path:
    return Path(__file__).with_suffix(".runs.json")


def _load_seen_runs() -> Set[str]:
    path = _seen_runs_path()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(data, list):
        return {str(item) for item in data}
    return set()


def _save_seen_runs(seen: Set[str]) -> None:
    path = _seen_runs_path()
    safe = sorted(str(item) for item in seen)
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")


def add_examples(
    dataset_name: str,
    project_name: Optional[str],
    limit: int,
    dry_run: bool,
) -> List[str]:
    client = Client()
    added: List[str] = []
    seen = _load_seen_runs()

    for run in _iter_candidate_runs(client, project_name, limit):
        if run.id in seen:
            continue
        outputs = run.outputs or {}
        if not _valid_output(outputs):
            continue

        inputs = run.inputs or {}
        input_payload = _build_input_payload(inputs)
        output_payload = _clean_output(outputs)

        if dry_run:
            added.append(str(run.id))
        else:
            client.create_example(
                inputs=input_payload,
                outputs=output_payload,
                dataset_name=dataset_name,
            )
            added.append(str(run.id))
            seen.add(str(run.id))

        if len(added) >= limit:
            break

    if not dry_run and added:
        _save_seen_runs(seen)
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Add N8 examples from LangSmith traces.")
    parser.add_argument("--dataset", default="n8_loss_cause_eval_v1")
    parser.add_argument("--project", default=os.getenv("LANGSMITH_PROJECT"))
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    added = add_examples(args.dataset, args.project, args.limit, args.dry_run)
    mode = "dry-run" if args.dry_run else "added"
    print(f"{mode} {len(added)} example(s): {', '.join(added) if added else 'none'}")


if __name__ == "__main__":
    main()
