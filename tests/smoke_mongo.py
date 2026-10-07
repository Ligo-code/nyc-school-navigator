"""Manual Atlas check; see docs/mongodb.md. Never print credentials."""

import argparse
import json
import math

from sentence_transformers import SentenceTransformer

from nyc_school_navigator.ingestion.chunking import SECTION_CATEGORIES
from nyc_school_navigator.ingestion.embeddings import MODEL_NAME
from nyc_school_navigator.ingestion.indexer import index_school_sections
from nyc_school_navigator.ingestion.loaders import TARGET_SCHOOLS
from nyc_school_navigator.retrieval import retrieve_sections


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--ingest-only", action="store_true")
    modes.add_argument("--search-only", action="store_true")
    args = parser.parse_args()

    # Import only for this live workflow; unit tests do not load URI settings.
    from nyc_school_navigator.db.mongo import get_school_collection

    collection = get_school_collection()
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    if not args.search_only:
        for _ in range(2):
            processed = index_school_sections(collection=collection, model=model)
            assert processed == 15
            assert collection.count_documents({}) == 15, (
                "Expected exactly 15 documents in the dedicated collection"
            )

    expected = {
        f"{dbn}:{category}"
        for dbn in TARGET_SCHOOLS
        for category in SECTION_CATEGORIES.values()
    }
    documents = list(collection.find({}, {"_id": 1, "metadata": 1}))
    assert len(documents) == 15
    assert {document["_id"] for document in documents} == expected
    assert {
        (document["metadata"]["dbn"], document["metadata"]["section"])
        for document in documents
    } == {
        (dbn, category)
        for dbn in TARGET_SCHOOLS
        for category in SECTION_CATEGORIES.values()
    }

    print("Verified: exactly 15 logical school sections.")
    if not args.search_only:
        print("Verified: two ingestion runs produced no duplicates.")
    if args.ingest_only:
        print("Next: run --search-only; no Atlas Search index is needed.")
        return

    query = "How many students are enrolled at The Christa McAuliffe School?"
    results = retrieve_sections(query, top_k=3, collection=collection, model=model)
    assert results, (
        "No search results: verify school_sections contains embedded documents"
    )
    assert len(results) == 3
    assert [result["score"] for result in results] == sorted(
        (result["score"] for result in results), reverse=True
    )
    for result in results:
        assert result["_id"] in expected
        assert result["content"]
        assert result["metadata"]["source_year"] == "2024-25"
        assert isinstance(result["score"], float)
        assert math.isfinite(result["score"])
        assert -1.0 <= result["score"] <= 1.0
        assert "embedding" not in result
    print(json.dumps({"query": query, "results": results}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        raise SystemExit(str(error)) from None
    except Exception as error:
        # Driver/config exceptions can include connection details; omit them.
        raise SystemExit(
            f"Atlas smoke check failed ({type(error).__name__}). "
            "Check MONGODB_URI, Atlas Network Access, database permissions, "
            "and stored embeddings. No Atlas Search index is required. Credentials are not logged."
        ) from None
