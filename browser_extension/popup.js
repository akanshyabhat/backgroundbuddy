document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("queryInput");
  const searchBtn = document.getElementById("searchBtn");
  const graph = document.getElementById("graph");

  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "searchEntity") {
      input.value = request.entity;
      // Trigger search automatically when text is selected
      searchBtn.click();
    }
  });

  searchBtn.addEventListener("click", async () => {
    const entity = input.value;
    if (!entity) return;

    chrome.runtime.sendMessage({ type: "searchEntity", entity }, (response) => {
      if (response && response.results && response.results[0].data) {
        displayResults(response.results[0].data);
      }
    });
  });

  function displayResults(data) {
    graph.innerHTML = ""; // Clear previous results

    const relationships = {};
    data.forEach((row) => {
      const source = row.row[0].name;
      const relationship = row.row[1].type;
      const target = row.row[2].name;

      if (!relationships[source]) {
        relationships[source] = [];
      }
      relationships[source].push({ relationship, target });
    });

    Object.entries(relationships).forEach(([entity, rels]) => {
      rels.forEach((rel) => {
        const relText = document.createElement("p");
        relText.innerHTML = `"${entity}" "${rel.relationship}" "${rel.target}"`;
        graph.appendChild(relText);
      });
    });
  }
});
