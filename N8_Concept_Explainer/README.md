# N8: Concept Explainer (용어/개념 설명 노드)

## 📋 개요

N8은 경제/주식 용어 설명과 투자 학습 가이드를 제공하는 노드입니다.

**두 가지 모드로 동작:**
1. **용어 설명 모드**: 경제/주식 용어를 초보자도 이해할 수 있게 설명
2. **학습 가이드 모드**: 투자 패턴을 분석하여 맞춤형 학습 경로 제시

## 🎯 핵심 기능

### 1. 용어 설명 (Term Explanation)

**목적**: 일반인이 잘 모르는 경제/주식 용어를 쉽게 설명

**출력 구조**:
```json
{
  "n8_concept_explanation": {
    "mode": "term",
    "term_explanation": {
      "term": "볼린저 밴드",
      "short_summary": "주가의 변동성을 보여주는 기술적 지표",
      "detailed_explanation": "볼린저 밴드는 주가가 평균에서 얼마나 벗어나 있는지를 표준편차를 사용해 시각화한 지표입니다...",
      "simple_example": "평균 온도에서 ±10도 범위를 표시하는 것처럼, 주가도 평균에서 일정 범위 내에서 움직입니다.",
      "usage_context": "과매수/과매도 구간 판단, 변동성 확인",
      "related_terms": ["이동평균선", "RSI", "표준편차"],
      "uncertainty_level": "low"
    },
    "learning_guide": null
  }
}
```

**특징**:
- `short_summary`: 돋보기 누르기 전 기본 표시 (30자 이내)
- `detailed_explanation`: 돋보기 눌렀을 때 상세 설명 (200-400자)
- 전문 용어 최소화, 비유와 예시 활용

### 2. 학습 가이드 (Learning Guide)

**목적**: 사용자의 투자 패턴을 분석하여 부족한 부분과 학습 방법 제시

**출력 구조**:
```json
{
  "n8_concept_explanation": {
    "mode": "learning",
    "term_explanation": null,
    "learning_guide": {
      "weakness_summary": "정보 검증 능력 부족",
      "weakness_detailed": "유튜브 추천 영상만 믿고 투자하는 패턴이 보입니다. 정보의 출처와 신뢰도를 검증하는 과정이 없었습니다...",
      "learning_path_summary": "정보 검증 → 기술적 분석 → 리스크 관리 순으로 학습",
      "learning_path_detailed": {
        "step1": "신뢰할 수 있는 정보원 구분하기 (기업 공시, 금융감독원 등)",
        "step2": "기본적인 재무제표 읽는 법 익히기",
        "step3": "손절선 설정과 리스크 관리 원칙 이해하기"
      },
      "recommended_topics": ["정보 검증", "재무제표 분석", "리스크 관리"],
      "estimated_difficulty": "보통",
      "uncertainty_level": "low"
    }
  }
}
```

**특징**:
- `weakness_summary`: 돋보기 누르기 전 기본 표시 (30자 이내)
- `weakness_detailed`, `learning_path_detailed`: 돋보기 눌렀을 때 표시
- 3단계 학습 경로 제시
- 구체적이고 실행 가능한 가이드

## 🔄 워크플로우

```
N3 (가이드라인) → N5 (라우팅) → N8 (용어 설명 또는 학습 가이드)
                                    ↓
                                N10 (결과 통합)
```

## 📥 입력

### 용어 설명 모드
```python
state = {
    "mode": "term",
    "term": "볼린저 밴드",  # 필수
    "context": "주가 분석 중 접한 용어"  # 선택
}
```

### 학습 가이드 모드
```python
state = {
    "mode": "learning",
    "investment_pattern": "유튜브 추천으로 매수",  # 필수
    "loss_causes": [...],  # 선택 (N3 분석 결과)
    "context": "추가 맥락"  # 선택
}
```

## 📤 출력

**공통 구조**:
```python
{
  "n8_concept_explanation": {
    "mode": "term" | "learning",
    "term_explanation": {...} | None,
    "learning_guide": {...} | None
  }
}
```

## 🛠 구현 세부사항

### 파일 구조
```
N8_Concept_Explainer/
├── __init__.py
├── n8.py              # 메인 로직
├── prompt.py          # 프롬프트 정의
├── schema.py          # 스키마 상수
├── n8_test.py         # 테스트 파일
└── README.md          # 이 문서
```

### 주요 함수

#### `node8_concept_explainer(state)`
메인 진입점. mode에 따라 적절한 함수 호출.

#### `explain_term(state)`
용어 설명 모드 처리.
- LLM으로 용어 설명 생성
- RAG 검색 (TODO: 구현 예정)
- 안전성 검사 & 스키마 검증

#### `provide_learning_guide(state)`
학습 가이드 모드 처리.
- 투자 패턴 분석
- 맞춤형 학습 경로 생성
- 안전성 검사 & 구조 검증

### Fallback 처리

3가지 fallback 함수:
1. `fallback_result()`: 일반 에러
2. `fallback_result_term()`: 용어 설명 실패
3. `fallback_result_learning()`: 학습 가이드 실패

**Fallback 발생 조건**:
- 필수 입력값 누락
- LLM 응답 파싱 실패
- 안전성 검사 실패 (투자 조언 포함)
- 스키마 검증 실패

## 🧪 테스트

### 테스트 실행
```bash
cd N8_Concept_Explainer
python n8_test.py
```

### 테스트 케이스
1. **용어 설명 모드**: "볼린저 밴드" 설명
2. **학습 가이드 모드**: 충동 매수 패턴 분석
3. **Fallback 테스트**: 필수 입력값 누락

## 📊 Validator 연동

`utils/validator.py`의 `validate_node8()` 사용.

**검증 항목**:
```python
{
  "concept_explanation": {
    "term": str,                    # 필수
    "short_definition": str,        # 필수
    "beginner_explanation": str,    # 필수
    "examples": [str],             # 필수 (리스트)
    "related_terms": [str],        # 필수 (리스트)
    "uncertainty_level": "low|medium|high"  # 필수
  }
}
```

## 🔮 향후 개선 사항

### 1. RAG 구현 (우선순위: 높음)
```python
def search_term_in_knowledge_base(term: str) -> str:
    # TODO: 벡터 DB 구축
    # - Chroma 또는 FAISS 사용
    # - 경제/주식 용어 문서 임베딩
    # - 유사도 기반 검색
    pass
```

**필요 작업**:
- 경제/주식 용어 데이터 수집
- 임베딩 모델 선택 (Upstage Embeddings?)
- 벡터 DB 구축
- 검색 로직 구현

### 2. 학습 자료 링크 제공
```json
{
  "learning_guide": {
    ...
    "resources": [
      {
        "title": "볼린저 밴드 이해하기",
        "url": "https://...",
        "type": "article|video|book"
      }
    ]
  }
}
```

### 3. 난이도 맞춤형 설명
사용자 레벨에 따라 설명 난이도 조절:
- Beginner: 비유 중심
- Intermediate: 개념 설명 + 예시
- Advanced: 심화 내용 + 수식

## 📝 팀원 참고사항

### N6 (rladhs123)과의 연동
N8은 N6의 기술적 분석 결과에서 나온 용어를 설명할 수 있습니다.

**예시 플로우**:
```
N6 → "볼린저 밴드 상단 돌파" 언급
  ↓
N8 → "볼린저 밴드"란? 설명 제공
```

### N3 (cykim0919)과의 연동
N8은 N3의 가이드라인을 받아 어떤 개념을 설명할지 결정합니다.

```python
n3_guideline = {
    "n8_loss_cause_guideline": {
        "concepts_to_explain": ["볼린저 밴드", "손절매"]
    }
}
```

## 🤝 기여

N8 개선 제안이나 버그 리포트는 팀 채널에 공유해 주세요!

---

**구현자**: [Your Name]  
**구현일**: 2026-01-11  
**LLM**: Upstage Solar Pro 2  
**RAG**: TODO (구현 예정)
