import asyncio
import random
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_observability.instrumentation import trace_llm_call
from shared_observability.middleware import FastAPITelemetryMiddleware

# Setup OpenTelemetry
resource = Resource(attributes={"service.name": "example_app"})
provider = TracerProvider(resource=resource)
# Note: we send to the collector on port 4317
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI(title="Dummy Host Application")
app.add_middleware(FastAPITelemetryMiddleware)

# Example token extractor
def extract_tokens(response, kwargs):
    return {"prompt": random.randint(50, 500), "completion": random.randint(10, 200)}

# Example cost calculator
def calculate_cost(tokens, model):
    # claude-3-5-sonnet prices per 1k tokens: prompt=$0.003, completion=$0.015
    prompt_cost = (tokens.get("prompt", 0) / 1000) * 0.003
    completion_cost = (tokens.get("completion", 0) / 1000) * 0.015
    return prompt_cost + completion_cost

@trace_llm_call(
    provider="anthropic",
    model="claude-3-5-sonnet-20240620",
    agent_node="EVIDENCE_RECONCILER",
    extract_tokens=extract_tokens,
    calculate_cost=calculate_cost
)
async def mock_llm_call(prompt: str):
    await asyncio.sleep(random.uniform(0.5, 2.0))
    return f"Mock response for: {prompt}"

@app.get("/run_agent")
async def run_agent(query: str = "test query"):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent_workflow") as span:
        span.set_attribute("agent.workflow.complete", True)
        
        # Step 1: LLM Call
        response = await mock_llm_call(f"Reconcile evidence for {query}")
        
        return {"status": "success", "response": response}

FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
