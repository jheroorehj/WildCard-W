import React from 'react';
import { LearningFrame } from '../../types';

interface LearningFrameCardProps {
  frame: LearningFrame;
}

export const LearningFrameCard: React.FC<LearningFrameCardProps> = ({ frame }) => {
  return (
    <div className="bg-slate-900/40 border border-emerald-500/20 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-base">🔄</span>
        <h4 className="text-[12px] font-bold text-emerald-400 tracking-tight">
          시각의 전환
        </h4>
      </div>

      <div className="space-y-4">
        {/* 손실 재정의 */}
        <div className="space-y-2">
          {/* 기존 시각 - 취소선 */}
          <div className="flex items-start gap-2">
            <span className="text-rose-400 text-[10px] mt-0.5">❌</span>
            <div>
              <span className="text-[10px] text-slate-500 block mb-0.5">기존 시각</span>
              <span className="text-[11px] text-slate-400 line-through">
                {frame.loss_reframe.original}
              </span>
            </div>
          </div>

          {/* 새로운 시각 */}
          <div className="flex items-start gap-2">
            <span className="text-emerald-400 text-[10px] mt-0.5">✓</span>
            <div>
              <span className="text-[10px] text-slate-500 block mb-0.5">새로운 시각</span>
              <span className="text-[11px] text-emerald-300 leading-relaxed">
                {frame.loss_reframe.reframed}
              </span>
            </div>
          </div>

          {/* 학습 가치 */}
          <div className="bg-slate-800/40 rounded-lg p-2.5 mt-2">
            <span className="text-[10px] text-slate-400">
              💡 {frame.loss_reframe.learning_value}
            </span>
          </div>
        </div>

        {/* 구분선 */}
        <div className="border-t border-slate-700/50" />

        {/* 강점 발견 */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-base">💪</span>
            <span className="text-[10px] font-bold text-emerald-400">발견된 강점</span>
          </div>
          <p className="text-[12px] text-emerald-300 font-medium">
            {frame.mistake_reframe.strength_focus}
          </p>
          <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">
            {frame.mistake_reframe.reframed}
          </p>
        </div>

        {/* 성장 메시지 */}
        <div className="text-center pt-2">
          <p className="text-[11px] text-slate-300 leading-relaxed">
            "{frame.progress_frame.message}"
          </p>
          <p className="text-[10px] text-slate-500 mt-1">
            {frame.progress_frame.comparison_anchor}
          </p>
        </div>
      </div>
    </div>
  );
};

export default LearningFrameCard;
