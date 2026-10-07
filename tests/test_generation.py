import io
import json
from unittest.mock import Mock
from urllib.error import URLError

import pytest

from nyc_school_navigator import generation


@pytest.fixture
def evidence(monkeypatch):
    sections = [{
        "content": "School: The Christa McAuliffe School / I.S. 187\nEnrollment: 954",
        "metadata": {
            "dbn": "20K187", "school_name": "The Christa McAuliffe School / I.S. 187",
            "section": "overview", "source_year": "2024-25", "source_type": "school_quality",
        },
        "score": 0.8,
    }]
    retrieve = Mock(return_value=sections)
    monkeypatch.setattr(generation, "retrieve_sections", retrieve)
    return sections, retrieve


def mock_response(monkeypatch, body):
    network = Mock(return_value=io.BytesIO(json.dumps(body).encode()))
    monkeypatch.setattr(generation, "urlopen", network)
    return network


def test_grounded_request_and_structured_answer(monkeypatch, evidence):
    sections, retrieve = evidence
    network = mock_response(monkeypatch, {"message": {"content": " McAuliffe enrolled 954 students [1]. "}})
    result = generation.answer_question("How many students?", top_k=3)
    retrieve.assert_called_once_with("How many students?", top_k=3)
    request = network.call_args.args[0]
    assert request.full_url == "http://localhost:11434/api/chat"
    assert request.get_method() == "POST"
    assert network.call_args.kwargs == {"timeout": 120}
    payload = json.loads(request.data)
    assert payload["model"] == "qwen3:4b-instruct"
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0
    assert "Answer only from the supplied school context" in payload["messages"][0]["content"]
    assert generation.INSUFFICIENT_DATA in payload["messages"][0]["content"]
    assert sections[0]["content"] in payload["messages"][1]["content"]
    assert "Question: How many students?" in payload["messages"][1]["content"]
    assert result == {
        "question": "How many students?", "answer": "McAuliffe enrolled 954 students [1].",
        "sources": [{
            "label": "[1]", **sections[0]["metadata"], "score": 0.8,
            "evidence_text": sections[0]["content"],
        }],
    }
    assert result["sources"][0]["evidence_text"] in payload["messages"][1]["content"]
    assert "embedding" not in json.dumps(result)


def test_every_source_preserves_exact_context_without_extra_calls(monkeypatch, evidence):
    sections, retrieve = evidence
    sections[0]["content"] = "  School: McAuliffe\nEnrollment: 954\n\nSource year: 2024-25\n"
    sections.append({
        "content": "School: Mark Twain\nEnrollment: 1290\n",
        "metadata": {**sections[0]["metadata"], "dbn": "21K239", "school_name": "Mark Twain"},
        "score": 0.63,
    })
    network = mock_response(monkeypatch, {"message": {"content": "Answer [1] [2]."}})
    result = generation.answer_question("Compare enrollment.")
    retrieve.assert_called_once_with("Compare enrollment.", top_k=5)
    network.assert_called_once()
    prompt = json.loads(network.call_args.args[0].data)["messages"][1]["content"]
    assert len(result["sources"]) == len(sections)
    for index, (source, section) in enumerate(zip(result["sources"], sections), start=1):
        assert source["label"] == f"[{index}]"
        assert source["evidence_text"] == section["content"]
        assert f'[{index}]\n{source["evidence_text"]}' in prompt
        assert source["dbn"] == section["metadata"]["dbn"]
        assert source["score"] == section["score"]


def test_empty_context_skips_ollama(monkeypatch):
    monkeypatch.setattr(generation, "retrieve_sections", Mock(return_value=[]))
    network = Mock()
    monkeypatch.setattr(generation, "urlopen", network)
    result = generation.answer_question("What are the admissions rules?")
    assert result["answer"] == generation.INSUFFICIENT_DATA
    assert result["sources"] == []
    network.assert_not_called()


def test_insufficient_data_answer_is_preserved(monkeypatch, evidence):
    mock_response(monkeypatch, {"message": {"content": generation.INSUFFICIENT_DATA}})
    assert generation.answer_question("What are the admissions rules?")["answer"] == generation.INSUFFICIENT_DATA


def test_ollama_unavailable_has_clear_error(monkeypatch, evidence):
    monkeypatch.setattr(generation, "urlopen", Mock(side_effect=URLError("refused")))
    with pytest.raises(RuntimeError, match="Local Ollama request failed"):
        generation.answer_question("Enrollment?")


@pytest.mark.parametrize("body", [{}, {"message": {}}, {"message": {"content": " "}}, {"message": {"content": None}}])
def test_invalid_ollama_response_is_rejected(monkeypatch, evidence, body):
    mock_response(monkeypatch, body)
    with pytest.raises(RuntimeError, match="Ollama returned"):
        generation.answer_question("Enrollment?")
