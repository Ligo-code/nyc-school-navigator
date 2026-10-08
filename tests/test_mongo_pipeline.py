from copy import deepcopy
from unittest.mock import Mock

import numpy as np
import pytest

from nyc_school_navigator.ingestion import indexer
from nyc_school_navigator.retrieval import retrieve_sections


@pytest.fixture
def record():
    return {
        "content": "McAuliffe enrollment: 954",
        "metadata": {
            "dbn": "20K187", "section": "overview",
            "school_name": "The Christa McAuliffe School / I.S. 187",
            "source_type": "school_quality", "source_year": "2024-25",
        },
        "embedding": [0.1] * 384,
    }


def test_document_identity_is_deterministic_and_school_specific(record):
    metadata = record["metadata"]
    assert indexer.section_document_id(metadata) == "20K187:overview"
    assert indexer.section_document_id(dict(metadata)) == "20K187:overview"
    assert indexer.section_document_id({**metadata, "dbn": "21K228"}) != "20K187:overview"
    assert indexer.section_document_id({**metadata, "section": "family_experience"}) != "20K187:overview"


def test_upsert_preserves_fields_and_reuses_identity(record):
    original = deepcopy(record)
    collection = Mock()
    assert indexer.upsert_sections([record], collection=collection) == 1
    assert indexer.upsert_sections([record], collection=collection) == 1
    expected = ({"_id": "20K187:overview"}, {"$set": original})
    assert collection.update_one.call_count == 2
    for call in collection.update_one.call_args_list:
        assert call.args == expected
        assert call.kwargs == {"upsert": True}
    assert record == original


def test_ingestion_connects_real_loader_sections_embeddings_and_upserts():
    model = Mock()
    model.encode.return_value = np.ones((15, 384))
    collection = Mock()
    assert indexer.index_school_sections(collection=collection, model=model) == 15
    texts = model.encode.call_args.args[0]
    assert len(texts) == 15
    assert collection.update_one.call_count == 15
    identities = set()
    for text, call in zip(texts, collection.update_one.call_args_list, strict=True):
        identities.add(call.args[0]["_id"])
        stored = call.args[1]["$set"]
        assert stored["content"] == text
        assert stored["embedding"] == [1.0] * 384
        assert stored["metadata"]["source_year"] == "2024-25"
        assert call.kwargs == {"upsert": True}
    assert len(identities) == 15


@pytest.mark.parametrize("top_k", [1, 2, 5, 20])
def test_query_embedding_local_ranking_and_result_format(record, top_k):
    model = Mock()
    # Deliberately non-unit vectors prove that cosine uses both norms.
    model.encode.return_value = np.array([[2.0, *([0.0] * 383)]])
    collection = Mock()
    documents = [
        {**record, "_id": "opposite", "embedding": [-3.0, *([0.0] * 383)]},
        {**record, "_id": "orthogonal", "embedding": [0.0, 4.0, *([0.0] * 382)]},
        {**record, "_id": "aligned", "embedding": [5.0, *([0.0] * 383)]},
    ]
    original = deepcopy(documents)
    collection.find.return_value = iter(documents)
    query = "How large is McAuliffe?"
    results = retrieve_sections(query, top_k=top_k, collection=collection, model=model)
    model.encode.assert_called_once_with(
        [query], convert_to_numpy=True, normalize_embeddings=True,
        show_progress_bar=False,
    )
    collection.find.assert_called_once_with(
        {}, {"_id": 1, "content": 1, "metadata": 1, "embedding": 1}
    )
    collection.aggregate.assert_not_called()
    assert [result["_id"] for result in results] == ["aligned", "orthogonal", "opposite"][:top_k]
    assert [result["score"] for result in results] == pytest.approx([1.0, 0.0, -1.0][:top_k])
    for result in results:
        assert result["content"] == record["content"]
        assert result["metadata"] == record["metadata"]
        assert set(result) == {"_id", "content", "metadata", "score"}
    assert documents == original


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True, "5"])
def test_invalid_top_k_is_rejected_before_any_io(top_k):
    collection, model = Mock(), Mock()
    with pytest.raises(ValueError, match="top_k"):
        retrieve_sections("attendance", top_k=top_k, collection=collection, model=model)
    model.encode.assert_not_called()
    collection.find.assert_not_called()


@pytest.mark.parametrize("query", ["", "   ", None])
def test_empty_query_is_rejected_before_any_io(query):
    collection, model = Mock(), Mock()
    with pytest.raises(ValueError, match="query"):
        retrieve_sections(query, collection=collection, model=model)
    model.encode.assert_not_called()
    collection.find.assert_not_called()


def test_retrieval_can_return_no_matches():
    collection, model = Mock(), Mock()
    collection.find.return_value = iter([])
    model.encode.return_value = np.ones((1, 384))
    assert retrieve_sections("attendance", collection=collection, model=model) == []


@pytest.mark.parametrize("vector", [[0.0] * 384, [1.0] * 383, [float("nan")] * 384])
def test_invalid_stored_vectors_raise_clear_error(record, vector):
    collection, model = Mock(), Mock()
    model.encode.return_value = np.ones((1, 384))
    collection.find.return_value = iter([{**record, "_id": "invalid", "embedding": vector}])
    with pytest.raises(ValueError, match="stored embedding"):
        retrieve_sections("attendance", collection=collection, model=model)
