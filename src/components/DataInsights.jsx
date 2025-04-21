import React from "react";
import Plot from "react-plotly.js";
import "../styling/datainsights.css";

const DataInsights = ({ visualizationData }) => {
  return (
    <section id="data" className="data-section">
      <h2>Data Insights</h2>
      <div className="visualization-container">
        {visualizationData ? (
          <Plot
            data={visualizationData.data}
            layout={{
              ...visualizationData.layout,
              autosize: true,
              margin: { l: 50, r: 50, t: 50, b: 50 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
            }}
            useResizeHandler={true}
            style={{ width: "100%", height: "100%" }}
          />
        ) : (
          <div className="loading">Loading visualization...</div>
        )}
      </div>
    </section>
  );
};

export default DataInsights;
