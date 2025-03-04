// Define the function to fetch graph data from the API
async function getGraphData() {
  try {
    const response = await fetch("http://localhost:3001/api/graph");
    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }
    const data = await response.json();
    console.log("Graph Data fetched successfully");
    return data;
  } catch (error) {
    console.error("Error fetching graph data:", error);
    return fakeGraph; // Fall back to fake data if API fails
  }
}

// Fallback data if Neo4j connection fails
const fakeGraph = {
  "Kyrees Darius Johnson": [
    {
      relationship: "HAS_PARTICIPANT",
      target: "Federal Investigation into Snapchat-based Gun Ring",
      evidence:
        "Kyrees Darius Johnson was sentenced to nearly eight years in prison as part of the investigation.",
      articleID: "600381433",
    },
    {
      relationship: "IS_CHARGED_WITH",
      target: "Unlawful Possession of Machine Guns",
      evidence:
        "Kyrees Darius Johnson pleaded guilty to one count of unlawful possession of machine guns.",
      articleID: "600381433",
    },
    {
      relationship: "HAS_LOCATION",
      target: "Minneapolis",
      evidence: "Kyrees Darius Johnson is from Minneapolis.",
      articleID: "600381433",
    },
    {
      relationship: "IS_ACCUSED_OF",
      target: "Attempted Carjacking",
      evidence:
        "Johnson was accused of an attempted carjacking in August 2023.",
      articleID: "600381433",
    },
  ],
  "Snapchat-based Gun Ring": [
    {
      relationship: "HAS_DATE",
      target: "2024-07-17",
      evidence:
        "The investigation into the gun ring concluded with sentencing on this date.",
      articleID: "600381433",
    },
    {
      relationship: "HAS_LOCATION",
      target: "Twin Cities Metro",
      evidence:
        "The Snapchat-based gun ring operated in the Twin Cities metro area.",
      articleID: "600381433",
    },
  ],
  "U.S. District Judge Donovan Frank": [
    {
      relationship: "HAS_PARTICIPANT",
      target: "Federal Investigation into Snapchat-based Gun Ring",
      evidence:
        "Judge Donovan Frank sentenced Kyrees Darius Johnson as part of the case.",
      articleID: "600381433",
    },
  ],
  "Central Minnesota Violent Offender Task Force": [
    {
      relationship: "MENTIONS",
      target: "Bureau of Alcohol, Tobacco, Firearms and Explosives",
      evidence:
        "The task force notified federal authorities about the Snapchat group suspected of trafficking firearms and illicit drugs.",
      articleID: "600381433",
    },
  ],
  "Undercover Officers": [
    {
      relationship: "HAS_PARTICIPANT",
      target: "Federal Investigation into Snapchat-based Gun Ring",
      evidence:
        "Undercover officers carried out about six controlled buys with various members of the group between March and June 2023.",
      articleID: "600381433",
    },
  ],
  "Assistant U.S. Attorney Ruth Shnider": [
    {
      relationship: "WORKS_FOR",
      target: "U.S. Department of Justice",
      evidence:
        "Assistant U.S. Attorney Ruth Shnider prosecuted the case against Johnson.",
      articleID: "600381433",
    },
  ],
  "Jacob Frey": [
    {
      relationship: "PARTICIPATING_IN",
      target: "Minneapolis Mayoral Election 2025",
      evidence: "Jacob Frey is running for mayor of Minneapolis in 2025.",
      articleID: "1234567890",
    },
    {
      relationship: "LIVES_IN",
      target: "Minneapolis",
      evidence: "Jacob Frey lives in Minneapolis.",
      articleID: "1234567890",
    },
  ],
  "Minnesota Legislature": [
    {
      relationship: "PROPOSED_BILL",
      target: "Gun Control Reform Act 2025",
      evidence:
        "Minnesota lawmakers proposed a new gun control reform act in early 2025.",
      articleID: "9876543210",
    },
    {
      relationship: "DEBATING",
      target: "Statewide Minimum Wage Increase",
      evidence:
        "Minnesota legislators are debating an increase in the statewide minimum wage.",
      articleID: "5678901234",
    },
  ],
  "Ilhan Omar": [
    {
      relationship: "ENDORSED",
      target: "Community Housing Initiative",
      evidence:
        "Ilhan Omar endorsed a community-led housing initiative in Minneapolis.",
      articleID: "8765432109",
    },
    {
      relationship: "CRITICIZED",
      target: "Minneapolis Police Department Policy",
      evidence:
        "Ilhan Omar publicly criticized new MPD policies on surveillance.",
      articleID: "3456789012",
    },
  ],
  "Tim Walz": [
    {
      relationship: "SIGNED_BILL",
      target: "Green Energy Investment Plan",
      evidence:
        "Governor Tim Walz signed a new bill to promote green energy investments in Minnesota.",
      articleID: "2345678901",
    },
    {
      relationship: "ANNOUNCED",
      target: "Infrastructure Rebuild Program",
      evidence:
        "Tim Walz announced a $500 million infrastructure rebuild program for roads and bridges.",
      articleID: "4567890123",
    },
  ],
};

// Initialize with fake data, then update with real data when available
let graphData = fakeGraph;

// Fetch the real graph data when the extension loads
async function initializeGraphData() {
  try {
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
}

// Initialize graph data
initializeGraphData();

// Track active overlays to prevent duplicates
let activeOverlay = null;

// Listen for text selection
document.addEventListener("mouseup", function (event) {
  // Remove any existing overlay if clicking outside
  if (activeOverlay && !activeOverlay.contains(event.target)) {
    activeOverlay.remove();
    activeOverlay = null;
  }

  const selectedText = window.getSelection().toString().trim();
  if (selectedText && selectedText.length > 0) {
    // Find all relationships where the selected text appears
    let foundRelationships = [];

    // Check each entity in the graph
    Object.entries(graphData).forEach(([source, relationships]) => {
      if (source.toLowerCase().includes(selectedText.toLowerCase())) {
        // If selected text is in the source, add its relationships
        relationships.forEach((rel) => {
          foundRelationships.push({
            ...rel,
            source: source,
          });
        });
      } else {
        // Check if selected text appears in any targets
        relationships.forEach((rel) => {
          if (rel.target.toLowerCase().includes(selectedText.toLowerCase())) {
            foundRelationships.push({
              ...rel,
              source: source,
            });
          }
        });
      }
    });

    if (foundRelationships.length > 0) {
      console.log(
        `Found ${foundRelationships.length} relationships for: ${selectedText}`
      );

      // Only show if we don't already have an active overlay
      if (!activeOverlay) {
        displayGraphOverlay(selectedText, foundRelationships);
      }
    }
  }
});

function displayGraphOverlay(selectedText, relationships) {
  // Create overlay
  const div = document.createElement("div");
  div.id = "kg-overlay";
  activeOverlay = div;

  // Get selection coordinates
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

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
    // Convert article ID to a URL (in a real implementation, you'd use your actual URL pattern)
    const articleUrl = `https://example.com/articles/${rel.articleID}`;

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
        const articleUrl = `https://example.com/articles/${rel.articleID}`;

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
