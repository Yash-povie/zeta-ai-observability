import asyncio
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import trace

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared_observability.instrumentation import trace_llm_call

_exporter = InMemorySpanExporter()

def pytest_configure(config):
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_exporter))
    trace.set_tracer_provider(provider)


@pytest.fixture(autouse=True)
def clear_spans():
    _exporter.clear()
    yield
    _exporter.clear()


def test_trace_llm_call_sets_attributes():
    def extract_tokens(resp, kwargs):
        return {"prompt": 100, "completion": 50}

    def calc_cost(tokens, model):
        return 0.005

    @trace_llm_call(
        provider="anthropic",
        model="claude-3-5-sonnet",
        agent_node="TEST_NODE",
        extract_tokens=extract_tokens,
        calculate_cost=calc_cost,
    )
    async def fake_llm(prompt: str):
        return "response"

    asyncio.run(fake_llm("hello"))

    spans = _exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = spans[0].attributes
    assert attrs["llm.provider"] == "anthropic"
    assert attrs["llm.model"] == "claude-3-5-sonnet"
    assert attrs["agent.node.name"] == "TEST_NODE"
    assert attrs["llm.prompt.tokens"] == 100
    assert attrs["llm.completion.tokens"] == 50
    assert attrs["llm.cost.usd"] == pytest.approx(0.005)
    assert attrs["error"] is False


def test_trace_llm_call_records_errors():
    @trace_llm_call(provider="openai", model="gpt-4", agent_node="ERROR_NODE")
    async def failing_llm(prompt: str):
        raise ValueError("LLM failed")

    with pytest.raises(ValueError):
        asyncio.run(failing_llm("hello"))

    spans = _exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes["error"] is True