# Observability

## Purpose

This repo uses OpenTelemetry as the primary observability framework for:
- traces
- metrics
- log correlation

The implementation is designed to be:
- development-friendly locally
- OTLP-ready for production
- explicit about sampling, service identity, and failure behavior

## Current Signals

### Traces

Implemented with:
- manual business spans in the orchestrator
- automatic `httpx` instrumentation
- automatic FastAPI instrumentation

Key spans:
- `travel_planner.run`
- `memory_load`
- `planner`
- `executor`
- `critic`
- `memory_save`
- `mcp.list_tools`
- `mcp.call_tool`

### Metrics

Current metrics include:

- `travel.graph.runs`
- `travel.graph.run.duration`
- `travel.graph.node.runs`
- `travel.graph.node.duration`
- `travel.mcp.list_tools.duration`
- `travel.mcp.list_tools.failures`
- `travel.mcp.tool.calls`
- `travel.mcp.tool.failures`
- `travel.mcp.tool.duration`
- `travel.mcp.server.requests`
- `travel.mcp.server.successes`
- `travel.mcp.server.failures`
- `travel.mcp.server.duration`

### Logs

Logs are emitted via standard Python logging and enriched with:
- `trace_id`
- `span_id`

This is log correlation, not a separate OpenTelemetry log export pipeline.

## Telemetry Bootstrap

Shared setup lives in [common/telemetry.py](/d:/agentic_travel_planner/common/telemetry.py).

Responsibilities:
- configure `TracerProvider`
- configure `MeterProvider`
- attach OTLP exporters when env vars are present
- fall back to console exporters in development
- enrich logs with active trace/span context
- instrument `httpx` and FastAPI

## Environment Variables

### Identity

```bash
APP_ENV=development
APP_VERSION=dev
OTEL_SERVICE_NAME=travel-orchestrator
```

### OTLP traces

```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
```

or

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### OTLP metrics

```bash
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:4318/v1/metrics
APP_OTEL_METRIC_EXPORT_INTERVAL_MS=5000
```

### Export headers

```bash
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer <token>
```

### Sampling

```bash
APP_OTEL_SAMPLER=always_on
APP_OTEL_SAMPLER_ARG=1.0
```

Supported sampler values:
- `always_on`
- `always_off`
- `traceidratio`
- `parentbased_traceidratio`

Recommended production default:

```bash
APP_OTEL_SAMPLER=parentbased_traceidratio
APP_OTEL_SAMPLER_ARG=0.1
```

## Runtime Behavior

### Development

If OTLP endpoints are not set and `APP_ENV` is not `production`:
- traces export to console
- metrics export to console

### Production

If `APP_ENV=production` and OTLP endpoints are missing:
- tracing setup fails fast
- metric setup fails fast

This prevents silent fallback to noisy console exporters in production.

## Guardrails

The current telemetry layer includes:
- explicit service identity
- configurable sampling
- protection against configuring the same process for multiple service names
- metric attribute guardrails to avoid high-cardinality labels
- explicit success/failure metrics for MCP paths

## Infrastructure Metadata

Cluster, namespace, pod, and related infra metadata should generally be added when deployed to real infrastructure such as EKS.

Preferred pattern:
- app code sets app-level metadata
- collector or platform adds infra-level metadata

Examples of later-stage infra metadata:
- `k8s.cluster.name`
- `k8s.namespace.name`
- `k8s.pod.name`
- `k8s.node.name`
- `k8s.container.name`

## Production Direction

For a production deployment, the preferred flow is:

```text
app -> OpenTelemetry / ADOT Collector -> backend
```

Instead of:

```text
app -> hosted backend directly
```

Benefits:
- auth/signing centralization
- batching and retry control
- easier backend migration
- better infra metadata enrichment
