"""
Metrics Evaluator

통합 평가 실행기 - 모든 Tier 메트릭을 한 번에 평가하고 리포트 생성
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import asyncio

from .models import EvaluationReport, MetricResult, GoldenTestCase
from .storage import save_metrics_json, append_metrics_csv
from .tier1_impact import (
    measure_time_efficiency,
    evaluate_blind_spot,
    measure_actionability,
)
from .tier2_trust import (
    measure_zero_anachronism,
    measure_signal_to_noise,
    measure_fact_consistency,
    extract_news_dates,
    parse_news_date,
)
from .tier3_stability import (
    measure_e2e_latency,
    measure_json_stability,
)
from .llm_judge import (
    judge_signal_or_noise,
    judge_actionability,
    judge_consistency,
    calculate_semantic_similarity,
)


class MetricsEvaluator:
    """
    통합 메트릭 평가기

    모든 Tier의 메트릭을 평가하고 리포트를 생성합니다.
    """

    def __init__(self, llm=None):
        """
        Args:
            llm: LLM 인스턴스 (LLM-as-a-Judge용, 없으면 해당 메트릭 스킵)
        """
        self.llm = llm
        self.metrics: List[MetricResult] = []

    async def evaluate_all(
        self,
        request_id: str,
        start_time: datetime,
        end_time: datetime,
        validation_results: List[bool],
        news_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        golden_truth: Optional[Dict[str, Any]] = None,
        save_results: bool = True
    ) -> EvaluationReport:
        """
        모든 Tier 메트릭 동시 평가

        Args:
            request_id: 요청 ID
            start_time: 분석 시작 시간
            end_time: 분석 종료 시간
            validation_results: 각 노드 JSON 검증 결과 리스트
            news_data: 뉴스 데이터 (items, dates, buy_date, sell_date, ticker)
            analysis_result: 분석 결과 (n8_loss_cause_analysis, learning_pattern_analysis 등)
            golden_truth: Golden Dataset 정답 데이터 (선택)
            save_results: 결과 파일 저장 여부

        Returns:
            평가 리포트
        """
        self.metrics = []

        # ============================
        # Tier 3: System Stability
        # ============================

        # E2E Latency
        latency_result = measure_e2e_latency(start_time, end_time, request_id)
        self.metrics.append(latency_result)

        # JSON Stability Rate
        json_stability = measure_json_stability(validation_results, request_id)
        self.metrics.append(json_stability)

        # ============================
        # Tier 2: Reliability & Trust
        # ============================

        # Zero-Anachronism Rate
        buy_date = self._parse_date(news_data.get("buy_date"))
        sell_date = self._parse_date(news_data.get("sell_date"))
        news_dates = news_data.get("dates", [])

        if not news_dates and news_data.get("items"):
            news_dates = extract_news_dates(news_data["items"])

        if buy_date and sell_date:
            anachronism = measure_zero_anachronism(
                news_dates=news_dates,
                buy_date=buy_date,
                sell_date=sell_date,
                request_id=request_id
            )
            self.metrics.append(anachronism)

        # Signal-to-Noise Ratio (LLM 필요)
        if self.llm and news_data.get("items"):
            snr_results = await self._evaluate_snr(news_data, request_id)
            if snr_results:
                self.metrics.append(snr_results)

        # Fact-Consistency Score (LLM 필요)
        if self.llm:
            consistency_result = await self._evaluate_consistency(
                news_data, analysis_result, request_id
            )
            if consistency_result:
                self.metrics.append(consistency_result)

        # ============================
        # Tier 1: Business Impact
        # ============================

        # Time-to-Insight Efficiency
        efficiency = measure_time_efficiency(
            ai_latency_seconds=latency_result["value"],
            request_id=request_id
        )
        self.metrics.append(efficiency)

        # Actionability Score (LLM 필요)
        if self.llm:
            actionability_result = await self._evaluate_actionability(
                analysis_result, request_id
            )
            if actionability_result:
                self.metrics.append(actionability_result)

        # Blind Spot Detection (Golden Dataset 필요)
        if golden_truth:
            blind_spot_result = await self._evaluate_blind_spot(
                analysis_result, golden_truth, request_id
            )
            if blind_spot_result:
                self.metrics.append(blind_spot_result)

        # 리포트 생성
        report = self._create_report(request_id)

        # 결과 저장
        if save_results:
            save_metrics_json(report)
            append_metrics_csv(report)

        return report

    async def _evaluate_snr(
        self,
        news_data: Dict[str, Any],
        request_id: str
    ) -> Optional[MetricResult]:
        """Signal-to-Noise Ratio 평가"""
        news_items = news_data.get("items", [])
        if not news_items:
            return None

        ticker = news_data.get("ticker", "")
        llm_results = []

        for item in news_items[:10]:  # 최대 10개만 평가
            try:
                is_signal, _ = await judge_signal_or_noise(
                    self.llm,
                    ticker=ticker,
                    date=str(item.get("date", "")),
                    news_content=item.get("content", item.get("title", "")),
                    title=item.get("title", "")
                )
                llm_results.append(is_signal)
            except Exception:
                llm_results.append(False)

        return measure_signal_to_noise(news_items, llm_results, request_id)

    async def _evaluate_consistency(
        self,
        news_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        request_id: str
    ) -> Optional[MetricResult]:
        """Fact-Consistency 평가"""
        news_items = news_data.get("items", [])
        ai_analysis = analysis_result.get("n8_loss_cause_analysis", {})

        if not news_items or not ai_analysis:
            return None

        # 원본 뉴스 텍스트 결합
        original_news = "\n".join([
            item.get("content", item.get("title", ""))[:200]
            for item in news_items[:5]
        ])

        # AI 분석 결과 텍스트
        ai_text = str(ai_analysis.get("root_causes", []))[:500]

        try:
            score = await judge_consistency(self.llm, original_news, ai_text)
            return measure_fact_consistency(
                faithfulness_score=score,
                original_sources=[item.get("title", "") for item in news_items[:5]],
                ai_claims=None,
                request_id=request_id
            )
        except Exception:
            return None

    async def _evaluate_actionability(
        self,
        analysis_result: Dict[str, Any],
        request_id: str
    ) -> Optional[MetricResult]:
        """Actionability Score 평가"""
        learning_pattern = analysis_result.get("learning_pattern_analysis", {})
        learning_rec = learning_pattern.get("learning_recommendation", {})

        if not learning_rec:
            return None

        # 학습 추천 내용을 텍스트로 변환
        rec_text = f"""
        Focus Area: {learning_rec.get('focus_area', '')}
        Learning Steps: {learning_rec.get('learning_steps', [])}
        Recommended Topics: {learning_rec.get('recommended_topics', [])}
        """

        try:
            score = await judge_actionability(self.llm, rec_text)
            return measure_actionability(
                llm_score=score,
                learning_recommendation=learning_rec,
                request_id=request_id
            )
        except Exception:
            return None

    async def _evaluate_blind_spot(
        self,
        analysis_result: Dict[str, Any],
        golden_truth: Dict[str, Any],
        request_id: str
    ) -> Optional[MetricResult]:
        """Blind Spot Detection 평가"""
        # 사용자 믿음 (layer3_decision_basis)
        user_belief = golden_truth.get("input", {}).get("layer3_decision_basis", "")

        # AI 결론 (root_causes에서 추출)
        ai_analysis = analysis_result.get("n8_loss_cause_analysis", {})
        root_causes = ai_analysis.get("root_causes", [])
        ai_conclusion = " ".join([
            rc.get("description", rc.get("title", ""))
            for rc in root_causes[:3]
        ])

        # 정답 (ground_truth)
        ground_truth = golden_truth.get("ground_truth", {})
        actual_cause = ground_truth.get("actual_cause", "")

        if not (user_belief and ai_conclusion and actual_cause):
            return None

        try:
            # 유사도 계산
            user_similarity = await calculate_semantic_similarity(
                self.llm, actual_cause, user_belief
            )
            ai_similarity = await calculate_semantic_similarity(
                self.llm, actual_cause, ai_conclusion
            )

            return evaluate_blind_spot(
                user_belief_similarity=user_similarity,
                ai_conclusion_similarity=ai_similarity,
                user_belief=user_belief,
                ai_conclusion=ai_conclusion,
                ground_truth=actual_cause,
                request_id=request_id
            )
        except Exception:
            return None

    def _parse_date(self, date_value: Any) -> Optional[date]:
        """날짜 파싱 헬퍼"""
        if date_value is None:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, str):
            return parse_news_date(date_value)
        return None

    def _create_report(self, request_id: str) -> EvaluationReport:
        """평가 리포트 생성"""
        summary = {}
        for tier in ["impact", "trust", "stability"]:
            tier_metrics = [m for m in self.metrics if m.get("tier") == tier]
            if tier_metrics:
                passed = sum(1 for m in tier_metrics if m.get("passed", False))
                summary[tier] = round(passed / len(tier_metrics) * 100, 1)

        # 전체 통과율
        total_metrics = len(self.metrics)
        total_passed = sum(1 for m in self.metrics if m.get("passed", False))
        summary["overall"] = round(total_passed / total_metrics * 100, 1) if total_metrics > 0 else 0

        return {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "summary": summary
        }


class BatchEvaluator:
    """
    배치 평가기

    Golden Dataset을 사용한 대량 테스트 실행
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.results: List[EvaluationReport] = []

    async def evaluate_golden_dataset(
        self,
        golden_cases: List[GoldenTestCase],
        analysis_function,  # async def analyze(input: dict) -> dict
    ) -> Dict[str, Any]:
        """
        Golden Dataset 전체 평가

        Args:
            golden_cases: 테스트 케이스 리스트
            analysis_function: 분석 실행 함수

        Returns:
            배치 평가 결과
        """
        self.results = []
        evaluator = MetricsEvaluator(llm=self.llm)

        for case in golden_cases:
            try:
                # 분석 실행
                start_time = datetime.now()
                analysis_result = await analysis_function(case["input"])
                end_time = datetime.now()

                # 메트릭 평가
                report = await evaluator.evaluate_all(
                    request_id=case["id"],
                    start_time=start_time,
                    end_time=end_time,
                    validation_results=[True],  # 성공 가정
                    news_data=self._extract_news_data(analysis_result),
                    analysis_result=analysis_result,
                    golden_truth=case,
                    save_results=True
                )
                self.results.append(report)
            except Exception as e:
                print(f"Error evaluating {case['id']}: {e}")

        return self._create_batch_summary()

    def _extract_news_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과에서 뉴스 데이터 추출"""
        news_analysis = analysis_result.get("n7_news_analysis", {})
        news_context = news_analysis.get("news_context", {})

        return {
            "ticker": news_context.get("ticker", ""),
            "buy_date": news_context.get("period", {}).get("buy_date"),
            "sell_date": news_context.get("period", {}).get("sell_date"),
            "items": news_context.get("key_headlines", []),
            "dates": [],
        }

    def _create_batch_summary(self) -> Dict[str, Any]:
        """배치 평가 요약 생성"""
        if not self.results:
            return {"total_cases": 0, "error": "No results"}

        tier_stats = {
            "impact": {"passed": 0, "total": 0},
            "trust": {"passed": 0, "total": 0},
            "stability": {"passed": 0, "total": 0},
        }

        for report in self.results:
            for metric in report.get("metrics", []):
                tier = metric.get("tier", "")
                if tier in tier_stats:
                    tier_stats[tier]["total"] += 1
                    if metric.get("passed", False):
                        tier_stats[tier]["passed"] += 1

        # 통과율 계산
        for tier in tier_stats:
            total = tier_stats[tier]["total"]
            passed = tier_stats[tier]["passed"]
            tier_stats[tier]["pass_rate"] = round(
                (passed / total * 100) if total > 0 else 0, 1
            )

        return {
            "total_cases": len(self.results),
            "timestamp": datetime.now().isoformat(),
            "tier_stats": tier_stats,
            "individual_results": [
                {
                    "request_id": r["request_id"],
                    "summary": r["summary"]
                }
                for r in self.results
            ]
        }


# ============================================
# 동기 버전 평가기 (테스트/디버깅용)
# ============================================
def evaluate_stability_sync(
    start_time: datetime,
    end_time: datetime,
    validation_results: List[bool],
    request_id: str = ""
) -> List[MetricResult]:
    """Tier 3 Stability 메트릭만 동기 평가"""
    return [
        measure_e2e_latency(start_time, end_time, request_id),
        measure_json_stability(validation_results, request_id),
    ]


def evaluate_basic_metrics(
    start_time: datetime,
    end_time: datetime,
    validation_results: List[bool],
    news_dates: List[date],
    buy_date: date,
    sell_date: date,
    request_id: str = ""
) -> List[MetricResult]:
    """LLM 없이 측정 가능한 기본 메트릭 평가"""
    latency = measure_e2e_latency(start_time, end_time, request_id)

    return [
        latency,
        measure_json_stability(validation_results, request_id),
        measure_zero_anachronism(news_dates, buy_date, sell_date, request_id),
        measure_time_efficiency(latency["value"], request_id),
    ]
