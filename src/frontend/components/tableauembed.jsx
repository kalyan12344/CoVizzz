import React from "react";

const TableauEmbed = ({ vizUrl }) => {
  const embedUrl = `${vizUrl}&:showVizHome=no&:embed=true`;

  return (
    <div style={{ marginTop: "10px" }}>
      <iframe
        src={embedUrl}
        width="100%"
        height="600"
        frameBorder="0"
        allowFullScreen
        title="Tableau Visualization"
        style={{ border: "1px solid #444", borderRadius: "8px" }}
      ></iframe>
    </div>
  );
};

export default TableauEmbed;
