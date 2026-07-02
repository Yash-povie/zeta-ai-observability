# Zeta-AI Observability Platform

> **"Datadog for LLMs"** — Production telemetry, real-time cost tracking, distributed tracing, and automated hallucination detection for multi-agent AI systems.

[![CI](https://github.com/your-username/zeta-ai-observability/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/zeta-ai-observability/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Problem This Solves

Most engineers ship an LLM application and have no idea what is happening inside it in production:

- **Are my agents hallucinating?** No idea — no one checked.
- **How much did that research query cost?** Unknown until the AWS bill arrives.
- **Which agent node is the latency bottleneck?** Can't tell without traces.
- **Did the FactChecker agent fail silently?** Maybe — there are no alerts.

Zeta-AI is a standalone observability plane that wraps any LLM application and answers all of these questions in real time — without changing how the application works.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  example_app  (any LLM service — drop in @trace_llm_call)       │
│                                                                  │
│  @trace_llm_call wraps every LLM API call                        │
│  FastAPITelemetryMiddleware propagates trace context             │
└──────────────┬──────────────────────────────────────────────────┘
               │ OTLP gRPC (spans + metrics)
               ▼
┌─────────────────────────┐
│  OpenTelemetry Collector │  ── spanmetrics processor extracts
│  (otel-collector:4317)   │     token counts, costs, latencies
└────────┬────────┬────────┘
         │        │
    Traces│    Metrics│
         ▼        ▼
┌────────────┐  ┌────────────┐
│   Jaeger   │  │ Prometheus │──► Grafana (port 3000)
│  (traces)  │  │ (metrics)  │    ├─ CFO View: costs
│  port:16686│  │ port:9090  │    ├─ SRE View: latency p95
└──────┬─────┘  └────────────┘    └─ AI Engineer: hallucination
       │
       │ polls every 15s, samples 5% of traces
       ▼
┌──────────────────────────────┐
│      eval_worker             │
│  LLM-as-Judge evaluation     │
│  ├─ /health  (port 8002)     │
│  ├─ /metrics (Prometheus)    │
│  └─ /evaluations/recent      │
└──────────────┬───────────────┘
               │ writes scores
               ▼
       ┌──────────────┐
       │  PostgreSQL  │──► Grafana quality panel
       │ llm_evaluations│
       └──────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Instrumentation | OpenTelemetry SDK, `opentelemetry-api` | Decorator + middleware for any FastAPI/LangGraph app |
| Trace backend | Jaeger (all-in-one) | Distributed trace storage + UI |
| Metrics pipeline | OTel Collector → Prometheus | spanmetrics processor extracts LLM metrics from spans |
| Dashboards | Grafana | Auto-provisioned LLM Control Plane dashboard |
| Eval worker | FastAPI + SQLAlchemy + requests | Async LLM-as-Judge loop |
| Eval storage | PostgreSQL 15 | `llm_evaluations` table with indexes |
| LLM judge | Anthropic Claude API (pluggable) | Scores traces for hallucination + relevance |
| Containerisation | Docker + docker-compose | Full local stack in one command |
| Orchestration | Kubernetes (manifests included) | Production deployment |
| CI | GitHub Actions | lint → test → docker build |

---

## Repository Structure

```
zeta-ai-observability/
│
├── shared_observability/          # Drop-in instrumentation library
│   ├── instrumentation.py         #   @trace_llm_call decorator
│   └── middleware.py              #   FastAPITelemetryMiddleware
│
├── example_app/                   # Reference instrumented FastAPI app
│   ├── main.py                    #   Uses @trace_llm_call + middleware
│   ├── Dockerfile
│   └── requirements.txt
│
├── eval_worker/                   # LLM-as-Judge async evaluation service
│   ├── api.py                     #   FastAPI: /health, /metrics, /evaluations/recent
│   ├── main.py                    #   Worker loop: polls Jaeger, scores traces
│   ├── metrics.py                 #   Prometheus gauges from PostgreSQL
│   ├── models.py                  #   SQLAlchemy: LLMEvaluation model
│   ├── database.py                #   SQLAlchemy engine + session
│   ├── init_db.py                 #   Table creation (non-Alembic fast path)
│   ├── Dockerfile
│   └── requirements.txt
│
├── infra/
│   ├── otel-collector-config.yaml #   Receivers → spanmetrics → Prometheus + Jaeger
│   ├── prometheus.yml             #   Scrapes otel-collector:8889 + eval-worker:8002
│   └── grafana/
│       └── provisioning/
│           ├── datasources/       #   Prometheus + PostgreSQL auto-wired
│           └── dashboards/
│               └── llm_control_plane.json  # CFO + SRE + AI Engineer panels
│
├── alembic/                       # Database migrations
│   ├── env.py
│   └── versions/
│       └── 001_create_llm_evaluations.py
│
├── kubernetes/
│   ├── namespace.yaml
│   ├── configmaps/zeta-config.yaml
│   ├── secrets/zeta-secrets.yaml
│   ├── deployments/
│   │   ├── example-app-deployment.yaml
│   │   └── eval-worker-deployment.yaml
│   └── services/
│       ├── example-app-svc.yaml
│       └── eval-worker-svc.yaml
│
├── tests/
│   ├── conftest.py                # SQLite in-memory DB fixture
│   ├── unit/
│   │   ├── test_instrumentation.py   # OTel span attribute assertions
│   │   └── test_eval_worker.py       # Worker logic + model tests
│   └── integration/
│       └── test_eval_flow.py         # FastAPI TestClient: /health, /metrics
│
├── .github/workflows/ci.yml       # lint → test → docker build
├── docker-compose.yml             # Full 7-service local stack
├── alembic.ini
├── requirements.txt
├── Makefile
├── .env.example
└── README.md
```

---

## Services & Ports

| Service | Port | What it does |
|---|---|---|
| `example_app` | **8001** | Reference LLM app. Hit `/run_agent` to generate traces |
| `eval_worker` | **8002** | Eval loop + `/health` + `/metrics` + `/evaluations/recent` |
| `otel-collector` | 4317 (gRPC), 4318 (HTTP) | Receives OTLP spans; extracts metrics via spanmetrics |
| `jaeger` | **16686** (UI) | Trace viewer |
| `prometheus` | **9090** | Metrics storage |
| `grafana` | **3000** | Dashboards — login: `admin / admin` |
| `postgres` | 5432 | Eval scores (`llm_evaluations` table) |

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-username/zeta-ai-observability
cd zeta-ai-observability
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 2. Start full stack
make up

# 3. Generate traces
curl "http://localhost:8001/run_agent?query=CRISPR+gene+therapy+mechanisms"

# 4. Open dashboards
make open-jaeger      # http://localhost:16686 — see spans
make open-grafana     # http://localhost:3000  — LLM Control Plane
make open-prometheus  # http://localhost:9090

# 5. Check eval scores
curl http://localhost:8002/evaluations/recent
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for real LLM-as-Judge scoring |
| `DATABASE_URL` | `postgresql://admin:password@postgres:5432/zeta_telemetry` | Eval scores DB |
| `JAEGER_API_URL` | `http://jaeger:16686/api/traces` | Where the eval worker polls for traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | Where instrumented apps send spans |
| `EVAL_SAMPLE_RATE` | `0.05` | Fraction of traces to evaluate (5%) |
| `EVAL_POLL_INTERVAL_SECONDS` | `15` | How often the eval worker polls Jaeger |
| `GF_SECURITY_ADMIN_PASSWORD` | `admin` | Grafana admin password |

---

## Using the Instrumentation Library in Your Own App

Drop the `shared_observability` folder into any Python project:

```python
from shared_observability.instrumentation import trace_llm_call
from shared_observability.middleware import FastAPITelemetryMiddleware

app = FastAPI()
app.add_middleware(FastAPITelemetryMiddleware)

def my_token_extractor(response, kwargs):
    return {"prompt": response.usage.input_tokens, "completion": response.usage.output_tokens}

def my_cost_calculator(tokens, model):
    return (tokens["prompt"] / 1000) * 0.003 + (tokens["completion"] / 1000) * 0.015

@trace_llm_call(
    provider="anthropic",
    model="claude-3-5-sonnet-20240620",
    agent_node="MY_AGENT_NODE",
    extract_tokens=my_token_extractor,
    calculate_cost=my_cost_calculator,
)
async def call_claude(prompt: str):
    return await anthropic_client.messages.create(...)
```

Every call automatically emits a span with `llm.model`, `llm.provider`, `llm.prompt.tokens`, `llm.completion.tokens`, `llm.cost.usd`, `agent.node.name`, and `error` attributes.

---

## Grafana Dashboards

The **LLM Control Plane** dashboard is auto-provisioned on first `make up`.

**CFO View (Costs)**
- Total daily spend: `sum(increase(llm_cost_usd_total[24h]))`
- Cost by agent node: `sum(rate(llm_cost_usd_total[1h])) by (agent_node)`

**SRE View (Performance)**
- Token velocity: `sum(rate(llm_tokens_total[5m])) by (token_type)`
- Latency p95 by model: `histogram_quantile(0.95, sum(rate(llm_inference_duration_seconds_bucket[5m])) by (le, llm_model))`

**AI Engineer View (Quality)**
- Avg hallucination rate: `avg_over_time(llm_hallucination_score[1h])` (from PostgreSQL via eval_worker `/metrics`)
- Error rate by node: ratio of `error=true` spans per `agent_node`

---

## Running Tests

```bash
pip install -r requirements.txt pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Kubernetes Deployment

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmaps/
# Edit secrets first: kubernetes/secrets/zeta-secrets.yaml
kubectl apply -f kubernetes/secrets/
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/
```

---

## Why This Is a Staff-Level Portfolio Signal

Most candidates build an LLM app. Almost none build the **infrastructure to measure it**. This project demonstrates:

- **Distributed tracing** — tracking a request through multiple agent hops via OpenTelemetry + Jaeger
- **FinOps** — per-model, per-node cost tracking in real time
- **Automated quality assurance** — async LLM-as-Judge that runs like a CI pipeline against live production traces
- **Production operations** — Prometheus scraping, Grafana dashboards, health probes, Kubernetes manifests