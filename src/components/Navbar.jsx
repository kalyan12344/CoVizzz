import React, { useState } from "react";
import { FaBars, FaTimes } from "react-icons/fa";
import "../styling/Navbar.css";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="navbar">
      <div className="logo">
        <h1>Chronicles of COVID</h1>
      </div>
      <div className={`nav-links ${isOpen ? "active" : ""}`}>
        <a href="#timeline">Timeline</a>
        <a href="#impact">Impact</a>
        <a href="#data">Data Insights</a>
        <a href="#chatbot">Chatbot</a>
      </div>
      <div className="menu-icon" onClick={toggleMenu}>
        {isOpen ? <FaTimes /> : <FaBars />}
      </div>
    </nav>
  );
};

export default Navbar;
