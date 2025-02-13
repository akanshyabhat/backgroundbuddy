chrome.runtime.onMessage.addListener(async (message, sender) => {
  if (message.type === "searchEntity") {
    console.log("🔍 Searching Neo4j for:", message.entity);

    try {
      const response = await fetch("http://localhost:7474/db/neo4j/tx/commit", {
        method: "POST",
        headers: {
          Authorization: "Basic " + btoa("neo4j:your_password_here"), // FIX THIS
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          statements: [
            {
              statement: `
                MATCH (a {name: $name})-[r]->(b)
                RETURN a.name AS entity, type(r) AS relationship, b.name AS target
                LIMIT 10
              `,
              parameters: { name: message.entity },
            },
          ],
        }),
      });

      const data = await response.json();

      if (data.errors && data.errors.length > 0) {
        console.error("🚨 Neo4j Error:", data.errors);
        return;
      }

      console.log("✅ Neo4j Response:", data);

      // Ensure we are extracting the right fields
      const extractedData = data.results[0].data.map((row) => ({
        entity: row.row[0], // Entity name
        relationship: row.row[1], // Relationship type
        target: row.row[2], // Target entity
      }));

      console.log("📊 Extracted Data:", extractedData);

      // Send results to content script for rendering
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "graphData",
        data: extractedData,
      });
    } catch (error) {
      console.error("❌ Neo4j query error:", error);
    }
  }
});
