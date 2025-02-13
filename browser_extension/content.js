chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "graphData") {
    displayGraphOverlay(message.data);
  }
});

// Listen for text selection
document.addEventListener("mouseup", function () {
  const selectedText = window.getSelection().toString().trim();
  if (selectedText && selectedText.length > 0) {
    console.log("📌 Selected text:", selectedText);
    chrome.runtime.sendMessage({
      type: "searchEntity",
      entity: selectedText,
    });
  }
});

function displayGraphOverlay(data) {
  document.querySelectorAll("#kg-overlay").forEach((e) => e.remove());

  if (!data || data.length === 0) return;

  const selectionRect = window
    .getSelection()
    .getRangeAt(0)
    .getBoundingClientRect();

  const div = document.createElement("div");
  div.id = "kg-overlay";
  div.style.position = "absolute";
  div.style.left = `${selectionRect.x}px`;
  div.style.top = `${selectionRect.y + window.scrollY + 20}px`;
  div.style.background = "#1e1e1e";
  div.style.color = "white";
  div.style.padding = "10px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";
  div.style.zIndex = "9999";
  div.style.fontSize = "14px";
  div.style.minWidth = "250px";

  div.innerHTML = `<h3 style="margin: 0 0 5px 0; font-size: 14px;">🔍 Relationships</h3><div id="kg-content"></div>`;

  document.body.appendChild(div);

  const content = div.querySelector("#kg-content");

  // Display relationships
  data.forEach((rel) => {
    const relationshipDiv = document.createElement("div");
    relationshipDiv.style.marginBottom = "10px";

    // Ensure all values exist
    const entity = rel.entity || "Unknown Entity";
    const relationship = rel.relationship || "Unknown Relationship";
    const target = rel.target || "Unknown Target";

    relationshipDiv.innerHTML = `<strong>${entity}</strong> <span style="color: #61dafb;">(${relationship})</span> → <strong>${target}</strong>`;

    content.appendChild(relationshipDiv);
  });

  // Remove overlay on click outside
  document.addEventListener("click", (e) => {
    if (!div.contains(e.target)) {
      div.remove();
    }
  });
}
