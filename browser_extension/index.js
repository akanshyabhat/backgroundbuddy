import express from "express";
import neo4j from "neo4j-driver";
import cors from "cors";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

const app = express();
app.use(cors()); // Allow requests from browser extension
app.use(express.json());

// Connect to Neo4j using environment variables
const neo4j_uri = process.env.NEO4J_URI || "bolt://localhost:7687";
const neo4j_user =
  process.env.NEO4J_USERNAME || process.env.NEO4J_USER || "neo4j";
const neo4j_password = process.env.NEO4J_PASSWORD || "password";

console.log(`Connecting to Neo4j at ${neo4j_uri} with user ${neo4j_user}`);

const driver = neo4j.driver(
  neo4j_uri,
  neo4j.auth.basic(neo4j_user, neo4j_password)
);

// Function to query Neo4j
async function getGraphData() {
  const session = driver.session();
  try {
    console.log("Querying Neo4j database...");

    // This query matches the structure of your Neo4j database
    // where you have Entity nodes connected by relationships
    const result = await session.run(`
      MATCH (source:Entity)-[r]->(target:Entity)
      RETURN source.name AS source, type(r) AS relationship, 
             target.name AS target, r.evidence AS evidence, 
             r.article_id AS articleID
      LIMIT 100
    `);

    console.log(`Found ${result.records.length} relationships`);

    // Transform the data into the format expected by the extension
    const graphData = {};

    result.records.forEach((record) => {
      const source = record.get("source");
      const relationship = record.get("relationship");
      const target = record.get("target");
      const evidence = record.get("evidence") || "No evidence provided";
      const articleID = record.get("articleID") || "Unknown";

      // Initialize the source entity if it doesn't exist
      if (!graphData[source]) {
        graphData[source] = [];
      }

      // Add this relationship to the source entity
      graphData[source].push({
        relationship,
        target,
        evidence,
        articleID,
      });
    });

    console.log("Graph data processed successfully");
    return graphData;
  } catch (error) {
    console.error("Neo4j Query Error:", error);
    return {};
  } finally {
    await session.close();
  }
}

// API Endpoint
app.get("/api/graph", async (req, res) => {
  try {
    const graphData = await getGraphData();
    console.log(
      `Returning graph data with ${Object.keys(graphData).length} entities`
    );
    res.json(graphData);
  } catch (error) {
    console.error("Error serving graph data:", error);
    res.status(500).json({ error: "Failed to retrieve graph data" });
  }
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Start the server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));

// Handle graceful shutdown
process.on("SIGINT", async () => {
  console.log("Closing Neo4j driver...");
  await driver.close();
  process.exit(0);
});
