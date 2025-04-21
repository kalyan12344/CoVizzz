import React from "react";
import { FaChartLine, FaSearch } from "react-icons/fa";
import "../styling/Hero.css";

const Hero = () => {
  const openPBI = () => {
    window.open(
      "https://app.powerbi.com/groups/me/reports/1836ebe1-8cb4-49f3-b2cc-c6082e76a0a3/a8e97e43a01e080990da?experience=power-bi",
      "_blank"
    );
  };
  return (
    <section className="hero">
      <div className="hero-content">
        <h1>Understanding COVID-19 Through Data</h1>
        <p>
          Explore the pandemic's impact through interactive visualizations and
          AI-powered insights
        </p>
        <div className="hero-buttons">
          <button className="primary-btn" onClick={openPBI}>
            <FaChartLine /> Explore Data
          </button>
          <button className="secondary-btn">
            <FaSearch /> Ask Questions
          </button>
        </div>
      </div>
    </section>
  );
};

export default Hero;
