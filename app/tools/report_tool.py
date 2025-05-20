import requests

API_BASE_URL = "http://localhost:5000/api/tickets"  

# === TOOL DEFINITIONS ===

solve_ticket_tool = {
    "type": "function",
    "function": {
        "name": "solve_ticket",
        "description": "Mark a troubleshooting ticket as resolved based on its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ID of the ticket of the current issue in the conversation"
                }
            },
            "required": ["ticket_id"]
        }
    }
}

create_ticket_tool = {
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": "Creates a troubleshooting ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "machine_id": {
                    "type": "string",
                    "description": "The ID of the machine (machine_id) that has the current issue in the conversation"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the issue, must be short"
                },
                "description": {
                    "type": "string",
                    "description": "The full description of the problem."
                }
            },
            "required": ["machine_id", "title", "description"]
        }
    }
}

edit_ticket_tool = {
    "type": "function",
    "function": {
        "name": "edit_ticket",
        "description": "Edit a ticket's title and description",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The unique ID of the ticket to edit"
                },
                "title": {
                    "type": "string",
                    "description": "The new title for the ticket"
                },
                "description": {
                    "type": "string",
                    "description": "The new description for the ticket.  All the relevant info collected based on the conversation (for now), issues, what has been checked, etc. Also if the ticket is solved, the SOLUTION should be added to the description."
                }
            },
            "required": ["ticket_id", "title", "description"]
        }
    }
}

# === TICKET FUNCTIONS ===

def create_ticket(machine_id: int, title: str, description: str):
    url = f"{API_BASE_URL}/add"
    payload = {
        "machine_id": machine_id,
        "title": title,
        "description": description
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return {
            "success": data.get("success", False),
            "ticket": data.get("ticket", {})
        }

    except requests.RequestException as e:
        print(f"Failed to create ticket: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def solve_ticket(ticket_id: str):
    url = f"{API_BASE_URL}/resolve/{ticket_id}"

    try:
        response = requests.put(url)
        response.raise_for_status()
        data = response.json()
        return {
            "success": data.get("success", False),
            "ticket": data.get("ticket", {})
        }

    except requests.RequestException as e:
        print(f"Failed to resolve ticket: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def edit_ticket(ticket_id: int, title: str, description: str):
    url = f"{API_BASE_URL}/edit/{ticket_id}"
    payload = {
        "title": title,
        "description": description
    }

    try:
        response = requests.put(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return {
            "success": data.get("success", False),
            "ticket": data.get("ticket", {})
        }

    except requests.RequestException as e:
        print(f"Failed to edit ticket: {e}")
        return {
            "success": False,
            "error": str(e)
        }
