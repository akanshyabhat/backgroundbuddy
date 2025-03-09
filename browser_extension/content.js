// Define the function to fetch graph data from the API
async function getGraphData() {
  try {
    console.log("Attempting to fetch graph data from API...");
    // Add a timeout to the fetch request to prevent long hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch("http://localhost:3001/api/graph", {
      signal: controller.signal,
      // Add cache control to prevent caching issues
      headers: {
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Graph Data fetched successfully");
    return data;
  } catch (error) {
    // Provide more specific error messages based on the error type
    if (error.name === "AbortError") {
      console.error(
        "Request timed out. The API server might be down or unreachable."
      );
    } else if (error.message.includes("Failed to fetch")) {
      console.error(
        "Failed to connect to API server. Make sure the backend is running at http://localhost:3001"
      );
    } else {
      console.error("Error fetching graph data:", error);
    }

    console.log("Using fallback data instead");
    return fakeGraph; // Fall back to fake data if API fails
  }
}

// Fallback data if Neo4j connection fails
const fakeGraph = {
  "Jacob Frey": [
    {
      relationship: "PROPOSED",
      target: "Third Precinct",
      evidence:
        "Minneapolis City Council members postponed a vote Tuesday on Mayor Jacob Frey's choice for a location for a future Third Precinct police station.",
      articleID: "600312948",
      headline:
        "Minneapolis City Council delays vote on Third Precinct police station",
      date: "2023-10-17T22:27:51.242Z",
    },
  ],
};

// Initialize with fake data, then update with real data when available
let graphData = fakeGraph;

// Fetch the real graph data when the extension loads
async function initializeGraphData() {
  try {
    console.log("Initializing graph data...");
    const data = await getGraphData();
    if (data && Object.keys(data).length > 0) {
      graphData = data;
      console.log("Graph data loaded successfully");
    } else {
      console.log("Using fallback data (empty response from API)");
    }
  } catch (error) {
    console.error("Failed to load graph data, using fallback data", error);
  }

  // Log the data we're using, whether from API or fallback
  console.log(
    `Using graph data with ${Object.keys(graphData).length} entities`
  );
}

// Initialize graph data
console.log(
  "Starting extension with fallback data while attempting to load from API"
);
initializeGraphData();

// Add a test function to help debug entity highlighting
function testEntityHighlighting() {
  console.log("Testing entity highlighting functionality...");

  // Log all entities in our graph
  const allEntities = getAllEntities();
  console.log(`Found ${allEntities.length} entities in our knowledge graph:`);
  console.log(allEntities.slice(0, 10)); // Show first 10 entities

  // Test finding entities in a sample text
  const testText =
    "Tim Walz announced a new infrastructure program in Minneapolis. Jacob Frey and Ilhan Omar were present at the event.";
  console.log("Test text:", testText);

  const foundEntities = findEntitiesInText(testText);
  console.log(
    `Found ${foundEntities.length} entities in test text:`,
    foundEntities
  );

  // Log success
  console.log(
    "Entity highlighting test complete. If entities were found, the highlighting functionality should work."
  );
}

// Run the test when the extension loads
setTimeout(testEntityHighlighting, 2000);

// Track active overlays to prevent duplicates
let activeOverlay = null;
// Track highlighted entities to prevent duplicates
let highlightedEntities = new Set();
// Track if we're currently processing a selection to prevent recursive calls
let isProcessingSelection = false;

// Helper function to escape special characters in regex
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Improved function to find entities in text - works with all selection types
function findEntitiesInText(text) {
  if (!text || text.length === 0) {
    return [];
  }

  console.log(`Finding entities in text (${text.length} chars)`);

  // Get all entities from our graph data
  const allEntities = getAllEntities();
  console.log(`Checking against ${allEntities.length} known entities`);

  // Create a map to track found entities (to avoid duplicates)
  const foundEntitiesMap = new Map();

  // Normalize the text for matching
  const normalizedText = text.toLowerCase();

  // ALWAYS use the same approach regardless of text length
  // Check each entity to see if it appears in the text
  allEntities.forEach((entity) => {
    // Skip empty entities
    if (!entity || entity.length === 0) return;

    const normalizedEntity = entity.toLowerCase();

    // Simple check: is the entity in the text?
    if (normalizedText.includes(normalizedEntity)) {
      console.log(`Found entity match: "${entity}" in the text`);
      foundEntitiesMap.set(entity, { entity, text: entity });
    }
  });

  // For short selections only, also check if they're part of a longer entity
  if (normalizedText.length < 30) {
    allEntities.forEach((entity) => {
      if (!entity || entity.length === 0 || foundEntitiesMap.has(entity))
        return;

      const normalizedEntity = entity.toLowerCase();

      if (
        normalizedEntity.includes(normalizedText) &&
        normalizedText.length > 2
      ) {
        console.log(
          `Found containing entity match: "${entity}" for the text "${text}"`
        );
        foundEntitiesMap.set(entity, {
          entity,
          text: entity,
          isContainingMatch: true,
        });
      }
    });
  }

  // Convert found entities to array
  const foundEntities = Array.from(foundEntitiesMap.values());

  // Sort results by entity length (longer entities first)
  foundEntities.sort((a, b) => b.entity.length - a.entity.length);

  console.log(
    `Found ${foundEntities.length} entities in text:`,
    foundEntities.map((e) => e.entity)
  );

  return foundEntities;
}

// Process the current text selection with improved reliability
function processSelection(selection, event) {
  if (!selection || selection.rangeCount === 0) return;

  const selectedText = selection.toString().trim();

  if (selectedText && selectedText.length > 0) {
    console.log("Text selected:", selectedText);

    // Find entities in the selected text using our improved function
    const entities = findEntitiesInText(selectedText);

    if (entities.length > 0) {
      console.log(`Found ${entities.length} entities in selection`);
      // Create a popup with the entities found
      showEntitiesPopup(entities, selection, event);
    } else {
      console.log("No entities found in selection");

      // Debug: Log all entities we're checking against
      const allEntities = getAllEntities();
      console.log(
        `Available entities (${allEntities.length}):`,
        allEntities.length > 20 ? allEntities.slice(0, 20) + "..." : allEntities
      );
    }
  }
}

// Listen for text selection with standardized behavior
document.addEventListener("mouseup", function (event) {
  // Don't process if we're already processing a selection
  if (isProcessingSelection) {
    return;
  }

  // Don't process if we clicked on a highlighted entity or inside an active overlay
  if (
    (event.target.classList &&
      event.target.classList.contains("kg-highlighted-entity")) ||
    (activeOverlay && activeOverlay.contains(event.target))
  ) {
    return;
  }

  // Remove any existing overlay if clicking outside
  if (activeOverlay && !activeOverlay.contains(event.target)) {
    activeOverlay.remove();
    activeOverlay = null;
  }

  // Get the selection
  const selection = window.getSelection();
  if (!selection) return;

  // Force a small delay to ensure the selection is complete
  setTimeout(() => {
    processSelection(selection, event);
  }, 10);
});

// Function to show a popup with the entities found - standardized for all selection types
function showEntitiesPopup(entities, selection, event) {
  // Remove any existing overlay
  if (activeOverlay) {
    activeOverlay.remove();
    activeOverlay = null;
  }

  // Get the selection coordinates
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  // Create the popup
  const div = document.createElement("div");
  div.className = "kg-entity-popup";
  div.style.position = "absolute";

  // Position the popup - ensure it's visible even for small selections
  if (rect.width < 5 || rect.height < 5) {
    // For very small selections, position near the mouse
    div.style.left = `${event.clientX + window.scrollX}px`;
    div.style.top = `${event.clientY + window.scrollY + 20}px`;
  } else {
    // Normal positioning
    div.style.left = `${rect.left + window.scrollX}px`;
    div.style.top = `${rect.bottom + window.scrollY + 10}px`;
  }

  div.style.background = "#1e1e1e";
  div.style.color = "white";
  div.style.padding = "15px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 4px 15px rgba(0, 0, 0, 0.2)";
  div.style.zIndex = "10000";
  div.style.fontSize = "14px";
  div.style.minWidth = "250px";
  div.style.maxWidth = "400px";

  // Make the popup draggable
  let isDragging = false;
  let offsetX, offsetY;

  div.addEventListener("mousedown", (e) => {
    if (e.target === div || e.target.classList.contains("popup-header")) {
      isDragging = true;
      offsetX = e.clientX - div.getBoundingClientRect().left;
      offsetY = e.clientY - div.getBoundingClientRect().top;
      document.body.style.cursor = "grabbing";
    }
  });

  document.addEventListener("mousemove", (e) => {
    if (isDragging) {
      div.style.left = `${e.clientX - offsetX}px`;
      div.style.top = `${e.clientY - offsetY}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default";
  });

  // Create the content
  let content = `
    <div class="popup-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; cursor: grab;">
      <div style="font-weight: bold;">Entities found in your selection:</div>
      <button class="close-btn" style="background: none; border: none; color: #aaa; font-size: 18px; cursor: pointer;">×</button>
    </div>
    <div style="max-height: 300px; overflow-y: auto;">
  `;

  // Add entities to the popup - always show all entities, even nested ones
  entities.forEach((entity) => {
    let matchType = "match";
    if (entity.isExactMatch) matchType = "exact match";
    else if (entity.isPartialMatch) matchType = "partial match";
    else if (entity.isContainingMatch) matchType = "related entity";

    content += `
      <div class="kg-entity-item" style="padding: 8px; margin-bottom: 8px; background: #333; border-radius: 4px; cursor: pointer;" data-entity="${entity.entity}">
        <strong>${entity.entity}</strong> 
        <span style="color: #61dafb; font-size: 12px;">(${matchType})</span>
        <div style="color: #aaa; font-size: 12px; margin-top: 4px;">Click to see relationships</div>
      </div>
    `;
  });

  content += `</div>`;

  div.innerHTML = content;
  document.body.appendChild(div);
  activeOverlay = div;

  // Add click handler for close button
  div.querySelector(".close-btn").addEventListener("click", () => {
    div.remove();
    activeOverlay = null;
  });

  // Add click handler for highlight button
  div.querySelector(".highlight-entities-btn").addEventListener("click", () => {
    highlightEntitiesInPage(entities, selection);
    div.remove();
    activeOverlay = null;
  });

  // Add click handlers for the entities
  div.querySelectorAll(".kg-entity-item").forEach((item) => {
    item.addEventListener("click", function () {
      const entityName = this.dataset.entity;
      console.log(`Clicked on entity: ${entityName}`);

      // Find relationships for this entity
      let foundRelationships = [];

      // Check if this entity is a source
      if (graphData[entityName]) {
        // Add all relationships where this entity is the source
        graphData[entityName].forEach((rel) => {
          foundRelationships.push({
            ...rel,
            source: entityName,
          });
        });
      }

      // Check if this entity appears as a target in any relationships
      Object.entries(graphData).forEach(([source, relationships]) => {
        relationships.forEach((rel) => {
          if (rel.target === entityName) {
            foundRelationships.push({
              ...rel,
              source: source,
            });
          }
        });
      });

      if (foundRelationships.length > 0) {
        console.log(
          `Found ${foundRelationships.length} relationships for entity: ${entityName}`
        );

        // Remove the entities popup
        div.remove();
        activeOverlay = null;

        // Show the relationships popup
        const itemRect = this.getBoundingClientRect();
        displayGraphOverlay(entityName, foundRelationships, itemRect);
      } else {
        console.log(`No relationships found for entity: ${entityName}`);
      }
    });
  });

  // Close popup when clicking outside
  document.addEventListener("mousedown", function closePopup(e) {
    if (activeOverlay && !activeOverlay.contains(e.target)) {
      activeOverlay.remove();
      activeOverlay = null;
      document.removeEventListener("mousedown", closePopup);
    }
  });
}

// Function to highlight entities in the page - improved to handle overlapping entities
function highlightEntitiesInPage(entities, selection) {
  if (
    !entities ||
    entities.length === 0 ||
    !selection ||
    selection.rangeCount === 0
  ) {
    console.log("No entities to highlight or no selection");
    return;
  }

  console.log(`Highlighting ${entities.length} entities in the page`);

  try {
    isProcessingSelection = true;

    // Get the current selection range
    const range = selection.getRangeAt(0);
    const selectedText = selection.toString();

    // Create a document fragment to hold our highlighted content
    const fragment = document.createDocumentFragment();

    // Find all occurrences of all entities in the text
    const occurrences = [];

    entities.forEach((entity) => {
      const entityText = entity.entity;
      const entityLower = entityText.toLowerCase();
      const textLower = selectedText.toLowerCase();

      let startIndex = 0;
      while ((startIndex = textLower.indexOf(entityLower, startIndex)) !== -1) {
        occurrences.push({
          entity: entityText,
          start: startIndex,
          end: startIndex + entityText.length,
          length: entityText.length,
        });
        startIndex += 1; // Move forward to find next occurrence
      }
    });

    // Sort occurrences by start position, then by length (descending) for overlaps
    occurrences.sort((a, b) => {
      if (a.start === b.start) return b.length - a.length;
      return a.start - b.start;
    });

    // Process occurrences to handle overlaps
    // We'll use a non-greedy approach that preserves shorter entities when possible
    const finalOccurrences = [];
    const coveredRanges = [];

    occurrences.forEach((occurrence) => {
      // Check if this occurrence overlaps with any covered range
      let isOverlapping = false;

      for (const range of coveredRanges) {
        // Check for overlap
        if (
          (occurrence.start >= range.start && occurrence.start < range.end) ||
          (occurrence.end > range.start && occurrence.end <= range.end) ||
          (occurrence.start <= range.start && occurrence.end >= range.end)
        ) {
          isOverlapping = true;

          // If this is a shorter entity contained within a longer one,
          // we still want to include it in the UI popup, but not highlight it
          if (occurrence.start >= range.start && occurrence.end <= range.end) {
            // This is a nested entity - we'll add it to finalOccurrences
            // but mark it as nested so we don't highlight it
            occurrence.nested = true;
            finalOccurrences.push(occurrence);
          }

          break;
        }
      }

      if (!isOverlapping) {
        // Add to final occurrences and mark the range as covered
        finalOccurrences.push(occurrence);
        coveredRanges.push({
          start: occurrence.start,
          end: occurrence.end,
        });
      }
    });

    // Sort final occurrences by start position for highlighting
    finalOccurrences.sort((a, b) => a.start - b.start);

    // Now build the highlighted text
    let currentPosition = 0;

    finalOccurrences.forEach((occurrence) => {
      // Skip nested occurrences for highlighting (but they're still in the popup)
      if (occurrence.nested) return;

      // Add text before this entity
      if (occurrence.start > currentPosition) {
        const beforeText = selectedText.substring(
          currentPosition,
          occurrence.start
        );
        fragment.appendChild(document.createTextNode(beforeText));
      }

      // Create a span for the entity
      const span = document.createElement("span");
      span.className = "kg-highlighted-entity";
      span.style.backgroundColor = "#61dafb33";
      span.style.borderBottom = "2px solid #61dafb";
      span.style.padding = "0 2px";
      span.style.cursor = "pointer";
      span.textContent = selectedText.substring(
        occurrence.start,
        occurrence.end
      );
      span.dataset.entity = occurrence.entity;

      // Add click handler to show relationships
      span.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();

        // Find relationships for this entity
        let foundRelationships = [];

        // Check if this entity is a source
        if (graphData[occurrence.entity]) {
          graphData[occurrence.entity].forEach((rel) => {
            foundRelationships.push({
              ...rel,
              source: occurrence.entity,
            });
          });
        }

        // Check if this entity appears as a target
        Object.entries(graphData).forEach(([source, relationships]) => {
          relationships.forEach((rel) => {
            if (rel.target === occurrence.entity) {
              foundRelationships.push({
                ...rel,
                source: source,
              });
            }
          });
        });

        if (foundRelationships.length > 0) {
          // Remove any existing overlay
          if (activeOverlay) {
            activeOverlay.remove();
            activeOverlay = null;
          }

          // Show the relationships popup
          const rect = span.getBoundingClientRect();
          displayGraphOverlay(occurrence.entity, foundRelationships, rect);
        }
      });

      fragment.appendChild(span);

      // Update the current position
      currentPosition = occurrence.end;
    });

    // Add any remaining text
    if (currentPosition < selectedText.length) {
      const afterText = selectedText.substring(currentPosition);
      fragment.appendChild(document.createTextNode(afterText));
    }

    // Clear the current selection
    range.deleteContents();

    // Insert our highlighted content
    range.insertNode(fragment);

    // Clear the selection
    selection.removeAllRanges();

    console.log("Entities highlighted successfully");
  } catch (error) {
    console.error("Error highlighting entities:", error);
  } finally {
    isProcessingSelection = false;
  }
}

function displayGraphOverlay(selectedText, relationships, rect) {
  // Create overlay
  const div = document.createElement("div");
  div.id = "kg-overlay";
  activeOverlay = div;

  // Position overlay below the selected text
  div.style.position = "absolute";
  div.style.left = `${rect.left + window.scrollX}px`;
  div.style.top = `${rect.bottom + window.scrollY + 10}px`;

  // Style overlay
  div.style.background = "#1e1e1e";
  div.style.color = "white";
  div.style.padding = "15px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 4px 15px rgba(0, 0, 0, 0.2)";
  div.style.zIndex = "10000";
  div.style.fontSize = "14px";
  div.style.minWidth = "300px";
  div.style.maxWidth = "450px";

  // Make the overlay draggable
  let isDragging = false;
  let offsetX, offsetY;

  div.addEventListener("mousedown", (e) => {
    if (e.target === div || e.target.classList.contains("overlay-header")) {
      isDragging = true;
      offsetX = e.clientX - div.getBoundingClientRect().left;
      offsetY = e.clientY - div.getBoundingClientRect().top;
      document.body.style.cursor = "grabbing";
    }
  });

  document.addEventListener("mousemove", (e) => {
    if (isDragging) {
      div.style.left = `${e.clientX - offsetX}px`;
      div.style.top = `${e.clientY - offsetY}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default";
  });

  // Add CSS for styling
  const style = document.createElement("style");
  style.textContent = `
    .relationship-box {
      background: #1e1e1e;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: white;
      width: 400px;
      position: absolute;
      z-index: 10000;
    }

    .overlay-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      cursor: grab;
    }

    .close-btn {
      background: none;
      border: none;
      color: #aaa;
      font-size: 18px;
      cursor: pointer;
      padding: 0;
      margin: 0;
    }

    .close-btn:hover {
      color: white;
    }

    .relationship-item {
      padding: 12px;
      margin-bottom: 12px;
      border-radius: 8px;
      background: #2a2a2a;
      position: relative;
      transition: background 0.2s;
    }

    .relationship-item:hover {
      background: #333;
    }

    .relationship-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 14px;
    }

    .relationship-text {
      flex-grow: 1;
      line-height: 1.4;
    }

    .action-buttons {
      display: flex;
      gap: 5px;
      margin-top: 8px;
    }

    .source-btn, .report-btn, .add-btn {
      background: none;
      border: none;
      color: #61dafb;
      cursor: pointer;
      padding: 4px 8px;
      font-size: 13px;
      opacity: 0.8;
      transition: opacity 0.2s;
      border-radius: 4px;
    }

    .source-btn:hover, .report-btn:hover, .add-btn:hover {
      opacity: 1;
      background: rgba(97, 218, 251, 0.1);
    }

    .source-content {
      display: none;
      margin-top: 10px;
      padding: 10px;
      background: #333;
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.4;
    }

    .report-form, .add-form {
      display: none;
      margin-top: 10px;
      padding: 12px;
      background: #333;
      border-radius: 6px;
    }

    .form-title {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 10px;
    }

    .form-input {
      width: 100%;
      padding: 8px;
      margin: 5px 0 10px 0;
      border: 1px solid #444;
      border-radius: 4px;
      background: #222;
      color: white;
      font-size: 13px;
    }

    .form-submit {
      width: 100%;
      padding: 8px;
      background: #61dafb;
      color: #1e1e1e;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
      font-size: 14px;
    }

    .form-submit:hover {
      background: #4fa8d8;
    }

    .relationship-type {
      color: #61dafb;
      font-weight: 500;
    }

    .show-more-btn {
      width: 100%;
      padding: 8px;
      margin-top: 5px;
      background: #333;
      color: #61dafb;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      transition: background 0.2s;
    }

    .show-more-btn:hover {
      background: #444;
    }

    .article-link {
      color: #61dafb;
      text-decoration: none;
      border-bottom: 1px dotted #61dafb;
    }

    .article-link:hover {
      border-bottom: 1px solid #61dafb;
    }
    
    .kg-highlighted-entity {
      background-color: rgba(255, 255, 150, 0.5);
      border-radius: 2px;
      cursor: pointer;
      padding: 0 2px;
    }
    
    .kg-highlighted-entity:hover {
      background-color: rgba(255, 255, 100, 0.7);
    }
  `;
  document.head.appendChild(style);

  // Create content - limit to 3 relationships by default
  const initialRelationships = relationships.slice(0, 3);
  const hasMoreRelationships = relationships.length > 3;

  let content = `
    <div class="overlay-header">
      <h3 style="margin: 0; font-size: 16px;">🔍 Relationships for "${selectedText}"</h3>
      <button class="close-btn">×</button>
    </div>
  `;

  // Add the first 3 relationships
  initialRelationships.forEach((rel, index) => {
    // Convert article ID to a URL
    const articleUrl = `https://startribune.com/search/${rel.articleID}`;

    content += `
      <div class="relationship-item" data-index="${index}">
        <div class="relationship-content">
          <div class="relationship-text">
            <strong>${rel.source}</strong>
            <span class="relationship-type">${rel.relationship}</span>
            <strong>${rel.target}</strong>
          </div>
        </div>
        <div class="action-buttons">
          <button class="source-btn" data-index="${index}">Source & Details</button>
          <button class="report-btn" data-index="${index}">Report</button>
          <button class="add-btn" data-index="${index}">Add Relationship</button>
        </div>
        <div class="source-content" id="source-${index}">
          <p><strong>Details:</strong> ${rel.evidence}</p>
          <p><strong>Source:</strong> <a href="${articleUrl}" target="_blank" class="article-link">Article #${rel.articleID}</a></p>
        </div>
        <div class="report-form" id="report-form-${index}">
          <div class="form-title">Report this relationship:</div>
          <textarea class="form-input" placeholder="What's incorrect about this relationship?" rows="3"></textarea>
          <button class="form-submit report-submit" data-index="${index}">Submit Report</button>
        </div>
        <div class="add-form" id="add-form-${index}">
          <div class="form-title">Add a new relationship:</div>
          <label>Subject:</label>
          <input type="text" class="form-input" placeholder="Entity name">
          <label>Relationship:</label>
          <input type="text" class="form-input" placeholder="Type of relationship">
          <label>Target:</label>
          <input type="text" class="form-input" placeholder="Related entity">
          <label>Source URL:</label>
          <input type="text" class="form-input" placeholder="Article URL">
          <button class="form-submit add-submit">Add Relationship</button>
        </div>
      </div>
    `;
  });

  // Add "Show More" button if needed
  if (hasMoreRelationships) {
    content += `
      <button class="show-more-btn" data-total="${relationships.length}">
        Show More (${relationships.length - 3} more)
      </button>
    `;
  }

  // Update the main container structure
  div.className = "relationship-box";
  div.innerHTML = content;
  document.body.appendChild(div);

  // Add event listeners for close button
  div.querySelector(".close-btn").addEventListener("click", () => {
    div.remove();
    activeOverlay = null;
  });

  // Add event listeners for source buttons
  div.querySelectorAll(".source-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const index = this.dataset.index;
      const sourceContent = document.getElementById(`source-${index}`);

      // Toggle source content
      if (sourceContent.style.display === "block") {
        sourceContent.style.display = "none";
        this.textContent = "Source & Details";
      } else {
        sourceContent.style.display = "block";
        this.textContent = "Hide Details";
      }
    });
  });

  // Add event listeners for report buttons
  div.querySelectorAll(".report-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const index = this.dataset.index;
      const reportForm = document.getElementById(`report-form-${index}`);

      // Toggle report form
      if (reportForm.style.display === "block") {
        reportForm.style.display = "none";
      } else {
        // Hide all other forms first
        div
          .querySelectorAll(".report-form, .add-form, .source-content")
          .forEach((el) => {
            if (el.id !== `report-form-${index}`) {
              el.style.display = "none";
            }
          });

        // Reset button text
        div.querySelectorAll(".source-btn").forEach((btn) => {
          btn.textContent = "Source & Details";
        });

        reportForm.style.display = "block";
      }
    });
  });

  // Add event listeners for add relationship buttons
  div.querySelectorAll(".add-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const index = this.dataset.index;
      const addForm = document.getElementById(`add-form-${index}`);

      // Toggle add form
      if (addForm.style.display === "block") {
        addForm.style.display = "none";
      } else {
        // Hide all other forms first
        div
          .querySelectorAll(".report-form, .add-form, .source-content")
          .forEach((el) => {
            if (el.id !== `add-form-${index}`) {
              el.style.display = "none";
            }
          });

        // Reset button text
        div.querySelectorAll(".source-btn").forEach((btn) => {
          btn.textContent = "Source & Details";
        });

        addForm.style.display = "block";
      }
    });
  });

  // Add event listener for "Show More" button
  const showMoreBtn = div.querySelector(".show-more-btn");
  if (showMoreBtn) {
    showMoreBtn.addEventListener("click", function () {
      // Get the remaining relationships
      const remainingRelationships = relationships.slice(3);
      const container = this.parentNode;

      // Remove the "Show More" button
      this.remove();

      // Add the remaining relationships
      remainingRelationships.forEach((rel, i) => {
        const index = i + 3; // Offset by the initial 3 relationships
        const articleUrl = `https://startribune.com/search/${rel.articleID}`;

        const relationshipItem = document.createElement("div");
        relationshipItem.className = "relationship-item";
        relationshipItem.dataset.index = index;

        relationshipItem.innerHTML = `
          <div class="relationship-content">
            <div class="relationship-text">
              <strong>${rel.source}</strong>
              <span class="relationship-type">${rel.relationship}</span>
              <strong>${rel.target}</strong>
            </div>
          </div>
          <div class="action-buttons">
            <button class="source-btn" data-index="${index}">Source & Details</button>
            <button class="report-btn" data-index="${index}">Report</button>
            <button class="add-btn" data-index="${index}">Add Relationship</button>
          </div>
          <div class="source-content" id="source-${index}">
            <p><strong>Details:</strong> ${rel.evidence}</p>
            <p><strong>Source:</strong> <a href="${articleUrl}" target="_blank" class="article-link">Article #${rel.articleID}</a></p>
          </div>
          <div class="report-form" id="report-form-${index}">
            <div class="form-title">Report this relationship:</div>
            <textarea class="form-input" placeholder="What's incorrect about this relationship?" rows="3"></textarea>
            <button class="form-submit report-submit" data-index="${index}">Submit Report</button>
          </div>
          <div class="add-form" id="add-form-${index}">
            <div class="form-title">Add a new relationship:</div>
            <label>Subject:</label>
            <input type="text" class="form-input" placeholder="Entity name">
            <label>Relationship:</label>
            <input type="text" class="form-input" placeholder="Type of relationship">
            <label>Target:</label>
            <input type="text" class="form-input" placeholder="Related entity">
            <label>Source URL:</label>
            <input type="text" class="form-input" placeholder="Article URL">
            <button class="form-submit add-submit">Add Relationship</button>
          </div>
        `;

        container.appendChild(relationshipItem);

        // Add event listeners for the new buttons
        const sourceBtn = relationshipItem.querySelector(".source-btn");
        sourceBtn.addEventListener("click", function () {
          const idx = this.dataset.index;
          const sourceContent = document.getElementById(`source-${idx}`);

          if (sourceContent.style.display === "block") {
            sourceContent.style.display = "none";
            this.textContent = "Source & Details";
          } else {
            sourceContent.style.display = "block";
            this.textContent = "Hide Details";
          }
        });

        const reportBtn = relationshipItem.querySelector(".report-btn");
        reportBtn.addEventListener("click", function () {
          const idx = this.dataset.index;
          const reportForm = document.getElementById(`report-form-${idx}`);

          if (reportForm.style.display === "block") {
            reportForm.style.display = "none";
          } else {
            div
              .querySelectorAll(".report-form, .add-form, .source-content")
              .forEach((el) => {
                if (el.id !== `report-form-${idx}`) {
                  el.style.display = "none";
                }
              });

            div.querySelectorAll(".source-btn").forEach((btn) => {
              btn.textContent = "Source & Details";
            });

            reportForm.style.display = "block";
          }
        });

        const addBtn = relationshipItem.querySelector(".add-btn");
        addBtn.addEventListener("click", function () {
          const idx = this.dataset.index;
          const addForm = document.getElementById(`add-form-${idx}`);

          if (addForm.style.display === "block") {
            addForm.style.display = "none";
          } else {
            div
              .querySelectorAll(".report-form, .add-form, .source-content")
              .forEach((el) => {
                if (el.id !== `add-form-${idx}`) {
                  el.style.display = "none";
                }
              });

            div.querySelectorAll(".source-btn").forEach((btn) => {
              btn.textContent = "Source & Details";
            });

            addForm.style.display = "block";
          }
        });
      });
    });
  }

  // Close overlay when clicking outside
  document.addEventListener("mousedown", function closeOverlay(e) {
    if (activeOverlay && !activeOverlay.contains(e.target)) {
      activeOverlay.remove();
      activeOverlay = null;
      document.removeEventListener("mousedown", closeOverlay);
    }
  });
}

// Function to get all entities from the graph data
function getAllEntities() {
  // Get unique entities from the graph data
  const entities = new Set();

  // Add all sources
  Object.keys(graphData).forEach((source) => {
    entities.add(source);

    // Add all targets
    if (graphData[source] && Array.isArray(graphData[source])) {
      graphData[source].forEach((rel) => {
        if (rel.target) {
          entities.add(rel.target);
        }
      });
    }
  });

  // Convert to array and filter out empty entities
  return Array.from(entities).filter(
    (entity) => entity && entity.trim().length > 0
  );
}

// Add a debug function to test entity detection with different selection types
function testEntityDetection() {
  console.log("Testing entity detection...");

  // Test cases - different selection types
  const testCases = [
    "Minnesota",
    "Minnesota Legislature",
    "The Minnesota Legislature passed a bill",
    "Tim Walz is the governor of Minnesota",
    "Minneapolis is a city in Minnesota where Jacob Frey is mayor",
  ];

  testCases.forEach((text) => {
    console.log(`\nTest case: "${text}"`);
    const entities = findEntitiesInText(text);
    console.log(
      `Found ${entities.length} entities:`,
      entities.map((e) => e.entity)
    );
  });

  console.log("Entity detection test complete");
}

// Run the test on page load
setTimeout(testEntityDetection, 2000);
