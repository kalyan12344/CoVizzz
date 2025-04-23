import React from "react";
import {
  FaUsers,
  FaGlobeAmericas,
  FaChartBar,
  FaHeartbeat,
} from "react-icons/fa";
import "../styling/Impact.css";

const Impact = () => {
  const impacts = [
    {
      icon: <FaUsers />,
      title: "Global Cases",
      value: "700M+",
      description: "Total confirmed cases worldwide",
    },
    {
      icon: <FaHeartbeat />,
      title: "Global Deaths",
      value: "6.9M+",
      description: "Total confirmed deaths worldwide",
    },
    {
      icon: <FaGlobeAmericas />,
      title: "Countries Affected",
      value: "200+",
      description: "Number of countries impacted",
    },
    {
      icon: <FaChartBar />,
      title: "Economic Impact",
      value: "$12T+",
      description: "Estimated global economic impact",
    },
  ];

  return (
    <section id="impact" className="impact-section">
      <h2>Global Impact</h2>
      <div className="impact-grid">
        {impacts.map((impact, index) => (
          <div key={index} className="impact-card">
            <div className="impact-icon">{impact.icon}</div>
            <h3>{impact.title}</h3>
            <div className="impact-value">{impact.value}</div>
            <p>{impact.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Impact;
