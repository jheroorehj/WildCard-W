import React, { useState } from 'react';
import { ActionMission } from '../../types';
import { IfThenPlanCard } from './IfThenPlanCard';

interface ActionMissionCardProps {
  mission: ActionMission;
  index: number;
}

const DifficultyBadge: React.FC<{ level: string }> = ({ level }) => {
  const styles: Record<string, string> = {
    easy: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    hard: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  };
  const labels: Record<string, string> = {
    easy: '쉬움',
    medium: '보통',
    hard: '어려움',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${styles[level] || styles.medium}`}>
      {labels[level] || level}
    </span>
  );
};

const ImpactBadge: React.FC<{ level: string }> = ({ level }) => {
  const styles: Record<string, string> = {
    low: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    medium: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    high: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  };
  const labels: Record<string, string> = {
    low: '효과 낮음',
    medium: '효과 보통',
    high: '효과 높음',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${styles[level] || styles.medium}`}>
      {labels[level] || level}
    </span>
  );
};

export const ActionMissionCard: React.FC<ActionMissionCardProps> = ({ mission, index }) => {
  const [showIfThen, setShowIfThen] = useState(false);

  return (
    <div className="bg-slate-900/40 border border-slate-700/50 rounded-2xl p-4">
      {/* 헤더 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-emerald-400 px-2 py-0.5 bg-emerald-500/20 rounded-full">
            #{mission.priority} 우선순위
          </span>
          <span className="text-[10px] text-slate-500">{mission.mission_id}</span>
        </div>
      </div>

      {/* 미션 제목 */}
      <div className="flex items-start gap-2 mb-2">
        <span className="text-base">📋</span>
        <h5 className="text-[13px] font-bold text-slate-200">{mission.title}</h5>
      </div>

      {/* 설명 */}
      <p className="text-[11px] text-slate-400 leading-relaxed mb-3 pl-6">
        {mission.description}
      </p>

      {/* 목표 & 기대효과 */}
      <div className="bg-slate-800/40 rounded-xl p-3 mb-3">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-[10px]">🎯</span>
          <div>
            <span className="text-[10px] text-slate-500">목표: </span>
            <span className="text-[10px] text-emerald-400">{mission.behavioral_target}</span>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-[10px]">✨</span>
          <div>
            <span className="text-[10px] text-slate-500">기대효과: </span>
            <span className="text-[10px] text-slate-300">{mission.expected_outcome}</span>
          </div>
        </div>
      </div>

      {/* 배지들 */}
      <div className="flex items-center gap-2 mb-3">
        <DifficultyBadge level={mission.difficulty} />
        <ImpactBadge level={mission.estimated_impact} />
      </div>

      {/* If-Then 플랜 토글 */}
      {mission.if_then_plan && (
        <>
          <button
            onClick={() => setShowIfThen(!showIfThen)}
            className="w-full flex items-center justify-between px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[11px] text-emerald-400 hover:bg-emerald-500/20 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <span>🧠</span>
              <span>행동 서약 {showIfThen ? '접기' : '보기'}</span>
            </span>
            <svg
              className={`w-4 h-4 transition-transform ${showIfThen ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showIfThen && <IfThenPlanCard plan={mission.if_then_plan} />}
        </>
      )}
    </div>
  );
};

export default ActionMissionCard;
