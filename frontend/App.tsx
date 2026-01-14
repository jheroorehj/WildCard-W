
import React, { useState, useEffect, useRef } from 'react';
import { InvestmentFormData, AnalysisResult, Message, StockDetail } from './types';
import { DECISION_OPTIONS, TRADE_PATTERNS, TRADE_PERIODS, ICONS } from './constants';
import { analyzeInvestmentLoss, chatWithAnalyst } from './services/solarService';

type ViewType = 'splash' | 'home' | 'form' | 'analysis';

// --- Mini Calendar Component ---
const DateRangePicker: React.FC<{ 
  value: string, 
  onChange: (val: string) => void 
}> = ({ value, onChange }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [range, setRange] = useState<{ start?: Date, end?: Date }>({});
  const [mode, setMode] = useState<'day' | 'yearMonth'>('day');

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay();

  const days = daysInMonth(year, month);
  const startDay = firstDayOfMonth(year, month);

  const formatDate = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  const handleDateClick = (day: number) => {
    const selected = new Date(year, month, day);
    if (!range.start || (range.start && range.end)) {
      setRange({ start: selected });
    } else if (selected < range.start) {
      setRange({ start: selected });
    } else {
      const newRange = { ...range, end: selected };
      setRange(newRange);
      if (newRange.start && newRange.end) {
        const startStr = formatDate(newRange.start);
        const endStr = formatDate(newRange.end);
        onChange(`${startStr} ~ ${endStr}`);
      }
    }
  };

  const isSelected = (day: number) => {
    const d = new Date(year, month, day);
    if (range.start && d.getTime() === range.start.getTime()) return true;
    if (range.end && d.getTime() === range.end.getTime()) return true;
    return false;
  };

  const isInRange = (day: number) => {
    const d = new Date(year, month, day);
    return range.start && range.end && d > range.start && d < range.end;
  };

  if (mode === 'yearMonth') {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 mt-2 select-none animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center mb-4 px-1">
          <button onClick={() => setCurrentDate(new Date(year - 1, month))} className="p-1 hover:bg-slate-800 rounded-md transition-colors text-slate-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <button onClick={() => setMode('day')} className="px-3 py-1 bg-blue-600/10 rounded-full text-[11px] font-black text-blue-400 border border-blue-500/20">
            {year}년
          </button>
          <button onClick={() => setCurrentDate(new Date(year + 1, month))} className="p-1 hover:bg-slate-800 rounded-md transition-colors text-slate-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 6 6 6-6 6"/></svg>
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <button
              key={i}
              onClick={() => {
                setCurrentDate(new Date(year, i));
                setMode('day');
              }}
              className={`py-2 text-[10px] font-bold rounded-lg transition-all ${
                i === month ? 'bg-blue-600 text-white' : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
              }`}
            >
              {i + 1}월
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 mt-2 select-none animate-in fade-in zoom-in-95 duration-200">
      <div className="flex justify-between items-center mb-4 px-1">
        <button onClick={() => setCurrentDate(new Date(year, month - 1))} className="p-1 hover:bg-slate-800 rounded-md transition-colors text-slate-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <button 
          onClick={() => setMode('yearMonth')}
          className="px-3 py-1 hover:bg-slate-800 rounded-lg transition-all text-[11px] font-black text-white flex items-center gap-1 group"
        >
          {year}년 {month + 1}월
          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-blue-500 opacity-50 group-hover:opacity-100 transition-transform"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        <button onClick={() => setCurrentDate(new Date(year, month + 1))} className="p-1 hover:bg-slate-800 rounded-md transition-colors text-slate-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 6 6 6-6 6"/></svg>
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center">
        {['일', '월', '화', '수', '목', '금', '토'].map(d => (
          <span key={d} className="text-[9px] font-bold text-slate-600 mb-1">{d}</span>
        ))}
        {Array.from({ length: startDay }).map((_, i) => <div key={`empty-${i}`} />)}
        {Array.from({ length: days }).map((_, i) => {
          const day = i + 1;
          const selected = isSelected(day);
          const inRange = isInRange(day);
          return (
            <button
              key={day}
              onClick={() => handleDateClick(day)}
              className={`text-[10px] h-7 w-7 rounded-lg flex items-center justify-center transition-all ${
                selected ? 'bg-blue-600 text-white font-bold' : 
                inRange ? 'bg-blue-600/20 text-blue-300' : 'hover:bg-slate-800 text-slate-400'
              }`}
            >
              {day}
            </button>
          );
        })}
      </div>
      <div className="mt-3 flex justify-between items-center border-t border-slate-800 pt-3">
        <p className="text-[9px] text-slate-500 font-medium">시작일과 종료일을 선택하세요</p>
        <button onClick={() => { setRange({}); onChange(''); }} className="text-[9px] font-bold text-red-400/70 hover:text-red-400 transition-colors">초기화</button>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [view, setView] = useState<ViewType>('splash');
  const [step, setStep] = useState<number>(1);
  const [stockInput, setStockInput] = useState('');
  const [formData, setFormData] = useState<InvestmentFormData>({
    stocks: [],
    decisionBasis: []
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const [showCustomPeriod, setShowCustomPeriod] = useState<Record<number, boolean>>({});
  
  // 개별 채팅 답변의 확장 상태 관리
  const [expandedChat, setExpandedChat] = useState<Record<number, boolean>>({});
  // 분석 결과 섹션별 확장 상태 관리
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    lossReason: false,
    marketAnalysis: false,
    patternAnalysis: false,
    learningPath: false
  });
  const [chatLoading, setChatLoading] = useState<boolean>(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setView('home');
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, chatLoading]);

  const startAnalysis = () => {
    setFormData({ stocks: [], decisionBasis: [] });
    setStockInput('');
    setStep(1);
    setShowCustomPeriod({});
    setView('form');
  };

  const nextStep = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setStep(prev => prev + 1);
  };
  const prevStep = () => {
    if (step > 1) setStep(prev => prev - 1);
    else setView('home');
  };
  
  const handleAnalysis = async () => {
    setLoading(true);
    try {
      const result = await analyzeInvestmentLoss(formData);
      setAnalysis(result);
      setMessages([]); 
      setExpanded({
        lossReason: false,
        marketAnalysis: false,
        patternAnalysis: false,
        learningPath: false
      });
      setView('analysis');
    } catch (error) {
      console.error(error);
      alert("분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const addStock = () => {
    const name = stockInput.trim();
    if (name && !formData.stocks.find(s => s.name === name)) {
      const newStock: StockDetail = {
        name,
        status: 'holding',
        period: TRADE_PERIODS[0],
        customPeriod: '',
        patterns: []
      };
      setFormData(prev => ({ ...prev, stocks: [...prev.stocks, newStock] }));
      setStockInput('');
    }
  };

  const removeStock = (name: string) => {
    setFormData(prev => ({ ...prev, stocks: prev.stocks.filter(s => s.name !== name) }));
  };

  const updateStockDetail = (index: number, updates: Partial<StockDetail>) => {
    setFormData(prev => {
      const newStocks = [...prev.stocks];
      newStocks[index] = { ...newStocks[index], ...updates };
      return { ...prev, stocks: newStocks };
    });
  };

  const toggleStockPattern = (index: number, pattern: string) => {
    const stock = formData.stocks[index];
    const newPatterns = stock.patterns.includes(pattern)
      ? stock.patterns.filter(p => p !== pattern)
      : [...stock.patterns, pattern];
    updateStockDetail(index, { patterns: newPatterns });
  };

  const toggleDecisionBasis = (option: string) => {
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

    const currentMessages = [...messages, { role: 'user' as const, content: text }];
    setMessages(currentMessages);
    setInput('');
    setChatLoading(true);

    try {
      const response = await chatWithAnalyst(
        currentMessages.map(m => ({ role: m.role, content: m.content })),
        text
      );
      // 새 메시지는 기본적으로 확장된 상태로 추가
      const newMsgIndex = messages.length + 1;
      setExpandedChat(prev => ({ ...prev, [newMsgIndex]: true }));
      setMessages(prev => [...prev, { role: 'assistant' as const, content: response }]);
    } catch (error) {
      console.error(error);
    } finally {
      setChatLoading(false);
    }
  };

  const toggleCustomInput = (index: number) => {
    setShowCustomPeriod(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const toggleChatExpand = (index: number) => {
    setExpandedChat(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const toggleExpand = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Dummy data for UI preview
  const handleQuickAnalysis = () => {
    const dummyStocks: StockDetail[] = [
      { name: '삼성전자', status: 'holding', period: '최근 1개월 내', customPeriod: '', patterns: ['물타기 (단가 낮추기)'] },
      { name: '엔비디아', status: 'sold', period: '1~6개월 사이', customPeriod: '', patterns: ['분할 매수 (Scaling In)'] },
      { name: '테슬라', status: 'holding', period: '6개월 이상', customPeriod: '', patterns: ['장기 보유 (Buy & Hold)'] }
    ];
    const dummyFormData: InvestmentFormData = {
      stocks: dummyStocks,
      decisionBasis: ['유튜브/인플루언서 추천', '뉴스/미디어 보도', 'FOMO (남들 다 사길래)']
    };

    // Create Solar API compatible dummy data
    const dummyAnalysis: AnalysisResult = {
      request_id: 'dummy-request-id',
      n10_loss_review_report: {
        report_title: '삼성전자 외 2건 투자 복기 분석',
        overall_summary: '시장 과열 국면에서의 추격 매수와 FOMO 심리로 인한 고점 매수가 주요 손실 원인으로 분석됩니다.',
        node_summaries: {
          n6: {
            summary: '리스크 노출도를 키운 비효율적 대응',
            details: [
              '삼성전자의 경우 하락장에서의 성급한 물타기가 리스크 노출도를 지나치게 높였습니다.',
              '엔비디아는 분할 매도로 대응했으나, 타이밍이 다소 늦었습니다.',
              '테슬라의 장기 보유 전략은 기회 비용 측면에서 다소 비효율적인 구간을 지나고 있습니다.'
            ]
          },
          n7: {
            summary: '금리 인하 기대감 후퇴와 변동성 장세',
            details: [
              '해당 기간 동안 연준의 금리 인하 기대감 후퇴로 인한 기술주 중심의 변동성이 확대되었습니다.',
              '엔비디아는 실적 발표 전후로 차익 실현 매물이 쏟아졌습니다.',
              '테슬라는 전기차 수요 둔화 우려가 하방 압력으로 작용했습니다.'
            ]
          },
          n8: {
            summary: '시장 과열 국면의 심리적 추격 매수',
            details: [
              '시장 과열 국면에서의 추격 매수와 매도 타이밍 실기가 주요 원인입니다.',
              'FOMO 심리로 인해 고점에서 비중을 확대한 것이 손실 폭을 키웠습니다.',
              '삼성전자의 경우 8만전자 돌파 기대감에 의한 고점 매수가 부담이 되었습니다.'
            ]
          },
          n9: {
            summary: '감정에 휘둘리는 직감이 아닌, 사전에 정의된 데이터 기반 원칙에 따라 매매 버튼을 누르십시오.',
            details: ['투자 결정 시 감정적 요소를 배제하고 객관적 지표를 활용하세요.']
          }
        },
        learning_materials: {
          key_takeaways: [
            '리스크 관리 원칙 재정립',
            '손절가 설정 의무화',
            '거시경제 지표 분석 학습'
          ],
          recommended_topics: [
            '기술적 분석 기초',
            '거시경제 지표 해석',
            '포지션 사이징 전략'
          ],
          practice_steps: [
            '분할 매수 원칙 재정립 및 종목별 비중 조절 (최대 20% 이내)',
            '매수 전 손절가(Stop-loss) 설정 의무화 및 자동 매도 활용',
            '거시 경제 지표(금리, 환율)와 기술주 상관관계 분석 학습'
          ]
        },
        uncertainty_level: 'low'
      }
    };

    setFormData(dummyFormData);
    setAnalysis(dummyAnalysis);
    setMessages([]);
    setExpanded({ lossReason: false, marketAnalysis: false, patternAnalysis: false, learningPath: false });
    setView('analysis');
  };

  const isNextDisabled = (step === 1 && formData.stocks.length === 0) ||
                       (step === 2 && formData.stocks.some(s => s.patterns.length === 0)) ||
                       (step === 3 && formData.decisionBasis.length === 0);

  // Solar API data mapping
  const report = analysis?.n10_loss_review_report;
  const lossAnalysisTitle = report?.node_summaries.n8.summary || '손실 원인 분석';
  const lossAnalysis = report?.node_summaries.n8.details.join('\n\n') || '';
  const marketAnalysisTitle = report?.node_summaries.n7.summary || '시장 상황 분석';
  const marketAnalysis = report?.node_summaries.n7.details.join('\n\n') || '';
  const patternAnalysisTitle = report?.node_summaries.n6.summary || '투자 패턴 분석';
  const patternAnalysis = report?.node_summaries.n6.details.join('\n\n') || '';
  const learningPath = {
    title: report?.learning_materials.key_takeaways.join(' · ') || '학습 경로',
    description: '제공된 학습 자료를 바탕으로 개선 방향을 찾아보세요.',
    actionItems: report?.learning_materials.practice_steps || []
  };
  const behavioralGuide = report?.node_summaries.n9.summary || '현명한 투자 결정을 위해 노력하세요.';
  const suggestedQuestions = [
    '이 패턴을 어떻게 개선할 수 있을까요?',
    '당시 시장 상황을 더 자세히 알려주세요.',
    '비슷한 실수를 방지하려면?'
  ];

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
          <p className="text-blue-400 font-bold tracking-[0.3em] text-[10px] uppercase opacity-80">Loss Analysis Engine</p>
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
        <h2 className="text-2xl font-bold mb-4 animate-pulse text-center">노트를<br/>정리하고 있습니다</h2>
        <p className="text-slate-400 text-center max-w-xs text-sm">기록된 매매 데이터와 시장 상황을 <br/>정밀하게 대조하고 있습니다.</p>
      </div>
    );
  }

  if (view === 'home') {
    return (
      <div className="h-screen max-w-md mx-auto bg-slate-950 text-white flex flex-col relative overflow-hidden">
        <div className="absolute top-[-50px] left-[-50px] w-64 h-64 bg-blue-600/10 blur-[100px] rounded-full pointer-events-none"></div>
        <header className="px-6 pt-6 pb-2 flex justify-between items-center shrink-0 z-20">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="w-6 h-6 bg-blue-600 rounded-lg flex items-center justify-center font-black text-[11px] shadow-lg shadow-blue-600/20">W</div>
            <span className="font-black tracking-tighter text-lg leading-none">WILDCARD</span>
          </div>
          <button className="p-2 text-slate-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </button>
        </header>
        <main className="flex-1 px-6 overflow-y-auto pb-8">
          <div className="mt-4 space-y-1">
            <h2 className="text-2xl font-bold leading-tight">당신의 <span className="text-blue-500">선택</span>이<br/>최고의 <span className="text-purple-400">자산</span>이 되도록</h2>
            <p className="text-slate-400 text-xs">와일드카드가 당신의 투자 여정을 함께 기록합니다.</p>
          </div>
          <button onClick={startAnalysis} className="mt-6 group relative w-full bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl p-5 flex flex-col justify-between overflow-hidden shadow-2xl shadow-blue-900/40 transition-transform active:scale-[0.98]">
            <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 blur-[30px] rounded-full -mr-12 -mt-12 group-hover:scale-110 transition-transform duration-500"></div>
            <div className="relative z-10 text-left mb-8">
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider">AI : WILDCARD</span>
              <h3 className="text-xl font-black mt-3 tracking-tight">AI 투자 결정 복기 시작</h3>
            </div>
            <div className="relative z-10 flex justify-between items-center">
              <p className="text-blue-100 text-[10px] font-medium opacity-80">포트폴리오 중심의 다중 분석 지원</p>
              <div className="bg-white text-blue-600 p-1.5 rounded-full shadow-lg">{ICONS.ArrowRight}</div>
            </div>
          </button>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="bg-slate-900/50 rounded-2xl p-4">
              <p className="text-slate-500 text-[9px] font-bold uppercase tracking-wider mb-1">나의 분석 노트</p>
              <div className="flex items-baseline gap-1"><span className="text-xl font-bold">12</span><span className="text-slate-400 text-[10px]">건</span></div>
            </div>
            <div className="bg-slate-900/50 rounded-2xl p-4">
              <p className="text-slate-500 text-[9px] font-bold uppercase tracking-wider mb-1">학습 성취도</p>
              <div className="flex items-baseline gap-1"><span className="text-xl font-bold text-green-400">84%</span></div>
            </div>
          </div>
          <div className="mt-8">
            <h4 className="text-xs font-bold text-slate-300 mb-4 flex items-center gap-2"><span className="w-1 h-3 bg-blue-500 rounded-full"></span>최근 복기 노트</h4>
            <div className="space-y-2.5">
              {[{ name: '삼성전자 외 2건', date: '2025.02.10', type: '포트폴리오 분석', onClick: handleQuickAnalysis }, { name: '테슬라', date: '2025.01.24', type: '매매 패턴 분석' }, { name: '엔비디아', date: '2025.01.05', type: '추격 매수 분석' }].map((item, i) => (
                <div key={i} onClick={item.onClick} className="bg-slate-900/30 rounded-xl p-3.5 flex justify-between items-center group hover:bg-slate-900/50 transition-colors cursor-pointer">
                  <div><h5 className="font-bold text-sm text-slate-200">{item.name}</h5><p className="text-[9px] text-slate-500">{item.date} • {item.type}</p></div>
                  <div className="text-slate-600 group-hover:text-slate-400 transition-colors">{ICONS.ArrowRight}</div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (view === 'form') {
    const nextButton = (
      <button 
        onClick={step === 3 ? handleAnalysis : nextStep} 
        disabled={isNextDisabled} 
        className="w-full bg-blue-600 disabled:bg-slate-800 disabled:opacity-50 text-white p-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xl shadow-blue-900/20"
      >
        {step === 3 ? '복기 노트 생성하기' : '다음으로 넘어가기'} {ICONS.ArrowRight}
      </button>
    );

    return (
      <div className="h-screen max-w-md mx-auto bg-slate-950 flex flex-col shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-[100px] rounded-full -mr-32 -mt-32"></div>
        
        {/* Fixed Header */}
        <div className="p-8 pb-4 shrink-0 z-20">
          <div className="flex items-center">
            <button onClick={prevStep} className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <div className="h-1 flex-1 bg-slate-800 mx-4 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${(step / 3) * 100}%` }}></div>
            </div>
            <span className="text-slate-500 font-mono text-xs">{step}/3</span>
          </div>
        </div>

        {step === 2 ? (
          /* Step 2 Only: Integrated Scroll Layout (Title + Content + Button all scroll together) */
          <div className="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar relative z-10">
            <div className="step-transition animate-in fade-in slide-in-from-bottom-4 flex flex-col">
              <h1 className="text-2xl font-bold mb-1 leading-tight">종목별 <span className="text-blue-400">거래 상황</span>을<br/>알려주세요.</h1>
              <p className="text-slate-500 text-[11px] mb-6 font-medium">기간을 입력하면 시장 상황과 연동하여 더 좋은 결과를 낼 수 있습니다.</p>
              
              <div className="space-y-4 mb-8">
                {formData.stocks.map((stock, idx) => (
                  <div key={stock.name} className="bg-slate-900/40 rounded-3xl p-4 border border-slate-800 space-y-4 shadow-sm">
                    <div className="flex justify-between items-center">
                      <h3 className="text-base font-black text-white">{stock.name}</h3>
                      <div className="flex bg-slate-800 p-0.5 rounded-lg shrink-0">
                        <button onClick={() => updateStockDetail(idx, {status: 'holding'})} className={`px-2.5 py-1 text-[9px] font-bold rounded-md transition-all ${stock.status === 'holding' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500'}`}>보유 중</button>
                        <button onClick={() => updateStockDetail(idx, {status: 'sold'})} className={`px-2.5 py-1 text-[9px] font-bold rounded-md transition-all ${stock.status === 'sold' ? 'bg-slate-700 text-white shadow-lg' : 'text-slate-500'}`}>매도 완료</button>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      <div className="flex justify-between items-center">
                        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1">언제 거래했나요? {ICONS.Calendar}</p>
                        <button onClick={() => toggleCustomInput(idx)} className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[8px] font-black uppercase transition-all border ${showCustomPeriod[idx] ? 'bg-blue-600 text-white border-blue-400' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                          {ICONS.Edit} 직접 입력
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {TRADE_PERIODS.map(p => (
                          <button key={p} onClick={() => updateStockDetail(idx, {period: p})} className={`px-2 py-1 rounded-full text-[9px] font-medium border transition-all ${stock.period === p ? 'bg-blue-600/20 border-blue-500 text-blue-400' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>{p}</button>
                        ))}
                      </div>
                      {showCustomPeriod[idx] && (
                        <div className="space-y-2">
                          <input 
                            type="text" 
                            placeholder="분석 기간 (예: 2024년 여름 등)" 
                            className="w-full bg-slate-950/50 border border-slate-700 rounded-xl px-3 py-2 text-[10px] text-white placeholder:text-slate-700 focus:border-blue-500 outline-none" 
                            value={stock.customPeriod} 
                            onChange={(e) => updateStockDetail(idx, { customPeriod: e.target.value })} 
                          />
                          <DateRangePicker value={stock.customPeriod || ''} onChange={(val) => updateStockDetail(idx, { customPeriod: val })} />
                        </div>
                      )}
                    </div>

                    <div className="space-y-2">
                      <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">매매 패턴 (중복 가능)</p>
                      <div className="flex flex-wrap gap-1">
                        {TRADE_PATTERNS.map(p => (
                          <button key={p} onClick={() => toggleStockPattern(idx, p)} className={`px-2 py-1 rounded-full text-[9px] font-medium border transition-all ${stock.patterns.includes(p) ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>{p}</button>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {nextButton}
            </div>
          </div>
        ) : (
          /* Step 1 and 3: Standard Layout (Fixed Button at bottom) */
          <>
            <div className="flex-1 flex flex-col px-8 overflow-hidden relative z-10">
              {step === 1 && (
                <div className="step-transition animate-in fade-in slide-in-from-bottom-4 flex flex-col h-full">
                  <h1 className="text-2xl font-bold mb-3 leading-tight shrink-0">이번에 복기할 <br/><span className="text-blue-400">종목은 무엇인가요?</span></h1>
                  <p className="text-slate-500 text-xs mb-6 shrink-0">투자 판단을 되돌아보고 싶은 모든 대상을 추가해주세요.</p>
                  
                  <div className="relative mb-4 h-[56px] bg-slate-900/60 rounded-2xl border border-slate-800 focus-within:border-blue-500 transition-all flex items-center shrink-0">
                    <input type="text" autoFocus placeholder="종목명 입력 (예: 삼성전자)" className="flex-1 h-full bg-transparent pl-5 pr-14 text-base font-bold text-white outline-none placeholder:text-slate-700" value={stockInput} onChange={e => setStockInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addStock()} />
                    <div className="absolute right-2.5 w-9 h-9 flex items-center justify-center">
                      <button onClick={addStock} className="w-full h-full flex items-center justify-center bg-blue-600 text-white rounded-lg active:scale-95 transition-all shadow-lg">{ICONS.Plus}</button>
                    </div>
                  </div>

                  {/* Dotted Separator 복구 */}
                  <div className="my-2 border-t-2 border-dotted border-slate-800/60 shrink-0"></div>

                  <div className="flex-1 overflow-y-auto space-y-2 mb-4 custom-scrollbar">
                    {formData.stocks.map(stock => (
                      <div key={stock.name} className="relative h-[56px] bg-slate-900/60 rounded-2xl flex items-center border border-slate-800 animate-in slide-in-from-top-2 shrink-0">
                        <span className="flex-1 pl-5 text-base font-bold text-white truncate">{stock.name}</span>
                        <button onClick={() => removeStock(stock.name)} className="absolute right-2.5 w-9 h-9 flex items-center justify-center bg-slate-800/80 text-slate-500 rounded-lg">{ICONS.Minus}</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="step-transition animate-in fade-in slide-in-from-bottom-4 flex flex-col h-full">
                  <h1 className="text-2xl font-bold mb-6 leading-tight shrink-0">투자 결정의 <span className="text-blue-400">핵심 근거</span>는<br/>무엇이었나요?</h1>
                  <div className="flex-1 overflow-y-auto space-y-3 mb-4 custom-scrollbar pr-1">
                    {DECISION_OPTIONS.map(option => (
                      <button key={option} onClick={() => toggleDecisionBasis(option)} className={`w-full p-4 rounded-2xl text-left transition-all border ${formData.decisionBasis.includes(option) ? 'bg-blue-600 border-blue-400 text-white shadow-lg' : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'}`}>
                        <div className="flex justify-between items-center"><span className="font-medium text-sm">{option}</span>{formData.decisionBasis.includes(option) && ICONS.Check}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {/* Fixed Footer for Step 1 and 3 */}
            <div className="p-8 pt-2 shrink-0 relative z-20">
              {nextButton}
            </div>
          </>
        )}
      </div>
    );
  }

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
                    {expandedChat[i] && (
                      <p className="text-[11px] text-slate-300 font-medium leading-relaxed opacity-90 whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                        {msg.content}
                      </p>
                    )}
                    {!expandedChat[i] && (
                      <p className="text-[11px] text-slate-500 italic">내용을 보려면 돋보기 버튼을 클릭하세요.</p>
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

export default App;
