import openai
import time
import json
import os
from app.tools.rag_tool import search_manuals
from app.tools.info_tool import match_model, match_serial_number

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

user_threads = {}  # user_id -> { phase -> thread }
user_info = {}     # user_id -> { "model_name": ..., "serial_number": ... }

tool_function_map = {
    "match_model": match_model,
    "match_serial_number": match_serial_number,
    "search_manuals": search_manuals,
}

# Helper function to handle tool calls
def handle_tool_calls(tool_calls, user_id):
    outputs = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if tool_name in tool_function_map:
            try:
                # Call the mapped Python function
                result = tool_function_map[tool_name](**arguments)
                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })

                # Update user info memory based on tool results
                if tool_name == "match_model" and isinstance(result, dict) and result.get("model_name"):
                    user_info[user_id]["model_name"] = result["model_name"]

                if tool_name == "match_serial_number" and isinstance(result, dict) and result.get("serial_number"):
                    user_info[user_id]["serial_number"] = result["serial_number"]

            except Exception as e:
                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Error while calling {tool_name}: {str(e)}"
                })
        else:
            outputs.append({
                "tool_call_id": tool_call.id,
                "output": f"Unknown tool {tool_name}"
            })
    return outputs

# Function to transition to troubleshooting phase
def transition_to_troubleshooting(user_id: str, model_name: str, serial_number: str):
    message = f"Now moving to troubleshooting for model {model_name} with serial number {serial_number}."
    return chat_with_assistant(user_id, "troubleshoot", message)

# Helper function to manage threads and phase
def get_or_create_thread(user_id: str, reset: bool):
    if user_id not in user_threads:
        user_threads[user_id] = {"phase": "info", "threads": {}}
    if reset or "info" not in user_threads[user_id]["threads"]:
        thread = client.beta.threads.create()
        user_threads[user_id]["phase"] = "info"  # Always start from 'info' on reset
        user_threads[user_id]["threads"]["info"] = thread
    return user_threads[user_id]["threads"][user_threads[user_id]["phase"]]

# Main function to interact with assistants
def chat_with_assistant(user_id: str, message: str, reset: bool = False):
    if reset or user_id not in user_threads:
        user_threads[user_id] = {"phase": "info", "threads": {}}
        user_info[user_id] = {"model_name": None, "serial_number": None}

    current_phase = user_threads[user_id]["phase"]

    if current_phase not in assistants:
        print(f"Warning: phase '{current_phase}' not found. Falling back to 'info'.")
        current_phase = "info"
        user_threads[user_id]["phase"] = "info"

    assistant = assistants[current_phase]
    thread = get_or_create_thread(user_id, reset)

    if reset:
        # Tell assistant to forget prior context
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Forget previous conversations. Start fresh."
        )

    # Step 1: Send user message to assistant
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    # Step 2: Create a run to interact with assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Step 3: Poll for run status and handle tool calls if needed
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            outputs = handle_tool_calls(tool_calls, user_id)

            # Submit tool outputs to assistant
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )

        elif run_status.status == "completed":
            break

        time.sleep(1)

    # Step 4: Read final assistant reply
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value

    # Step 5: Check if we have collected all required info to move on
    if current_phase == "info" and user_info[user_id]["model_name"] and user_info[user_id]["serial_number"]:
        print("✅ All information collected. Moving to troubleshooting...")
        model_name = user_info[user_id]["model_name"]
        serial_number = user_info[user_id]["serial_number"]

        # Move phase to troubleshooting
        user_threads[user_id]["phase"] = "troubleshoot"

        # Start a new thread for troubleshooting
        thread = client.beta.threads.create()
        user_threads[user_id]["threads"]["troubleshoot"] = thread

        # Send the transition message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Now moving to troubleshooting for model {model_name} with serial number {serial_number}."
        )

        # Start troubleshooting assistant
        assistant = assistants["troubleshoot"]
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value

    return response
