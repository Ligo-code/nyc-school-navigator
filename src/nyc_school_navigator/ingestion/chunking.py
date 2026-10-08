from nyc_school_navigator.ingestion.normalizers import normalize_school_quality


# These headings are the semantic blocks produced by the existing normalizer.
SECTION_CATEGORIES = {
    "School size:": "overview",
    "Overall quality:": "school_quality",
    "School experience:": "student_experience",
    "Family experience:": "family_experience",
    "Student outcomes:": "student_outcomes",
}


def section_school_quality(record: dict) -> list[dict]:
    """Turn one loader record into five self-contained retrieval sections.

    Reuse normalized text and metadata so percentage formatting and school
    names stay consistent. Each section repeats the identity header because
    it may later be retrieved independently of the other sections.
    """
    document = normalize_school_quality(record)
    identity, *blocks = document["content"].split("\n\n")

    sections = []
    for block in blocks:
        heading = block.split("\n", 1)[0]
        sections.append(
            {
                "content": f"{identity}\n\n{block}",
                "metadata": {
                    **document["metadata"],
                    "section": SECTION_CATEGORIES[heading],
                },
            }
        )

    return sections
