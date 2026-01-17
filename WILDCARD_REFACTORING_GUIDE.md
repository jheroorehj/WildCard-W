# WildCard 프로젝트 리팩토링 가이드

> **목적**: CLI 에이전트(Claude Code, Codex 등)가 WildCard 프로젝트의 노드 이름 및 폴더 구조를 워크플로우 설계와 일치시키도록 리팩토링하는 작업 가이드

---

## 📋 프로젝트 개요

**WildCard**는 투자 손실을 경험한 사용자에게 맞춤형 학습 경로를 제공하는 LangGraph 기반 에이전트 시스템입니다.

### 기술 스택
- **Backend**: FastAPI + LangGraph
- **LLM**: Upstage Solar Pro2
- **데이터**: yfinance, FinanceData, Serper API
- **상태 관리**: LangGraph StateGraph

### GitHub 저장소
```
https://github.com/jheroorehj/WildCard-W
```

---

## 🎯 TODO List

### Phase 1: 폴더명 변경 (우선순위: HIGH)

#### Task 1.1: N9 폴더명 변경
- [ ] `N9_Fallback_Handler/` → `N9_Learning_Pattern_Analyzer/` 로 변경
- [ ] 변경 후 모든 import 경로 업데이트

#### Task 1.2: N10 폴더명 변경  
- [ ] `N10_Report_Writer/` → `N10_Learning_Tutor/` 로 변경
- [ ] 변경 후 모든 import 경로 업데이트

---

### Phase 2: Import 경로 수정 (우선순위: HIGH)

#### Task 2.1: 영향받는 파일 확인 및 수정

**확인 필요 파일 목록:**
```
├── workflow/graph.py
├── nodes/n9_learning_pattern.py
├── nodes/n10_learning_tutor.py
├── app/api.py (있다면)
├── app/service/ (하위 파일들)
└── 기타 테스트 파일들
```

#### Task 2.2: Import 패턴 수정

**Before:**
```python
from N9_Fallback_Handler.n9 import node9_fallback_handler
from N10_Report_Writer.n10 import node10_loss_review_report
```

**After:**
```python
from N9_Learning_Pattern_Analyzer.n9 import node9_learning_pattern_analyzer
from N10_Learning_Tutor.n10 import node10_learning_tutor
```

---

### Phase 3: 함수명 통일 (우선순위: MEDIUM)

#### Task 3.1: N9 함수명 변경

| 파일 | 현재 함수명 | 변경 후 함수명 |
|------|------------|---------------|
| `N9_*/n9.py` | `node9_fallback_handler` | `node9_learning_pattern_analyzer` |
| `N9_*/__init__.py` | export 수정 | 동일하게 변경 |

#### Task 3.2: N10 함수명 변경

| 파일 | 현재 함수명 | 변경 후 함수명 |
|------|------------|---------------|
| `N10_*/n10.py` | `node10_loss_review_report` | `node10_learning_tutor` |
| `N10_*/__init__.py` | export 수정 | 동일하게 변경 |

---

### Phase 4: nodes/ 폴더 내 래퍼 함수 확인 (우선순위: MEDIUM)

#### Task 4.1: nodes/n9_learning_pattern.py 확인
```python
# 확인사항:
# 1. N9_Fallback_Handler를 import하는지 확인
# 2. import 경로가 새 폴더명과 일치하는지 확인
# 3. 함수명이 graph.py에서 사용하는 이름과 일치하는지 확인
```

#### Task 4.2: nodes/n10_learning_tutor.py 확인
```python
# 확인사항:
# 1. N10_Report_Writer를 import하는지 확인
# 2. import 경로가 새 폴더명과 일치하는지 확인
# 3. 함수명이 graph.py에서 사용하는 이름과 일치하는지 확인
```

---

### Phase 5: graph.py 업데이트 (우선순위: HIGH)

#### Task 5.1: 노드 등록 확인
```python
# workflow/graph.py에서 확인할 사항

# 현재 구조:
g.add_node("N9", node9_learning_pattern)
g.add_node("N10", node10_learning_tutor)

# 함수명 변경 시 업데이트 필요 여부 확인
```

---

### Phase 6: 테스트 및 검증 (우선순위: HIGH)

#### Task 6.1: Import 테스트
```bash
# 프로젝트 루트에서 실행
python -c "from workflow.graph import build_graph; print('Import OK')"
```

#### Task 6.2: 노드 실행 테스트
```bash
# 각 노드 개별 테스트
python -c "from N9_Learning_Pattern_Analyzer import node9_learning_pattern_analyzer; print('N9 OK')"
python -c "from N10_Learning_Tutor import node10_learning_tutor; print('N10 OK')"
```

#### Task 6.3: 전체 워크플로우 테스트
```bash
# 샘플 입력으로 전체 파이프라인 테스트
python -m pytest tests/ -v
```

---

## 📊 현재 vs 목표 네이밍 비교

### 폴더 구조

| 현재 폴더명 | 목표 폴더명 | 워크플로우 노드명 |
|------------|------------|-----------------|
| `N1_Input_Handler/` | ✅ 유지 | N1: Loss Input |
| `N6_Stock_Analyst/` | ✅ 유지 | N6: Stock Analyst |
| `N7_News_Summarizer/` | ✅ 유지 | N7: News Summarizer |
| `N8_Loss_Analyst/` | ✅ 유지 | N8: 손실 분석가 |
| `N9_Fallback_Handler/` | **→ `N9_Learning_Pattern_Analyzer/`** | N9: 학습 패턴 분석가 |
| `N10_Report_Writer/` | **→ `N10_Learning_Tutor/`** | N10: 투자 학습 튜터 |

### 함수 네이밍 컨벤션

| 노드 ID | 현재 함수명 | 목표 함수명 |
|---------|------------|------------|
| N1 | `node1_loss_input` | ✅ 유지 |
| N6 | `node6_stock_analyst_wrapper` | ✅ 유지 |
| N7 | `node7_news_summarizer_wrapper` | ✅ 유지 |
| N8 | `node8_loss_analyzer` | ✅ 유지 |
| N9 | `node9_fallback_handler` | **→ `node9_learning_pattern_analyzer`** |
| N10 | `node10_loss_review_report` | **→ `node10_learning_tutor`** |
| N4 | `node4_chat_entry` | ✅ 유지 |

---

## 🔍 기능 검증 결과 (변경 불필요)

### N9: 학습 패턴 분석가 - 기능 일치 ✅

**워크플로우 요구사항:**
- 투자 사유 조합 분석 ✅
- 패턴의 강점/약점 균형 서술 ✅
- 보완 학습 방향 제시 ✅

**현재 코드 출력 스키마:**
```json
{
  "learning_pattern_analysis": {
    "pattern_summary": "투자 판단 패턴 요약",
    "pattern_strengths": ["장점"],
    "pattern_weaknesses": ["한계"],
    "learning_recommendation": {
      "focus_area": "보완 영역",
      "learning_reason": "학습 이유",
      "learning_steps": ["단계"],
      "recommended_topics": ["추천 주제"]
    }
  }
}
```

### N10: 투자 학습 튜터 - 기능 일치 ✅

**워크플로우 요구사항:**
- 3가지 분석 종합 (손실 원인, 시장 상황, 학습 패턴) ✅
- 맞춤형 투자 학습 경로 제시 ✅
- 학습 자료 생성 ✅
- 공감 기반 조언 문구 ✅
- 행동 유도 추천 질문 생성 ✅

**현재 코드 출력 스키마:**
```json
{
  "learning_tutor": {
    "custom_learning_path": {
      "path_summary": "학습 경로 요약",
      "learning_materials": ["학습 자료"],
      "practice_steps": ["실행 단계"],
      "recommended_topics": ["추천 주제"]
    },
    "investment_advisor": {
      "advisor_message": "공감 기반 조언",
      "recommended_questions": ["행동 유도 질문"]
    }
  }
}
```

---

## ⚠️ 주의사항

### 1. 파일 수정 순서
```
1. 폴더명 변경 (mv 명령어)
2. __init__.py 내 export 수정
3. 메인 함수 파일(n9.py, n10.py) 내 함수명 수정
4. nodes/ 폴더 내 래퍼 파일 import 경로 수정
5. workflow/graph.py import 경로 수정
6. 테스트 실행
```

### 2. Git 작업 권장사항
```bash
# 변경 전 브랜치 생성
git checkout -b refactor/rename-nodes

# 폴더명 변경 (git mv 사용으로 히스토리 보존)
git mv N9_Fallback_Handler N9_Learning_Pattern_Analyzer
git mv N10_Report_Writer N10_Learning_Tutor

# 커밋 메시지 예시
git commit -m "refactor: rename N9, N10 folders to match workflow design"
```

### 3. IDE/Editor 검색 패턴
```
# 전체 프로젝트에서 검색해야 할 문자열
- "N9_Fallback_Handler"
- "N10_Report_Writer"
- "node9_fallback_handler"
- "node10_loss_review_report"
```

---

## 📁 예상 최종 프로젝트 구조

```
WildCard-W/
├── N1_Input_Handler/
│   ├── __init__.py
│   └── n1.py
├── N6_Stock_Analyst/
│   ├── __init__.py
│   ├── n6.py
│   ├── judge.py
│   ├── prompt.py
│   └── schema.py
├── N7_News_Summarizer/
│   ├── __init__.py
│   ├── n7.py
│   ├── prompt.py
│   ├── schema.py
│   ├── search_tool.py
│   └── metrics.py
├── N8_Loss_Analyst/
│   ├── __init__.py
│   ├── n8.py
│   ├── prompt.py
│   └── schema.py
├── N9_Learning_Pattern_Analyzer/    # ← 변경됨
│   ├── __init__.py
│   ├── n9.py
│   ├── prompt.py
│   └── schema.py
├── N10_Learning_Tutor/               # ← 변경됨
│   ├── __init__.py
│   ├── n10.py
│   └── prompt.py
├── nodes/
│   ├── __init__.py
│   ├── n1_loss_input.py
│   ├── n4_chat_entry.py
│   ├── n6_stock_analyst.py
│   ├── n7_news_summarizer.py
│   ├── n8_loss_analyzer.py
│   ├── n9_learning_pattern.py        # import 경로 수정 필요
│   └── n10_learning_tutor.py         # import 경로 수정 필요
├── workflow/
│   └── graph.py                      # import 경로 수정 필요
├── state/
│   ├── __init__.py
│   ├── main_state.py
│   └── combined_schema.json
├── app/
│   ├── __init__.py
│   ├── api.py
│   ├── server.py
│   └── service/
├── core/
├── utils/
├── metrics/
└── frontend/
```

---

## 🚀 실행 명령어 요약

```bash
# 1. 폴더명 변경
git mv N9_Fallback_Handler N9_Learning_Pattern_Analyzer
git mv N10_Report_Writer N10_Learning_Tutor

# 2. 전체 검색 및 치환 (sed 예시)
# macOS:
find . -type f -name "*.py" -exec sed -i '' 's/N9_Fallback_Handler/N9_Learning_Pattern_Analyzer/g' {} +
find . -type f -name "*.py" -exec sed -i '' 's/N10_Report_Writer/N10_Learning_Tutor/g' {} +

# Linux:
find . -type f -name "*.py" -exec sed -i 's/N9_Fallback_Handler/N9_Learning_Pattern_Analyzer/g' {} +
find . -type f -name "*.py" -exec sed -i 's/N10_Report_Writer/N10_Learning_Tutor/g' {} +

# 3. 함수명 치환 (선택사항)
find . -type f -name "*.py" -exec sed -i '' 's/node9_fallback_handler/node9_learning_pattern_analyzer/g' {} +
find . -type f -name "*.py" -exec sed -i '' 's/node10_loss_review_report/node10_learning_tutor/g' {} +

# 4. Import 테스트
python -c "from workflow.graph import build_graph; g = build_graph(); print('Build OK')"

# 5. 커밋
git add .
git commit -m "refactor: rename N9, N10 to match workflow design

- N9_Fallback_Handler → N9_Learning_Pattern_Analyzer
- N10_Report_Writer → N10_Learning_Tutor
- Updated all import paths and function names"
```

---

## 📝 체크리스트

### 리팩토링 전 확인
- [ ] 현재 코드가 정상 작동하는지 테스트
- [ ] 변경 전 브랜치 생성 완료
- [ ] 백업 또는 스테이징 완료

### 리팩토링 중 확인
- [ ] N9 폴더명 변경 완료
- [ ] N10 폴더명 변경 완료
- [ ] `__init__.py` 파일들 export 수정 완료
- [ ] `nodes/` 폴더 내 import 경로 수정 완료
- [ ] `workflow/graph.py` import 경로 수정 완료
- [ ] 기타 참조 파일 수정 완료

### 리팩토링 후 확인
- [ ] Python import 테스트 통과
- [ ] 전체 워크플로우 빌드 테스트 통과
- [ ] 샘플 입력으로 파이프라인 실행 테스트 통과
- [ ] Git 커밋 및 푸시 완료

---

## 🔗 참고 자료

- **워크플로우 이미지**: `/mnt/user-data/uploads/버전4_워크플로우.png`
- **LangGraph 문서**: https://langchain-ai.github.io/langgraph/
- **프로젝트 저장소**: https://github.com/jheroorehj/WildCard-W

---

*이 문서는 CLI 에이전트가 WildCard 프로젝트를 리팩토링할 때 참고하는 가이드입니다.*
*작성일: 2025-01-17*
