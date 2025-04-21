import { useState } from "react";

import "./App.css";
import Chatbot from "./components/Chatbot";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Timeline from "./components/Timeline";
import Impact from "./components/Impact";
import Footer from "./components/Footer";
import DataInsights from "./components/DataInsights";
import { FaRobot, FaTimes } from "react-icons/fa";

function App() {
  const [showChatbot, setShowChatbot] = useState(false);

  return (
    <>
      <Navbar />
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
            <Chatbot />
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
