import React, { useState, useRef, useEffect } from "react";
import { FaRobot, FaUser } from "react-icons/fa";
import Plot from "react-plotly.js";
import axios from "axios";
import "../styling/Chatbot.css";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [dataset, setDataset] = useState("global_deaths");
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
        "http://localhost:5000/query",
        {
          query: input,
          dataset: dataset,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );



      const botMessage = {
        text:
          response.data.error ||
          response.data.text ||
          "Here is the data you requested:",
        visualization: response.data.visualization,
        sender: "bot",
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          text: "Sorry, I encountered an error. Please try again.",
          sender: "bot",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <h1 className="chatbot-title">COVID-19 Data Assistant</h1>
      </div>

      <div className="chat-options">
        <label htmlFor="dataset" className="dataset-label">
          Select Dataset:
        </label>
        <select
          id="dataset"
          className="dataset-select"
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
        >
          <option value="global_deaths">🌍 Global Deaths</option>
          <option value="global_cases">🌍 Global Cases</option>
          <option value="us_deaths">🇺🇸 US Deaths</option>
          <option value="us_cases">🇺🇸 US Cases</option>
        </select>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message-container ${message.sender}`}>
            <div className={`message-bubble ${message.sender}`}>
              <div className="message-header">
                {message.sender === "user" ? (
                  <FaUser className="message-icon user" />
                ) : (
                  <FaRobot className="message-icon bot" />
                )}
                <span className={`message-sender ${message.sender}`}>
                  {message.sender === "user" ? "You" : "COVID-19 Assistant"}
                </span>
              </div>

              <p className="message-text">{message.text}</p>

              {message.visualization &&
              message.visualization.data?.length > 0 ? (
                <div className="visualization-container">
                  <Plot
                    data={message.visualization.data}
                    layout={{
                      ...message.visualization.layout,
                      paper_bgcolor: "rgba(0,0,0,0)",
                      plot_bgcolor: "rgba(0,0,0,0)",
                      font: { color: "#fff" },
                      xaxis: { gridcolor: "rgba(255,255,255,0.1)" },
                      yaxis: { gridcolor: "rgba(255,255,255,0.1)" },
                    }}
                    config={{ responsive: true }}
                    className="w-full"
                  />
                </div>
              ) : message.visualization ? (
                <p className="error-text">⚠️ No data available to display.</p>
              ) : null}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {loading && <p className="loading-indicator">🌀 Thinking...</p>}

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about COVID-19 data..."
            className="chat-input"
          />
          <button type="submit" className="send-button">
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chatbot;
