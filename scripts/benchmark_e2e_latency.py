import argparse
import json
import statistics
import time
from typing import List, Tuple
from urllib.request import Request, urlopen


DEFAULT_PAYLOAD = {
    "layer1_stock": "AAPL",
    "layer2_buy_date": "2024-03-12",
    "layer2_sell_date": "2024-04-18",
    "position_status": "sold",
    "layer3_decision_basis": "뉴스/미디어 보도, 기업 재무제표 분석",
}


def _summarize(samples: List[float]) -> Tuple[float, float, float, float]:
    if not samples:
        return 0.0, 0.0, 0.0, 0.0
    sorted_samples = sorted(samples)
    avg = statistics.mean(sorted_samples)
    p50 = sorted_samples[int(0.50 * (len(sorted_samples) - 1))]
    p95 = sorted_samples[int(0.95 * (len(sorted_samples) - 1))]
    p99 = sorted_samples[int(0.99 * (len(sorted_samples) - 1))]
    return avg, p50, p95, p99


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=120) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark /v1/analyze latency.")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/v1/analyze",
        help="Target analyze endpoint.",
    )
    parser.add_argument("--runs", type=int, default=5, help="Number of measured runs.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs.")
    parser.add_argument(
        "--payload",
        default="",
        help="JSON payload string (overrides default sample).",
    )
    args = parser.parse_args()

    payload = DEFAULT_PAYLOAD
    if args.payload:
        payload = json.loads(args.payload)

    print("Target:", args.url)
    print("Runs:", args.runs, "Warmup:", args.warmup)
    print("Payload:", json.dumps(payload, ensure_ascii=False))
    print("-" * 60)

    for _ in range(args.warmup):
        _post_json(args.url, payload)

    samples: List[float] = []
    token_samples: List[int] = []
    for i in range(args.runs):
        start = time.perf_counter()
        response = _post_json(args.url, payload)
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
        token_total = None
        if isinstance(response, dict):
            token_usage = response.get("token_usage") or {}
            if isinstance(token_usage, dict):
                total = token_usage.get("total") or {}
                if isinstance(total, dict):
                    token_total = total.get("total_tokens")
        if isinstance(token_total, int):
            token_samples.append(token_total)
            print(f"run {i + 1}: {elapsed:.3f}s tokens={token_total}")
        else:
            print(f"run {i + 1}: {elapsed:.3f}s")

    avg, p50, p95, p99 = _summarize(samples)
    print("-" * 60)
    print(f"avg={avg:.3f}s p50={p50:.3f}s p95={p95:.3f}s p99={p99:.3f}s")
    if token_samples:
        token_avg = statistics.mean(token_samples)
        print(f"token_avg={token_avg:.1f} token_min={min(token_samples)} token_max={max(token_samples)}")


if __name__ == "__main__":
    main()
