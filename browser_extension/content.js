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

// Listen for text selection
document.addEventListener("mouseup", function (event) {
  // Remove any existing overlay first
  const existingOverlay = document.getElementById("kg-overlay");
  if (existingOverlay && !existingOverlay.contains(event.target)) {
    existingOverlay.remove();
  }

  const selectedText = window.getSelection().toString().trim();
  if (selectedText && selectedText.length > 0) {
    // Check if the selected text exists in our fakeGraph
    if (fakeGraph[selectedText]) {
      console.log("Found relationships for:", selectedText);
      displayGraphOverlay(selectedText, fakeGraph[selectedText]);
    }
  }
});

function displayGraphOverlay(selectedText, relationships) {
  // Create overlay
  const div = document.createElement("div");
  div.id = "kg-overlay";

  // Get selection coordinates
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  // Position overlay below the selected text
  div.style.position = "absolute";
  div.style.left = `${rect.left + window.scrollX}px`;
  div.style.top = `${rect.bottom + window.scrollY}px`;

  // Style overlay
  div.style.background = "#1e1e1e";
  div.style.color = "white";
  div.style.padding = "10px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";
  div.style.zIndex = "10000";
  div.style.fontSize = "14px";
  div.style.minWidth = "250px";
  div.style.maxWidth = "400px";

  // Create content
  let content = `<h3 style="margin: 0 0 8px 0; font-size: 16px;">🔍 Relationships for "${selectedText}"</h3>`;

  relationships.forEach((rel) => {
    content += `
      <div style="margin-bottom: 8px; padding: 4px;">
        <strong>${selectedText}</strong>
        <span style="color: #61dafb"> (${rel.relationship})</span>
        → <strong>${rel.target}</strong>
      </div>
    `;
  });

  div.innerHTML = content;
  document.body.appendChild(div);

  // Close overlay when clicking outside
  document.addEventListener("mousedown", function closeOverlay(e) {
    if (!div.contains(e.target)) {
      div.remove();
      document.removeEventListener("mousedown", closeOverlay);
    }
  });
}

// Prevent overlay from closing when clicking inside it
document.addEventListener("mousedown", function (e) {
  const overlay = document.getElementById("kg-overlay");
  if (overlay && overlay.contains(e.target)) {
    e.stopPropagation();
  }
});
