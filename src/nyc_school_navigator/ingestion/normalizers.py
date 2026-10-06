def _format_percent(value: float | None) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def normalize_school_quality(record: dict) -> dict:
    """Convert an extracted school-quality record into RAG-ready content."""

    school_name = record["school_name"].replace("\\", " / ")

    content = f"""
School: {school_name}
DBN: {record["dbn"]}
School year: {record["source_year"]}

School size:
Enrollment: {record["enrollment"]}

Overall quality:
Instruction and Performance: {record["instruction_performance_rating"]}
Safety and School Climate: {record["safety_school_climate_rating"]}
Relationships with Families: {record["relationships_with_families_rating"]}

School experience:
Instruction and Learning Environment: {_format_percent(record["learning_environment_positive"])} positive
Safety: {_format_percent(record["safety_positive"])} positive
Student Support: {_format_percent(record["student_support_positive"])} positive
Advising and Planning: {_format_percent(record["advising_planning_positive"])} positive

Family experience:
Family-School Trust: {_format_percent(record["family_school_trust_positive"])} positive
Communication: {_format_percent(record["communication_positive"])} positive
Family Involvement: {_format_percent(record["family_involvement_positive"])} positive

Student outcomes:
Average Student Attendance: {_format_percent(record["average_student_attendance"])}
8th Graders Earning High School Math Credit: {_format_percent(record["high_school_math_credit"])}
8th Graders Earning High School Science Credit: {_format_percent(record["high_school_science_credit"])}
""".strip()

    return {
        "content": content,
        "metadata": {
            "dbn": record["dbn"],
            "school_name": school_name,
            "source_type": record["source_type"],
            "source_year": record["source_year"],
        },
    }