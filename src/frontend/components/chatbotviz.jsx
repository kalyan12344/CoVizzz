import React, { useState, useRef, useEffect } from "react";
import { FaRobot, FaUser } from "react-icons/fa";
import axios from "axios";
import TableauEmbed from "./tableauembed";
import "../styling/chatbotviz.css";

const ChatbotViz = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(
        "http://localhost:5002/get_visualization",
        { query: input },
        { headers: { "Content-Type": "application/json" } }
      );

      console.log("🎯 Backend Response:", response.data);

      const botMessage = {
        text: response.data.text,
        viz_url: response.data.viz_url, // Ensure backend sends correct field
        title: response.data.title,
        description: response.data.description,
        sender: "bot",
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("❌ Error fetching visualization:", error);
      setMessages((prev) => [
        ...prev,
        { text: "⚠️ Error fetching visualization.", sender: "bot" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbotviz-container">
      <h1 className="chatbotviz-header">📊 COVID-19 Viz Assistant</h1>

      <div className="chatbotviz-messages">
        {messages.map((message, index) => {
          console.log("📝 Rendering message:", message);
          return (
            <div key={index} className={`message-bubble ${message.sender}`}>
              <div className="message-header">
                {message.sender === "user" ? (
                  <FaUser className="message-icon" />
                ) : (
                  <FaRobot className="message-icon" />
                )}
                <span>
                  {message.sender === "user" ? "You" : "Viz Assistant"}
                </span>
              </div>

              <p>{message.text}</p>

              {message.viz_url && (
                <div className="viz-section">
                  <h3>{message.title}</h3>
                  <p>{message.description}</p>
                  <TableauEmbed vizUrl={message.viz_url} />
                </div>
              )}
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {loading && (
        <p className="loading-indicator">🌀 Fetching visualization...</p>
      )}

      <form onSubmit={handleSubmit} className="chatbotviz-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for a COVID-19 visualization..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatbotViz;
