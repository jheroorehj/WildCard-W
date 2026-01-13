from app.service.embedding_service import EmbeddingService


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
