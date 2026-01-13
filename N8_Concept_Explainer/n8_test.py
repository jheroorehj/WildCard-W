"""
N8 Concept Explainer 테스트 (학습 가이드 전용)
"""

import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from N8_Concept_Explainer.n8 import node8_concept_explainer


def test_learning_guide():
    print("=" * 50)
    print("테스트: 학습 가이드 모드")
    print("=" * 50)

    state = {
        "investment_pattern": "유튜브 추천 영상을 보고 충동적으로 매수",
        "loss_causes": [
            {"type": "information_bias", "description": "검증되지 않은 정보 의존"},
            {"type": "emotional_trading", "description": "감정 기반 의사결정"},
        ],
        "context": "손실 원인을 학습 관점으로 정리해줘",
    }

    result = node8_concept_explainer(state)
    explanation = result.get("n8_concept_explanation", {})
    guide = explanation.get("learning_guide", {})

    print("입력:")
    print(f"  - 투자 패턴: {state['investment_pattern']}")
    print(f"  - 손실 원인: {len(state['loss_causes'])}개")
    print("\n출력:")
    print(f"  - 약점 요약: {guide.get('weakness_summary')}")
    print(f"  - 학습 요약: {guide.get('learning_path_summary')}")
    print(f"  - 추천 주제: {guide.get('recommended_topics')}")
    print(f"  - 난이도: {guide.get('estimated_difficulty')}")
    print(f"  - 불확실성: {guide.get('uncertainty_level')}")


if __name__ == "__main__":
    try:
        test_learning_guide()
        print("\n테스트 완료")
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
