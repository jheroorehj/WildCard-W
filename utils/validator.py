from typing import Dict, Any


def validate_node3(data: Dict[str, Any]) -> bool:
    """
    Node3 출력 JSON 최소 스키마 검증
    검증 실패 시 False 반환 → fallback 사용
    """
    allowed_uncertainty = {"low", "medium", "high"}

    def _validate_guideline(block: Dict[str, Any]) -> bool:
        if not isinstance(block, dict):
            return False
        if not isinstance(block.get("objective"), str):
            return False
        required_inputs = block.get("required_inputs")
        if not isinstance(required_inputs, list):
            return False
        if any(not isinstance(item, str) for item in required_inputs):
            return False
        analysis_steps = block.get("analysis_steps")
        if not isinstance(analysis_steps, list):
            return False
        if any(not isinstance(item, str) for item in analysis_steps):
            return False
        output_requirements = block.get("output_requirements")
        if not isinstance(output_requirements, list):
            return False
        if any(not isinstance(item, str) for item in output_requirements):
            return False
        return True

    n6 = data.get("n6_tech_indicator_guideline")
    if not _validate_guideline(n6):
        return False

    n7 = data.get("n7_news_market_guideline")
    if not _validate_guideline(n7):
        return False

    n9 = data.get("n9_mistake_pattern_guideline")
    if not _validate_guideline(n9):
        return False

    n8 = data.get("n8_loss_cause_guideline")
    if not isinstance(n8, dict):
        return False
    if not isinstance(n8.get("objective"), str):
        return False
    if n8.get("loss_cause_count") != 3:
        return False
    loss_cause_types = n8.get("loss_cause_types")
    if not isinstance(loss_cause_types, list):
        return False
    if any(not isinstance(item, str) for item in loss_cause_types):
        return False
    if not _validate_guideline(n8):
        return False

    global_constraints = data.get("global_constraints")
    if not isinstance(global_constraints, list):
        return False
    if any(not isinstance(item, str) for item in global_constraints):
        return False

    if data.get("uncertainty_level") not in allowed_uncertainty:
        return False

    return True


def validate_node6(data: Dict[str, Any]) -> bool:
    """
    Node6 출력 JSON 최소 스키마 검증
    """
    from N6_Stock_Analyst.schema import ALLOWED_TRENDS
    allowed_uncertainty = {"low", "medium", "high"}

    analysis = data.get("stock_analysis")
    if not isinstance(analysis, dict):
        return False

    if not isinstance(analysis.get("summary"), str):
        return False

    price_move = analysis.get("price_move")
    if not isinstance(price_move, dict):
        return False

    for key in ("start_price", "end_price", "pct_change"):
        if not isinstance(price_move.get(key), str):
            return False

    if analysis.get("trend") not in ALLOWED_TRENDS:
        return False

    indicators = analysis.get("indicators")
    if not isinstance(indicators, list):
        return False

    for indicator in indicators:
        if not isinstance(indicator, dict):
            return False
        if not isinstance(indicator.get("name"), str):
            return False
        if not isinstance(indicator.get("value"), str):
            return False
        if not isinstance(indicator.get("interpretation"), str):
            return False

    risk_notes = analysis.get("risk_notes")
    if not isinstance(risk_notes, list):
        return False
    if any(not isinstance(note, str) for note in risk_notes):
        return False

    if analysis.get("uncertainty_level") not in allowed_uncertainty:
        return False

    return True


def validate_node7(data: Dict[str, Any]) -> bool:
    """
    Node7 ??? JSON ??? ?????????
    """
    allowed_uncertainty = {"low", "medium", "high"}

    context = data.get("news_context")
    if not isinstance(context, dict):
        return False

    if not isinstance(context.get("ticker"), str):
        return False

    period = context.get("period")
    if not isinstance(period, dict):
        return False
    if not isinstance(period.get("buy_date"), str):
        return False

    if not isinstance(context.get("summary"), str):
        return False

    market_sentiment = context.get("market_sentiment")
    if not isinstance(market_sentiment, dict):
        return False
    if not isinstance(market_sentiment.get("label"), str):
        return False
    if not isinstance(market_sentiment.get("description"), str):
        return False

    key_headlines = context.get("key_headlines")
    if not isinstance(key_headlines, list):
        return False
    for item in key_headlines:
        if not isinstance(item, dict):
            return False
        for key in ("title", "source", "date", "link"):
            if not isinstance(item.get(key), str):
                return False

    news_summaries = context.get("news_summaries")
    if news_summaries is not None:
        if not isinstance(news_summaries, list):
            return False
        for item in news_summaries:
            if not isinstance(item, dict):
                return False
            for key in ("title", "source", "date", "link", "summary"):
                if not isinstance(item.get(key), str):
                    return False

    fact_check = context.get("fact_check")
    if not isinstance(fact_check, dict):
        return False
    for key in ("user_belief", "actual_fact", "verdict"):
        if not isinstance(fact_check.get(key), str):
            return False

    if context.get("uncertainty_level") not in allowed_uncertainty:
        return False

    return True


def validate_node8(data: Dict[str, Any]) -> bool:
    """
    Node8 JSON schema validator (loss analyst)
    """
    loss_cause = data.get("n8_loss_cause_analysis")
    if not isinstance(loss_cause, dict):
        return False

    for key in ("loss_check", "one_line_summary", "detailed_explanation"):
        if not isinstance(loss_cause.get(key), str):
            return False

    root_causes = loss_cause.get("root_causes")
    if not isinstance(root_causes, list):
        return False
    if any(not isinstance(item, str) for item in root_causes):
        return False

    market_context = data.get("n8_market_context_analysis")
    if not isinstance(market_context, dict):
        return False

    if not isinstance(market_context.get("market_situation_analysis"), str):
        return False

    news_at_loss = market_context.get("news_at_loss_time")
    if not isinstance(news_at_loss, list):
        return False
    if any(not isinstance(item, str) for item in news_at_loss):
        return False

    related_news = market_context.get("related_news")
    if not isinstance(related_news, list):
        return False
    if any(not isinstance(item, str) for item in related_news):
        return False

    n9_input = data.get("n9_input")
    if not isinstance(n9_input, dict):
        return False

    for key in ("investment_reason", "loss_cause_summary"):
        if not isinstance(n9_input.get(key), str):
            return False

    loss_details = n9_input.get("loss_cause_details")
    if not isinstance(loss_details, list):
        return False
    if any(not isinstance(item, str) for item in loss_details):
        return False

    objective = n9_input.get("objective_signals")
    if not isinstance(objective, dict):
        return False

    for key in ("price_trend", "volatility_level"):
        if not isinstance(objective.get(key), str):
            return False

    obj_tech = objective.get("technical_indicators")
    if not isinstance(obj_tech, list):
        return False
    for indicator in obj_tech:
        if not isinstance(indicator, dict):
            return False
        if not isinstance(indicator.get("name"), str):
            return False
        if not isinstance(indicator.get("value"), str):
            return False
        if not isinstance(indicator.get("interpretation"), str):
            return False

    obj_news = objective.get("news_facts")
    if not isinstance(obj_news, list):
        return False
    if any(not isinstance(item, str) for item in obj_news):
        return False

    if not isinstance(n9_input.get("uncertainty_level"), str):
        return False

    return True


def validate_node9(data: Dict[str, Any]) -> bool:
    """
    Node9 ?? JSON ?? ??? ?? (?? ?? ??)
    """
    allowed_uncertainty = {"low", "medium", "high"}

    analysis = data.get("learning_pattern_analysis")
    if not isinstance(analysis, dict):
        return False

    if not isinstance(analysis.get("pattern_summary"), str):
        return False

    strengths = analysis.get("pattern_strengths")
    if not isinstance(strengths, list) or any(not isinstance(item, str) for item in strengths):
        return False

    weaknesses = analysis.get("pattern_weaknesses")
    if not isinstance(weaknesses, list) or any(not isinstance(item, str) for item in weaknesses):
        return False

    recommendation = analysis.get("learning_recommendation")
    if not isinstance(recommendation, dict):
        return False

    for key in ("focus_area", "learning_reason"):
        if not isinstance(recommendation.get(key), str):
            return False

    steps = recommendation.get("learning_steps")
    if not isinstance(steps, list) or any(not isinstance(item, str) for item in steps):
        return False

    topics = recommendation.get("recommended_topics")
    if not isinstance(topics, list) or any(not isinstance(item, str) for item in topics):
        return False

    if analysis.get("uncertainty_level") not in allowed_uncertainty:
        return False

    return True
