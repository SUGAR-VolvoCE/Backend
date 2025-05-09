# app/tools/info_tool.py
def match_model(model_name: str):
    print(f"DEBUG: Validating model_name: {model_name}")  # Debug statement
    # Simulate validation logic
    if model_name.lower() in ["ec160e", "ec220d"]:
        return {"model_name": model_name}
    return {}

def match_serial_number(serial_number: str):
    print(f"DEBUG: Validating serial_number: {serial_number}")  # Debug statement
    # Simulate validation logic
    if len(serial_number) >= 6 and serial_number.isalnum():
        return {"serial_number": serial_number}
    return {}

match_model_tool = {
    "type": "function",
    "function": {
        "name": "match_model",
        "description": "Validate a construction machine model name provided by the customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "The machine model name to validate, e.g., 'CAT D6' or 'Komatsu PC200'."
                }
            },
            "required": ["model_name"]
        }
    }
}

match_serial_number_tool = {
    "type": "function",
    "function": {
        "name": "match_serial_number",
        "description": "Validate a construction machine serial number provided by the customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "serial_number": {
                    "type": "string",
                    "description": "The serial number to validate. Must be alphanumeric and at least 6 characters long."
                }
            },
            "required": ["serial_number"]
        }
    }
}
