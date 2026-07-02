import time
import functools
from typing import Any, Callable, Dict, Optional
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

def trace_llm_call(
    provider: str,
    model: str,
    agent_node: str,
    extract_tokens: Optional[Callable[[Any, Any], Dict[str, int]]] = None,
    calculate_cost: Optional[Callable[[Dict[str, int], str], float]] = None
):
    """
    Decorator to trace an LLM call using OpenTelemetry.
    
    :param provider: e.g., 'anthropic', 'openai'
    :param model: e.g., 'claude-3-5-sonnet-20240620'
    :param agent_node: e.g., 'EVIDENCE_RECONCILER'
    :param extract_tokens: Function that takes (response, kwargs) and returns token counts
    :param calculate_cost: Function that calculates cost based on tokens and model
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(f"{provider}.{model}") as span:
                span.set_attribute("llm.provider", provider)
                span.set_attribute("llm.model", model)
                span.set_attribute("agent.node.name", agent_node)
                span.set_attribute("error", False)
                
                try:
                    start_time = time.time()
                    response = await func(*args, **kwargs)
                    latency = time.time() - start_time
                    
                    if extract_tokens:
                        tokens = extract_tokens(response, kwargs)
                        span.set_attribute("llm.prompt.tokens", tokens.get("prompt", 0))
                        span.set_attribute("llm.completion.tokens", tokens.get("completion", 0))
                        
                        if calculate_cost:
                            cost = calculate_cost(tokens, model)
                            span.set_attribute("llm.cost.usd", cost)
                    
                    span.set_status(Status(StatusCode.OK))
                    return response
                except Exception as e:
                    span.set_attribute("error", True)
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(f"{provider}.{model}") as span:
                span.set_attribute("llm.provider", provider)
                span.set_attribute("llm.model", model)
                span.set_attribute("agent.node.name", agent_node)
                span.set_attribute("error", False)
                
                try:
                    start_time = time.time()
                    response = func(*args, **kwargs)
                    latency = time.time() - start_time
                    
                    if extract_tokens:
                        tokens = extract_tokens(response, kwargs)
                        span.set_attribute("llm.prompt.tokens", tokens.get("prompt", 0))
                        span.set_attribute("llm.completion.tokens", tokens.get("completion", 0))
                        
                        if calculate_cost:
                            cost = calculate_cost(tokens, model)
                            span.set_attribute("llm.cost.usd", cost)
                            
                    span.set_status(Status(StatusCode.OK))
                    return response
                except Exception as e:
                    span.set_attribute("error", True)
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
