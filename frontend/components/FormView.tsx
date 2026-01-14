
import React from 'react';
import { InvestmentFormData, StockDetail } from '../types';
import { DECISION_OPTIONS, TRADE_PATTERNS, ICONS } from '../constants';
import { DateRangePicker } from './DateRangePicker';

interface FormViewProps {
  step: number;
  formData: InvestmentFormData;
  stockInput: string;
  setStockInput: (val: string) => void;
  showCustomPeriod: Record<number, boolean>;
  handleAnalysis: () => void;
  nextStep: () => void;
  prevStep: () => void;
  addStock: () => void;
  removeStock: (name: string) => void;
  updateStockDetail: (index: number, updates: Partial<StockDetail>) => void;
  toggleStockPattern: (index: number, pattern: string) => void;
  toggleDecisionBasis: (option: string) => void;
  toggleCustomInput: (index: number) => void;
  isNextDisabled: boolean;
}

export const FormView: React.FC<FormViewProps> = ({
  step,
  formData,
  stockInput,
  setStockInput,
  handleAnalysis,
  nextStep,
  prevStep,
  addStock,
  removeStock,
  updateStockDetail,
  toggleStockPattern,
  toggleDecisionBasis,
  isNextDisabled
}) => {
  const nextButton = (
    <button 
      onClick={step === 3 ? handleAnalysis : nextStep} 
      disabled={isNextDisabled} 
      className="w-full bg-blue-600 disabled:bg-slate-800 disabled:opacity-50 text-white p-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xl shadow-blue-900/20"
    >
      {step === 3 ? '복기 노트 생성하기' : '다음으로 넘어가기'} {ICONS.ArrowRight}
    </button>
  );

  const parseParts = (val: string = "") => {
    const parts = val.split(" ~ ");
    const start = parts[0] || "";
    const end = parts[1] || "";
    
    const getDigits = (s: string) => s.replace(/\D/g, "");
    const sDigits = getDigits(start);
    const eDigits = getDigits(end);

    return {
      sY: sDigits.substring(0, 4),
      sM: sDigits.substring(4, 6),
      sD: sDigits.substring(6, 8),
      eY: eDigits.substring(0, 4),
      eM: eDigits.substring(4, 6),
      eD: eDigits.substring(6, 8),
    };
  };

  const handleBoxChange = (idx: number, field: string, val: string) => {
    const digits = val.replace(/\D/g, "");
    const parts = parseParts(formData.stocks[idx].customPeriod);
    const newParts = { ...parts, [field]: digits };

    // Construct YYYY 년 MM 월 DD 일 format
    const formatPart = (y: string, m: string, d: string) => {
      if (!y && !m && !d) return "";
      return `${y.padStart(4, '0')} 년 ${m.padStart(2, '0')} 월 ${d.padStart(2, '0')} 일`;
    };

    const startStr = formatPart(newParts.sY, newParts.sM, newParts.sD);
    const endStr = formatPart(newParts.eY, newParts.eM, newParts.eD);

    const final = endStr ? `${startStr} ~ ${endStr}` : startStr;
    updateStockDetail(idx, { customPeriod: final });
  };

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
        <div className="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar relative z-10">
          <div className="step-transition animate-in fade-in slide-in-from-bottom-4 flex flex-col">
            <h1 className="text-2xl font-bold mb-1 leading-tight">종목별 <span className="text-blue-400">거래 상황</span>을<br/>알려주세요.</h1>
            <p className="text-slate-500 text-[11px] mb-6 font-medium">기간을 입력하면 시장 상황과 연동하여 더 좋은 결과를 낼 수 있습니다.</p>
            
            <div className="space-y-4 mb-8">
              {formData.stocks.map((stock, idx) => {
                const parts = parseParts(stock.customPeriod);
                return (
                  <div key={stock.name} className="bg-slate-900/40 rounded-3xl p-4 border border-slate-800 space-y-4 shadow-sm">
                    <div className="flex justify-between items-center">
                      <h3 className="text-base font-black text-white">{stock.name}</h3>
                      <div className="flex bg-slate-800 p-0.5 rounded-lg shrink-0">
                        <button onClick={() => updateStockDetail(idx, {status: 'holding'})} className={`px-2.5 py-1 text-[9px] font-bold rounded-md transition-all ${stock.status === 'holding' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500'}`}>보유 중</button>
                        <button onClick={() => updateStockDetail(idx, {status: 'sold'})} className={`px-2.5 py-1 text-[9px] font-bold rounded-md transition-all ${stock.status === 'sold' ? 'bg-slate-700 text-white shadow-lg' : 'text-slate-500'}`}>매도 완료</button>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <p className="text-[10px] font-bold text-slate-300 flex items-center gap-1">{ICONS.Calendar} 언제 거래했나요? </p>
                      </div>
                      
                      {/* Segmented Inputs - Realigned to Horizontal */}
                      <div className="bg-slate-950/30 p-3 rounded-2xl border border-white/5">
                        <div className="flex items-center justify-between gap-1">
                          {/* Start Date Column */}
                          <div className="flex flex-col gap-1.5 flex-1">
                            <label className="text-[9px] font-bold text-slate-500">시작일</label>
                            <div className="flex items-center gap-1">
                              <input 
                                type="text" maxLength={4} placeholder="0000"
                                className="w-[38px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.sY} onChange={(e) => handleBoxChange(idx, 'sY', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">년</span>
                              <input 
                                type="text" maxLength={2} placeholder="00"
                                className="w-[24px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.sM} onChange={(e) => handleBoxChange(idx, 'sM', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">월</span>
                              <input 
                                type="text" maxLength={2} placeholder="00"
                                className="w-[24px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.sD} onChange={(e) => handleBoxChange(idx, 'sD', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">일</span>
                            </div>
                          </div>

                          <div className="pt-4 px-0.5">
                            <span className="text-slate-700 font-bold text-xs opacity-50">~</span>
                          </div>

                          {/* End Date Column */}
                          <div className="flex flex-col gap-1.5 flex-1">
                            <label className="text-[9px] font-bold text-slate-500 whitespace-nowrap pl-1"> 종료일 <span className="text-[7px] font-normal opacity-50">(입력하지 않으면 현재 기준)</span></label>
                            <div className="flex items-center justify-end gap-1">
                              <input 
                                type="text" maxLength={4} placeholder="0000"
                                className="w-[38px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.eY} onChange={(e) => handleBoxChange(idx, 'eY', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">년</span>
                              <input 
                                type="text" maxLength={2} placeholder="00"
                                className="w-[24px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.eM} onChange={(e) => handleBoxChange(idx, 'eM', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">월</span>
                              <input 
                                type="text" maxLength={2} placeholder="00"
                                className="w-[24px] bg-slate-900 border border-slate-700 rounded-lg py-1 text-[9px] text-white text-center focus:border-blue-500 outline-none font-mono"
                                value={parts.eD} onChange={(e) => handleBoxChange(idx, 'eD', e.target.value)}
                              />
                              <span className="text-[8px] text-slate-600">일</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <DateRangePicker value={stock.customPeriod || ''} onChange={(val) => updateStockDetail(idx, { customPeriod: val })} />
                    </div>

                    <div className="space-y-2">
                      <p className="text-[9px] font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1 whitespace-nowrap">
                        {ICONS.Pattern}
                        매매 패턴 (중복 가능)
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {TRADE_PATTERNS.map(p => (
                          <button key={p} onClick={() => toggleStockPattern(idx, p)} className={`px-2 py-1 rounded-full text-[9px] font-medium border transition-all ${stock.patterns.includes(p) ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>{p}</button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            {nextButton}
          </div>
        </div>
      ) : (
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
          <div className="p-8 pt-2 shrink-0 relative z-20">
            {nextButton}
          </div>
        </>
      )}
    </div>
  );
};
