import React from 'react';
import { AnalysisResult, Message, InvestmentFormData } from '../types';
import { ICONS } from '../constants';

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
  // Solar API data mapping
  const report = analysis?.n10_loss_review_report;
  const lossCause = analysis?.n8_loss_cause_analysis;
  const marketContext = analysis?.n8_market_context_analysis;
  const pattern = analysis?.learning_pattern_analysis;
  const recommendation = pattern?.learning_recommendation;

  const lossAnalysisTitle =
    lossCause?.one_line_summary || lossCause?.loss_check || '손실 원인 분석';
  const lossAnalysisDetails = [
    ...(lossCause?.root_causes || []),
    lossCause?.detailed_explanation || ''
  ].filter(Boolean);
  const lossAnalysis = lossAnalysisDetails.join('\n\n');

  const marketAnalysisTitle =
    marketContext?.market_situation_analysis || '시장 상황 분석';
  const marketAnalysisDetails = [
    ...(marketContext?.news_at_loss_time || []),
    ...(marketContext?.related_news || [])
  ].filter(Boolean);
  const marketAnalysis = marketAnalysisDetails.join('\n\n');

  const patternAnalysisTitle = pattern?.pattern_summary || '투자 패턴 분석';
  const patternAnalysisDetails = [
    ...(pattern?.pattern_strengths || []),
    ...(pattern?.pattern_weaknesses || [])
  ].filter(Boolean);
  const patternAnalysis = patternAnalysisDetails.join('\n\n');

  const learningMaterials = report?.learning_materials || {
    key_takeaways: recommendation?.recommended_topics || [],
    recommended_topics: recommendation?.recommended_topics || [],
    practice_steps: recommendation?.learning_steps || []
  };
  const learningPath = {
    title: learningMaterials.key_takeaways.join(' · ') || '학습 경로',
    description: '제공된 학습 자료를 바탕으로 개선 방향을 찾아보세요.',
    actionItems: learningMaterials.practice_steps || []
  };
  const behavioralGuide =
    recommendation?.learning_reason || '현명한 투자 결정을 위해 노력하세요.';
  const suggestedQuestions = [
    '이 패턴을 어떻게 개선할 수 있을까요?',
    '당시 시장 상황을 더 자세히 알려주세요.',
    '비슷한 실수를 방지하려면?'
  ];

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
            {/* 손실 원인 분석 */}
            <section className="bg-slate-900/40 border border-amber-500/20 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 relative">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="text-amber-400 shrink-0">{ICONS.AlertCircle}</div>
                  <h4 className="text-amber-300 text-[11px] font-black uppercase tracking-tight">손실 원인 분석</h4>
                </div>
                <button 
                  onClick={() => toggleExpand('lossReason')}
                  className={`p-1 rounded-md transition-colors ${expanded.lossReason ? 'bg-amber-500/20 text-amber-400' : 'text-slate-600 hover:text-amber-400 hover:bg-white/5'}`}
                >
                  {ICONS.Search}
                </button>
              </div>
              <div className="space-y-2">
                <h5 className="text-base font-bold text-white tracking-tight">{lossAnalysisTitle}</h5>
                {expanded.lossReason && (
                  <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                    {lossAnalysis}
                  </p>
                )}
              </div>
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
                  <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                    {marketAnalysis}
                  </p>
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
                <button 
                  onClick={() => toggleExpand('learningPath')}
                  className={`p-1 rounded-md transition-colors ${expanded.learningPath ? 'bg-white/20 text-white' : 'text-slate-600 hover:text-white hover:bg-white/5'}`}
                >
                  {ICONS.Search}
                </button>
              </div>
              <div className="space-y-3">
                <h5 className="text-base font-bold text-white tracking-tight">{learningPath.title}</h5>
                {expanded.learningPath && (
                  <div className="animate-in fade-in slide-in-from-top-1 duration-300 space-y-3">
                    <p className="text-[11px] text-slate-400 font-medium leading-relaxed">{learningPath.description}</p>
                    <div className="space-y-2 pt-1">
                      {learningPath.actionItems.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 group">
                          <div className="w-1 h-1 rounded-full bg-blue-500 mt-1.5 shrink-0"></div>
                          <p className="text-[12px] text-slate-200 font-medium leading-tight">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>

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
