import { useState } from "react";

import "./App.css";


import { FaRobot, FaTimes } from "react-icons/fa";
import Navbar from "./frontend/components/Navbar";
import Hero from "./frontend/components/Hero";
import Timeline from "./frontend/components/Timeline";
import Impact from "./frontend/components/Impact";
import DataInsights from "./frontend/components/DataInsights";
import Chatbot from "./frontend/components/Chatbot";
import Footer from "./frontend/components/Footer";
import ChatbotViz from "./frontend/components/chatbotviz";

function App() {
  const [showChatbot, setShowChatbot] = useState(false);

  return (
    <>
      <Navbar/>
      <Hero />
      <Timeline />
      <Impact />
      <DataInsights />

      {showChatbot && (
        <div className="chatbot-overlay">
          <div className="chatbot-wrapper">
            <button
              className="close-chatbot"
              onClick={() => setShowChatbot(false)}
            >
              <FaTimes />
            </button>
            <ChatbotViz />
          </div>
        </div>
      )}

      <button className="chatbot-icon" onClick={() => setShowChatbot(true)}>
        <FaRobot />
      </button>

      <Footer />
    </>
  );
}

export default App;
