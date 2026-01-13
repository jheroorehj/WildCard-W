"""
WildCard LLM 코어(팩토리)
- Upstage Solar(Pro2) Chat 모델과 Upstage Embeddings를 로드하는 모듈

필수 환경 변수:
- UPSTAGE_API_KEY

선택 환경 변수:
- UPSTAGE_CHAT_MODEL (기본값: solar-pro2)
- UPSTAGE_EMBEDDING_MODEL (기본값: solar-embedding-1-large)

주의:
- Kubernetes 배포 환경에서는 ConfigMap/Secret로 env가 주입되므로 .env 로드를 건너뜁니다.
- 로컬 개발 환경에서는 .env.local (우선) 또는 .env를 자동으로 로드합니다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_upstage import ChatUpstage, UpstageEmbeddings


def _load_env_if_local() -> None:
    """K8s 환경이 아니면 로컬 개발 환경으로 보고 .env 또는 .env.local을 로드합니다."""
    if os.getenv("KUBERNETES_SERVICE_HOST") is None:
        # 현재 작업 디렉터리부터, 그 다음 이 파일 기준으로 상위 탐색
        # .env.local을 우선적으로 찾고, 없으면 .env를 찾습니다
        for base in (Path.cwd(), Path(__file__).resolve()):
            current = base if base.is_dir() else base.parent
            for parent in [current, *current.parents]:
                # .env.local 우선
                candidate_local = parent / ".env.local"
                if candidate_local.is_file():
                    load_dotenv(dotenv_path=candidate_local, override=False)
                    return
                # .env 대체
                candidate = parent / ".env"
                if candidate.is_file():
                    load_dotenv(dotenv_path=candidate, override=False)
                    return
        # Fallback: 기본 동작 (예: 환경 변수가 이미 설정됨)
        load_dotenv(override=False)


class UpstageClient:
    """
    Upstage Solar Chat/Embedding 인스턴스를 캐시하는 경량 클라이언트
    - 모델 인스턴스 생성 비용/오버헤드를 줄이기 위해 최초 1회만 생성 후 캐시합니다.
    """

    _instance: Optional["UpstageClient"] = None

    def __new__(cls) -> "UpstageClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # __init__가 여러 번 호출될 수 있으므로 중복 초기화 방지
        if getattr(self, "_initialized", False):
            return

        _load_env_if_local()

        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 필요합니다.")

        self.chat_model_name = os.getenv("UPSTAGE_CHAT_MODEL", "solar-pro2")
        self.embedding_model_name = os.getenv(
            "UPSTAGE_EMBEDDING_MODEL", "solar-embedding-1-large"
        )

        self._chat_instance: Optional[ChatUpstage] = None
        self._embedding_instance: Optional[UpstageEmbeddings] = None
        self._initialized = True

    def get_chat_model(self) -> ChatUpstage:
        if self._chat_instance is None:
            self._chat_instance = ChatUpstage(
                api_key=self.api_key,
                model=self.chat_model_name,
            )
        return self._chat_instance

    def get_embedding_model(self) -> UpstageEmbeddings:
        if self._embedding_instance is None:
            self._embedding_instance = UpstageEmbeddings(
                api_key=self.api_key,
                model=self.embedding_model_name,
            )
        return self._embedding_instance


# ---- 팩토리 함수 (프로젝트 전역에서 사용) ----
_client = UpstageClient()


def get_solar_chat() -> ChatUpstage:
    """
    Upstage Solar Chat 모델을 반환합니다.
    사용처:
    - WildCard/N3/node.py 등 LLM 호출이 필요한 모든 노드
    """
    return _client.get_chat_model()


def get_upstage_embeddings() -> UpstageEmbeddings:
    """
    Upstage Embedding 모델을 반환합니다.
    사용처:
    - VectorDB 구축/검색 RAG 등
    """
    return _client.get_embedding_model()

