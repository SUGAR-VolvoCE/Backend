import openai
import time
import json
import os
from dotenv import load_dotenv
from app.tools.rag_tool import search_manuals
from app.tools.info_tool import match_model, match_serial_number

load_dotenv(override=True)  # Explicitly reload the .env file

# Strip extra characters from environment variables
assistant_ids = {
    "info": os.getenv("INFO_ASSISTANT_ID", "").strip(),
    "troubleshoot": os.getenv("TROUBLESHOOT_ASSISTANT_ID", "").strip(),
    "solve": os.getenv("SOLVE_ASSISTANT_ID", "").strip(),
}

print("DEBUG: Stripped SOLVE_ASSISTANT_ID:", assistant_ids["solve"])
print("DEBUG: All Environment Variables:", dict(os.environ))

client = openai.OpenAI()

assistants = {
    phase: client.beta.assistants.retrieve(assistant_id=assistant_id)
    for phase, assistant_id in assistant_ids.items()
    if assistant_id
}

user_threads = {}
user_info = {}

tool_function_map = {
    "match_model": match_model,
    "match_serial_number": match_serial_number,
    "search_manuals": search_manuals,
}

def handle_tool_calls(tool_calls, user_id):
    outputs = []
    extra_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"DEBUG: Processing tool call for {tool_name} with arguments: {arguments}")  # Debug statement

        if tool_name in tool_function_map:
            try:
                if tool_name == "search_manuals" and "machine_name" not in arguments:
                    print("USING RAG")
                    arguments["machine_name"] = user_info[user_id]["model_name"]

                if tool_name == "search_manuals":
                    query = arguments.get("query", "default query")
                    machine_name = arguments.get("machine_name", "DEFAULT")
                    result = tool_function_map[tool_name](query=query, machine_name=machine_name)

                    documents = result.get("documents", [])
                    if documents:
                        print("DOCUMENTSSSS")
                        docs_text = "\n\n".join(documents)
                        extra_messages.append(f"The knowledge base returned the following documents:\n\n{docs_text}\n\nPlease use this information to answer my question.")

                else:
                    result = tool_function_map[tool_name](**arguments)

                print(f"DEBUG: Tool {tool_name} result: {result}")  # Debug statement

                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })

                if tool_name == "match_model" and isinstance(result, dict) and result.get("model_name"):
                    user_info[user_id]["model_name"] = result["model_name"]
                    print(f"DEBUG: Updated model_name for user {user_id}: {user_info[user_id]['model_name']}")  # Debug statement

                if tool_name == "match_serial_number" and isinstance(result, dict) and result.get("serial_number"):
                    user_info[user_id]["serial_number"] = result["serial_number"]
                    print(f"DEBUG: Updated serial_number for user {user_id}: {user_info[user_id]['serial_number']}")  # Debug statement

            except Exception as e:
                print(f"DEBUG: Error while calling tool {tool_name}: {e}")  # Debug statement
                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Error while calling {tool_name}: {str(e)}"
                })
        else:
            print(f"DEBUG: Unknown tool {tool_name}")  # Debug statement
            outputs.append({
                "tool_call_id": tool_call.id,
                "output": f"Unknown tool {tool_name}"
            })

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
        content="Would you like to troubleshoot an issue with the device? Please reply 'yes' or 'no'."
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
            outputs, extra_messages = handle_tool_calls(tool_calls, user_id)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )

        elif run_status.status == "completed":
            break

        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    print("DEBUG: Messages from thread:", messages)  # Debug statement

    # Extract the response
    if messages.data and messages.data[0].content:
        response = messages.data[0].content[0].text.value
    else:
        response = "No response from assistant."  # Fallback message

    print("DEBUG: Assistant response:", response)  # Debug statement

    print("DEBUG: model_name =", user_info[user_id]["model_name"])
    print("DEBUG: serial_number =", user_info[user_id]["serial_number"])

    if current_phase == "info" and user_info[user_id]["model_name"] and user_info[user_id]["serial_number"]:
        print("✅ All information collected. Moving to troubleshooting...")
        ask_troubleshoot_intent(user_id)
        time.sleep(5)

        user_threads[user_id]["phase"] = "troubleshoot"
        model_name = user_info[user_id]["model_name"]
        serial_number = user_info[user_id]["serial_number"]
        print(f"MOVING TO TROUBLESHOOT for model {model_name} and serial number {serial_number}")

        assistant = assistants["troubleshoot"]
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

        time.sleep(1)

    for msg in extra_messages_to_send:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=msg
        )

    return response
