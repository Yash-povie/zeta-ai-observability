import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from eval_worker.main import evaluate_trace, query_jaeger_for_traces
from eval_worker.models import LLMEvaluation


def test_evaluate_trace_returns_scores():
    fake_trace = {
        "traceID": "abc123",
        "spans": [
            {"tags": [{"key": "agent.node.name", "value": "SUMMARIZER"}, {"key": "llm.cost.usd", "value": "0.003"}]}
        ],
    }
    result = evaluate_trace(fake_trace)
    assert "hallucination_score" in result
    assert "relevance_score" in result
    assert 0.0 <= result["hallucination_score"] <= 1.0
    assert 0.0 <= result["relevance_score"] <= 1.0


def test_evaluate_trace_returns_reasoning():
    result = evaluate_trace({"traceID": "x", "spans": []})
    assert isinstance(result["eval_reasoning"], str)
    assert len(result["eval_reasoning"]) > 0


@patch("eval_worker.main.requests.get")
def test_query_jaeger_returns_traces(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"traceID": "trace1"}, {"traceID": "trace2"}]}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    traces = query_jaeger_for_traces()
    assert len(traces) == 2
    assert traces[0]["traceID"] == "trace1"


@patch("eval_worker.main.requests.get")
def test_query_jaeger_handles_error(mock_get):
    mock_get.side_effect = Exception("Connection refused")
    traces = query_jaeger_for_traces()
    assert traces == []


def test_llm_evaluation_model_fields(db_session):
    record = LLMEvaluation(
        trace_id="a" * 32,
        agent_node="TEST_NODE",
        eval_model="gpt-4o-mini",
        hallucination_score=0.1,
        relevance_score=0.9,
        eval_reasoning="Test reasoning",
        cost_usd=0.002,
    )
    db_session.add(record)
    db_session.commit()

    saved = db_session.query(LLMEvaluation).filter_by(agent_node="TEST_NODE").first()
    assert saved is not None
    assert saved.hallucination_score == pytest.approx(0.1)
    assert saved.relevance_score == pytest.approx(0.9)