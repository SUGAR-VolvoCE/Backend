import openai
from app.config import settings
from app.tools.rag_tool import rag_tool

client = openai.OpenAI()

def create_all_assistants():
    assistants = {}

    assistants["info"] = client.beta.assistants.create(
        name="Info Assistant",
        instructions="Collect machine serial number, model, etc.",
        model="gpt-4"
    )
    assistants["troubleshoot"] = client.beta.assistants.create(
        name="Troubleshooting Assistant",
        instructions="Find the problem using context and user input.",
        model="gpt-4",
        tools=[rag_tool]
    )
    assistants["solve"] = client.beta.assistants.create(
        name="Solution Assistant",
        instructions="Provide detailed instructions to fix the identified issue.",
        model="gpt-4",
        tools=[rag_tool]
    )
    return assistants
