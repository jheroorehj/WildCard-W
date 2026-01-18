import React from 'react';
import { IfThenPlan } from '../../types';

interface IfThenPlanCardProps {
  plan: IfThenPlan;
}

export const IfThenPlanCard: React.FC<IfThenPlanCardProps> = ({ plan }) => {
  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-4 mt-3">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base">🧠</span>
        <h4 className="text-[11px] font-bold text-emerald-400 tracking-tight">
          나의 행동 서약
        </h4>
      </div>

      <div className="space-y-3">
        {/* IF 섹션 */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-[10px] font-bold text-amber-400 px-1.5 py-0.5 bg-amber-500/20 rounded">
              IF
            </span>
            <span className="text-[10px] text-amber-400/70">이 상황이 오면</span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-start gap-2">
              <span className="text-[10px] text-slate-400 w-10 shrink-0">상황:</span>
              <span className="text-[11px] text-slate-200">{plan.trigger_situation}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-[10px] text-slate-400 w-10 shrink-0">감정:</span>
              <span className="text-[11px] text-slate-200">{plan.trigger_emotion}</span>
            </div>
          </div>
        </div>

        {/* 화살표 */}
        <div className="flex justify-center">
          <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>

        {/* THEN 섹션 */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-[10px] font-bold text-emerald-400 px-1.5 py-0.5 bg-emerald-500/20 rounded">
              THEN
            </span>
            <span className="text-[10px] text-emerald-400/70">이렇게 행동한다</span>
          </div>
          <p className="text-[11px] text-slate-200">{plan.then_action}</p>
        </div>

        {/* 서약문 */}
        <div className="bg-slate-900/60 border border-slate-600/30 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-base">✍️</span>
            <span className="text-[10px] font-bold text-slate-300">서약문</span>
          </div>
          <p className="text-[11px] text-slate-300 italic leading-relaxed">
            "{plan.commitment_phrase}"
          </p>
        </div>
      </div>
    </div>
  );
};

export default IfThenPlanCard;
