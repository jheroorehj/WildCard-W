
import React, { useState, useEffect, useRef } from 'react';
import { InvestmentFormData, AnalysisResult, Message, StockDetail } from './types';
import { DECISION_OPTIONS, TRADE_PATTERNS, TRADE_PERIODS, ICONS } from './constants';
import { analyzeInvestmentLoss, chatWithAnalyst } from './services/solarService';
import { SplashView } from './components/SplashView';
import { LoadingView } from './components/LoadingView';
import { HomeView } from './components/HomeView';
import { FormView } from './components/FormView';
import { AnalysisView } from './components/AnalysisView';

type ViewType = 'splash' | 'home' | 'form' | 'analysis';

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
      const message = typeof response?.message === 'string' ? response.message : '';
      // 새 메시지는 기본적으로 확장된 상태로 추가
      const newMsgIndex = messages.length + 1;
      setExpandedChat(prev => ({ ...prev, [newMsgIndex]: true }));
      setMessages(prev => [
        ...prev,
        { role: 'assistant' as const, content: message, raw: response?.raw }
      ]);
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

  const report = analysis?.n10_loss_review_report;

  if (view === 'splash') {
    return <SplashView />;
  }

  if (loading) {
    return <LoadingView />;
  }

  if (view === 'home') {
    return <HomeView startAnalysis={startAnalysis} handleQuickAnalysis={handleQuickAnalysis} />;
  }

  if (view === 'form') {
    return (
      <FormView
        step={step}
        formData={formData}
        stockInput={stockInput}
        setStockInput={setStockInput}
        showCustomPeriod={showCustomPeriod}
        handleAnalysis={handleAnalysis}
        nextStep={nextStep}
        prevStep={prevStep}
        addStock={addStock}
        removeStock={removeStock}
        updateStockDetail={updateStockDetail}
        toggleStockPattern={toggleStockPattern}
        toggleDecisionBasis={toggleDecisionBasis}
        toggleCustomInput={toggleCustomInput}
        isNextDisabled={isNextDisabled}
      />
    );
  }

  return (
    <AnalysisView
      analysis={analysis}
      messages={messages}
      input={input}
      setInput={setInput}
      handleSendMessage={handleSendMessage}
      expanded={expanded}
      toggleExpand={toggleExpand}
      expandedChat={expandedChat}
      toggleChatExpand={toggleChatExpand}
      chatLoading={chatLoading}
      scrollRef={scrollRef}
      setView={setView}
      formData={formData}
    />
  );
};

export default App;
