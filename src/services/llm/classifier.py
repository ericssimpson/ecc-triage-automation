import os
import logging
from langchain_openai import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from .prompt_templates import prompt_911

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

# Define response schemas
response_schemas = [
    ResponseSchema(name="priority", description="The priority of the call"),
    ResponseSchema(name="summary", description="A summary of the call"),
    ResponseSchema(name="department", description="The department the call dispatched to"),
    ResponseSchema(name="confidence", description="The confidence in the priority"),
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

def process_emergency_call(call_text: str) -> dict:
    """Process an emergency call and classify it."""
    try:
        # Get the LLM instance lazily
        llm = LLMHandler.get_llm()
        
        # Get the response from the language model
        response = llm.invoke(
            prompt_911.format_messages(
                call_text=call_text, 
                format_instructions=output_parser.get_format_instructions()
            )
        )

        # Parse the response
        return output_parser.parse(response.content)
        
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise