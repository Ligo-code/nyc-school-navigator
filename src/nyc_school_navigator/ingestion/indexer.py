from pathlib import Path

from nyc_school_navigator.ingestion.chunking import section_school_quality
from nyc_school_navigator.ingestion.embeddings import embed_sections
from nyc_school_navigator.ingestion.loaders import load_school_quality


WORKBOOK_PATH = (
    Path(__file__).resolve().parents[3]
    / "data/raw/school_quality/202425-ems-sqr-results.xlsx"
)


def section_document_id(metadata: dict) -> str:
    """Identify a section independently of its content or ingestion run."""
    return f'{metadata["dbn"]}:{metadata["section"]}'


def upsert_sections(records: list[dict], *, collection=None) -> int:
    """Write embedded sections using MongoDB's unique _id to avoid duplicates.

    Return the number of successfully processed records, not newly inserted
    records. A supplied collection allows testing without settings or Atlas.
    """
    if collection is None:
        from nyc_school_navigator.db.mongo import get_school_collection

        collection = get_school_collection()

    for record in records:
        collection.update_one(
            {"_id": section_document_id(record["metadata"])},
            {"$set": {
                "content": record["content"],
                "metadata": record["metadata"],
                "embedding": record["embedding"],
            }},
            upsert=True,
        )
    return len(records)


def index_school_sections(
    workbook_path: str | Path = WORKBOOK_PATH, *, collection=None, model=None
) -> int:
    """Load the three schools, section, embed locally, and upsert into MongoDB."""
    sections = [
        section
        for record in load_school_quality(workbook_path)
        for section in section_school_quality(record)
    ]
    embedded = embed_sections(sections, model=model)
    return upsert_sections(embedded, collection=collection)
