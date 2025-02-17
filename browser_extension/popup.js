// Define the same fakeGraph as in content.js to make the demo work in the popup
const fakeGraph = {
  "Jacob Frey": [
    {
      relationship: "PARTICIPATING_IN",
      target: "Minneapolis Mayoral Election 2025",
    },
    { relationship: "LIVES_IN", target: "Minneapolis" },
  ],
  Minneapolis: [
    { relationship: "IS_A_CITY_IN", target: "Minnesota" },
    { relationship: "FAMOUS_FOR", target: "St Anthony Falls" },
  ],
  "Omar Fateh": [
    { relationship: "LIVES_IN", target: "Minneapolis" },
    {
      relationship: "PARTICIPATING_IN",
      target: "Minneapolis Mayoral Election 2025",
    },
    { relationship: "CHALLENGING", target: "Jacob Frey" },
    { relationship: "MEMBER_OF", target: "Senate" },
  ],
};

document.addEventListener("DOMContentLoaded", function () {
  // Add mouseup event listener to the demo entities in the popup
  document.querySelectorAll(".highlight").forEach((element) => {
    element.addEventListener("mouseup", function () {
      const selectedText = window.getSelection().toString().trim();
      if (selectedText && fakeGraph[selectedText]) {
        displayRelationships(selectedText);
      }
    });
  });

  function displayRelationships(entity) {
    // Remove any existing relationship displays
    const existingResults = document.querySelector(".relationships");
    if (existingResults) {
      existingResults.remove();
    }

    const relationships = fakeGraph[entity];
    const resultsDiv = document.createElement("div");
    resultsDiv.className = "relationships";
    resultsDiv.style.marginTop = "15px";
    resultsDiv.style.padding = "10px";
    resultsDiv.style.backgroundColor = "#f8f9fa";
    resultsDiv.style.borderRadius = "5px";

    if (relationships && relationships.length > 0) {
      relationships.forEach((rel) => {
        const relDiv = document.createElement("div");
        relDiv.style.marginBottom = "8px";
        relDiv.innerHTML = `<strong>${entity}</strong> <span style="color: #666;">(${rel.relationship})</span> → <strong>${rel.target}</strong>`;
        resultsDiv.appendChild(relDiv);
      });
    } else {
      resultsDiv.innerHTML = `<div>No relationships found for "${entity}"</div>`;
    }

    document.body.appendChild(resultsDiv);
  }
});
