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
            "You help verify construction equipment details. "
            "Your messages must be short and clear. "
            "Ask only ONE question at a time. "
            "First, ask for the machine model. "
            "Use the 'match_model' tool to check it. "
            "Wait for validation before proceeding. "
            "Then, ask for the serial number. "
            "Validate it with the 'match_serial_number' tool. "
            "Do NOT proceed until both are valid. "
            "Always confirm each step before continuing."
        ),
        model="gpt-4.1-mini",
        tools=[match_model_tool, match_serial_number_tool],
    )
    assistant_ids["INFO_ASSISTANT_ID"] = info.id
    print(f"Info Assistant created: {info.id}")

    # Troubleshoot Assistant
    troubleshoot = client.beta.assistants.create(
        name="Troubleshooting Assistant",
        instructions=(
            "You troubleshoot construction equipment. "
            "Your messages must be short and clear. "
            "Ask only ONE question at a time. "
            "Start by asking about the user's machine problem. "
            "For each question, always call 'search_manuals' first. "
            "Reply ONLY using info from 'search_manuals'. "
            "Messages must be short and clear. "
            "Do NOT invent answers. "
            "If you need to ask more questions, do ONE at a time, one per message. "
            "If no document is found, say so clearly. "
            "If the user gives an error code (like 'E1234'), use ONLY that code to search. "
            "Provide steps one at a time. "
            "Wait for user confirmation before giving the next step."
        ),
        model="gpt-4.1-mini",
        tools=[rag_tool]
    )
    assistant_ids["TROUBLESHOOT_ASSISTANT_ID"] = troubleshoot.id
    print(f"Troubleshoot Assistant created: {troubleshoot.id}")

    # Solution Assistant
    solve = client.beta.assistants.create(
        name="Solution Assistant",
        instructions=(
            "You give repair and maintenance steps. "
            "Base answers on the problem identified by Troubleshooting Assistant. "
            "Use 'rag_tool' for manuals if needed. "
            "Messages must be short and clear. "
            "Give steps one at a time. "
            "Ask user to confirm before moving to the next step. "
            "Prioritize safety and clarity. "
            "NEVER list all steps at once. "
            "Ask only ONE question per message."
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
