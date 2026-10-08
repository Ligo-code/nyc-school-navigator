from pathlib import Path

from nyc_school_navigator.ingestion.loaders import load_school_quality


WORKBOOK_PATH = Path(
    "data/raw/school_quality/202425-ems-sqr-results.xlsx"
)

EXPECTED_DBNS = {
    "20K187",
    "21K228",
    "21K239",
}


def test_load_school_quality_returns_target_schools():
    records = load_school_quality(WORKBOOK_PATH)

    assert len(records) == 3

    actual_dbns = {record["dbn"] for record in records}

    assert actual_dbns == EXPECTED_DBNS


def test_load_school_quality_extracts_expected_values():
    records = load_school_quality(WORKBOOK_PATH)

    records_by_dbn = {
        record["dbn"]: record
        for record in records
    }

    mcauliffe = records_by_dbn["20K187"]

    assert mcauliffe["enrollment"] == 954
    assert mcauliffe["instruction_performance_rating"] == "Excellent"
    assert mcauliffe["safety_positive"] == 0.83
    assert mcauliffe["high_school_math_credit"] == 0.759
    assert mcauliffe["source_type"] == "school_quality"
    assert mcauliffe["source_year"] == "2024-25"


def test_load_school_quality_contains_expected_fields():
    records = load_school_quality(WORKBOOK_PATH)

    expected_fields = {
        "dbn",
        "school_name",
        "enrollment",
        "instruction_performance_rating",
        "safety_school_climate_rating",
        "relationships_with_families_rating",
        "learning_environment_positive",
        "safety_positive",
        "student_support_positive",
        "advising_planning_positive",
        "family_school_trust_positive",
        "communication_positive",
        "family_involvement_positive",
        "average_student_attendance",
        "high_school_math_credit",
        "high_school_science_credit",
        "source_type",
        "source_year",
    }

    for record in records:
        assert set(record) == expected_fields