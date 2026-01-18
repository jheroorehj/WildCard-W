
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

export interface N9LearningPatternResponse {
  message: string;
  intent_hint: string;
}

// === N9 학습 패턴 분석 고도화 타입 ===
export type BiasFrequency = "low" | "medium" | "high";
export type MissionDifficulty = "easy" | "medium" | "hard";
export type MissionImpact = "low" | "medium" | "high";
export type UncertaintyLevel = "low" | "medium" | "high";

export interface InvestorCharacter {
  type: string;
  description: string;
  behavioral_bias: string;
}

export interface ProfileMetric {
  score: number;
  label: string;
  bias_detected: string | null;
}

export interface ProfileMetrics {
  information_sensitivity: ProfileMetric;
  analysis_depth: ProfileMetric;
  risk_management: ProfileMetric;
  decisiveness: ProfileMetric;
  emotional_control: ProfileMetric;
  learning_adaptability: ProfileMetric;
}

export interface PrimaryBias {
  name: string;
  english: string;
  description: string;
  impact: string;
}

export interface SecondaryBias {
  name: string;
  english: string;
  description: string;
}

export interface CognitiveAnalysis {
  primary_bias: PrimaryBias;
  secondary_biases: SecondaryBias[];
}

export interface DecisionProblem {
  problem_type: string;
  psychological_trigger: string;
  situation: string;
  thought_pattern: string;
  consequence: string;
  frequency: BiasFrequency;
}

// If-Then 플랜 (구현 의도 - Implementation Intentions)
export interface IfThenPlan {
  trigger_situation: string;
  trigger_emotion: string;
  then_action: string;
  commitment_phrase: string;
}

export interface ActionMission {
  mission_id: string;
  priority: number;
  title: string;
  description: string;
  behavioral_target: string;
  expected_outcome: string;
  difficulty: MissionDifficulty;
  estimated_impact: MissionImpact;
  if_then_plan?: IfThenPlan;
}

export interface N9LearningPatternAnalysis {
  investor_character: InvestorCharacter;
  profile_metrics: ProfileMetrics;
  cognitive_analysis: CognitiveAnalysis;
  decision_problems: DecisionProblem[];
  // action_missions는 N10으로 이동됨
  uncertainty_level: UncertaintyLevel;
}

// 프레이밍 효과 (Framing Effect) - 손실/실수 재정의
export interface LearningFrame {
  loss_reframe: {
    original: string;
    reframed: string;
    learning_value: string;
  };
  mistake_reframe: {
    original: string;
    reframed: string;
    strength_focus: string;
  };
  progress_frame: {
    message: string;
    comparison_anchor: string;
  };
}

// N10 학습 튜터 타입
export interface N10LearningTutor {
  custom_learning_path: {
    path_summary: string;
    learning_materials: string[];
    practice_steps: string[];
    recommended_topics: string[];
  };
  investment_advisor: {
    advisor_message: string;
    recommended_questions: string[];
  };
  learning_frame?: LearningFrame;
  action_missions: ActionMission[];
  uncertainty_level: UncertaintyLevel;
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

// === N8 손실 원인 분석 고도화 타입 ===
export type CauseCategory = "internal" | "external";
export type InternalSubcategory =
  | "judgment_error"
  | "emotional_trading"
  | "timing_mistake"
  | "risk_management"
  | "insufficient_research";
export type ExternalSubcategory =
  | "market_condition"
  | "company_news"
  | "macro_event"
  | "sector_rotation"
  | "unexpected_event";
export type ImpactLevel = "low" | "medium" | "high" | "critical";
export type TimelineRelevance = "before_buy" | "during_hold" | "at_sell" | "throughout";
export type EvidenceSource = "n6" | "n7" | "user_input";
export type EvidenceType = "price" | "indicator" | "news" | "sentiment" | "user_decision";
export type ConfidenceLevel = "low" | "medium" | "high";

export interface Evidence {
  source: EvidenceSource;
  type: EvidenceType;
  data_point: string;
  interpretation: string;
}

export interface RootCause {
  id: string;
  category: CauseCategory;
  subcategory: InternalSubcategory | ExternalSubcategory;
  title: string;
  description: string;
  impact_score: number;
  impact_level: ImpactLevel;
  evidence: Evidence[];
  timeline_relevance: TimelineRelevance;
}

export interface N8LossCauseAnalysis {
  loss_check: string;
  loss_amount_pct: string;
  one_line_summary: string;
  root_causes: RootCause[];
  cause_breakdown: {
    internal_ratio: number;
    external_ratio: number;
  };
  detailed_explanation: string;
  confidence_level: ConfidenceLevel;
}

export interface AnalysisResult {
  request_id: string;
  n10_loss_review_report?: {
    report_title?: string;
    overall_summary?: string;
    node_summaries?: {
      n6: { summary: string; details: string[] };
      n7: { summary: string; details: string[] };
      n8: { summary: string; details: string[] };
      n9: { summary: string; details: string[] };
    };
    learning_materials?: {
      key_takeaways: string[];
      recommended_topics: string[];
      practice_steps: string[];
    };
    // 새로운 N10 learning_tutor 구조
    learning_tutor?: N10LearningTutor;
    uncertainty_level?: string;
  };
  n8_loss_cause_analysis?: N8LossCauseAnalysis;
  n8_market_context_analysis?: {
    news_at_loss_time: string[];
    market_situation_analysis: string;
    related_news: string[];
  };
  learning_pattern_analysis?: N9LearningPatternAnalysis;
  n7_news_analysis?: N7NewsAnalysis;
}

export interface QuizOption {
  text: string;
  solution?: string;
}

export interface Quiz {
  question: string;
  type: 'standard' | 'personality';
  options: QuizOption[];
  correctAnswerIndex?: number;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  raw?: {
    learning_pattern_analysis?: N9LearningPatternAnalysis;
    chat_summary?: string;
    chat_detail?: string;
  };
}
