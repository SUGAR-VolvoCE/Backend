# app/tools/info_tool.py
def match_model(model_name: str) -> bool:
    valid_models = ["EC140E", "EC160E", "EC180E", "EC200E", "EC220E", "EC250E", "EC300E", "EC350E", "EC380E", "EC480E", "EC750E", "EC950F", "EW60E", "EW160E", "EW180E", "EW220E", "L20H", "L25H", "L30G", "L35G", "L45H", "L50H", "L60H", "L70H", "L90H", "L110H", "L120H", "L150H", "L180H", "L220H", "L260H", "L350H", "A25G", "A30G", "A35G", "A40G", "A45G", "A60H", "EC380EHR", "EC480EHR", "P6820D ABG", "P7820D ABG", "P8820D ABG"]

    if model_name in valid_models:
        return f"The model '{model_name}' is valid."
    else:
        return f"The model '{model_name}' is not in the list."

def match_serial_number(serial_number: str) -> bool:
    if serial_number.isalnum() and len(serial_number) >= 6:
        return f"The number '{serial_number}' is valid."
    else: 
        return f"The number '{serial_number}' is not in the list."


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
