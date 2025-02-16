import React, { useState, useEffect, useRef } from "react";
import { ForceGraph2D } from "react-force-graph";

const fakeGraph = {
  "Jacob Frey": [
    { relationship: "PARTICIPATING_IN", target: "Minneapolis Mayoral Election 2025" },
    { relationship: "LIVES_IN", target: "Minneapolis" },
  ],
  Minneapolis: [
    { relationship: "IS_A_CITY_IN", target: "Minnesota" },
    { relationship: "FAMOUS_FOR", target: "St Anthony Falls" },
  ],
  "Omar Fateh": [
    { relationship: "LIVES_IN", target: "Minneapolis" },
    { relationship: "PARTICIPATING_IN", target: "Minneapolis Mayoral Election 2025" },
    { relationship: "CHALLENGING", target: "Jacob Frey" },
    { relationship: "MEMBER_OF", target: "Senate" },
  ],
};

function getRandomColor() {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

// Transform fakeGraph into ForceGraph2D format
const transformGraphData = (graph, entity) => {
  if (!entity || !graph[entity]) return { nodes: [], links: [] };

  const nodes = [{ id: entity, name: entity, color: getRandomColor()}];
  const links = graph[entity].map((connection) => ({
    source: entity,
    target: connection.target,
    relationship: connection.relationship,
  }));

  // Add unique target nodes
  graph[entity].forEach((connection) => {
    if (!nodes.find((node) => node.id === connection.target)) {
      nodes.push({ id: connection.target, name: connection.target, color: getRandomColor() });
    }
  });

  return { nodes, links };
};

function App() {
  const [userText, setUserText] = useState("");
  const [entities, setEntities] = useState([]);
  const [hoveredEntity, setHoveredEntity] = useState(null);
  const [clickedEntity, setClickedEntity] = useState(null);
  const [showGraphModal, setShowGraphModal] = useState(false);
  const graphRef = useRef(null);

  // Extract entities from text
  useEffect(() => {
    const results = [];
    Object.keys(fakeGraph).forEach((entity) => {
      const index = userText.indexOf(entity);
      if (index !== -1) {
        results.push({ text: entity, start: index, end: index + entity.length });
      }
    });
    results.sort((a, b) => a.start - b.start);
    setEntities(results);
  }, [userText]);
  

  const segments = [];
  let lastIndex = 0;

  entities.forEach((ent) => {
    if (ent.start > lastIndex) {
      segments.push({ text: userText.slice(lastIndex, ent.start), isEntity: false });
    }
    segments.push({ text: userText.slice(ent.start, ent.end), isEntity: true });
    lastIndex = ent.end;
  });
  if (lastIndex < userText.length) {
    segments.push({ text: userText.slice(lastIndex), isEntity: false });
  }

  const graphData = clickedEntity ? transformGraphData(fakeGraph, clickedEntity) : { nodes: [], links: [] };

  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force("link").distance(70); // Link distance
      graphRef.current.d3Force("charge").strength(-20); // Node repulsion
      graphRef.current.d3ReheatSimulation(); // Restart the simulation
    }
  }, [clickedEntity]);

  return (
    <div className="w-screen h-screen bg-gray-900 text-white p-6 flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Knowledge Graph Demo</h1>

      {/* Text Entry and Highlights */}
      <div className="flex-1 overflow-auto mb-4">
        <textarea
          className="w-full p-2 mb-4 rounded bg-gray-800 text-white focus:outline-none h-32"
          value={userText}
          onChange={(e) => setUserText(e.target.value)}
          placeholder="Type something here."
        />
        <div className="bg-gray-800 p-2 rounded min-h-[100px] relative">
          {segments.map((seg, idx) => {
            if (!seg.isEntity) {
              return <span key={idx}>{seg.text}</span>;
            }
            return (
              <span
                key={idx}
                className="bg-yellow-400 text-gray-900 px-1 rounded cursor-pointer relative"
                onMouseEnter={() => setHoveredEntity(seg.text)}
                onMouseLeave={() => setHoveredEntity(null)}
                onClick={() => {
                  setClickedEntity(seg.text);
                  setShowGraphModal(true);
                }}
              >
                {seg.text}
                {/* Tooltip */}
                {hoveredEntity === seg.text && (
                  <div
                    className="absolute top-full left-0 mt-1 w-64 bg-gray-800 text-white p-2 rounded shadow-lg z-10"
                    style={{ pointerEvents: "none" }}
                  >
                    <div className="font-bold mb-1">{seg.text}</div>
                    {fakeGraph[seg.text]?.length > 0 ? (
                      <ul className="text-sm">
                        {fakeGraph[seg.text].map((conn, idx) => (
                          <li key={idx}>
                            <span className="text-green-400">{conn.relationship}</span> →{" "}
                            <span className="text-blue-300">{conn.target}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm text-gray-400">No connections found.</div>
                    )}
                  </div>
                )}
              </span>
            );
          })}
        </div>
      </div>

      {/* Graph Modal */}
      {showGraphModal && (
        <div
          className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
          onClick={() => setShowGraphModal(false)}
        >
          <div
            className="relative bg-gray-800 p-6 rounded shadow-lg w-3/4 h-3/4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded"
              onClick={() => setShowGraphModal(false)}
            >
              Close
            </button>
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              linkDirectionalArrowLength={5}
              linkDirectionalArrowRelPos={1}
              nodeCanvasObject={(node, ctx, globalScale) => {
                
                const radius = 6;
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                ctx.fillStyle = node.color;
                ctx.fill();

                const label = node.name || node.id;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.fillStyle = "white";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(label, node.x, node.y - 10); // Position above the node
              }}
              linkCanvasObject={(link, ctx, globalScale) => {
                const label = link.relationship;
                //ctx.fillStyle = "white";
                if (!label) return;

                const midX = (link.source.x + link.target.x) / 2;
                const midY = (link.source.y + link.target.y) / 2;

                const fontSize = 10 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.fillStyle = "white";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(label, midX, midY);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
