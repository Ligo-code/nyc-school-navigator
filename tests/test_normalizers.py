from nyc_school_navigator.ingestion.normalizers import normalize_school_quality


SAMPLE_RECORD = {
    "dbn": "20K187",
    "school_name": "The Christa McAuliffe School\\I.S. 187",
    "enrollment": 954,
    "instruction_performance_rating": "Excellent",
    "safety_school_climate_rating": "Excellent",
    "relationships_with_families_rating": "Excellent",
    "learning_environment_positive": 0.83,
    "safety_positive": 0.83,
    "student_support_positive": 0.75,
    "advising_planning_positive": 0.89,
    "family_school_trust_positive": 0.98,
    "communication_positive": 0.95,
    "family_involvement_positive": 0.88,
    "average_student_attendance": 0.976,
    "high_school_math_credit": 0.759,
    "high_school_science_credit": 0.879,
    "source_type": "school_quality",
    "source_year": "2024-25",
}


def test_normalize_school_quality_formats_content():
    document = normalize_school_quality(SAMPLE_RECORD)

    content = document["content"]

    assert "The Christa McAuliffe School / I.S. 187" in content
    assert "Safety: 83.0% positive" in content
    assert "Average Student Attendance: 97.6%" in content
    assert "75.9%" in content
    assert "87.9%" in content


def test_normalize_school_quality_preserves_metadata():
    document = normalize_school_quality(SAMPLE_RECORD)

    assert document["metadata"] == {
        "dbn": "20K187",
        "school_name": "The Christa McAuliffe School / I.S. 187",
        "source_type": "school_quality",
        "source_year": "2024-25",
    }