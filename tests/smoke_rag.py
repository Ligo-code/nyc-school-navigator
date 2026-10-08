"""Run `uv run tests/smoke_rag.py` with MongoDB configured and Ollama running."""

import json
import re

from nyc_school_navigator.generation import answer_question


def main() -> None:
    question = "How many students are enrolled at The Christa McAuliffe School?"
    result = answer_question(question)
    print(json.dumps(result, indent=2))
    assert re.search(r"\b954\b", result["answer"]), "Expected grounded answer to contain 954."
    assert any(
        source["dbn"] == "20K187" and source["section"] == "overview"
        for source in result["sources"]
    ), "Expected McAuliffe enrollment evidence among retrieved sources."
    print("Verified: real retrieval + local Ollama answer containing 954.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        raise SystemExit(str(error)) from None
    except Exception as error:
        raise SystemExit(
            f"RAG smoke check failed ({type(error).__name__}). "
            "Check MongoDB settings/data and local Ollama with qwen3:4b-instruct. "
            "Connection details are not logged."
        ) from None
