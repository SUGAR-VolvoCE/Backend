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

    # Troubleshoot Assistant
    # Troubleshoot Assistant
    troubleshoot = client.beta.assistants.create(
        name="Troubleshooting Assistant",
       instructions=(
            "You are a Troubleshooting Assistant for construction equipment.\n"
            "- For each user question, always call the 'search_manuals' function first.\n"
            "- After getting the documents from 'search_manuals', base your entire reply ONLY on the contents retrieved.\n"
            "- DO NOT invent answers. DO NOT answer unless 'search_manuals' returns relevant documents.\n"
            "- Do not include machine model or serial number in the 'search_manuals' query.\n"
            "- If the user's message contains an error code (e.g., 'E1234'), use ONLY the code 'E1234' as the query for 'search_manuals'."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool]  # Enable the 'rag_tool' for retrieving manuals
    )

    print(f"Troubleshoot Assistant ID: {troubleshoot.id}")
    assistant_ids["TROUBLESHOOT_ASSISTANT_ID"] = troubleshoot.id


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
