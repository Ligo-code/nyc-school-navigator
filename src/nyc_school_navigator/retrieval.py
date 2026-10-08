import numpy as np

from nyc_school_navigator.ingestion.embeddings import embed_sections


def retrieve_sections(
    query: str, *, top_k: int = 5, collection=None, model=None
) -> list[dict]:
    """Read sections from MongoDB and rank them by local cosine similarity.

    MongoDB provides persistence only. Scores range from -1 to 1; larger
    values mean closer vector directions, not greater factual confidence.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    if collection is None:
        from nyc_school_navigator.db.mongo import get_school_collection

        collection = get_school_collection()

    query_vector = embed_sections(
        [{"content": query, "metadata": {}}], model=model
    )[0]["embedding"]

    query_vector = np.asarray(query_vector, dtype=float)
    query_norm = np.linalg.norm(query_vector)
    if query_vector.ndim != 1 or not np.isfinite(query_vector).all() or query_norm == 0:
        raise ValueError("query embedding must be a finite, non-zero vector")

    results = []
    documents = collection.find(
        {}, {"_id": 1, "content": 1, "metadata": 1, "embedding": 1}
    )
    for document in documents:
        vector = np.asarray(document["embedding"], dtype=float)
        norm = np.linalg.norm(vector)
        if vector.shape != query_vector.shape or not np.isfinite(vector).all() or norm == 0:
            raise ValueError("stored embedding must match query dimensions and be finite and non-zero")
        score = float(np.dot(query_vector, vector) / (query_norm * norm))
        results.append({
            "_id": document["_id"],
            "content": document["content"],
            "metadata": document["metadata"],
            "score": float(np.clip(score, -1.0, 1.0)),
        })

    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:top_k]
