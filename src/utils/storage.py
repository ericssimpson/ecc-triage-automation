import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

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

    # Append new call and save
    calls.append(call_entry)
    with open(file_path, "w") as f:
        json.dump(calls, f, indent=2)