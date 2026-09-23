exporters:
  otlphttp/okapi:
    endpoint: ${OKAPI_INGESTER_URL}
    encoding: proto
    compression: none

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, transform/sanitize_spans]
      exporters: [debug, span_metrics, otlphttp/okapi]
    metrics:
      receivers: [docker_stats, http_check/frontend-proxy, host_metrics, nginx, otlp, redis, postgresql, prometheus/ad, span_metrics]
      processors: [resourcedetection, memory_limiter]
      exporters: [debug, otlphttp/okapi]
    logs:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, transform/sanitize_logs]
      exporters: [debug, otlphttp/okapi]
