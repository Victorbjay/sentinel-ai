import logging
import math
import re
from functools import lru_cache
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_model():
    """
    Lazy-loads the lightweight ONNX-based FastEmbed model (384-dim).
    Uses BAAI/bge-small-en-v1.5 or sentence-transformers/all-MiniLM-L6-v2.
    """
    try:
        from fastembed import TextEmbedding

        model_name = settings.EMBEDDING_MODEL_NAME
        # FastEmbed supports sentence-transformers/all-MiniLM-L6-v2 and BAAI/bge-small-en-v1.5
        logger.info(f"Loading FastEmbed model: {model_name}")
        return TextEmbedding(model_name=model_name)
    except Exception as e:
        logger.warning(f"FastEmbed unavailable ({e}); falling back to deterministic hash embeddings.")
        return None


def _fallback_deterministic_embedding(text: str, dim: int = 384) -> List[float]:
    """Deterministic L2-normalized token-hash fallback when ONNX model is unavailable."""
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    for word in words:
        h = hash(word)
        idx1 = abs(h) % dim
        idx2 = abs(h * 31) % dim
        vec[idx1] += 1.0
        vec[idx2] += 0.5

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def generate_embedding(text: str) -> List[float]:
    """
    Generates an L2-normalized 384-dimensional semantic embedding for the given text.
    """
    if not text or not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION

    model = _get_embedding_model()
    if model is not None:
        try:
            # fastembed returns a generator of numpy arrays
            embeddings = list(model.embed([text]))
            if embeddings:
                vec = embeddings[0].tolist()
                return vec
        except Exception as e:
            logger.warning(f"FastEmbed inference error ({e}); using fallback.")

    return _fallback_deterministic_embedding(text, settings.EMBEDDING_DIMENSION)
