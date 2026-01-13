
import React, { useState, useEffect, useRef } from 'react';
import { InvestmentFormData, AnalysisResult, Message } from './types';
import { DECISION_OPTIONS, ICONS } from './constants';
import { analyzeInvestmentLoss, chatWithAnalyst } from './services/solarService';

type ViewType = 'splash' | 'home' | 'form' | 'analysis';

const App: React.FC = () => {
  const [view, setView] = useState<ViewType>('splash');
  const [step, setStep] = useState<number>(1);
  const [formData, setFormData] = useState<InvestmentFormData>({
    stockName: '',
    buyDate: '',
    sellDate: '',
    decisionBasis: []
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [reportExpanded, setReportExpanded] = useState<boolean>(true);
  const [marketExpanded, setMarketExpanded] = useState<boolean>(true);
  const [techExpanded, setTechExpanded] = useState<boolean>(true);
  const [showMarket, setShowMarket] = useState<boolean>(true);
  const [showTech, setShowTech] = useState<boolean>(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initial Splash Screen effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setView('home');
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  // Auto-scroll when new content is added to the report
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const startAnalysis = () => {
    setFormData({
      stockName: '',
      buyDate: '',
      sellDate: '',
      decisionBasis: []
    });
    setStep(1);
    setView('form');
  };

  const nextStep = () => setStep(prev => prev + 1);
  const prevStep = () => {
    if (step > 1) setStep(prev => prev - 1);
    else setView('home');
  };
  
  const handleAnalysis = async () => {
    setLoading(true);
    try {
      const result = await analyzeInvestmentLoss(formData);
      setAnalysis(result);
      setMessages([]); // Clear previous session messages
      setReportExpanded(true);
      setMarketExpanded(true);
      setTechExpanded(true);
      setShowMarket(true);
      setShowTech(true);
      setView('analysis');
    } catch (error) {
      console.error(error);
      alert("분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const toggleDecision = (option: string) => {
    setFormData(prev => ({
      ...prev,
      decisionBasis: prev.decisionBasis.includes(option)
        ? prev.decisionBasis.filter(o => o !== option)
        : [...prev.decisionBasis, option]
    }));
  };

  const handleSendMessage = async (msgOverride?: string) => {
    const text = msgOverride || input;
    if (!text.trim()) return;

    // Add user question to the log (we might not show it as a bubble, but we need it for context)
    const currentMessages = [...messages, { role: 'user' as const, content: text }];
    setMessages(currentMessages);
    setInput('');

    try {
      const response = await chatWithAnalyst(
        currentMessages.map(m => ({ role: m.role, content: m.content })),
        text
      );
      setMessages(prev => [...prev, { role: 'assistant' as const, content: response }]);
    } catch (error) {
      console.error(error);
    }
  };

  const report = analysis?.n10_loss_review_report;
  const newsSummaries = analysis?.n7_news_analysis?.news_context?.news_summaries || [];
  const newsHeadlines = analysis?.n7_news_analysis?.news_context?.key_headlines || [];
  const newsItems = (newsSummaries.length ? newsSummaries : newsHeadlines).slice(0, 3);
  const formatNewsDate = (value?: string) => {
    if (!value) return '날짜 정보 없음';
    const match = value.match(/(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})/);
    if (!match) return value;
    const year = match[1];
    const month = match[2].padStart(2, '0');
    const day = match[3].padStart(2, '0');
    return `${year}. ${month}. ${day}.`;
  };
  const suggestedQuestions = report
    ? [
        "기술적 지표 요약을 더 자세히 알려줘",
        "뉴스 이벤트를 좀 더 설명해줘",
        "학습 경로를 더 구체적으로 알려줘",
      ]
    : [];

  if (view === 'splash') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 transition-opacity duration-700">
        <div className="relative flex items-center justify-center w-40 h-40">
          <div className="absolute inset-0 border-2 border-blue-500/20 rounded-[3rem] animate-[spin_10s_linear_infinite]"></div>
          <div className="absolute inset-4 border border-blue-400/10 rounded-[2.5rem] animate-[spin_15s_linear_infinite_reverse]"></div>
          <div className="z-10 w-28 h-28 bg-blue-600 rounded-[2.2rem] flex items-center justify-center shadow-[0_0_60px_rgba(37,99,235,0.5)] animate-pulse overflow-hidden">
            <span className="text-white text-6xl font-black leading-none select-none tracking-tighter">W</span>
          </div>
        </div>
        <div className="mt-12 text-center space-y-3">
          <h1 className="text-4xl font-black tracking-tighter text-white">WILDCARD</h1>
          <p className="text-blue-400 font-bold tracking-[0.3em] text-[20px] uppercase opacity-80">Loss Analysis Engine</p>
        </div>
        <div className="absolute bottom-12 text-center">
            <p className="text-slate-500 text-sm font-medium animate-bounce">투자 패턴 분석의 새로운 기준</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-white p-6">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-8"></div>
        <h2 className="text-2xl font-bold mb-4 animate-pulse text-center">
          고객님의 투자 패턴을<br/>분석 중입니다
        </h2>
        <p className="text-slate-400 text-center max-w-xs text-sm">
          과거의 실수에서 새로운 기회를 찾고 있습니다. <br/>잠시만 기다려주세요.
        </p>
      </div>
    );
  }

  // --- HOME SCREEN ---
  if (view === 'home') {
    return (
      <div className="h-screen max-w-md mx-auto bg-slate-950 text-white flex flex-col relative overflow-hidden">
        <div className="absolute top-[-50px] left-[-50px] w-64 h-64 bg-blue-600/10 blur-[100px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-[-100px] right-[-100px] w-80 h-80 bg-purple-600/5 blur-[120px] rounded-full pointer-events-none"></div>

        <header className="px-6 pt-6 pb-2 flex justify-between items-center shrink-0 z-20">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="w-6 h-6 bg-blue-600 rounded-lg flex items-center justify-center font-black text-[22px] shadow-lg shadow-blue-600/20">W</div>
            <span className="font-black tracking-tighter text-lg leading-none">WILDCARD</span>
          </div>
          <button className="p-2 text-slate-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </button>
        </header>

        <main className="flex-1 px-6 overflow-y-auto pb-8">
          <div className="mt-4 space-y-1">
            <h2 className="text-2xl font-bold leading-tight">
              당신의 <span className="text-blue-500">선택</span>이<br/>
              최고의 <span className="text-purple-400">자산</span>이 되도록
            </h2>
            <p className="text-slate-400 text-xs">
              인공지능 투자 비서 와일드카드가 <br/>
              당신의 손실 패턴을 분석합니다.
            </p>
          </div>

          <button 
            onClick={startAnalysis}
            className="mt-6 group relative w-full bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl p-5 flex flex-col justify-between overflow-hidden shadow-2xl shadow-blue-900/40 transition-transform active:scale-[0.98]"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 blur-[30px] rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform duration-500"></div>
            <div className="relative z-10 text-left mb-8">
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-[18px] font-bold uppercase tracking-wider">AI 분석 시작</span>
              <h3 className="text-xl font-black mt-3 tracking-tight">손실 패턴 분석하러가기</h3>
            </div>
            <div className="relative z-10 flex justify-between items-center">
              <p className="text-blue-100 text-[20px] font-medium opacity-80">원하는 종목을 지금 분석해보세요</p>
              <div className="bg-white text-blue-600 p-1.5 rounded-full shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
              </div>
            </div>
          </button>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="bg-slate-900/50 rounded-2xl p-4">
              <p className="text-slate-500 text-[18px] font-bold uppercase tracking-wider mb-1">나의 분석 횟수</p>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold">12</span>
                <span className="text-slate-400 text-[20px]">건</span>
              </div>
            </div>
            <div className="bg-slate-900/50 rounded-2xl p-4">
              <p className="text-slate-500 text-[18px] font-bold uppercase tracking-wider mb-1">학습 성취도</p>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-green-400">84%</span>
              </div>
            </div>
          </div>

          <div className="mt-8">
            <h4 className="text-xs font-bold text-slate-300 mb-4 flex items-center gap-2">
              <span className="w-1 h-3 bg-blue-500 rounded-full"></span>
              최근 분석한 종목
            </h4>
            <div className="space-y-2.5">
              {[
                { name: '삼성전자', date: '2025.02.10', type: '기술적 분석' },
                { name: '테슬라', date: '2025.01.24', type: '뇌동 매매' },
                { name: '엔비디아', date: '2025.01.05', type: '추격 매수' },
              ].map((item, i) => (
                <div key={i} className="bg-slate-900/30 rounded-xl p-3.5 flex justify-between items-center group hover:bg-slate-900/50 transition-colors cursor-pointer">
                  <div>
                    <h5 className="font-bold text-sm text-slate-200">{item.name}</h5>
                    <p className="text-[18px] text-slate-500">{item.date} • {item.type}</p>
                  </div>
                  <div className="text-slate-600 group-hover:text-slate-400 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  // --- FORM SCREEN ---
  if (view === 'form') {
    return (
      <div className="h-screen max-w-md mx-auto bg-slate-950 flex flex-col shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-[100px] rounded-full -mr-32 -mt-32"></div>
        <div className="p-8 h-full flex flex-col">
          <div className="mb-12 flex items-center shrink-0">
            <button onClick={prevStep} className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <div className="h-1 flex-1 bg-slate-800 mx-4 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${(step / 3) * 100}%` }}></div>
            </div>
            <span className="text-slate-500 font-mono text-xs">{step}/3</span>
          </div>
          <div className="flex-1 overflow-hidden">
            {step === 1 && (
              <div className="step-transition animate-in fade-in slide-in-from-bottom-4">
                <h1 className="text-3xl font-bold mb-8 leading-tight">손실이 발생한 종목은<br/><span className="text-blue-400">무엇입니까?</span></h1>
                <div className="relative group">
                  <input type="text" autoFocus placeholder="예: 삼성전자, 테슬라, 비트코인 등" className="w-full bg-slate-900 border-b-2 border-slate-800 p-4 text-xl focus:border-blue-500 outline-none transition-colors rounded-t-lg text-white" value={formData.stockName} onChange={e => setFormData({...formData, stockName: e.target.value})} />
                </div>
              </div>
            )}
            {step === 2 && (
              <div className="step-transition animate-in fade-in slide-in-from-bottom-4">
                <h1 className="text-3xl font-bold mb-8 leading-tight">언제 <span className="text-blue-400">매매</span>하셨나요?</h1>
                <div className="space-y-8">
                  <div className="group">
                    <label className="text-xs font-bold text-slate-500 mb-2 block uppercase tracking-widest">매수 시점</label>
                    <input type="date" className="w-full bg-slate-900 border-b-2 border-slate-800 p-4 text-lg focus:border-blue-500 outline-none rounded-t-lg text-white appearance-none" value={formData.buyDate} onChange={e => setFormData({...formData, buyDate: e.target.value})} />
                  </div>
                  <div className="group">
                    <label className="text-xs font-bold text-slate-500 mb-2 block uppercase tracking-widest">매도 시점 (혹은 현재)</label>
                    <input type="date" className="w-full bg-slate-900 border-b-2 border-slate-800 p-4 text-lg focus:border-blue-500 outline-none rounded-t-lg text-white appearance-none" value={formData.sellDate} onChange={e => setFormData({...formData, sellDate: e.target.value})} />
                  </div>
                </div>
              </div>
            )}
            {step === 3 && (
              <div className="step-transition animate-in fade-in slide-in-from-bottom-4 flex flex-col h-full">
                <h1 className="text-3xl font-bold mb-8 leading-tight shrink-0">매수 전 <span className="text-blue-400">무엇을 보고</span><br/>결정했는지 기억하시나요?</h1>
                <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-3 scroll-smooth">
                  {DECISION_OPTIONS.map(option => (
                    <button key={option} onClick={() => toggleDecision(option)} className={`w-full p-4 rounded-2xl text-left transition-all border ${formData.decisionBasis.includes(option) ? 'bg-blue-600 border-blue-400 text-white shadow-lg shadow-blue-900/30 scale-[1.01]' : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-sm">{option}</span>
                        {formData.decisionBasis.includes(option) && <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="mt-8 space-y-4 shrink-0">
            <button onClick={step === 3 ? handleAnalysis : nextStep} disabled={(step === 1 && !formData.stockName) || (step === 2 && (!formData.buyDate || !formData.sellDate)) || (step === 3 && formData.decisionBasis.length === 0)} className="w-full bg-blue-600 disabled:bg-slate-800 disabled:opacity-50 text-white p-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xl shadow-blue-900/20">{step === 3 ? 'AI 분석 리포트 생성' : '다음으로 넘어가기'} {ICONS.ArrowRight}</button>
          </div>
        </div>
      </div>
    );
  }

  // --- ANALYSIS REPORT (NOTE FORMAT) ---
  return (
    <div className="h-screen max-w-md mx-auto bg-slate-950 flex flex-col shadow-2xl relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/5 blur-[100px] rounded-full -mr-32 -mt-32"></div>

      {/* COMPACT Header */}
      <header className="px-5 py-4 flex items-center gap-3 shrink-0 bg-slate-950/80 backdrop-blur-md sticky top-0 z-20 border-b border-white/5">
        <button 
          onClick={() => setView('home')}
          className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-xs shadow-lg shadow-blue-600/30 transition-transform active:scale-90"
        >
          W
        </button>
        <div>
          <h1 className="text-sm font-bold text-white leading-tight">{formData.stockName} 투자 분석 노트</h1>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></span>
            <span className="text-[12px] text-emerald-500 font-bold uppercase tracking-widest">실시간 튜터링 활성화</span>
          </div>
        </div>
      </header>

      {/* Report Body (Investment History Note) */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 space-y-4 pt-4 pb-12 scroll-smooth"
      >
        {analysis && (
          <div className="space-y-4">
            <section className="bg-slate-900/40 border border-white/5 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4">
              <div className="flex items-center justify-between mb-3">
                <button
                  type="button"
                  onClick={() => {
                    setAnalysis(null);
                    setMessages([]);
                    setReportExpanded(true);
                    setMarketExpanded(true);
                    setTechExpanded(true);
                    setShowMarket(true);
                    setShowTech(true);
                  }}
                  className="text-slate-400 hover:text-white text-[20px] font-black"
                  aria-label="답변 지우기"
                >
                  X
                </button>
                <h4 className="text-blue-400 text-[20px] font-black uppercase tracking-tight">손실 복기 요약</h4>
                <button
                  type="button"
                  onClick={() => setReportExpanded(prev => !prev)}
                  className="text-slate-400 hover:text-white text-[20px] font-black"
                  aria-label="답변 접기/펼치기"
                >
                  {reportExpanded ? '-' : '+'}
                </button>
              </div>
              {report ? (
                <>
                  <p className="text-slate-200 leading-relaxed text-sm whitespace-pre-wrap">{report.report_title}</p>
                  {reportExpanded ? (
                    <p className="mt-2 text-slate-300 leading-relaxed text-xs whitespace-pre-wrap opacity-90">{report.overall_summary}</p>
                  ) : null}
                </>
              ) : (
                <p className="text-slate-500 text-sm">요약이 없습니다.</p>
              )}
            </section>

            {showMarket ? (
              <section className="bg-slate-900/40 border border-white/5 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 delay-75">
                <div className="flex items-center justify-between mb-3">
                  <button
                    type="button"
                    onClick={() => setShowMarket(false)}
                    className="text-slate-400 hover:text-white text-[20px] font-black"
                    aria-label="시장 상황 숨기기"
                  >
                    X
                  </button>
                  <div className="flex items-center gap-2">
                    <div className="text-purple-400 scale-75">{ICONS.Search}</div>
                    <h4 className="text-purple-400 text-[20px] font-black uppercase tracking-tight">시장 상황</h4>
                  </div>
                  <button
                    type="button"
                    onClick={() => setMarketExpanded(prev => !prev)}
                    className="text-slate-400 hover:text-white text-[20px] font-black"
                    aria-label="시장 상황 접기/펼치기"
                  >
                    {marketExpanded ? '-' : '+'}
                  </button>
                </div>
                {report ? (
                  <div className="space-y-2 text-xs text-slate-300">
                    <p className="leading-relaxed whitespace-pre-wrap opacity-90">{report.node_summaries.n7.summary}</p>
                                        {marketExpanded ? (
                      <div className="space-y-3 text-slate-400">
                        <div className="space-y-1">
                          {report.node_summaries.n7.details.map((detail, idx) => (
                            <div key={idx}>- {detail}</div>
                          ))}
                        </div>
                        {newsItems.length ? (
                          <div className="space-y-2">
                            {newsItems.map((item, idx) => (
                              <div key={idx} className="relative rounded-xl border border-white/5 bg-slate-950/40">
                                <a
                                  href={item.link}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mx-3 my-2 block rounded-lg border border-white/5 bg-slate-950/40 p-3 transition hover:border-emerald-400/40 hover:bg-slate-950/70"
                                >
                                  <div className="text-[12px] font-semibold text-slate-200">
                                    {item.title || `News ${idx + 1}`}
                                  </div>
                                  <div className="text-[11px] text-slate-500 mt-0.5">
                                    {formatNewsDate(item.date)}
                                  </div>
                                  {"summary" in item && item.summary ? (
                                    <p className="text-[12px] text-slate-300 leading-relaxed mt-1 whitespace-pre-wrap">
                                      {item.summary}
                                    </p>
                                  ) : null}
                                </a>
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <p className="text-slate-500 text-xs">시장 요약이 없습니다.</p>
                )}
              </section>
            ) : null}

            {showTech ? (
              <section className="bg-slate-900/40 border border-white/5 p-5 rounded-3xl shadow-sm animate-in fade-in slide-in-from-bottom-4 delay-75">
                <div className="flex items-center justify-between mb-3">
                  <button
                    type="button"
                    onClick={() => setShowTech(false)}
                    className="text-slate-400 hover:text-white text-[20px] font-black"
                    aria-label="기술적 요약 숨기기"
                  >
                    X
                  </button>
                  <div className="flex items-center gap-2">
                    <div className="text-blue-400 scale-75">{ICONS.Lightbulb}</div>
                    <h4 className="text-blue-400 text-[20px] font-black uppercase tracking-tight">기술적 요약</h4>
                  </div>
                  <button
                    type="button"
                    onClick={() => setTechExpanded(prev => !prev)}
                    className="text-slate-400 hover:text-white text-[20px] font-black"
                    aria-label="기술적 요약 접기/펼치기"
                  >
                    {techExpanded ? '-' : '+'}
                  </button>
                </div>
                {report ? (
                  <div className="space-y-2 text-xs text-slate-300">
                    <p className="leading-relaxed whitespace-pre-wrap opacity-90">{report.node_summaries.n6.summary}</p>
                    {techExpanded ? (
                      <div className="space-y-1 text-slate-400">
                        {report.node_summaries.n6.details.map((detail, idx) => (
                          <div key={idx}>- {detail}</div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <p className="text-slate-500 text-xs">기술 요약이 없습니다.</p>
                )}
              </section>
            ) : null}

            <section className="bg-slate-900/60 border border-blue-500/10 p-5 rounded-3xl shadow-xl animate-in fade-in slide-in-from-bottom-4 delay-150">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-white scale-75">{ICONS.Lightbulb}</div>
                <h4 className="text-white text-[20px] font-black uppercase tracking-tight">학습 경로</h4>
              </div>
              {report ? (
                <div className="space-y-3">
                  <p className="text-[14px] text-slate-400 font-medium leading-relaxed">
                    {report.learning_materials.key_takeaways.join(' · ') || '요약 없음'}
                  </p>
                  <div className="space-y-2 pt-1">
                    {report.learning_materials.practice_steps.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 group">
                        <div className="w-1 h-1 rounded-full bg-blue-500 mt-1.5 shrink-0 group-hover:scale-150 transition-transform"></div>
                        <p className="text-[16px] text-slate-200 font-medium leading-tight">{item}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-[14px] text-slate-500 font-medium leading-relaxed">학습 가이드가 없습니다.</p>
              )}
            </section>

            <div className="px-3 py-3 border-l-2 border-emerald-500/50 bg-emerald-500/5 rounded-r-xl">
               <p className="text-emerald-400/90 text-[14px] italic font-medium">"{report?.node_summaries.n9.summary || '추가 안내가 없습니다.'}"</p>
            </div>
          </div>
        )}

        {/* Additional Context Cards */}
        {messages.map((msg, i) => (
          <section
            key={i}
            className={
              msg.role === 'user'
                ? 'bg-slate-900/40 border-r-2 border-emerald-500 p-5 rounded-l-3xl shadow-lg animate-in fade-in slide-in-from-bottom-6'
                : 'bg-slate-900/60 border-l-2 border-blue-600 p-5 rounded-r-3xl shadow-lg animate-in fade-in slide-in-from-bottom-6'
            }
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className={
                  msg.role === 'user'
                    ? 'w-0.5 h-2.5 bg-emerald-400 rounded-full'
                    : 'w-0.5 h-2.5 bg-blue-500 rounded-full'
                }
              ></div>
              <h4
                className={
                  msg.role === 'user'
                    ? 'text-emerald-400 text-[18px] font-black uppercase tracking-widest'
                    : 'text-blue-400 text-[18px] font-black uppercase tracking-widest'
                }
              >
                {msg.role === 'user' ? '내 질문' : '추가 인사이트'}
              </h4>
            </div>
            <p className="text-slate-200 text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          </section>
        ))}

        {/* Suggested Questions */}
        {analysis && (
          <div className="flex flex-wrap gap-2 pt-4 pb-2">
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(q)}
                className="bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white text-[14px] px-3 py-1.5 rounded-full border border-white/5 transition-all active:scale-95"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* COMPACT Input Area */}
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
          <button 
            onClick={() => handleSendMessage()}
            className="p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all active:scale-90"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
