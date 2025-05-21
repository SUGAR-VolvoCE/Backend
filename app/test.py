import traceback
from uuid import uuid4
from datetime import datetime, timezone
from routes import add_conversation, ConversationMessage  # adjust import

def test_call_add_conversation():
    test_msg = ConversationMessage(
        thread_id=uuid4(),
        ticket_id=42,
        sender="tester",
        message="Hello from test",
        media_url=None,
        timestamp=datetime.now(timezone.utc)
    )

    try:
        result = add_conversation(test_msg)
        print("Function output:", result)
    except Exception as e:
        print("Error:", e)
        traceback.print_exc()

if __name__ == "__main__":
    test_call_add_conversation()
