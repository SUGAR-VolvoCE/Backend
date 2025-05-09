import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Chat from "./components/Chat";
import FileUpload from "./components/FileUpload";

function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Assistant Interface</h1>
      <nav>
        <Link to="/" style={{ marginRight: "10px" }}>Chat</Link>
        <Link to="/upload">Upload Files</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/upload" element={<FileUpload />} />
      </Routes>
    </div>
  );
}

export default App;
