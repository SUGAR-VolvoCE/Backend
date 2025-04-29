# Doc

# 💬 Assistant Backend

This project implements a backend using OpenAI Assistants to guide users through a multi-phase conversation flow (`info → troubleshoot → solve`). It handles user interactions, remembers context using threads, and manages tool calls (e.g., for matching model numbers or searching manuals).

---

## 📦 Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.com:SUGAR-VolvoCE/Backend.git
cd Backend
```

### 2. Create Virtual Environment and Install Dependencies

```
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file in the root directory with your OpenAI credentials and assistant IDs:

```
OPENAI_API_KEY=sk-...
INFO_ASSISTANT_ID=asst_...
TROUBLESHOOT_ASSISTANT_ID=asst_...
SOLVE_ASSISTANT_ID=asst_..
```

## 🚀 Run the Backend

Start the FastAPI application using [uvicorn](https://www.uvicorn.org/):

```
uvicorn app.main:app --reload
```

This launches the server at:

```
http://127.0.0.1:8000
```

## 🧪 Test the Conversation Flow

You can test the backend using `curl`.

### Step 1: Start a New Session

Use reset = True, if it is a new chat.

```jsx
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hey, ....",
    "reset": true
  }'
```

### Step 2: Provide Model Information

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "My model is the EC160E",
    "reset": false
  }'
```

### Step 3: Provide Serial Number

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "My serial number is SN12345678",
    "reset": false
  }'
```

Once both model and serial number are collected, the backend automatically transitions to the **troubleshooting** phase.

### Step 4: Troubleshooting

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "It is making a strange noise",
    "reset": false
  }'
```

For now, it is not correctly using RAG Tools. PDFs from machines should be better organized too.
