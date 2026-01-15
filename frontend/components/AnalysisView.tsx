import React, { useEffect, useState } from 'react';
import { AnalysisResult, Message, InvestmentFormData, RootCause, Evidence, N8LossCauseAnalysis, Quiz } from '../types';
import { ICONS, CAUSE_CATEGORY_META, IMPACT_LEVEL_META } from '../constants';
import { generateInvestmentQuiz } from '../services/solarService';

// === 하위 호환성: 구버전 데이터 변환 ===
const isLegacyFormat = (lossCause: any): boolean => {
  if (!lossCause?.root_causes) return true;
  if (lossCause.root_causes.length === 0) return false;
  return typeof lossCause.root_causes[0] === 'string';
};

const normalizeLossCauseData = (lossCause: any): N8LossCauseAnalysis | null => {
  if (!lossCause) return null;

  // 새 형식이면 그대로 반환
  if (!isLegacyFormat(lossCause)) {
    return lossCause as N8LossCauseAnalysis;
  }

  // 구버전 형식 → 새 형식으로 변환
  const legacyCauses = (lossCause.root_causes || []) as string[];
  return {
    loss_check: lossCause.loss_check || '',
    loss_amount_pct: lossCause.loss_amount_pct || 'N/A',
    one_line_summary: lossCause.one_line_summary || '',
    root_causes: legacyCauses.map((text: string, idx: number) => ({
      id: `RC${String(idx + 1).padStart(3, '0')}`,
      category: 'internal' as const,
      subcategory: 'judgment_error' as const,
      title: text.slice(0, 20) + (text.length > 20 ? '...' : ''),
      description: text,
      impact_score: 5,
      impact_level: 'medium' as const,
      evidence: [],
      timeline_relevance: 'throughout' as const
    })),
    cause_breakdown: { internal_ratio: 50, external_ratio: 50 },
    detailed_explanation: lossCause.detailed_explanation || '',
    confidence_level: 'medium' as const
  };
};

// === 서브 컴포넌트: 내부/외부 비중 바 ===
const CauseBreakdownBar: React.FC<{ internal: number; external: number }> = ({ internal, external }) => (
  <div className="my-4">
    <div className="flex text-[10px] mb-1.5 font-medium">
      <span className="text-amber-400 flex items-center gap-1">
        {ICONS.User}
        <span>내부 요인 {internal}%</span>
      </span>
      <span className="flex-1" />
      <span className="text-indigo-400 flex items-center gap-1">
        <span>외부 요인 {external}%</span>
        {ICONS.Globe}
      </span>
    </div>
    <div className="h-2 rounded-full overflow-hidden flex bg-slate-800">
      <div
        className="bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-500"
        style={{ width: `${internal}%` }}
      />
      <div
        className="bg-gradient-to-r from-indigo-400 to-indigo-600 transition-all duration-500"
        style={{ width: `${external}%` }}
      />
    </div>
  </div>
);

// === 서브 컴포넌트: 영향도 배지 ===
const ImpactBadge: React.FC<{ score: number; level: string }> = ({ score, level }) => {
  const meta = IMPACT_LEVEL_META[level as keyof typeof IMPACT_LEVEL_META] || IMPACT_LEVEL_META.medium;
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${meta.bgClass} border ${meta.borderClass}`}>
      <div className="flex gap-0.5">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className={`w-0.5 h-2.5 rounded-sm transition-all ${
              i < score ? meta.textClass.replace('text-', 'bg-') : 'bg-slate-700'
            }`}
          />
        ))}
      </div>
      <span className={`${meta.textClass} text-[10px] font-bold`}>
        {score}/10
      </span>
    </div>
  );
};

// === 서브 컴포넌트: 근거 아이템 ===
const EvidenceItem: React.FC<{ evidence: Evidence }> = ({ evidence }) => {
  const sourceLabels = { n6: '기술분석', n7: '뉴스분석', user_input: '사용자입력' };
  const sourceColors = { n6: 'text-blue-400', n7: 'text-purple-400', user_input: 'text-green-400' };

  return (
    <div className="flex items-start gap-2 text-[10px] bg-slate-800/50 rounded-lg p-2">
      <span className={`font-bold shrink-0 ${sourceColors[evidence.source]}`}>
        [{sourceLabels[evidence.source]}]
      </span>
      <div className="flex-1">
        <span className="text-slate-200 font-medium">{evidence.data_point}</span>
        <span className="text-slate-500 mx-1">→</span>
        <span className="text-slate-400">{evidence.interpretation}</span>
      </div>
    </div>
  );
};

// === 서브 컴포넌트: 원인 카드 ===
const CauseCard: React.FC<{ cause: RootCause; index: number }> = ({ cause, index }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  const categoryMeta = CAUSE_CATEGORY_META[cause.category];
  const subcategoryMeta = categoryMeta?.subcategories[cause.subcategory as keyof typeof categoryMeta.subcategories];

  const borderColor = cause.category === 'internal' ? 'border-amber-500/30' : 'border-indigo-500/30';
  const bgColor = cause.category === 'internal' ? 'bg-amber-500/5' : 'bg-indigo-500/5';
  const accentColor = cause.category === 'internal' ? 'text-amber-400' : 'text-indigo-400';
  const iconKey = subcategoryMeta?.icon as keyof typeof ICONS;

  return (
    <div className={`p-3 rounded-2xl border ${borderColor} ${bgColor} space-y-2`}>
      {/* 상단: 제목 + 영향도 */}
      <div className="flex justify-between items-start gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className={`shrink-0 ${accentColor}`}>
            {iconKey && ICONS[iconKey] ? ICONS[iconKey] : ICONS.AlertCircle}
          </span>
          <div className="min-w-0">
            <span className={`text-[10px] ${accentColor} font-medium`}>
              {subcategoryMeta?.label || cause.subcategory}
            </span>
            <h6 className="text-sm font-bold text-white">{cause.title}</h6>
          </div>
        </div>
        <ImpactBadge score={cause.impact_score} level={cause.impact_level} />
      </div>

      {/* 설명 */}
      <p className="text-[11px] text-slate-300 leading-relaxed">{cause.description}</p>

      {/* 근거 데이터 토글 */}
      {cause.evidence && cause.evidence.length > 0 && (
        <div>
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className={`flex items-center gap-1 text-[10px] font-medium transition-colors ${
              showEvidence ? accentColor : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {showEvidence ? ICONS.ChevronUp : ICONS.ChevronDown}
            <span>근거 데이터 {cause.evidence.length}건</span>
          </button>

          {showEvidence && (
            <div className="mt-2 space-y-1.5 animate-in fade-in slide-in-from-top-1 duration-200">
              {cause.evidence.map((ev, i) => (
                <EvidenceItem key={i} evidence={ev} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface AnalysisViewProps {
  analysis: AnalysisResult | null;
  messages: Message[];
  input: string;
  setInput: (val: string) => void;
  handleSendMessage: (msgOverride?: string) => void;
  expanded: Record<string, boolean>;
  toggleExpand: (section: string) => void;
  expandedChat: Record<number, boolean>;
  toggleChatExpand: (index: number) => void;
  chatLoading: boolean;
  scrollRef: React.RefObject<HTMLDivElement>;
  setView: (view: any) => void;
  formData: InvestmentFormData;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({
  analysis,
  messages,
  input,
  setInput,
  handleSendMessage,
  expanded,
  toggleExpand,
  expandedChat,
  toggleChatExpand,
  chatLoading,
  scrollRef,
  setView,
  formData
}) => {
  const [quizOpen, setQuizOpen] = useState(false);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [quizLoading, setQuizLoading] = useState(false);
  const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | null>(null);
  const [quizFinished, setQuizFinished] = useState(false);

  useEffect(() => {
    setQuizOpen(false);
    setQuizzes([]);
    setCurrentQuizIndex(0);
    setSelectedOptionIndex(null);
    setQuizFinished(false);
  }, [analysis]);

  const handleToggleQuiz = async () => {
    if (!analysis) return;
    if (!quizOpen && quizzes.length == 0) {
      setQuizLoading(true);
      setQuizOpen(true);
      try {
        const generated = await generateInvestmentQuiz(analysis);
        setQuizzes(generated);
      } catch (error) {
        console.error(error);
      } finally {
        setQuizLoading(false);
      }
      return;
    }
    setQuizOpen(prev => !prev);
  };

  const handleQuizSelect = (index: number) => {
    if (selectedOptionIndex != null) return;
    setSelectedOptionIndex(index);
  };

  const nextQuiz = () => {
    if (currentQuizIndex < quizzes.length - 1) {
      setCurrentQuizIndex(prev => prev + 1);
      setSelectedOptionIndex(null);
    } else {
      setQuizFinished(true);
    }
  };

  // Solar API data mapping
  const report = analysis?.n10_loss_review_report;
  const lossCauseRaw = analysis?.n8_loss_cause_analysis;
  const marketContext = analysis?.n8_market_context_analysis;
  const pattern = analysis?.learning_pattern_analysis;
  const tutor = report?.learning_tutor;
  const learningPath = tutor?.custom_learning_path;
  const advisor = tutor?.investment_advisor;

  // 손실 원인 분석 데이터 정규화 (하위 호환성)
  const lossCause = normalizeLossCauseData(lossCauseRaw);

  // 카테고리별 원인 분류
  const internalCauses = lossCause?.root_causes?.filter(c => c.category === 'internal') || [];
  const externalCauses = lossCause?.root_causes?.filter(c => c.category === 'external') || [];

  const marketAnalysisTitle =
    marketContext?.market_situation_analysis || '시장 상황 분석';
  const marketAnalysis =
    marketContext?.market_situation_analysis || '';

  const patternAnalysisTitle = pattern?.pattern_summary || '투자 패턴 분석';
  const patternAnalysisDetails = [
    ...(pattern?.pattern_strengths || []),
    ...(pattern?.pattern_weaknesses || [])
  ].filter(Boolean);
  const patternAnalysis = patternAnalysisDetails.join('\n\n');

  const learningMaterials = learningPath?.learning_materials || [];
  const learningPathSummary = learningPath?.path_summary || '학습 경로';
  const learningPathSteps = learningPath?.practice_steps || [];
  const learningPathTopics = learningPath?.recommended_topics || [];
  const behavioralGuide =
    advisor?.advisor_message || '현명한 투자 결정을 위해 노력하세요.';
  const suggestedQuestions = advisor?.recommended_questions || [
    '이 패턴을 어떻게 개선할 수 있을까요?',
    '당시 시장 상황을 더 자세히 알려주세요.',
    '비슷한 실수를 방지하려면?'
  ];
  const newsSummaries = analysis?.n7_news_analysis?.news_context?.news_summaries || [];
  const newsHeadlines = analysis?.n7_news_analysis?.news_context?.key_headlines || [];
  const newsItems = (newsSummaries.length ? newsSummaries : newsHeadlines).slice(0, 3);

  return (
    <div className="h-screen max-w-md mx-auto bg-slate-950 flex flex-col shadow-2xl relative overflow-hidden">
      {/* Note Background Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none z-0" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
      <div className="absolute inset-0 opacity-[0.05] pointer-events-none z-0" style={{ backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)', backgroundSize: '100px 100px' }}></div>
      
      <header className="px-5 py-4 flex items-center gap-3 shrink-0 bg-slate-950/80 backdrop-blur-md sticky top-0 z-20 border-b border-white/5">
        <button onClick={() => setView('home')} className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-xs shadow-lg shadow-blue-600/30">W</button>
        <div>
          <h1 className="text-sm font-bold text-white leading-tight">{formData.stocks.length > 1 ? `${formData.stocks[0].name} 외 ${formData.stocks.length - 1}건` : formData.stocks[0]?.name} 분석 리포트</h1>
          <div className="flex items-center gap-1.5 mt-0.5"><span className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></span><span className="text-[9px] text-blue-500 font-bold uppercase tracking-widest">실시간 인사이트 메모 중</span></div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 space-y-4 pt-4 pb-12 scroll-smooth custom-scrollbar relative z-10">
        {analysis && (
          <div className="space-y-4">
            {/* 손실 원인 분석 (고도화) */}
            <section className="bg-slate-900/40 border border-amber-500/20 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 relative">
              {/* 헤더 */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="text-amber-400 shrink-0">{ICONS.AlertCircle}</div>
                  <h4 className="text-amber-300 text-[11px] font-black uppercase tracking-tight">손실 원인 분석</h4>
                  {lossCause?.loss_amount_pct && lossCause.loss_amount_pct !== 'N/A' && (
                    <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-[10px] font-bold rounded-full">
                      {lossCause.loss_amount_pct}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => toggleExpand('lossReason')}
                  className={`p-1 rounded-md transition-colors ${expanded.lossReason ? 'bg-amber-500/20 text-amber-400' : 'text-slate-600 hover:text-amber-400 hover:bg-white/5'}`}
                >
                  {ICONS.Search}
                </button>
              </div>

              {/* 한 줄 요약 */}
              <h5 className="text-base font-bold text-white tracking-tight mb-2">
                {lossCause?.one_line_summary || lossCause?.loss_check || '손실 원인 분석'}
              </h5>

              {/* 내부/외부 비중 바 */}
              {lossCause?.cause_breakdown && (
                <CauseBreakdownBar
                  internal={lossCause.cause_breakdown.internal_ratio}
                  external={lossCause.cause_breakdown.external_ratio}
                />
              )}

              {/* 확장 시 상세 내용 */}
              {expanded.lossReason && lossCause && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-1 duration-300">
                  {/* 내부 요인 그룹 */}
                  {internalCauses.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-amber-400">
                        {ICONS.User}
                        <span className="text-[10px] font-bold uppercase tracking-wider">
                          내부 요인 ({internalCauses.length})
                        </span>
                      </div>
                      <div className="space-y-2">
                        {internalCauses.map((cause, idx) => (
                          <CauseCard key={cause.id} cause={cause} index={idx} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 외부 요인 그룹 */}
                  {externalCauses.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-indigo-400">
                        {ICONS.Globe}
                        <span className="text-[10px] font-bold uppercase tracking-wider">
                          외부 요인 ({externalCauses.length})
                        </span>
                      </div>
                      <div className="space-y-2">
                        {externalCauses.map((cause, idx) => (
                          <CauseCard key={cause.id} cause={cause} index={idx} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 상세 설명 */}
                  {lossCause.detailed_explanation && (
                    <div className="pt-3 border-t border-slate-700/50">
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {lossCause.detailed_explanation}
                      </p>
                    </div>
                  )}

                  {/* 신뢰도 표시 */}
                  {lossCause.confidence_level && (
                    <div className="flex justify-end">
                      <span className={`text-[9px] px-2 py-0.5 rounded-full ${
                        lossCause.confidence_level === 'high' ? 'bg-green-500/20 text-green-400' :
                        lossCause.confidence_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-slate-500/20 text-slate-400'
                      }`}>
                        분석 신뢰도: {lossCause.confidence_level === 'high' ? '높음' : lossCause.confidence_level === 'medium' ? '보통' : '낮음'}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* 시장 상황 분석 */}
            <section className="bg-slate-900/40 border border-indigo-500/20 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 delay-75 relative">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="text-indigo-400 shrink-0">{ICONS.BarChart3}</div>
                  <h4 className="text-indigo-400 text-[11px] font-black uppercase tracking-tight">시장 상황 분석</h4>
                </div>
                <button 
                  onClick={() => toggleExpand('marketAnalysis')}
                  className={`p-1 rounded-md transition-colors ${expanded.marketAnalysis ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-600 hover:text-indigo-400 hover:bg-white/5'}`}
                >
                  {ICONS.Search}
                </button>
              </div>
              <div className="space-y-2">
                <h5 className="text-base font-bold text-white tracking-tight">{marketAnalysisTitle}</h5>
                {expanded.marketAnalysis && (
                  <>
                    {newsItems.length ? (
                      <div className="space-y-2 pt-3">
                        {newsItems.map((item, idx) => (
                          <a
                            key={idx}
                            href={item.link}
                            target="_blank"
                            rel="noreferrer"
                            className="block rounded-xl border border-white/5 bg-slate-950/40 p-3 hover:bg-slate-900/60 transition-colors"
                          >
                            <div className="text-[12px] font-semibold text-slate-200">
                              {item.title || `News ${idx + 1}`}
                            </div>
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              {item.source ? `${item.source} - ` : ''}
                              {item.date || 'Date unavailable'}
                            </div>
                            {'summary' in item && item.summary ? (
                              <p className="text-[12px] text-slate-300 leading-relaxed mt-1 whitespace-pre-wrap">
                                {item.summary}
                              </p>
                            ) : null}
                          </a>
                        ))}
                      </div>
                    ) : null}
                  </>
                )}
              </div>
            </section>

            {/* 투자 패턴 분석 */}
            <section className="bg-slate-900/40 border border-emerald-500/20 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 delay-100 relative">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="text-emerald-400 shrink-0">{ICONS.Activity}</div>
                  <h4 className="text-emerald-400 text-[11px] font-black uppercase tracking-tight">투자 패턴 분석</h4>
                </div>
                <button 
                  onClick={() => toggleExpand('patternAnalysis')}
                  className={`p-1 rounded-md transition-colors ${expanded.patternAnalysis ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-600 hover:text-emerald-400 hover:bg-white/5'}`}
                >
                  {ICONS.Search}
                </button>
              </div>
              <div className="space-y-2">
                <h5 className="text-base font-bold text-white tracking-tight">{patternAnalysisTitle}</h5>
                {expanded.patternAnalysis && (
                  <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                    {patternAnalysis}
                  </p>
                )}
              </div>
            </section>

            {/* 맞춤형 투자 학습 경로 */}
            <section className="bg-slate-900/60 border border-blue-500/10 p-5 rounded-3xl shadow-xl animate-in fade-in slide-in-from-bottom-4 delay-150 relative">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="text-white shrink-0">{ICONS.Lightbulb}</div>
                  <h4 className="text-white text-[11px] font-black uppercase tracking-tight">맞춤형 투자 학습 경로</h4>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleToggleQuiz}
                    className={`p-1 rounded-md transition-colors ${quizOpen ? 'bg-blue-500/20 text-blue-400' : 'text-slate-600 hover:text-blue-400 hover:bg-white/5'}`}
                  >
                    {ICONS.HelpCircle}
                  </button>
                  <button 
                    onClick={() => toggleExpand('learningPath')}
                    className={`p-1 rounded-md transition-colors ${expanded.learningPath ? 'bg-white/20 text-white' : 'text-slate-600 hover:text-white hover:bg-white/5'}`}
                  >
                    {ICONS.Search}
                  </button>
                </div>
              </div>
              <div className="space-y-3">
                <h5 className="text-base font-bold text-white tracking-tight">{learningPathSummary}</h5>
                {expanded.learningPath && (
                  <div className="animate-in fade-in slide-in-from-top-1 duration-300 space-y-3">
                    {!!learningMaterials.length && (
                      <div className="space-y-2">
                        <p className="text-[11px] text-slate-400 font-medium">학습 자료</p>
                        {learningMaterials.map((item, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 group">
                            <div className="w-1 h-1 rounded-full bg-blue-400 mt-1.5 shrink-0"></div>
                            <p className="text-[12px] text-slate-200 font-medium leading-tight">{item}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {!!learningPathSteps.length && (
                      <div className="space-y-2">
                        <p className="text-[11px] text-slate-400 font-medium">실행 단계</p>
                        {learningPathSteps.map((item, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 group">
                            <div className="w-1 h-1 rounded-full bg-blue-500 mt-1.5 shrink-0"></div>
                            <p className="text-[12px] text-slate-200 font-medium leading-tight">{item}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {!!learningPathTopics.length && (
                      <div className="space-y-2">
                        <p className="text-[11px] text-slate-400 font-medium">추천 주제</p>
                        {learningPathTopics.map((item, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 group">
                            <div className="w-1 h-1 rounded-full bg-blue-300 mt-1.5 shrink-0"></div>
                            <p className="text-[12px] text-slate-200 font-medium leading-tight">{item}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>


              {quizOpen && (
                <div className="mt-6 pt-6 border-t border-white/5 animate-in fade-in slide-in-from-top-4 duration-500">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[8px] font-black rounded uppercase tracking-tighter">AI 퀴즈</span>
                      <p className="text-[10px] font-bold text-slate-500">자가 점검 ({currentQuizIndex + 1}/3)</p>
                    </div>
                    {quizFinished && (
                      <button
                        onClick={() => {
                          setQuizFinished(false);
                          setCurrentQuizIndex(0);
                          setSelectedOptionIndex(null);
                        }}
                        className="text-[9px] font-bold text-blue-400 hover:underline"
                      >
                        다시 하기
                      </button>
                    )}
                  </div>

                  {quizLoading ? (
                    <div className="py-8 flex flex-col items-center justify-center gap-3">
                      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      <p className="text-[10px] text-slate-500 font-medium">퀴즈 생성 중...</p>
                    </div>
                  ) : quizzes.length > 0 && !quizFinished ? (
                    <div className="space-y-4">
                      <p className="text-sm font-bold text-slate-100 leading-snug">{quizzes[currentQuizIndex].question}</p>
                      <div className="grid gap-2">
                        {quizzes[currentQuizIndex].options.map((option, idx) => {
                          const isSelected = selectedOptionIndex === idx;
                          const isCorrect = quizzes[currentQuizIndex].correctAnswerIndex === idx;
                          const showResult = selectedOptionIndex !== null;
                          const isPersonality = quizzes[currentQuizIndex].type === 'personality';

                          let variantClass = "bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-500";
                          if (showResult) {
                            if (isPersonality) {
                              variantClass = isSelected ? "bg-blue-600/20 border-blue-500 text-blue-300 shadow-lg" : "opacity-50 border-slate-800 text-slate-600";
                            } else {
                              if (isCorrect) variantClass = "bg-emerald-600/20 border-emerald-500 text-emerald-400 shadow-lg";
                              else if (isSelected) variantClass = "bg-red-600/20 border-red-500 text-red-400";
                              else variantClass = "opacity-30 border-slate-800 text-slate-600";
                            }
                          }

                          return (
                            <button
                              key={idx}
                              onClick={() => handleQuizSelect(idx)}
                              disabled={showResult}
                              className={`w-full text-left p-4 rounded-2xl border text-xs font-bold transition-all ${variantClass}`}
                            >
                              <div className="flex items-center justify-between">
                                <span>{option.text}</span>
                                {showResult && !isPersonality && isCorrect && <span className="text-emerald-500">{ICONS.Check}</span>}
                              </div>
                            </button>
                          );
                        })}
                      </div>

                      {selectedOptionIndex !== null && (
                        <div className="mt-4 animate-in fade-in slide-in-from-bottom-2">
                          {quizzes[currentQuizIndex].type === 'personality' ? (
                            <div className="bg-blue-500/10 border-l-2 border-blue-500 p-4 rounded-r-2xl">
                              <p className="text-[11px] text-blue-300 leading-relaxed font-medium">
                                <span className="font-black">해석:</span> {quizzes[currentQuizIndex].options[selectedOptionIndex].solution}
                              </p>
                            </div>
                          ) : (
                            <div className={`p-4 rounded-2xl ${selectedOptionIndex === quizzes[currentQuizIndex].correctAnswerIndex ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                              <p className="text-[11px] font-bold">
                                {selectedOptionIndex === quizzes[currentQuizIndex].correctAnswerIndex ? '정답입니다.' : '정답이 아니에요. 분석 내용을 다시 보고 도전해 보세요.'}
                              </p>
                            </div>
                          )}
                          <button
                            onClick={nextQuiz}
                            className="w-full mt-4 bg-slate-800 hover:bg-slate-700 text-white py-3 rounded-2xl font-black text-xs transition-all flex items-center justify-center gap-2"
                          >
                            {currentQuizIndex === quizzes.length - 1 ? '끝내기' : '다음'} {ICONS.ArrowRight}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : quizFinished ? (
                    <div className="py-6 text-center space-y-4">
                      <div className="w-12 h-12 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto text-blue-500 animate-bounce">
                        {ICONS.Check}
                      </div>
                      <h6 className="text-base font-black text-white">퀴즈 완료!</h6>
                      <p className="text-[11px] text-slate-500 font-medium px-4">
                        핵심 내용을 확인했어요. 다음 거래에 체크리스트를 적용해 보세요.
                      </p>
                      <button
                        onClick={() => setQuizOpen(false)}
                        className="bg-blue-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs shadow-lg shadow-blue-600/30"
                      >
                        닫기
                      </button>
                    </div>
                  ) : null}
                </div>
              )}

            {/* 행동 강령 (Behavioral Guide) */}
            <div className="px-3 py-3 border-l-2 border-emerald-500/50 bg-emerald-500/5 rounded-r-xl"><p className="text-emerald-400/90 text-[11px] italic font-medium">"{behavioralGuide}"</p></div>
          </div>
        )}

        {/* 채팅 히스토리 섹션 */}
        <div className="space-y-8 pt-6 pb-2">
          {messages.map((msg, i) => (
            msg.role === 'user' ? (
              <div key={i} className="flex justify-end animate-in slide-in-from-right-4 fade-in duration-300">
              <div className="px-3 py-3 border-r-2 border-slate-400/40 bg-slate-400/5 rounded-l-xl max-w-[95%]">
                <p className="text-slate-300 text-[11px] italic font-medium whitespace-pre-wrap">
                  "{msg.content}"
                </p>
              </div>
            </div>
            ) : (
              <div key={i} className="animate-in fade-in slide-in-from-bottom-4 relative">
                <section className="bg-slate-900/40 border border-blue-500/20 p-5 rounded-3xl shadow-sm">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="text-blue-400 shrink-0">{ICONS.Sparkles}</div>
                      <h4 className="text-blue-400 text-[11px] font-black uppercase tracking-tight">분석가 인사이트</h4>
                    </div>
                    <button 
                      onClick={() => toggleChatExpand(i)}
                      className={`p-1 rounded-md transition-colors ${expandedChat[i] ? 'bg-blue-500/20 text-blue-400' : 'text-slate-600 hover:text-blue-400 hover:bg-white/5'}`}
                    >
                      {ICONS.Search}
                    </button>
                  </div>
                  <div className="space-y-2">
                    {expandedChat[i] ? (
                      msg.raw?.learning_pattern_analysis ? (
                        <div className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300 space-y-2">
                          <p className="font-semibold">
                            {msg.raw.learning_pattern_analysis.pattern_summary}
                          </p>
                          <div className="space-y-1">
                            <p className="text-slate-400">강점</p>
                            {msg.raw.learning_pattern_analysis.pattern_strengths.map((item, idx) => (
                              <div key={idx}>- {item}</div>
                            ))}
                          </div>
                          <div className="space-y-1">
                            <p className="text-slate-400">약점</p>
                            {msg.raw.learning_pattern_analysis.pattern_weaknesses.map((item, idx) => (
                              <div key={idx}>- {item}</div>
                            ))}
                          </div>
                          <div className="space-y-1">
                            <p className="text-slate-400">학습 추천</p>
                            {msg.raw.learning_pattern_analysis.learning_recommendation.learning_steps.map(
                              (item, idx) => (
                                <div key={idx}>- {item}</div>
                              )
                            )}
                          </div>
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                          {msg.content}
                        </p>
                      )
                    ) : (
                      <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap">
                        {msg.content}
                      </p>
                    )}
                  </div>
                </section>
              </div>
            )
          ))}

          {/* 답변 로딩 상태 */}
          {chatLoading && (
            <div className="animate-in fade-in slide-in-from-bottom-2 relative">
              <section className="bg-slate-900/40 border border-slate-700/50 p-5 rounded-3xl shadow-sm">
                <div className="flex items-center gap-2.5 mb-3 opacity-50">
                  <div className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></div>
                  <h4 className="text-slate-500 text-[11px] font-black uppercase tracking-tight">답변을 구성하는 중...</h4>
                </div>
                <div className="space-y-3">
                  <div className="h-2 w-full bg-slate-800/50 rounded animate-pulse"></div>
                  <div className="h-2 w-5/6 bg-slate-800/50 rounded animate-pulse delay-75"></div>
                  <div className="h-2 w-4/6 bg-slate-800/50 rounded animate-pulse delay-150"></div>
                </div>
              </section>
            </div>
          )}
        </div>

        {analysis && (
          <div className="flex flex-col gap-3 pt-8 pb-2">
            <p className="text-[10px] font-bold text-slate-500 mb-1 px-1">추가로 궁금한 점이 있으신가요?</p>
            <div className="flex flex-col gap-2">
              {suggestedQuestions.map((q, i) => (
                <button 
                  key={i} 
                  onClick={() => handleSendMessage(q)} 
                  className="w-full text-left bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white text-[11px] px-4 py-3 rounded-2xl border border-white/5 transition-all active:scale-[0.98] leading-snug break-words flex items-start gap-3"
                >
                  <span className="text-blue-500/50 font-black shrink-0">Q.</span>
                  <span className="flex-1">{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-white/5 bg-slate-950/90 backdrop-blur-2xl shrink-0 sticky bottom-0 z-30">
        <div className="relative flex items-center bg-white/5 rounded-xl border border-white/10 focus-within:border-blue-500/50 transition-all px-3 py-1 shadow-lg">
          <input 
            type="text" 
            value={input} 
            onChange={e => setInput(e.target.value)} 
            onKeyDown={e => e.key === 'Enter' && handleSendMessage()} 
            placeholder="추가 질문을 입력하세요" 
            className="flex-1 bg-transparent border-none outline-none py-1.5 text-xs text-slate-100 placeholder:text-slate-600" 
          />
          <button onClick={() => handleSendMessage()} className="p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all active:scale-90">{ICONS.Send}</button>
        </div>
      </div>
    </div>
  );
};
