# arize phoenix integration
from phoenix.otel import register
import os 
from opentelemetry import trace 
from opentelemetry.sdk.trace import TracerProvider 
from opentelemetry.sdk.trace.export import BatchSpanProcessor 
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Phoenix Cloud endpoint
endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
api_key = os.getenv("PHOENIX_API_KEY")


tracer_provider = register(
    project_name="visionFlow",
    endpoint="https://app.phoenix.arize.com/s/thisisswastik",
    auto_instrument = True
)


tracer = trace.get_tracer("vision-agent")


