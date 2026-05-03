import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased, TraceIdRatioBased

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - dependency may be absent until installed
    OTLPSpanExporter = None

try:
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
except ImportError:  # pragma: no cover - dependency may be absent until installed
    OTLPMetricExporter = None

_configured_service = None
_httpx_instrumented = False
_logging_configured = False
_BANNED_METRIC_ATTRIBUTE_KEYS = {"user_id", "trace_id", "span_id", "travel.user_query", "payload"}


def metrics_enabled():
    return os.getenv("APP_OTEL_METRICS_ENABLED", "true").lower() != "false"


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


def _is_production_env():
    return os.getenv("APP_ENV", "development").lower() == "production"


def _resolve_otlp_endpoint():
    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if traces_endpoint:
        return traces_endpoint

    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if base_endpoint:
        return f"{base_endpoint.rstrip('/')}/v1/traces"

    return None


def _resolve_otlp_metrics_endpoint():
    metrics_endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT")
    if metrics_endpoint:
        return metrics_endpoint

    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if base_endpoint:
        return f"{base_endpoint.rstrip('/')}/v1/metrics"

    return None


def _build_span_processor():
    endpoint = _resolve_otlp_endpoint()

    if endpoint and OTLPSpanExporter is not None:
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=os.getenv("OTEL_EXPORTER_OTLP_HEADERS"),
        )
        return BatchSpanProcessor(exporter)

    if _is_production_env():
        raise RuntimeError(
            "Tracing is running in production, but no OTLP traces endpoint is configured. "
            "Set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT."
        )

    return SimpleSpanProcessor(ConsoleSpanExporter())


def _build_metric_reader():
    if not metrics_enabled():
        return None

    endpoint = _resolve_otlp_metrics_endpoint()
    export_interval = int(os.getenv("APP_OTEL_METRIC_EXPORT_INTERVAL_MS", "5000"))

    if endpoint and OTLPMetricExporter is not None:
        exporter = OTLPMetricExporter(
            endpoint=endpoint,
            headers=os.getenv("OTEL_EXPORTER_OTLP_HEADERS"),
        )
        return PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval)

    if _is_production_env():
        raise RuntimeError(
            "Metrics are running in production, but no OTLP metrics endpoint is configured. "
            "Set OTEL_EXPORTER_OTLP_METRICS_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT."
        )

    return PeriodicExportingMetricReader(
        ConsoleMetricExporter(),
        export_interval_millis=export_interval,
    )


def configure_tracing(service_name):
    global _configured_service
    global _httpx_instrumented

    if _configured_service == service_name:
        return trace.get_tracer(service_name)

    if _configured_service is not None and _configured_service != service_name:
        raise RuntimeError(
            f"Telemetry is already configured for service '{_configured_service}'. "
            f"Cannot reconfigure the same process for '{service_name}'."
        )

    _configure_logging()

    if _configured_service is None:
        resource = _build_resource(service_name)
        provider = TracerProvider(
            resource=resource,
            sampler=_resolve_sampler(),
        )
        provider.add_span_processor(_build_span_processor())
        trace.set_tracer_provider(provider)
        metric_reader = _build_metric_reader()
        if metric_reader is None:
            metrics.set_meter_provider(
                MeterProvider(
                    resource=resource,
                )
            )
        else:
            metrics.set_meter_provider(
                MeterProvider(
                    resource=resource,
                    metric_readers=[metric_reader],
                )
            )
        _configured_service = service_name

    if service_name == "travel-orchestrator" and not _httpx_instrumented:
        HTTPXClientInstrumentor().instrument()
        _httpx_instrumented = True

    return trace.get_tracer(service_name)


def get_tracer(name):
    return trace.get_tracer(name)


def get_meter(name):
    return metrics.get_meter(name)


def metric_attributes(**attributes):
    for key, value in attributes.items():
        if key in _BANNED_METRIC_ATTRIBUTE_KEYS:
            raise ValueError(f"Metric attribute '{key}' is not allowed due to cardinality risk.")
        if isinstance(value, str) and len(value) > 100:
            raise ValueError(f"Metric attribute '{key}' is too long and may be high-cardinality.")
    return attributes


def instrument_fastapi(app):
    if not getattr(app.state, "otel_fastapi_instrumented", False):
        FastAPIInstrumentor.instrument_app(app)
        app.state.otel_fastapi_instrumented = True
