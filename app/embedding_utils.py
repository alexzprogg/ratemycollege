import numpy as np
import threading
from sentence_transformers import SentenceTransformer
from app import db
from .models import Review, ReviewEmbedding

_MODEL_NAME = "all-MiniLM-L6-v2"
_model_lock = threading.Lock()
_model_singleton = None

def _get_model():
    global _model_singleton
    with _model_lock:
        if _model_singleton is None:
            _model_singleton = SentenceTransformer(_MODEL_NAME)
        return _model_singleton

def _to_bytes(vec: np.ndarray) -> bytes:
    # ensure float32 for space
    if vec.dtype != np.float32:
        vec = vec.astype(np.float32)
    return vec.tobytes()

def _from_bytes(b: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32).reshape(dim)

def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    emb = model.encode([text], normalize_embeddings=True)  # (1, d)
    return emb[0].astype(np.float32)

def upsert_review_embedding(review_id: int):
    """Create or update the embedding row for a single review."""
    review = Review.query.get(review_id)
    if not review or not review.text:
        return

    vec = embed_text(review.text)
    dim = vec.shape[0]
    blob = _to_bytes(vec)

    existing = ReviewEmbedding.query.filter_by(review_id=review_id).first()
    if existing:
        existing.model = _MODEL_NAME
        existing.dim = dim
        existing.vector = blob
    else:
        rec = ReviewEmbedding(
            review_id=review_id,
            model=_MODEL_NAME,
            dim=dim,
            vector=blob,
        )
        db.session.add(rec)
    db.session.commit()

def batch_embed_all():
    """Embed every review that doesn’t have an embedding yet (or re-embed all if you like)."""
    q = Review.query.all()
    for r in q:
        upsert_review_embedding(r.id)
