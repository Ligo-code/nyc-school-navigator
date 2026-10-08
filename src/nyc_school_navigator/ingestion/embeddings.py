from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def embed_sections(
    sections: list[dict], *, model: SentenceTransformer | None = None
) -> list[dict]:
    """Embed section content locally, retaining text and all metadata.

    Supply an already loaded model to reuse it across calls. Otherwise load
    the baseline model on CPU; its first use downloads weights, and later
    uses read the local model cache. Empty input does not load a model.
    """
    if not sections:
        return []

    if model is None:
        model = SentenceTransformer(MODEL_NAME, device="cpu")

    vectors = model.encode(
        [section["content"] for section in sections],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return [
        {
            **section,
            "metadata": dict(section["metadata"]),
            "embedding": vector.tolist(),
        }
        for section, vector in zip(sections, vectors, strict=True)
    ]
