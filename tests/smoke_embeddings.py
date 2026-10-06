"""Run separately with `uv run tests/smoke_embeddings.py` (downloads once)."""

import json
import math
from pathlib import Path

from nyc_school_navigator.ingestion.chunking import section_school_quality
from nyc_school_navigator.ingestion.embeddings import MODEL_NAME, embed_sections
from nyc_school_navigator.ingestion.loaders import load_school_quality


def main() -> None:
    workbook = (
        Path(__file__).resolve().parents[1]
        / "data/raw/school_quality/202425-ems-sqr-results.xlsx"
    )
    sections = [
        section
        for record in load_school_quality(workbook)
        for section in section_school_quality(record)
    ]
    records = embed_sections(sections)

    assert len(records) == len(sections) == 15
    for section, record in zip(sections, records, strict=True):
        assert record["content"] == section["content"]
        assert record["metadata"] == section["metadata"]
        assert len(record["embedding"]) == 384
        assert all(
            isinstance(value, float) and math.isfinite(value)
            for value in record["embedding"]
        )
    assert len({tuple(record["embedding"]) for record in records}) == 15

    print(json.dumps({
        "model": MODEL_NAME,
        "dimension": 384,
        "sections_embedded": len(records),
        "all_15_successful": True,
        "all_vectors_distinct": True,
        "example_metadata": records[0]["metadata"],
        "example_vector_prefix": records[0]["embedding"][:5],
    }, indent=2))


if __name__ == "__main__":
    main()
