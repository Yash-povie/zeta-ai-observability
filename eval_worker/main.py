import os
import time
import requests
import random
from typing import Dict, Any

from .database import SessionLocal
from .models import LLMEvaluation

JAEGER_API_URL = os.getenv("JAEGER_API_URL", "http://localhost:16686/api/traces")
EVAL_MODEL = "gpt-4o-mini-mock"

def query_jaeger_for_traces() -> list:
    """
    Query Jaeger for traces that have completed recently.
    In a real app, you would query by tag `agent.workflow.complete=true`.
    """
    try:
        # We query the 'dummy_app' service from Jaeger
        params = {
            "service": "dummy_app",
            "limit": 50,
            "lookback": "1h"
        }
        response = requests.get(JAEGER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Error querying Jaeger: {e}")
        return []

def evaluate_trace(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock LLM-as-a-judge evaluation.
    In a real scenario, we extract the prompt/completion from the trace 
    and call an LLM to evaluate hallucination and relevance.
    """
    # Mock scores
    hallucination_score = random.uniform(0.0, 0.3)  # Mostly good
    relevance_score = random.uniform(0.7, 1.0)      # Mostly relevant
    
    return {
        "hallucination_score": hallucination_score,
        "relevance_score": relevance_score,
        "eval_reasoning": "Mock evaluation based on extracted trace data."
    }

def worker_loop():
    print("Starting Eval Worker Loop...")
    while True:
        traces = query_jaeger_for_traces()
        if traces:
            # Randomly sample 5% (or just 1 for testing)
            sampled_traces = random.sample(traces, min(len(traces), max(1, int(len(traces) * 0.05))))
            
            db = SessionLocal()
            try:
                for trace in sampled_traces:
                    trace_id = trace.get("traceID")
                    
                    # Check if already evaluated
                    existing = db.query(LLMEvaluation).filter(LLMEvaluation.trace_id == trace_id).first()
                    if existing:
                        continue
                        
                    print(f"Evaluating trace: {trace_id}")
                    
                    # Find LLM spans
                    agent_node = "UNKNOWN"
                    cost = 0.0
                    
                    for span in trace.get("spans", []):
                        tags = {t["key"]: t["value"] for t in span.get("tags", [])}
                        if "agent.node.name" in tags:
                            agent_node = tags["agent.node.name"]
                        if "llm.cost.usd" in tags:
                            cost += float(tags["llm.cost.usd"])
                            
                    eval_results = evaluate_trace(trace)
                    
                    eval_record = LLMEvaluation(
                        trace_id=trace_id,
                        agent_node=agent_node,
                        eval_model=EVAL_MODEL,
                        hallucination_score=eval_results["hallucination_score"],
                        relevance_score=eval_results["relevance_score"],
                        eval_reasoning=eval_results["eval_reasoning"],
                        cost_usd=cost
                    )
                    
                    db.add(eval_record)
                    db.commit()
                    print(f"Saved evaluation for {trace_id}")
            except Exception as e:
                print(f"Error processing traces: {e}")
                db.rollback()
            finally:
                db.close()
        
        # Sleep before next polling interval
        time.sleep(15)

if __name__ == "__main__":
    worker_loop()
