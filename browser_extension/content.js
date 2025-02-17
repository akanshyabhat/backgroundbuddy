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
    }

    .relationship-title {
      font-size: 18px;
      margin: 0 0 20px 0;
      padding-bottom: 15px;
      border-bottom: 1px solid #333;
    }

    .relationship-item {
      padding: 12px;
      margin-bottom: 12px;
      border-radius: 6px;
      background: #2a2a2a;
      position: relative;
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
            <strong>${selectedText}</strong>
            <span class="relationship-type">(${rel.relationship})</span>
            → <strong>${rel.target}</strong>
          </div>
          <button class="report-btn" data-index="${index}" data-source="${selectedText}" 
            data-relationship="${rel.relationship}" data-target="${rel.target}">
            🔍 Report
          </button>
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
  document.body.appendChild(div);

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

  // Add event listeners for report buttons
  addReportButtonListeners();

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
}
