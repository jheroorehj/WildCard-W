import argparse
import os
import statistics
import time
from typing import List, Tuple

from langchain_upstage import ChatUpstage


def _parse_models(value: str) -> List[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise ValueError("No models provided.")
    return items


def _summarize(samples: List[float]) -> Tuple[float, float, float, float]:
    if not samples:
        return 0.0, 0.0, 0.0, 0.0
    sorted_samples = sorted(samples)
    avg = statistics.mean(sorted_samples)
    p50 = sorted_samples[int(0.50 * (len(sorted_samples) - 1))]
    p95 = sorted_samples[int(0.95 * (len(sorted_samples) - 1))]
    p99 = sorted_samples[int(0.99 * (len(sorted_samples) - 1))]
    return avg, p50, p95, p99


def _run_single_model(
    model: str,
    api_key: str,
    prompt: str,
    runs: int,
    warmup: int,
) -> List[float]:
    client = ChatUpstage(api_key=api_key, model=model)
    samples: List[float] = []

    for _ in range(warmup):
        client.invoke(prompt)

    for _ in range(runs):
        start = time.perf_counter()
        client.invoke(prompt)
        elapsed = time.perf_counter() - start
        samples.append(elapsed)

    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Upstage chat model latency.")
    parser.add_argument(
        "--models",
        default="solar-pro2,solar-mini",
        help="Comma-separated model list.",
    )
    parser.add_argument("--runs", type=int, default=5, help="Number of measured runs.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per model.")
    parser.add_argument(
        "--prompt",
        default="투자 손실 원인을 한 문장으로 요약해줘.",
        help="Prompt text to send.",
    )
    args = parser.parse_args()

    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise SystemExit("UPSTAGE_API_KEY is not set.")

    models = _parse_models(args.models)

    print("Runs:", args.runs, "Warmup:", args.warmup)
    print("Prompt:", args.prompt)
    print("-" * 60)

    for model in models:
        samples = _run_single_model(
            model=model,
            api_key=api_key,
            prompt=args.prompt,
            runs=args.runs,
            warmup=args.warmup,
        )
        avg, p50, p95, p99 = _summarize(samples)
        print(
            f"{model}: avg={avg:.3f}s p50={p50:.3f}s p95={p95:.3f}s p99={p99:.3f}s"
        )


if __name__ == "__main__":
    main()
