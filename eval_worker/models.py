from sqlalchemy import Column, String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class LLMEvaluation(Base):
    __tablename__ = 'llm_evaluations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(32), nullable=False, index=True)
    agent_node = Column(String, nullable=False, index=True)
    eval_model = Column(String, nullable=False)
    hallucination_score = Column(Float, nullable=False) # 0.0 to 1.0
    relevance_score = Column(Float, nullable=False)
    eval_reasoning = Column(String, nullable=True)
    cost_usd = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
