import openai
import time
import json
import os
from typing import Dict, List, Tuple
from app.tools.rag_tool import search_manuals
from app.tools.report_tool import create_ticket, edit_ticket, solve_ticket
from app.tools.info_tool import match_model, match_serial_number, create_machine

client = openai.OpenAI()

assistant_ids = {
    "info": os.getenv("INFO_ASSISTANT_ID"),
    "troubleshoot": os.getenv("TROUBLESHOOT_ASSISTANT_ID"),
    "solve": os.getenv("SOLVE_ASSISTANT_ID"),
}

assistants = {
    phase: client.beta.assistants.retrieve(assistant_id=assistant_id)
    for phase, assistant_id in assistant_ids.items()
    if assistant_id is not None
}

user_threads = {}
user_info = {}
tickets_info = {}

tool_function_map = {
    "match_model": match_model,
    "match_serial_number": match_serial_number,
    "create_machine": create_machine,
    "search_manuals": search_manuals,
    "solve_ticket" : solve_ticket,
    "create_ticket": create_ticket,
    "edit_ticket": edit_ticket
}

def handle_tool_calls(tool_calls, user_id) -> Tuple[List[Dict], List[str]]:
    outputs = []
    extra_messages = []
    processed_ids = set()  # Set to track processed tool call IDs

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Skip processing if this tool_call_id has already been processed
        if tool_call.id in processed_ids:
            continue  # Avoid processing duplicate tool call

        # Add the tool call id to the processed set
        processed_ids.add(tool_call.id)

        try:
            # Check if the tool_name is in the map of tool functions
            if tool_name not in tool_function_map:
                print(f"Unknown tool: {tool_name}")  # Debug log
                outputs.append({"tool_call_id": tool_call.id, "output": f"Unknown tool {tool_name}"})
                continue

            try:
                # Processing tool calls based on the tool_name
                if tool_name == "search_manuals":
                    try:
                        args.setdefault("machine_name", user_info[user_id].get("model_name", "DEFAULT"))
                        result = tool_function_map[tool_name](
                            query=args.get("query", "default query"),
                            machine_name=args["machine_name"]
                        )
                    except Exception as e:
                        print(f"Error in search_manuals: {str(e)}")  # Log error
                        result = {"error": f"Error in search manuals: {str(e)}"}

                    docs = result.get("documents", [])
                    if docs:
                        docs_text = "\n\n".join(docs)
                        extra_messages.append(
                            f"The knowledge base returned the following documents:\n\n{docs_text}\n\nPlease use this information to answer my question."
                        )
                else:
                    # Inject user_id where necessary for other tool calls
                    if tool_name in ["match_model", "match_serial_number", "create_machine"]:
                        args["user_id"] = user_id
                    if tool_name == "create_ticket":
                        args["machine_id"] = user_info[user_id]["machine_id"]
                    if tool_name in ["solve_ticket", "edit_ticket"]:
                        if user_id not in tickets_info:
                            raise ValueError(f"Tickets information for user {user_id} not found.")
                        args["ticket_id"] = tickets_info[user_id]["ticket_id"]

                    try:
                        result = tool_function_map[tool_name](**args)
                    except Exception as e:
                        print(f"Error in calling {tool_name}: {str(e)}")  # Log error
                        result = {"error": f"Error in calling tool {tool_name}: {str(e)}"}

                # Store user data when available based on tool_name
                try:
                    if user_id not in user_info:
                        raise ValueError(f"User info for user_id {user_id} is missing.")
                    
                    if tool_name == "match_model":
                        user_info[user_id]["model_name"] = result.get("model_name")
                        possible_serials = result.get("related_serial_numbers")
                        if possible_serials:
                            serials_list = ", ".join(possible_serials)
                            extra_messages.append(
                                f"The found serial numbers for that model are: {serials_list}. Check if the serial number is one of those"
                            )

                    elif tool_name == "match_serial_number":
                        user_info[user_id]["serial_number"] = result.get("serial_number")
                        machine_data = result.get("data", {})
                        user_info[user_id].update({
                            "machine_id": machine_data.get("machine_id"),
                            "model_name": machine_data.get("machine_model"),
                            "serial_number": machine_data.get("machine_number"),
                        })
                    elif tool_name == "create_machine":
                        machine_data = result.get("data", {})
                        user_info[user_id].update({
                            "machine_id": machine_data.get("machine_id"),
                            "user_id": machine_data.get("user_id"),
                            "model_name": machine_data.get("model"),
                            "serial_number": machine_data.get("serial_number"),
                        })
                    elif tool_name in ["edit_ticket"]:
                        ticket_data = result.get("ticket", {})
                        if user_id not in tickets_info:
                            tickets_info[user_id] = {}
                        tickets_info[user_id].update({
                            "ticket_id": ticket_data.get("ticket_id"),
                            "machine_id": ticket_data.get("machine_id"),
                            "title": ticket_data.get("title"),
                            "description": ticket_data.get("description"),
                            "resolved": ticket_data.get("resolved")
                        })
                    elif tool_name == "create_ticket":
                        try:
                            ticket_data = result.get("ticket", {})
                            
                            # Debugging: Log the result and data to inspect what's being returned
                            print(f"Received ticket data: {ticket_data}")  # Log the ticket data

                            # Check if ticket data contains all necessary fields before updating
                            if "ticket_id" in ticket_data and "machine_id" in ticket_data and "title" in ticket_data and "description" in ticket_data:
                                if user_id not in tickets_info:
                                    tickets_info[user_id] = {}
                                tickets_info[user_id].update({
                                    "ticket_id": ticket_data.get("ticket_id"),
                                    "machine_id": ticket_data.get("machine_id"),
                                    "title": ticket_data.get("title"),
                                    "description": ticket_data.get("description"),
                                    "resolved": ticket_data.get("resolved", False)  # Default to False if not provided
                                })
                            else:
                                raise ValueError("Missing required fields in ticket data")
                            
                        except Exception as e:
                            print(f"Error while storing ticket data for {user_id}: {str(e)}")  # Log specific error for create_ticket
                            outputs.append({"tool_call_id": tool_call.id, "output": f"Error in creating ticket: {str(e)}"})

                    elif tool_name == "solve_ticket":
                        ticket_data = result.get("ticket", {})
                        if user_id not in tickets_info:
                            tickets_info[user_id] = {}
                        tickets_info[user_id].update({
                            "resolved": ticket_data.get("resolved")
                        })

                except Exception as e:
                    print(f"Error in storing user data for {tool_name}: {str(e)}")  # Log error

            except Exception as e:
                print(f"General error in processing tool call {tool_name}: {str(e)}")  # Log any unexpected errors
                result = {"error": f"General error processing tool call: {str(e)}"}

            # Append result
            outputs.append({"tool_call_id": tool_call.id, "output": json.dumps(result)})

        except Exception as e:
            print(f"Exception while processing tool call {tool_call.id}: {str(e)}")  # Log outer exception
            outputs.append({"tool_call_id": tool_call.id, "output": f"Error: {str(e)}"})

    return outputs, extra_messages


def get_or_create_thread(user_id: str, reset: bool):
    if user_id not in user_threads:
        user_threads[user_id] = {"phase": "info", "threads": {}}
    if reset or "info" not in user_threads[user_id]["threads"]:
        thread = client.beta.threads.create()
        user_threads[user_id]["phase"] = "info"
        user_threads[user_id]["threads"]["info"] = thread
    return user_threads[user_id]["threads"][user_threads[user_id]["phase"]]

def ask_troubleshoot_intent(user_id):
    thread = get_or_create_thread(user_id, reset=False)
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Please help me troubleshoot the problem with my machine."
    )

def chat_with_assistant(user_id: str, message: str, reset: bool = False):
    if reset or user_id not in user_threads:
        user_threads[user_id] = {"phase": "info", "threads": {}}
        user_info[user_id] = {"model_name": None, "serial_number": None, "machine_name": None}

    current_phase = user_threads[user_id]["phase"]

    if current_phase not in assistants:
        print(f"Warning: phase '{current_phase}' not found. Falling back to 'info'.")
        current_phase = "info"
        user_threads[user_id]["phase"] = "info"

    assistant = assistants[current_phase]
    thread = get_or_create_thread(user_id, reset)

    if reset:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Forget previous conversations. Start fresh."
        )

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            print(f"Tool calls received: {[tc.id for tc in tool_calls]}")  # DEBUG
            outputs, extra_messages = handle_tool_calls(tool_calls, user_id)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )

        elif run_status.status == "completed":
            break

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value

    print("DEBUG: model_name =", user_info[user_id]["model_name"])
    print("DEBUG: serial_number =", user_info[user_id]["serial_number"])

    if current_phase == "info" and user_info[user_id]["model_name"] and user_info[user_id]["serial_number"]:
        print("✅ All information collected. Moving to troubleshooting...")
        ask_troubleshoot_intent(user_id)

        model_name = user_info[user_id]["model_name"]
        serial_number = user_info[user_id]["serial_number"]
        print(f"MOVING TO TROUBLESHOOT for model {model_name} and serial number {serial_number}")

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        user_threads[user_id]["phase"] = "troubleshoot"

        thread = client.beta.threads.create()
        user_threads[user_id]["threads"]["troubleshoot"] = thread

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Now moving to troubleshooting for model {model_name} with serial number {serial_number}."
        )

        assistant = assistants["troubleshoot"]
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

    extra_messages_to_send = []

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            outputs, extra_messages = handle_tool_calls(tool_calls, user_id)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )

            extra_messages_to_send.extend(extra_messages)

        elif run_status.status == "completed":
            break

    for msg in extra_messages_to_send:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=msg
        )

    return response
