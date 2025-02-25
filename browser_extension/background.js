// We can remove most of the background.js content since we're not making Neo4j queries anymore
chrome.runtime.onInstalled.addListener(() => {
  console.log("Knowledge Graph Extension installed");
});

// You can add more background functionality here as needed
