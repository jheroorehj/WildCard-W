from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from supabase import Client, create_client

_supabase_client: Optional[Client] = None
_chroma_client: Optional[chromadb.ClientAPI] = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL or SUPABASE key is missing.")
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        persist_path = os.getenv(
            "CHROMA_PERSIST_PATH",
            str(Path(__file__).resolve().parent.parent / "data" / "chroma_db"),
        )
        Path(persist_path).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_path, settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_chroma_collection(name: str) -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)
