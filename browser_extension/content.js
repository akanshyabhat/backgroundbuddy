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
// Listen for text selection
document.addEventListener("mouseup", function (event) {
  // Remove any existing overlay first
  const existingOverlay = document.getElementById("kg-overlay");
  if (existingOverlay && !existingOverlay.contains(event.target)) {
    existingOverlay.remove();
  }

  const selectedText = window.getSelection().toString().trim();
  if (selectedText && selectedText.length > 0) {
    // Find all relationships where the selected text appears in either the source or target
    let foundRelationships = [];

    // Check each entity in the graph
    Object.entries(fakeGraph).forEach(([source, relationships]) => {
      if (source.toLowerCase().includes(selectedText.toLowerCase())) {
        // If selected text is in the source, add all its relationships
        relationships.forEach((rel) => {
          foundRelationships.push({
            ...rel,
            source: source, // Add source to the relationship object
          });
        });
      } else {
        // Check if selected text appears in any targets
        relationships.forEach((rel) => {
          if (rel.target.toLowerCase().includes(selectedText.toLowerCase())) {
            foundRelationships.push({
              ...rel,
              source: source, // Add source to the relationship object
            });
          }
        });
      }
    });

    if (foundRelationships.length > 0) {
      console.log("Found relationships for:", selectedText);
      displayGraphOverlay(selectedText, foundRelationships);
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

  // Make the overlay draggable
  let isDragging = false;
  let offsetX, offsetY;

  div.addEventListener("mousedown", (e) => {
    isDragging = true;
    offsetX = e.clientX - div.getBoundingClientRect().left;
    offsetY = e.clientY - div.getBoundingClientRect().top;
    document.body.style.cursor = "grabbing"; // Change cursor to grabbing
  });

  document.addEventListener("mousemove", (e) => {
    if (isDragging) {
      div.style.left = `${e.clientX - offsetX}px`;
      div.style.top = `${e.clientY - offsetY}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default"; // Reset cursor
  });

  // Add CSS for report button and form
  const style = document.createElement("style");
  style.textContent = `
    .relationship-box {
      background: #1e1e1e;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      font-family: Arial, sans-serif;
      color: white;
      width: 400px;
      position: absolute;
      z-index: 10000;
      margin-top: 10px;
    }

    .relationship-item {
      padding: 12px;
      margin-bottom: 20px;
      border-radius: 6px;
      background: #2a2a2a;
      position: relative;
    }

    .relationship-title {
      font-size: 18px;
      margin: 0 0 20px 0;
      padding-bottom: 15px;
      border-bottom: 1px solid #333;
    }

    .relationship-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 16px;
    }

    .relationship-text {
      flex-grow: 1;
    }

    .evidence-btn {
      background: none;
      border: none;
      color: #61dafb;
      cursor: pointer;
      padding: 4px 8px;
      font-size: 14px;
      opacity: 0.7;
      transition: opacity 0.2s;
    }

    .evidence-btn:hover {
      opacity: 1;
    }

    .evidence-content {
      display: none;
      margin-top: 8px;
      padding: 8px;
      background: #333;
      border-radius: 6px;
    }

    .report-btn {
      background: none;
      border: none;
      color: #61dafb;
      cursor: pointer;
      padding: 4px 8px;
      font-size: 14px;
      opacity: 0.7;
      transition: opacity 0.2s;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .report-btn:hover {
      opacity: 1;
    }

    .report-form {
      background: #1e1e1e;
      padding: 15px;
      margin-top: 15px;
      border-radius: 8px;
      border: 1px solid #333;
    }

    .report-form-title {
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 12px;
    }

    .report-input {
      width: 90%;
      padding: 12px;
      margin: 8px 0 12px 0;
      border: 1px solid #444;
      border-radius: 6px;
      background: #333;
      color: white;
      font-size: 14px;
    }

    .report-submit {
      width: 100%;
      padding: 12px;
      background: #61dafb;
      color: #1e1e1e;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: bold;
      font-size: 16px;
    }

    .report-submit:hover {
      background: #4fa8d8;
    }

    .relationship-type {
      color: #61dafb;
    }
  `;
  document.head.appendChild(style);

  // Create content
  let content = `<h3 style="margin: 0 0 8px 0; font-size: 16px;">🔍 Relationships for "${selectedText}"</h3>`;
  relationships.forEach((rel, index) => {
    content += `
      <div class="relationship-item">
        <div class="relationship-content">
          <div class="relationship-text">
            <strong>${rel.source}</strong>
            <span class="relationship-type">(${rel.relationship})</span>
            → <strong>${rel.target}</strong>
          </div>
          <button class="evidence-btn" data-index="${index}">📝 Evidence</button>
          <button class="report-btn" data-index="${index}" 
            data-source="${rel.source}" 
            data-relationship="${rel.relationship}" 
            data-target="${rel.target}">
            🔍 Report
          </button>
        </div>
        <div class="evidence-content" id="evidence-${index}">
          <strong>Evidence:</strong> ${rel.evidence} <br>
          <strong>Article ID:</strong> ${rel.articleID}
        </div>
        <div class="report-form" id="form-${index}" style="display: none; width: 100%;">
          <div class="report-form-inner">
            <div class="report-form-title">Report this relationship:</div>
            <div class="report-form-content">
              <input type="text" class="report-input" id="input-${index}" 
                placeholder="What's incorrect about this relationship?">
              <button class="report-submit" data-index="${index}">
                Submit Report
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  // Update the main container structure
  div.className = "relationship-box";
  div.innerHTML = `${content}`;

  // Function to add event listeners for report buttons
  function addReportButtonListeners() {
    div.querySelectorAll(".report-btn").forEach((button) => {
      button.addEventListener("click", function (e) {
        const index = this.dataset.index;
        const form = document.getElementById(`form-${index}`);

        // Hide all forms first
        div.querySelectorAll(".report-form").forEach((f) => {
          f.style.display = "none";
        });

        // Show current form
        if (form) {
          form.style.display = "block";
        }
      });
    });
  }

  // Function to add event listeners for evidence buttons
  function addEvidenceButtonListeners() {
    div.querySelectorAll(".evidence-btn").forEach((button) => {
      button.addEventListener("click", function (e) {
        const index = this.dataset.index;
        const evidenceContent = document.getElementById(`evidence-${index}`);

        // Toggle evidence display
        if (
          evidenceContent.style.display === "none" ||
          evidenceContent.style.display === ""
        ) {
          evidenceContent.style.display = "block";
        } else {
          evidenceContent.style.display = "none";
        }
      });
    });
  }

  // Add event listeners for report buttons
  addReportButtonListeners();
  // Add event listeners for evidence buttons
  addEvidenceButtonListeners();

  // Add event listeners for submit buttons
  div.querySelectorAll(".report-submit").forEach((button) => {
    button.addEventListener("click", function (e) {
      const index = this.dataset.index;
      const reportBtn = e.target
        .closest(".relationship-item")
        .querySelector(".report-btn");
      const source = reportBtn.dataset.source;
      const relationship = reportBtn.dataset.relationship;
      const target = reportBtn.dataset.target;
      const input = document.getElementById(`input-${index}`);
      const report = input.value.trim();

      if (report) {
        console.log("Relationship Report:", {
          source,
          relationship,
          target,
          report,
        });

        // Find the relationship in the fakeGraph and update it
        const relToUpdate = fakeGraph[source].find(
          (rel) => rel.relationship === relationship && rel.target === target
        );
        if (relToUpdate) {
          // Update the relationship with the report
          relToUpdate.report = report; // You can store the report or handle it as needed
        }

        // Replace the entire relationship item with success message
        const relItem = e.target.closest(".relationship-item");
        const originalContent = relItem.innerHTML;
        relItem.innerHTML = `
          <div class="success-message">
            ✅ Thank you for your report!
          </div>
        `;

        // Remove the success message and restore the relationship after animation
        setTimeout(() => {
          relItem.innerHTML = originalContent;
          // Reattach event listeners
          addReportButtonListeners(); // Re-add listeners for all report buttons
        }, 3000);
      }
    });
  });

  // Close overlay when clicking outside
  document.addEventListener("mousedown", function closeOverlay(e) {
    if (!div.contains(e.target)) {
      div.remove();
      document.removeEventListener("mousedown", closeOverlay);
    }
  });

  document.body.appendChild(div);
}
