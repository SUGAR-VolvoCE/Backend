import openai
import time
import json
import os
import requests
from app.utils.replace_image_placeholders import process_text_return_image_url
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from app.tools.rag_tool import search_manuals
from app.tools.report_tool import create_ticket, edit_ticket, solve_ticket
from app.tools.info_tool import match_model, match_serial_number, create_machine
from app.yolo.yolo_tool import detect_yolo
from app.utils import replace_image_placeholders
import time
from .logger import logger
from .routes import ConversationMessage, add_conversation

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dn8rj0auz/image/upload"
UPLOAD_PRESET = "sugar-2025"

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
custom_thread_id = {}

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
                        result = (
                            f"\n\nThe knowledge base returned the following documents:\n\n{docs_text}\n\n"
                            "Please use this information to answer the user's question."
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
                            result = (
                                f"\n\nThe found serial numbers for that model are: {serials_list}. "
                                "Check if the serial number is one of those."
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

    return outputs

def get_or_create_thread(user_id: str, reset: bool):
    if user_id not in user_threads:
        user_threads[user_id] = {"phase": "info", "threads": {}}
    if reset or "object" not in user_threads[user_id]["threads"]:
        thread = client.beta.threads.create()
        user_threads[user_id]["phase"] = "info"
        user_threads[user_id]["threads"]["object"] = thread
        user_threads[user_id]["threads"]["basic_info"] = False

    return [user_threads[user_id]["threads"], user_threads[user_id]["threads"]["object"]]


def chat_with_assistant(user_id: str, message: str, reset: bool = False, file_url: str = None):
    if reset or user_id not in user_threads:
        tickets_info[user_id] = {}
        custom_thread_id[user_id] = str(uuid.uuid4())
        user_threads[user_id] = {"phase": "info", "threads": {}}
        user_info[user_id] = {"model_name": None, "serial_number": None, "machine_name": None}

    current_phase = user_threads[user_id]["phase"]
    image_url = None

    if current_phase not in assistants:
        print(f"Warning: phase '{current_phase}' not found. Falling back to 'info'.")
        current_phase = "info"
        user_threads[user_id]["phase"] = "info"

    assistant = assistants[current_phase]
    thread_vector, thread = get_or_create_thread(user_id, reset)

    if reset:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Forget previous conversations. Start fresh."
        )

            # *** Save user message to your DB with custom thread_id and ticket_id ***
    try:
        db_message = ConversationMessage(
            thread_id=custom_thread_id[user_id],
            ticket_id=tickets_info[user_id].get("ticket_id") if user_id in tickets_info else None,
            sender="user",
            message=message,
            media_url=file_url,
            timestamp=datetime.now(timezone.utc)  # Provide timestamp here

        )
        add_conversation(db_message)
    except Exception as e:
        logger.debug(f"Error saving user message: {str(e)}")
    
    if file_url:
        try:
            result = detect_yolo(file_url)  # result is a dict
            detections = result["detections"]
            print(detections)

            image_url = result["annotated_image_url"]
            print(image_url)

            if detections:
                detected_text = "\n".join([
                    f"- {label} at {location}"
                    for label, location in detections
                ])
                print(detected_text)

                message += f"System analysis of image (not user input):\n\n**Detected Issues:**\n{detected_text}\n\n**Annotated Image:** {image_url}"
            else:
                message += "System analysis of image (not user input): \n\n✅ No issues detected with confidence above 25% in the image (from the image uploaded)."

        except Exception as e:
            message += f"System analysis of image \n\n❌ Error processing image: {e}"

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    retries = 0
    MAX_RETRIES = 30

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        logger.debug(f"***** Run status: {run_status.status}")
        if retries >= MAX_RETRIES:
            logger.error("Timeout or max retries exceeded. Exiting.")
            break
        retries += 1
        if run_status.status == "incomplete":
            logger.debug(f"***** {run_status.incomplete_details}")
            break
        elif run_status.status == "failed":
            logger.debug(f"***** {run_status.last_error}")
            break
        elif run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            logger.debug(f"Tool calls received: {[tc.id for tc in tool_calls]}")
            outputs = handle_tool_calls(tool_calls, user_id)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )
        elif run_status.status == "completed":
            break

        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value
    response, image_url = process_text_return_image_url(response, image_dir="data/static/images")

    print("DEBUG: model_name =", user_info[user_id]["model_name"])
    print("DEBUG: serial_number =", user_info[user_id]["serial_number"])

    # Transition to troubleshoot phase if info is complete
    if current_phase == "info" and user_info[user_id]["model_name"] and user_info[user_id]["serial_number"]:
        
        if not thread_vector["basic_info"]:
            print("TURNING IT INTO TRUE")
            thread_vector["basic_info"] = True
            return response, None
        
        print("✅ All information collected. Moving to troubleshooting...")

        model_name = user_info[user_id]["model_name"]
        serial_number = user_info[user_id]["serial_number"]
        print(f"MOVING TO TROUBLESHOOT for model {model_name} and serial number {serial_number}")

        user_threads[user_id]["phase"] = "troubleshoot"
        assistant = assistants["troubleshoot"]

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            additional_instructions=f"The user's machine model is {model_name} and serial number is {serial_number}"
        )

        # Poll again for troubleshoot phase
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            if run_status.status == "requires_action":
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                outputs = handle_tool_calls(tool_calls, user_id)

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=outputs
                )
            elif run_status.status == "completed":
                break

            time.sleep(1)

    try:
        db_message = ConversationMessage(
            thread_id=custom_thread_id[user_id],
            ticket_id=tickets_info[user_id].get("ticket_id") if user_id in tickets_info else None,
            sender="assistant",
            message=response,
            media_url=image_url,
            timestamp=datetime.now(timezone.utc)  # Provide timestamp here
        )
        add_conversation(db_message)
    except Exception as e:
        logger.debug(f"Error saving assistant message: {str(e)}")

    # FOR NOW: NONE
    return response, image_url