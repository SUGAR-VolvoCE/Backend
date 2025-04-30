# app/tools/info_tool.py
def match_model(model_name: str):
    # Validate the model (e.g., against your DB or predefined list)
    valid = model_name in ["EC220D", "EC250E", "EC300E"]
    if valid:
        return {"model_name": model_name}  # ✅ must return in this format
    else:
        return {"model_name": None}


def match_serial_number(serial_number: str):
    # Validate serial (e.g., numeric and correct length)
    valid = serial_number.isdigit() and len(serial_number) == 10
    if valid:
        return {"serial_number": serial_number}  # ✅ must return in this format
    else:
        return {"serial_number": None}

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
