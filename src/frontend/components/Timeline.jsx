import React from "react";
import { FaVirus, FaHospital, FaGlobe, FaSyringe } from "react-icons/fa";
import "../styling/Timeline.css";

const events = [
  {
    date: "December 2019",
    title: "First Cases Reported",
    description: "First cases of COVID-19 reported in Wuhan, China.",
    icon: <FaVirus />,
  },
  {
    date: "March 2020",
    title: "Global Pandemic Declared",
    description: "WHO declares COVID-19 a global pandemic.",
    icon: <FaGlobe />,
  },
  {
    date: "December 2020",
    title: "Vaccine Rollout Begins",
    description: "First COVID-19 vaccines authorized for emergency use.",
    icon: <FaSyringe />,
  },
  {
    date: "2021–2022",
    title: "Variants and Waves",
    description: "Multiple waves and variants impact global response.",
    icon: <FaHospital />,
  },
];

const Timeline = () => {
  return (
    <section id="timeline" className="timeline-section">
      <h2>🕒 COVID-19 Timeline</h2>
      <div className="timeline">
        {events.map((event, index) => (
          <div
            key={index}
            className={`timeline-item ${index % 2 === 0 ? "left" : "right"}`}
          >
            <div className="timeline-icon">{event.icon}</div>
            <div className="timeline-box">
              <h3>{event.title}</h3>
              <p className="date">{event.date}</p>
              <p>{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Timeline;
