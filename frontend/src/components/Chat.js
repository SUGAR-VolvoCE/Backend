import React, { useState } from "react";
import axios from "axios";

function Chat() {
  const [userMessage, setUserMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!userMessage.trim()) return;

    const newChat = [...chatHistory, { sender: "user", message: userMessage }];
    setChatHistory(newChat);
    setUserMessage("");
    setLoading(true);

    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        user_id: "user123",
        message: userMessage,
        reset: chatHistory.length === 0,
      });

      setChatHistory([
        ...newChat,
        { sender: "assistant", message: response.data.reply },
      ]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div
        style={{
          border: "1px solid #ccc",
          padding: "10px",
          height: "400px",
          overflowY: "scroll",
          marginBottom: "10px",
        }}
      >
        {chatHistory.map((chat, index) => (
          <div
            key={index}
            style={{
              textAlign: chat.sender === "user" ? "right" : "left",
              margin: "5px 0",
            }}
          >
            <strong>{chat.sender === "user" ? "You" : "Assistant"}:</strong>{" "}
            {chat.message}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={userMessage}
        onChange={(e) => setUserMessage(e.target.value)}
        placeholder="Type your message..."
        style={{ width: "80%", padding: "10px" }}
      />
      <button onClick={sendMessage} disabled={loading} style={{ padding: "10px" }}>
        {loading ? "Sending..." : "Send"}
      </button>
    </div>
  );
}

export default Chat;
