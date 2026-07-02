import threading
from fastapi import FastAPI, Response
from .main import worker_loop
from .metrics import metrics_output
from .init_db import init_db

app = FastAPI(title="Zeta-AI Eval Worker", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()


@app.get("/health")
def health():
    return {"status": "ok", "service": "eval-worker"}


@app.get("/metrics")
def metrics():
    data, content_type = metrics_output()
    return Response(content=data, media_type=content_type)


@app.get("/evaluations/recent")
def recent_evaluations():
    from .database import SessionLocal
    from .models import LLMEvaluation
    from sqlalchemy import desc
    db = SessionLocal()
    try:
        evals = (
            db.query(LLMEvaluation)
            .order_by(desc(LLMEvaluation.created_at))
            .limit(20)
            .all()
        )
        return [
            {
                "trace_id": e.trace_id,
                "agent_node": e.agent_node,
                "hallucination_score": e.hallucination_score,
                "relevance_score": e.relevance_score,
                "eval_reasoning": e.eval_reasoning,
                "cost_usd": e.cost_usd,
                "created_at": str(e.created_at),
            }
            for e in evals
        ]
    finally:
        db.close()