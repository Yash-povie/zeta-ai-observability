from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from .database import SessionLocal

REGISTRY = CollectorRegistry()

hallucination_score_gauge = Gauge(
    "llm_hallucination_score",
    "Average hallucination score from LLM-as-Judge evaluations",
    ["agent_node"],
    registry=REGISTRY,
)
relevance_score_gauge = Gauge(
    "llm_relevance_score",
    "Average relevance score from LLM-as-Judge evaluations",
    ["agent_node"],
    registry=REGISTRY,
)
eval_total_counter = Counter(
    "llm_evaluations_total",
    "Total number of traces evaluated",
    registry=REGISTRY,
)


def refresh_metrics():
    """Pull latest scores from PostgreSQL and update Prometheus gauges."""
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT agent_node,
                       AVG(hallucination_score) AS avg_hallucination,
                       AVG(relevance_score)     AS avg_relevance,
                       COUNT(*)                 AS total
                FROM llm_evaluations
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY agent_node
                """
            )
        ).fetchall()
        for row in rows:
            hallucination_score_gauge.labels(agent_node=row.agent_node).set(row.avg_hallucination)
            relevance_score_gauge.labels(agent_node=row.agent_node).set(row.avg_relevance)
    except Exception as e:
        print(f"[metrics] Error refreshing metrics: {e}")
    finally:
        db.close()


def metrics_output() -> tuple[bytes, str]:
    refresh_metrics()
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST