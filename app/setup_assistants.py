import openai
from app.tools.rag_tool import rag_tool
from app.tools.info_tool import match_model_tool, match_serial_number_tool

client = openai.OpenAI()

def create_assistants():
    assistant_ids = {}

    # Info Assistant
    info = client.beta.assistants.create(
        name="Info Assistant",
        instructions=(
            "You are a helpful assistant for verifying construction equipment details.\n"
            "- Ask the customer for the machine model first.\n"
            "- Use the 'match_model' tool to validate the model name.\n"
            "- After the model is confirmed, ask for the serial number.\n"
            "- Use the 'match_serial_number' tool to validate the serial number.\n"
            "Only proceed once both model and serial number are validated."
        ),
        model="gpt-4.1-mini",
        tools=[match_model_tool, match_serial_number_tool],
    )
    assistant_ids["INFO_ASSISTANT_ID"] = info.id
    print(f"Info Assistant created: {info.id}")

    # Troubleshooting Assistant
    troubleshoot = client.beta.assistants.create(
        name="Troubleshooting Assistant",
        instructions=(
            "You help users diagnose potential issues with their construction equipment.\n"
            "- Ask clear and detailed diagnostic questions based on the machine model.\n"
            "- Use the 'rag_tool' knowledge base to find related issues and solutions.\n"
            "- Be logical and methodical in narrowing down problems."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool],
    )
    assistant_ids["TROUBLESHOOT_ASSISTANT_ID"] = troubleshoot.id
    print(f"Troubleshoot Assistant created: {troubleshoot.id}")

    # Solution Assistant
    solve = client.beta.assistants.create(
        name="Solution Assistant",
        instructions=(
            "You provide detailed repair and maintenance steps for known issues.\n"
            "- Base your answers on the problem identified by the Troubleshooting Assistant.\n"
            "- Use the 'rag_tool' knowledge base when needed for manuals and guides.\n"
            "- Prioritize safety and clarity in your instructions."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool],
    )
    assistant_ids["SOLVE_ASSISTANT_ID"] = solve.id
    print(f"Solve Assistant created: {solve.id}")

    # Output all assistant IDs nicely
    print("\n✅ Add these lines to your .env file:")
    for key, value in assistant_ids.items():
        print(f"{key}={value}")

if __name__ == "__main__":
    create_assistants()
