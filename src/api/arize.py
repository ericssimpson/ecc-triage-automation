import logging
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register
from src.services.llm.classifier import process_emergency_call
from src.utils.storage import save_call_to_json

logger = logging.getLogger(__name__)

# Initialize tracing
tracer_provider = register(
    project_name="911evaluator",
    endpoint="http://localhost:6006/v1/traces",
)

LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

def process_call(call_text: str) -> dict:
    """Process a call with telemetry tracking."""
    try:
        # Process the call using the LLM
        response = process_emergency_call(call_text)
        
        # Save to JSON file
        save_call_to_json(call_text, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in process_call: {e}")
        raise