"""
Metrics Storage Module

로컬 파일 시스템에 메트릭 결과를 JSON/CSV 형식으로 저장
"""

import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import EvaluationReport, MetricResult


# 메트릭 결과 저장 디렉토리
METRICS_DIR = Path(__file__).parent / "results"


def ensure_metrics_dir() -> Path:
    """메트릭 저장 디렉토리 생성"""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    return METRICS_DIR


def save_metrics_json(report: EvaluationReport) -> Path:
    """
    평가 리포트를 JSON 파일로 저장

    Args:
        report: 평가 리포트

    Returns:
        저장된 파일 경로
    """
    ensure_metrics_dir()

    request_id = report.get("request_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"metrics_{request_id}_{timestamp}.json"
    filepath = METRICS_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filepath


def append_metrics_csv(report: EvaluationReport) -> Path:
    """
    평가 결과를 CSV 파일에 추가 (시계열 분석용)

    Args:
        report: 평가 리포트

    Returns:
        CSV 파일 경로
    """
    ensure_metrics_dir()
    filepath = METRICS_DIR / "metrics_history.csv"

    # CSV 헤더 정의
    fieldnames = [
        "timestamp",
        "request_id",
        "metric_name",
        "tier",
        "value",
        "target",
        "passed",
    ]

    file_exists = filepath.exists()

    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for metric in report.get("metrics", []):
            writer.writerow({
                "timestamp": report.get("timestamp", ""),
                "request_id": report.get("request_id", ""),
                "metric_name": metric.get("metric_name", ""),
                "tier": metric.get("tier", ""),
                "value": metric.get("value", 0),
                "target": metric.get("target", 0),
                "passed": metric.get("passed", False),
            })

    return filepath


def load_metrics_json(request_id: str) -> Optional[EvaluationReport]:
    """
    특정 요청의 메트릭 결과 로드

    Args:
        request_id: 요청 ID

    Returns:
        평가 리포트 또는 None
    """
    ensure_metrics_dir()

    # 해당 request_id로 시작하는 가장 최근 파일 찾기
    pattern = f"metrics_{request_id}_*.json"
    files = list(METRICS_DIR.glob(pattern))

    if not files:
        return None

    # 가장 최근 파일 선택
    latest_file = max(files, key=lambda f: f.stat().st_mtime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_metrics_history(limit: int = 100) -> List[Dict[str, Any]]:
    """
    CSV에서 메트릭 이력 로드

    Args:
        limit: 최대 로드 행 수

    Returns:
        메트릭 이력 리스트
    """
    filepath = METRICS_DIR / "metrics_history.csv"

    if not filepath.exists():
        return []

    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            results.append(row)

    return results


def get_metrics_summary() -> Dict[str, Any]:
    """
    전체 메트릭 통계 요약

    Returns:
        Tier별 평균 통과율 및 통계
    """
    history = load_metrics_history(limit=1000)

    if not history:
        return {"total_evaluations": 0, "tier_stats": {}}

    # Tier별 통계 계산
    tier_stats: Dict[str, Dict[str, Any]] = {
        "impact": {"total": 0, "passed": 0, "metrics": {}},
        "trust": {"total": 0, "passed": 0, "metrics": {}},
        "stability": {"total": 0, "passed": 0, "metrics": {}},
    }

    for row in history:
        tier = row.get("tier", "")
        metric_name = row.get("metric_name", "")
        passed = row.get("passed", "False") == "True"

        if tier in tier_stats:
            tier_stats[tier]["total"] += 1
            if passed:
                tier_stats[tier]["passed"] += 1

            # 메트릭별 통계
            if metric_name not in tier_stats[tier]["metrics"]:
                tier_stats[tier]["metrics"][metric_name] = {"total": 0, "passed": 0}
            tier_stats[tier]["metrics"][metric_name]["total"] += 1
            if passed:
                tier_stats[tier]["metrics"][metric_name]["passed"] += 1

    # 통과율 계산
    for tier in tier_stats:
        total = tier_stats[tier]["total"]
        passed = tier_stats[tier]["passed"]
        tier_stats[tier]["pass_rate"] = (passed / total * 100) if total > 0 else 0

        for metric in tier_stats[tier]["metrics"]:
            m_total = tier_stats[tier]["metrics"][metric]["total"]
            m_passed = tier_stats[tier]["metrics"][metric]["passed"]
            tier_stats[tier]["metrics"][metric]["pass_rate"] = (
                (m_passed / m_total * 100) if m_total > 0 else 0
            )

    # 고유 요청 수 계산
    unique_requests = len(set(row.get("request_id", "") for row in history))

    return {
        "total_evaluations": unique_requests,
        "total_metrics": len(history),
        "tier_stats": tier_stats,
    }
