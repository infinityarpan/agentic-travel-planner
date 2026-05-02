import logging
import os

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased, TraceIdRatioBased

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - dependency may be absent until installed
    OTLPSpanExporter = None

_configured_service = None
_httpx_instrumented = False
_logging_configured = False


class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context and span_context.is_valid:
            record.otel_trace_id = format(span_context.trace_id, "032x")
            record.otel_span_id = format(span_context.span_id, "016x")
        else:
            record.otel_trace_id = "-"
            record.otel_span_id = "-"
        return True


def _configure_logging():
    global _logging_configured

    if _logging_configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | "
            "trace_id=%(otel_trace_id)s span_id=%(otel_span_id)s | %(message)s"
        )
    )
    handler.addFilter(TraceContextFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    _logging_configured = True


def _resolve_sampler():
    sampler_name = os.getenv("APP_OTEL_SAMPLER", "always_on").lower()
    sampler_arg = os.getenv("APP_OTEL_SAMPLER_ARG", "1.0")

    if sampler_name == "always_off":
        return ALWAYS_OFF
    if sampler_name == "traceidratio":
        return TraceIdRatioBased(float(sampler_arg))
    if sampler_name == "parentbased_traceidratio":
        return ParentBased(TraceIdRatioBased(float(sampler_arg)))
    return ALWAYS_ON


def _build_resource(service_name):
    resource_attributes = {
        "service.name": os.getenv("OTEL_SERVICE_NAME", service_name),
        "service.version": os.getenv("APP_VERSION", "dev"),
        "deployment.environment": os.getenv("APP_ENV", "development"),
    }
    return Resource.create(resource_attributes)


def _resolve_otlp_endpoint():
    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if traces_endpoint:
        return traces_endpoint

    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if base_endpoint:
        return f"{base_endpoint.rstrip('/')}/v1/traces"

    return None


def _build_span_processor():
    endpoint = _resolve_otlp_endpoint()

    if endpoint and OTLPSpanExporter is not None:
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=os.getenv("OTEL_EXPORTER_OTLP_HEADERS"),
        )
        return BatchSpanProcessor(exporter)

    return SimpleSpanProcessor(ConsoleSpanExporter())


def configure_tracing(service_name):
    global _configured_service
    global _httpx_instrumented

    if _configured_service == service_name:
        return trace.get_tracer(service_name)

    _configure_logging()

    if _configured_service is None:
        provider = TracerProvider(
            resource=_build_resource(service_name),
            sampler=_resolve_sampler(),
        )
        provider.add_span_processor(_build_span_processor())
        trace.set_tracer_provider(provider)
        _configured_service = service_name

    if service_name == "travel-orchestrator" and not _httpx_instrumented:
        HTTPXClientInstrumentor().instrument()
        _httpx_instrumented = True

    return trace.get_tracer(service_name)


def get_tracer(name):
    return trace.get_tracer(name)


def instrument_fastapi(app):
    if not getattr(app.state, "otel_fastapi_instrumented", False):
        FastAPIInstrumentor.instrument_app(app)
        app.state.otel_fastapi_instrumented = True
