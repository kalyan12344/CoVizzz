import React from "react";
import { FaGithub, FaLinkedin, FaTwitter } from "react-icons/fa";
import "../styling/Footer.css";

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>Chronicles of COVID</h3>
          <p>
            A data visualization and analysis platform for COVID-19 insights
          </p>
        </div>
        <div className="footer-section">
          <h3>Quick Links</h3>
          <ul>
            <li>
              <a href="#timeline">Timeline</a>
            </li>
            <li>
              <a href="#impact">Impact</a>
            </li>
            <li>
              <a href="#data">Data Insights</a>
            </li>
            <li>
              <a href="#chatbot">Chatbot</a>
            </li>
          </ul>
        </div>
        <div className="footer-section">
          <h3>Connect</h3>
          <div className="social-links">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaGithub />
            </a>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaLinkedin />
            </a>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaTwitter />
            </a>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <p>
          &copy; {new Date().getFullYear()} Chronicles of COVID. All rights
          reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
