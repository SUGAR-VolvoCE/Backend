import openai
from app.assistants import create_all_assistants

client = openai.OpenAI()
assistants = create_all_assistants()

threads = {key: client.beta.threads.create() for key in assistants.keys()}

def chat_with_assistant(phase: str, message: str):

    if phase not in assistants:
        print(f"Warning: phase '{phase}' not found. Falling back to 'default'.")
        phase = "default"
    
    if phase not in threads:
        threads[phase] = client.beta.threads.create()

    thread = threads[phase]
    assistant = assistants[phase]

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    import time
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
