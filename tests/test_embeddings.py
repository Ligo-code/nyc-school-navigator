from copy import deepcopy
from unittest.mock import Mock

import numpy as np
import pytest

from nyc_school_navigator.ingestion import embeddings


@pytest.fixture
def sections():
    return [
        {
            "content": "McAuliffe enrollment: 954",
            "metadata": {
                "dbn": "20K187",
                "school_name": "The Christa McAuliffe School / I.S. 187",
                "section": "overview",
                "source_type": "school_quality",
                "source_year": "2024-25",
                "extra_source_field": "preserve this too",
            },
        },
        {
            "content": "Boody attendance: 92.1%",
            "metadata": {
                "dbn": "21K228",
                "school_name": "I.S. 228 David A. Boody",
                "section": "student_outcomes",
                "source_type": "school_quality",
                "source_year": "2024-25",
            },
        },
    ]


@pytest.fixture
def model():
    # Test the wrapper without downloading a model or running neural inference.
    model = Mock()
    model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return model


def test_embeds_content_only_in_one_batch(sections, model):
    results = embeddings.embed_sections(sections, model=model)
    assert len(results) == len(sections)
    model.encode.assert_called_once_with(
        [section["content"] for section in sections],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )


def test_preserves_content_metadata_and_input(sections, model):
    original = deepcopy(sections)
    results = embeddings.embed_sections(sections, model=model)
    assert sections == original
    for section, result in zip(sections, results, strict=True):
        assert result["content"] == section["content"]
        assert result["metadata"] == section["metadata"]
        assert "embedding" not in section
    results[0]["metadata"]["dbn"] = "changed"
    assert sections == original


def test_returns_numeric_vectors_with_consistent_dimensions(sections, model):
    results = embeddings.embed_sections(sections, model=model)
    assert {len(result["embedding"]) for result in results} == {3}
    assert all(
        isinstance(value, float)
        for result in results
        for value in result["embedding"]
    )
    # Distinct encoder outputs must stay associated with their original texts.
    assert results[0]["embedding"] == [0.1, 0.2, 0.3]
    assert results[1]["embedding"] == [0.4, 0.5, 0.6]
    assert results[0]["embedding"] != results[1]["embedding"]


def test_default_model_is_local_baseline_on_cpu(monkeypatch, sections, model):
    constructor = Mock(return_value=model)
    monkeypatch.setattr(embeddings, "SentenceTransformer", constructor)
    assert len(embeddings.embed_sections(sections)) == 2
    constructor.assert_called_once_with(embeddings.MODEL_NAME, device="cpu")


def test_empty_input_does_not_load_model(monkeypatch):
    constructor = Mock()
    monkeypatch.setattr(embeddings, "SentenceTransformer", constructor)
    assert embeddings.embed_sections([]) == []
    constructor.assert_not_called()
