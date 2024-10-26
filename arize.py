from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers import (
    ResponseSchema,
    StructuredOutputParser,
    BooleanOutputParser,
)

import json
from datetime import datetime
from pathlib import Path
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register


def save_call_to_json(
    call_text: str, response_data: dict, filename: str = "emergency_calls.json"
) -> None:
    # Create entry with timestamp
    call_entry = {
        "timestamp": datetime.now().isoformat(),
        "call_text": call_text,
        "priority": response_data["priority"],
        "summary": response_data["summary"],
        "confidence": response_data["confidence"],
    }

    # Load existing data or create new list
    file_path = Path(filename)
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                calls = json.load(f)
        except json.JSONDecodeError:
            calls = []
    else:
        calls = []

    # Append new call and save
    calls.append(call_entry)
    with open(file_path, "w") as f:
        json.dump(calls, f, indent=2)


# COLLECTOR_HOST = os.getenv("COLLECTOR_HOST", "localhost")
# endpoint = f"http://{COLLECTOR_HOST}:6006/v1"
# tracer_provider = trace_sdk.TracerProvider()
# tracer_provider.add_span_processor(
#     SimpleSpanProcessor(OTLPSpanExporter(f"{endpoint}/traces"))
# )
# trace_api.set_tracer_provider(tracer_provider)
# tracer = trace_api.get_tracer(__name__)

tracer_provider = register(
    project_name="911evaluator",  # Default is 'default'
    endpoint="http://localhost:6006/v1/traces",
)


LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# tracer_provider = register(
#     project_name="my-llm-app",  # Default is 'default'
#     endpoint="http://localhost:6006/v1/traces",
# )

response_schemas = [
    ResponseSchema(name="priority", description="The priority of the call"),
    ResponseSchema(name="summary", description="A summary of the call"),
    ResponseSchema(name="confidence", description="The confidence in the priority"),
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

user_prompt = HumanMessagePromptTemplate.from_template("{call_text}")

system_prompt = SystemMessagePromptTemplate.from_template("""
You are an operator for a emergency call line, you simply need to determine, rapidly, if the text you see qualifies as 1 of three possible options. 

you will provide will be in the form of a JSON, such as (priority: 'RED' ) (summary: 'car suspicious hoodie' ) ( confidence: '80' ) 

1: RED - the words you are hearing qualify as needing rapid emergency services, and the operator will need to read text that says "This is an emergency CODE RED" - for example, if the person is bleeding, saying words like "please help" "coming after me" "knife" "gun" - things of that nature, that raise an immediate alarm.

2: ORANGE - the words you are hearing qualify as in the middle, where a sense of urgency is involved, but might not qualify as needing an ambulance deployed to the location immediately. This might happen if the person is saying "umm" or "wait" or if you are unsure if it's an immediate emergency, or if it could be something non-serious.

3: GREEN - the nature of the call doesn't sound immediately dangerous, as in, the person calling is reporting a missing cat, or issuing a noise complaint about their neighbor, which doesn't require any type of immediate response. Example might be, the person is calling about a suspicious person, or car in their neighborhood.

Also, you will only provide the threat level in terms of its priority - followed by a three word summary - or the words used by the caller that indicate to you that there is indeed a justification for the chosen priority. And you will rate your confidence in the priority level you have assigned things to.

An example output you will provide will be in the form of a JSON, such as 
 (priority: 'GREEN' ) (summary: 'cat tree lost' ) ( confidence: '60' )
{format_instructions}
""")

prompt_911 = ChatPromptTemplate.from_messages([system_prompt, user_prompt])

# Initialize the language model
llm_streaming = ChatOpenAI(
    model_name="gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"],
    temperature=1.0,
    streaming=False,
)


def process_call(call_text: str) -> dict:
    # Get the response from the language model
    response = llm_streaming.invoke(
        prompt_911.format_messages(
            call_text=call_text, format_instructions=format_instructions
        )
    )

    # Parse the response
    parsed_response = output_parser.parse(response.content)

    # Save to JSON file
    save_call_to_json(call_text, parsed_response)

    return parsed_response
