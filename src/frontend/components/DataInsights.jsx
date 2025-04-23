import React from "react";
import "../styling/datainsights.css";

const DataInsights = () => {
  // Hardcoded Power BI Embed URL (Make sure it's a public 'Publish to Web' link)
  const embedUrl = "https://app.powerbi.com/view?r=eyJrIjoiOWFmMmRiMGYtNTIyZC00OTk5LThmNDItNTg0MDNiMzVkNWEzIiwidCI6IjcwZGUxOTkyLTA3YzYtNDgwZi1hMzE4LWExYWZjYmEwMzk4MyIsImMiOjN9";

  return (
    <section id="data" className="data-section">
      <h2>Data Insights</h2>
      <div className="visualization-container">
        <iframe
          title="Power BI Report"
          width="100%"
          height="600px"
          src={embedUrl}
          frameBorder="0"
          allowFullScreen={true}
        ></iframe>
      </div>
    </section>
  );
};

export default DataInsights;
