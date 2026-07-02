from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST
from .database import SessionLocal
from .models import LLMEvaluation
from sqlalchemy import func

# Create a custom registry for metrics
registry = CollectorRegistry()

# Define Prometheus metrics
hallucination_gauge = Gauge(
    'llm_hallucination_score',
    'Average hallucination score from LLM evaluations',
    registry=registry
)

relevance_gauge = Gauge(
    'llm_relevance_score',
    'Average relevance score from LLM evaluations',
    registry=registry
)

eval_count_gauge = Gauge(
    'llm_eval_count_total',
    'Total number of LLM evaluations',
    registry=registry
)

cost_gauge = Gauge(
    'llm_total_cost_usd',
    'Total cost in USD from LLM evaluations',
    registry=registry
)

def update_metrics():
    """Update Prometheus metrics from database."""
    db = SessionLocal()
    try:
        # Calculate averages and totals
        avg_hallucination = db.query(func.avg(LLMEvaluation.hallucination_score)).scalar() or 0.0
        avg_relevance = db.query(func.avg(LLMEvaluation.relevance_score)).scalar() or 0.0
        eval_count = db.query(func.count(LLMEvaluation.id)).scalar() or 0
        total_cost = db.query(func.sum(LLMEvaluation.cost_usd)).scalar() or 0.0
        
        hallucination_gauge.set(avg_hallucination)
        relevance_gauge.set(avg_relevance)
        eval_count_gauge.set(eval_count)
        cost_gauge.set(total_cost)
    finally:
        db.close()

def metrics_output():
    """Generate Prometheus metrics output."""
    update_metrics()
    return generate_latest(registry), CONTENT_TYPE_LATEST
