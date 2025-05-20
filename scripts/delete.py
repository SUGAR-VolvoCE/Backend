import openai

client = openai.OpenAI()

# List all assistants
assistants = client.beta.assistants.list()

# Delete each assistant
for assistant in assistants.data:
    print(f"Deleting Assistant: {assistant.id} - {assistant.name}")
    client.beta.assistants.delete(assistant.id)
