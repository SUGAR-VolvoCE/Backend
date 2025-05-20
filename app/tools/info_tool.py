# app/tools/info_tool.py

import requests

API_BASE_URL = "http://localhost:5000/api/machines"  

def search_machine(user_id: int, serial_number: str):
    response = requests.post(f"{API_BASE_URL}/find", json={
        "user_id": user_id,
        "search_string": serial_number
    })
    if response.status_code == 200:
        return {"found": True, "data": response.json()}
    else:
        return {"found": False}

def search_machines_by_model(user_id: int, model_name: str):
    print(user_id)
    response = requests.post(f"{API_BASE_URL}/find_by_model", json={
        "user_id": user_id,
        "model": model_name
    })
    if response.status_code == 200:
        return {"found": True, "data": response.json()}
    else:
        return {"found": False}

def create_machine(user_id: int, model: str, serial_number: str):
    response = requests.post(f"{API_BASE_URL}/", json={
        "user_id": user_id,
        "model": model,
        "serial_number": serial_number
    })
    data = response.json()  # Always get the full response JSON

    if response.status_code == 201:
        return {"created": True, "data": data}
    else:
        return {"created": False, "error": data, "status_code": response.status_code}


def match_model(model_name: str, user_id: int):
    # Validate against known models
    valid_models = ["EC220D", "WLOL60H"]
    valid = model_name.upper() in valid_models
    if valid:
        machines_result = search_machines_by_model(user_id, model_name)
        if machines_result["found"]:
            serials = [m["serial_number"] for m in machines_result["data"]["machines"]]
            return {
                "model_name": model_name,
                "related_serial_numbers": serials  # ✅ return related serials
            }
        else:
            print("Not found")

            return {
                "model_name": model_name,
                "related_serial_numbers": []
            }
    else:
        return {"model_name": None, "related_serial_numbers": []}

def match_serial_number(serial_number: str, user_id: int):
    try:
        print("Trying to get machine")
        data = search_machine(user_id, serial_number)
    except Exception as e:
        print(e)
        return {"serial_number": None}

    if data["found"]:
        return {"found": True, "data": data["data"]}
    else:
        return {"serial_number": None}


create_machine_tool = {
    "type": "function",
    "function": {
        "name": "create_machine",
        "description": "Create a new machine record in the database with the given model and serial number.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The ID of the user who owns this machine."
                },
                "model": {
                    "type": "string",
                    "description": "The model name of the machine, e.g., 'EC220D'."
                },
                "serial_number": {
                    "type": "string",
                    "description": "The serial number of the machine, must be unique per user."
                }
            },
            "required": ["user_id", "model", "serial_number"]
        }
    }
}


match_model_tool = {
    "type": "function",
    "function": {
        "name": "match_model",
        "description": "Validate a construction machine model name provided by the customer and list matching serial numbers if any.",
        "parameters": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "The machine model name to validate, e.g., 'EC220D' or 'LH60'."
                },
                "user_id": {
                    "type": "string",
                    "description": "The ID of the user who owns the machines."
                }
            },
            "required": ["model_name", "user_id"]
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
                },
                "user_id": {
                    "type": "string",
                    "description": "The ID of the user who owns this machine."
                }
            },
            "required": ["serial_number", "user_id"]
        }
    }
}
