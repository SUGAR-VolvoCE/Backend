import openai
from ..app.tools.rag_tool import rag_tool

client = openai.OpenAI()

def create_assistants():
    # Info Assistant
    info = client.beta.assistants.create(
        name="Info Assistant",
        instructions=(
            "You are a helpful assistant for verifying construction equipment details. "
            "Ask the customer for the machine model and serial number. "
            "Use the 'match_model' function to validate the model. "
            "Then, use the 'match_serial_number' function to validate the serial number. "
            "Make sure to confirm both before proceeding."
        ),
        model="gpt-4.1-mini",
        tools=[]  # tools must be correctly registered with OpenAI
    )
    print(f"Info Assistant ID: {info.id}")

    # Troubleshoot Assistant
    troubleshoot = client.beta.assistants.create(
        name="Troubleshooting Assistant",
        instructions=(
            "You help users identify what might be wrong with their construction equipment. "
            "Ask clear diagnostic questions based on the provided context and machine model. "
            "Use the knowledge base via 'rag_tool' to reference manuals and past troubleshooting data."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool]
    )
    print(f"Troubleshoot Assistant ID: {troubleshoot.id}")

    # Solution Assistant
    solve = client.beta.assistants.create(
        name="Solution Assistant",
        instructions=(
            "You give step-by-step repair or maintenance instructions for known issues. "
            "Base your solutions on the issue identified by the Troubleshooting Assistant. "
            "Be clear, technical, and safety-conscious. Use 'rag_tool' for reference if needed."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool]
    )
    print(f"Solve Assistant ID: {solve.id}")

if __name__ == "__main__":
    create_assistants()
