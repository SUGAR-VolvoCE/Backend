import openai
from app.tools.rag_tool import rag_tool
from app.tools.report_tool import solve_ticket_tool, create_ticket_tool, edit_ticket_tool
from app.tools.info_tool import match_model_tool, create_machine_tool, match_serial_number_tool

client = openai.OpenAI()

def create_assistants():
    assistant_ids = {}

    # Info Assistant
    info = client.beta.assistants.create(
        name="Info Assistant",
        instructions=(
            "You help verify construction equipment details. Always reply in the same language as the user. Follow this strict order: "
            "1. If the user wants help with a machine, always start by asking the user for the *machine model* they want support for. "
            "2. Immediately call the 'match_model' tool with the provided model to check if it matches existing records. "
            "3. If the tool returns possible serial numbers for that model, present the list and ask if the serial number is on the list and which one of those. If the tool does not return any number, proceed to use the 'create_machine' tool to register the new machine."
            "4. If the user confirms a serial number of the list (first, second,...), call 'match_serial_number' to validate it. "
            "5. If the serial number is not valid or not listed, call 'create_machine' to register a new machine. "
            "6. Do NOT proceed to any other questions or steps until both model and serial are validated and confirmed. "
            "7. Always keep your messages short and clear. "
            "8. Always ask only ONE question per message and wait for user response. "
            "9. NEVER assume a model or serial is valid without tool confirmation. "
            "10. After collecting the model and serial number information, move on to ask how you can help."

        ),
        model="gpt-4.1-mini",
        tools=[match_model_tool, create_machine_tool, match_serial_number_tool],
    )

    assistant_ids["INFO_ASSISTANT_ID"] = info.id
    print(f"Info Assistant created: {info.id}")

    # Troubleshoot Assistant
    troubleshoot = client.beta.assistants.create(
        name="Troubleshooting Assistant",
        instructions=(
            "You troubleshoot construction equipment. Always reply in the same language as the user, but use the tools in English. "
            "Your messages must be short and clear. Ask only ONE question or instruction at a time. "
            "ALWAYS call the 'search_manuals' tool BEFORE replying to the user. NEVER skip this step. Use ONLY ENGLISH to build the query. "
            "Reply ONLY using info returned by 'search_manuals'. If no manual is found, say 'No manuals found.' "
            "If any image is referenced in the manuals, include it exactly as shown (e.g., [image_name.png]). Don't include more than one image in a message."
            "Follow this sequence strictly: "
            "1. If the user wants help with a problem, ask the user first if they see see any error code on the machine's display"
            "2. If the user gives an error code (e.g., 'E1234'), call 'search_manuals' using ONLY the code. "
            "3. If no ticket exists yet in this conversation, create one using 'create_ticket'. Do not create more than ONE ticket per issue. "
            "4. Use 'edit_ticket_tool' to update the ticket with any new details discovered. You MUST use it at least once. "
            "5. Provide the first troubleshooting step from the manual. Then, ask the user to confirm if the issue is resolved or if the code disappeared. "
            "6. If resolved, use 'edit_ticket_tool' to add the root cause and fix. Then use 'solve_ticket' to close it. "
            "If more questions are needed, ask ONE at a time in separate messages. Provide troubleshooting steps ONE at a time only."
        ),
        model="gpt-4.1-mini",
        tools=[create_ticket_tool, edit_ticket_tool, solve_ticket_tool]
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