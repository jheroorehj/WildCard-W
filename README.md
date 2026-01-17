# WildCard - AI 기반 투자 분석 플랫폼

투자 손실을 분석하고 학습 경로를 제공하는 LangGraph 기반 AI 에이전트 시스템

## 🏗 프로젝트 구조

```
WildCard/
├── .env.local                      # 환경 변수 설정 (gitignore됨)
├── frontend/                       # React 프론트엔드
├── core/                           # LLM 코어 모듈
├── N6_Stock_Analyst/               # 주식 분석 노드
├── N7_News_Summarizer/             # 뉴스 요약 노드
├── N8_Loss_Analyst/                # 손실 분석 노드
├── N9_Learning_Pattern_Analyzer/   # 학습 패턴 분석 노드
├── N10_Learning_Tutor/             # 투자 학습 튜터
├── state/                          # 상태 관리
├── utils/                          # 유틸리티
└── workflow/                       # 워크플로우 정의
```

## 🚀 빠른 시작

### 1. 환경 변수 설정

프로젝트 루트에 `.env.local` 파일을 생성하고 다음 내용을 추가합니다:

```bash
# 필수: Upstage API 키
UPSTAGE_API_KEY=your_api_key_here

# 선택사항 (기본값이 설정되어 있음)
UPSTAGE_CHAT_MODEL=solar-pro2
UPSTAGE_EMBEDDING_MODEL=solar-embedding-1-large
```

**중요**:
- `.env.local` 파일은 프로젝트 **루트 디렉토리**에 위치해야 합니다
- 이 파일은 자동으로 gitignore되어 Git에 커밋되지 않습니다
- 프론트엔드와 백엔드 모두 이 파일을 자동으로 참조합니다

### 2. 백엔드 설정 (Python)

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 로드 테스트
python test_env.py
```

### 3. 프론트엔드 설정 (React)

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## 🔧 기술 스택

### Backend
- **Framework**: LangGraph
- **LLM**: Upstage Solar Pro 2
- **Embeddings**: Upstage Solar Embedding 1 Large
- **Language**: Python 3.10+

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **AI Integration**: Upstage Solar Pro 2 API

## 📝 환경 변수 참조 구조

### Backend (Python)

[core/llm.py](core/llm.py)가 자동으로 `.env.local` 또는 `.env`를 찾아 로드합니다:

1. 현재 작업 디렉토리부터 상위로 탐색
2. `.env.local` 우선 검색
3. 없으면 `.env` 검색
4. Kubernetes 환경에서는 ConfigMap/Secret 사용

### Frontend (React)

[frontend/vite.config.ts](frontend/vite.config.ts)가 프로젝트 루트의 `.env.local`을 로드:

```typescript
const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
```

이렇게 하면 `process.env.UPSTAGE_API_KEY`로 접근 가능합니다.

## 🧪 테스트

### 환경 변수 로드 테스트

```bash
python test_env.py
```

성공하면 다음과 같은 출력이 표시됩니다:

```
============================================================
환경 변수 로드 테스트
============================================================
✅ UPSTAGE_API_KEY 로드 성공: up_0sYYkCj********************
✅ Chat Model: solar-pro2
✅ Embedding Model: solar-embedding-1-large
✅ Chat Model 인스턴스 생성 성공: ChatUpstage
✅ Embedding Model 인스턴스 생성 성공: UpstageEmbeddings

============================================================
모든 테스트 통과! 🎉
============================================================
```

## 🔐 보안 주의사항

1. **절대 `.env.local` 파일을 Git에 커밋하지 마세요**
2. API 키가 노출되었다면 즉시 재발급하세요
3. 프로덕션 환경에서는 환경 변수를 시스템 레벨에서 관리하세요

## 📚 주요 기능

### N3 - Loss Analyzer
투자 손실 원인을 분석하고 학습 경로를 제공

### N6 - Stock Analyst
특정 종목에 대한 심층 분석

### N7 - News Summarizer
관련 뉴스를 요약하고 시장 맥락 제공

### N8 - Concept Explainer
투자 개념과 용어 설명

### N9 - Learning Pattern Analyzer

학습 패턴 분석 및 맞춤 학습 경로 제시

### N10 - Learning Tutor

투자 학습 튜터 및 공감 기반 조언

## 🤝 협업 가이드

Git 협업 규칙은 [GIT_COLLABORATION_GUIDE.md](GIT_COLLABORATION_GUIDE.md)를 참고하세요.

## 📄 라이센스

이 프로젝트는 팀 내부 사용을 위한 것입니다.

## 🙋‍♂️ 문의

프로젝트 관련 문의사항은 팀 채널을 통해 공유해주세요.
