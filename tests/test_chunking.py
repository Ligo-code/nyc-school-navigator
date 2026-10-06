from pathlib import Path

import pytest

from nyc_school_navigator.ingestion.chunking import section_school_quality
from nyc_school_navigator.ingestion.loaders import load_school_quality
from nyc_school_navigator.ingestion.normalizers import normalize_school_quality


@pytest.fixture(scope="module")
def school_records():
    workbook = (
        Path(__file__).resolve().parents[1]
        / "data/raw/school_quality/202425-ems-sqr-results.xlsx"
    )
    return load_school_quality(workbook)


def test_all_three_schools_produce_expected_sections(school_records):
    assert {record["dbn"] for record in school_records} == {
        "20K187", "21K228", "21K239"
    }
    for record in school_records:
        sections = section_school_quality(record)
        assert len(sections) == 5
        assert [section["metadata"]["section"] for section in sections] == [
            "overview",
            "school_quality",
            "student_experience",
            "family_experience",
            "student_outcomes",
        ]


def test_metrics_are_preserved_in_the_appropriate_sections(school_records):
    for record in school_records:
        contents = {
            section["metadata"]["section"]: section["content"]
            for section in section_school_quality(record)
        }
        assert f'Enrollment: {record["enrollment"]}' in contents["overview"]

        ratings = {
            "Instruction and Performance": "instruction_performance_rating",
            "Safety and School Climate": "safety_school_climate_rating",
            "Relationships with Families": "relationships_with_families_rating",
        }
        for label, field in ratings.items():
            assert f"{label}: {record[field]}" in contents["school_quality"]

        percentage_groups = {
            "student_experience": {
                "Instruction and Learning Environment": "learning_environment_positive",
                "Safety": "safety_positive",
                "Student Support": "student_support_positive",
                "Advising and Planning": "advising_planning_positive",
            },
            "family_experience": {
                "Family-School Trust": "family_school_trust_positive",
                "Communication": "communication_positive",
                "Family Involvement": "family_involvement_positive",
            },
            "student_outcomes": {
                "Average Student Attendance": "average_student_attendance",
                "8th Graders Earning High School Math Credit": "high_school_math_credit",
                "8th Graders Earning High School Science Credit": "high_school_science_credit",
            },
        }
        for category, fields in percentage_groups.items():
            for label, field in fields.items():
                expected = f"{label}: {record[field] * 100:.1f}%"
                if category != "student_outcomes":
                    expected += " positive"
                assert expected in contents[category]
                for other_category, content in contents.items():
                    if other_category != category:
                        assert f"{label}:" not in content


def test_sections_preserve_identity_and_source_without_mixing_schools(school_records):
    identities = set()
    for record in school_records:
        school_name = record["school_name"].replace("\\", " / ")
        for section in section_school_quality(record):
            metadata = section["metadata"]
            assert metadata == {
                "dbn": record["dbn"],
                "school_name": school_name,
                "source_type": "school_quality",
                "source_year": "2024-25",
                "section": metadata["section"],
            }
            assert f"School: {school_name}\n" in section["content"]
            assert f'DBN: {record["dbn"]}\n' in section["content"]
            assert "School year: 2024-25" in section["content"]
            identities.add((metadata["dbn"], metadata["section"]))
            for other in school_records:
                if other["dbn"] != record["dbn"]:
                    assert other["dbn"] not in section["content"]
                    assert other["school_name"].replace("\\", " / ") not in section["content"]
    assert len(identities) == 15


def test_sections_retain_all_normalized_content(school_records):
    for record in school_records:
        document = normalize_school_quality(record)
        identity, *blocks = document["content"].split("\n\n")
        sections = section_school_quality(record)
        assert [section["content"] for section in sections] == [
            f"{identity}\n\n{block}" for block in blocks
        ]
