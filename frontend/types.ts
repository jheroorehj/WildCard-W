
export interface StockDetail {
  name: string;
  status: 'holding' | 'sold';
  period: string;
  customPeriod?: string;
  patterns: string[];
}

export interface InvestmentFormData {
  stocks: StockDetail[];
  decisionBasis: string[];
}

export interface N3LossDiagnosis {
  n6_tech_indicator_guideline: GuidelineBlock;
  n7_news_market_guideline: GuidelineBlock;
  n8_loss_cause_guideline: GuidelineBlock & {
    loss_cause_count: number;
    loss_cause_types: string[];
  };
  n9_mistake_pattern_guideline: GuidelineBlock;
  global_constraints: string[];
  uncertainty_level: string;
}

export interface GuidelineBlock {
  objective: string;
  required_inputs: string[];
  analysis_steps: string[];
  output_requirements: string[];
}

export interface N6StockAnalysis {
  stock_analysis: {
    ticker: string;
    period: {
      buy_date: string;
      sell_date: string;
    };
    summary: string;
    price_move: {
      start_price: string;
      end_price: string;
      pct_change: string;
      highest?: string;
      lowest?: string;
    };
    trend: string;
    indicators: {
      name: string;
      value: string;
      interpretation: string;
    }[];
    risk_notes: string[];
    uncertainty_level: string;
  };
}

export interface N7NewsSummary {
  news_summary: {
    query: string;
    key_events: {
      headline: string;
      source: string;
      date: string;
      summary: string;
    }[];
    sentiment: string;
    impact_assessment: string;
    uncertainty_level: string;
  };
}

export interface N8ConceptExplanation {
  mode: string;
  term_explanation?: {
    term: string;
    short_summary: string;
    detailed_explanation: string;
    simple_example: string;
    usage_context?: string;
    related_terms: string[];
    uncertainty_level: string;
  } | null;
  learning_guide?: {
    weakness_summary: string;
    weakness_detailed: string;
    learning_path_summary: string;
    learning_path_detailed: {
      step1: string;
      step2: string;
      step3: string;
    };
    recommended_topics: string[];
    estimated_difficulty: string;
    uncertainty_level: string;
  } | null;
  error_message?: string;
  uncertainty_level?: string;
}

export interface N9FallbackResponse {
  message: string;
  intent_hint: string;
}

export interface N7NewsAnalysis {
  news_context: {
    ticker: string;
    period: {
      buy_date: string;
      sell_date?: string;
    };
    summary: string;
    market_sentiment: {
      index: number;
      label: string;
      description: string;
    };
    key_headlines: {
      title: string;
      source: string;
      date: string;
      snippet?: string;
      link: string;
    }[];
    news_summaries?: {
      title: string;
      source: string;
      date: string;
      link: string;
      summary: string;
    }[];
    fact_check: {
      user_belief: string;
      actual_fact: string;
      verdict: string;
    };
    uncertainty_level: string;
  };
}

export interface AnalysisResult {
  request_id: string;
  n10_loss_review_report?: {
    report_title: string;
    overall_summary: string;
    node_summaries: {
      n6: { summary: string; details: string[] };
      n7: { summary: string; details: string[] };
      n8: { summary: string; details: string[] };
      n9: { summary: string; details: string[] };
    };
    learning_materials: {
      key_takeaways: string[];
      recommended_topics: string[];
      practice_steps: string[];
    };
    uncertainty_level: string;
  };
  n8_loss_cause_analysis?: {
    loss_check: string;
    root_causes: string[];
    one_line_summary: string;
    detailed_explanation: string;
  };
  n8_market_context_analysis?: {
    news_at_loss_time: string[];
    market_situation_analysis: string;
    related_news: string[];
  };
  learning_pattern_analysis?: {
    pattern_summary: string;
    pattern_strengths: string[];
    pattern_weaknesses: string[];
    learning_recommendation: {
      focus_area: string;
      learning_reason: string;
      learning_steps: string[];
      recommended_topics: string[];
    };
    uncertainty_level: string;
  };
  n7_news_analysis?: N7NewsAnalysis;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  raw?: {
    learning_pattern_analysis?: {
      pattern_summary: string;
      pattern_strengths: string[];
      pattern_weaknesses: string[];
      learning_recommendation: {
        focus_area: string;
        learning_reason: string;
        learning_steps: string[];
        recommended_topics: string[];
      };
      uncertainty_level: string;
    };
  };
}
