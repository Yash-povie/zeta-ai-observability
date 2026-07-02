from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.propagate import extract

class FastAPITelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract the trace context from the incoming headers (like traceparent)
        context = extract(request.headers)
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=context,
            kind=trace.SpanKind.SERVER
        ) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                return response
            except Exception as e:
                span.set_attribute("error", True)
                span.record_exception(e)
                raise
