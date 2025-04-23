import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FaRobot, FaUser, FaTimes } from "react-icons/fa";
import "../styling/Chatbot.css";
import "../styling/summarybot.css"; // Create this CSS file

const SummaryBotOverlay = ({ onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [dataset, setDataset] = useState("global_deaths");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages((prev) => [...prev, { text: input, sender: "user" }]);
    setInput("");

    try {
      const response = await axios.post(
        "http://localhost:5000/summary",
        // "https://covizzz-backend.onrender.com/summary",
        { query: input, dataset },
        { headers: { "Content-Type": "application/json" } }
      );

      const summary = response.data.summary || "No summary found.";
      setMessages((prev) => [...prev, { text: summary, sender: "bot" }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { text: "Error getting summary.", sender: "bot" },
      ]);
    }
  };

  return (
    <div className="overlay-backdrop">
      <div className="overlay-panel">
        <button className="overlay-close" onClick={onClose}>
          <FaTimes />
        </button>
        <h2>🧠 Ask COVID-19 Questions</h2>

        <div className="chat-options">
          <select
            value={dataset}
            onChange={(e) => setDataset(e.target.value)}
            className="dataset-select"
          >
            <option value="global_deaths">🌍 Global Deaths</option>
            <option value="global_cases">🌍 Global Cases</option>
            <option value="us_deaths">🇺🇸 US Deaths</option>
            <option value="us_cases">🇺🇸 US Cases</option>
          </select>
        </div>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message-container ${msg.sender}`}>
              <div className={`message-bubble ${msg.sender}`}>
                <div className="message-header">
                  {msg.sender === "user" ? (
                    <FaUser className="message-icon user" />
                  ) : (
                    <FaRobot className="message-icon bot" />
                  )}
                  <span className="message-sender">
                    {msg.sender === "user" ? "You" : "Summary Assistant"}
                  </span>
                </div>
                <p className="message-text">{msg.text}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            className="chat-input"
          />
          <button type="submit" className="send-button">
            Ask
          </button>
        </form>
      </div>
    </div>
  );
};

export default SummaryBotOverlay;
