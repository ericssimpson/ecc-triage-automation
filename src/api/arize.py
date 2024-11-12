from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
import os
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers import (
    ResponseSchema,
    StructuredOutputParser,
)
import json
from datetime import datetime
from pathlib import Path
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

logger = logging.getLogger(__name__)

class LLMHandler:
    _instance = None
    _llm = None

    @classmethod
    def get_llm(cls):
        if cls._llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API key not found in environment variables")
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            cls._llm = ChatOpenAI(
                model_name="gpt-4",
                api_key=api_key,
                temperature=1.0,
                streaming=False,
            )
        return cls._llm

def save_call_to_json(
    call_text: str, response_data: dict, filename: str = "data/call_logs.json"
) -> None:
    try:
        call_entry = {
            "timestamp": datetime.now().isoformat(),
            "call_text": call_text,
            "priority": response_data["priority"],
            "department": response_data["department"],
            "summary": response_data["summary"],
            "confidence": response_data["confidence"],
        }
    except Exception as e:
        logger.error(f"Error creating call entry: {e}")
        raise

    # Get project root directory
    root_dir = Path(__file__).parent.parent.parent
    file_path = root_dir / filename

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data or create new list
    calls = []
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                calls = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error reading JSON file: {e}")
            # Continue with empty list if file is corrupted

    # Append new call and save
    calls.append(call_entry)
    with open(file_path, "w") as f:
        json.dump(calls, f, indent=2)

# Initialize tracing
tracer_provider = register(
    project_name="911evaluator",
    endpoint="http://localhost:6006/v1/traces",
)

LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Define response schemas
response_schemas = [
    ResponseSchema(name="priority", description="The priority of the call"),
    ResponseSchema(name="summary", description="A summary of the call"),
    ResponseSchema(name="department", description="The department the call dispatched to"),
    ResponseSchema(name="confidence", description="The confidence in the priority"),
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# Define prompts
user_prompt = HumanMessagePromptTemplate.from_template("{call_text}")
system_prompt = SystemMessagePromptTemplate.from_template("""
You are an operator for a emergency call line, you simply need to determine, rapidly, if the text you see qualifies as 1 of three possible options. 

you will provide will be in the form of a JSON, such as (priority: 'RED' ) (summary: 'car suspicious hoodie' ) ( confidence: '80' ) 

1: RED - the words you are hearing qualify as needing rapid emergency services, and the operator will need to read text that says "This is an emergency CODE RED" - for example, if the person is bleeding, saying words like "please help" "coming after me" "knife" "gun" - things of that nature, that raise an immediate alarm.

2: ORANGE - the words you are hearing qualify as in the middle, where a sense of urgency is involved, but might not qualify as needing an ambulance deployed to the location immediately. This might happen if the person is saying "umm" or "wait" or if you are unsure if it's an immediate emergency, or if it could be something non-serious.

3: GREEN - the nature of the call doesn't sound immediately dangerous, as in, the person calling is reporting a missing cat, or issuing a noise complaint about their neighbor, which doesn't require any type of immediate response. Example might be, the person is calling about a suspicious person, or car in their neighborhood.

In addition, you will provide the department this call will be dispatched to.
                    
1: EMS - the words you are hearing relate to people or living animals' physical health, such as bleeding out , injury, and coma. 

2: FIRDEPT - the words you are hearing relate to the fire hazard in public space and require fire department to operate.  

3: POLICEDEPT - the words you are hearing relate to the violence, community safety, and everything concerning policing. 

An example output you will provide will be in the form of a JSON, such as 
(priority: 'GREEN' ) (summary: 'cat tree lost' ) (department: 'POLICEDEPT') ( confidence: '60' )

Respond in JSON format with these fields:
{{
    "priority": "PRIORITY_LEVEL",
    "summary": "summary of event",
    "confidence": "confidence of event",
    "department": "DEPARTMENT"
}}
{format_instructions}""")

prompt_911 = ChatPromptTemplate.from_messages([system_prompt, user_prompt])

def process_call(call_text: str) -> dict:
    """Process an emergency call and classify it."""
    try:
        # Get the LLM instance lazily
        llm = LLMHandler.get_llm()
        
        # Get the response from the language model
        response = llm.invoke(
            prompt_911.format_messages(
                call_text=call_text, 
                format_instructions=format_instructions
            )
        )

        # Parse the response
        parsed_response = output_parser.parse(response.content)
        
        # Save to JSON file
        save_call_to_json(call_text, parsed_response)
        
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise