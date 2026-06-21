import os
import json
from typing import Any, Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "validation_config.json")

class ValidationError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

def load_validation_config() -> Dict[str, List[Any]]:
    if not os.path.exists(CONFIG_PATH):
        # Fallback to defaults if file is missing
        default_config = {
            "process_type": ["Standard", "Express", "Proc A"],
            "letter_language": ["English", "Hindi", "Marathi"],
            "letter_type": ["Official letter", "Ltr", "Demiofficial"],
            "office": ["Central Office", "Office X", "Regional Office"],
            "department": ["DBR", "Legal", "Dept Y", "GEN"],
            "case_access_level": ["limited", "wider", "restricted"],
            "privacy_level": ["confidential", "public"],
            "inward_priority_level": ["high", "medium", "low"],
            "division": ["Legis", "Gen", "Division A"],
            "sub_section": ["Section A", "Sec 1", "Section B"]
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def validate_field(field_name: str, value: Any):
    config = load_validation_config()
    allowed_values = config.get(field_name)
    if allowed_values is not None:
        if value not in allowed_values:
            raise ValidationError(
                message=f"Invalid value '{value}' for field '{field_name}'. Allowed values: {allowed_values}",
                error_code=f"INVALID_{field_name.upper()}"
            )
