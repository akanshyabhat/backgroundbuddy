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

const fakeGraph = {
  "Jacob Frey": [
    {
      relationship: "OPPOSED_BY",
      target: "City Council Member Emily Koski",
      evidence:
        "Minneapolis City Council Member Emily Koski announced her candidacy for mayor, challenging incumbent Mayor Jacob Frey in the upcoming 2025 election.",
      articleID: "601213414",
      articleName:
        "Minneapolis Mayor Jacob Frey is running for re-election in 2025",
      relevance: 0.9,
      date: "2025-01-29",
    },
    {
      relationship: "OPPOSED_BY",
      target: "Jazz Hampton",
      evidence:
        "Jazz Hampton, an app developer and former attorney, has declared his intention to run against Mayor Jacob Frey in the 2025 Minneapolis mayoral election.",
      articleID: "601213414",
      articleName:
        "Minneapolis Mayor Jacob Frey is running for re-election in 2025",
      relevance: 0.8,
      date: "2025-01-29",
    },
    {
      relationship: "OPPOSED_BY",
      target: "Rev. DeWayne Davis",
      evidence:
        "The Rev. DeWayne Davis has announced his candidacy for the 2025 Minneapolis mayoral election, positioning himself as a challenger to incumbent Mayor Jacob Frey.",
      articleID: "601213414",
      articleName:
        "Minneapolis Mayor Jacob Frey is running for re-election in 2025",
      relevance: 0.8,
      date: "2025-01-29",
    },
    {
      relationship: "OPPOSED_BY",
      target: "State Sen. Omar Fateh",
      evidence:
        "State Senator Omar Fateh has declared his intention to run for mayor of Minneapolis in 2025, challenging incumbent Mayor Jacob Frey.",
      articleID: "601213414",
      articleName:
        "Minneapolis Mayor Jacob Frey is running for re-election in 2025",
      relevance: 0.8,
      date: "2025-01-29",
    },
    {
      relationship: "OPPOSED_BY",
      target: "Brenda Short",
      evidence:
        "Brenda Short has announced her candidacy for the 2025 Minneapolis mayoral election, joining the list of challengers to incumbent Mayor Jacob Frey.",
      articleID: "601213414",
      articleName:
        "Minneapolis Mayor Jacob Frey is running for re-election in 2025",
      relevance: 0.7,
      date: "2025-01-29",
    },
    {
      relationship: "VETOED",
      target: "2025 Minneapolis Budget",
      evidence:
        "Minneapolis Mayor Jacob Frey on Wednesday vetoed the $1.9 billion budget passed by the City Council on Tuesday night.",
      articleID: "601193824",
      articleName:
        "Minneapolis City Council passes 2025 budget after veto override",
      relevance: 0.4,
      date: "2024-12-11",
    },
    {
      relationship: "VETOED",
      target: "Labor Standards Board Ordinance",
      evidence:
        "Minneapolis Mayor Jacob Frey vetoed an ordinance Thursday creating a labor standards board made up of workers and employers that would recommend industry regulations for pay, safety, and equity.",
      articleID: "601185075",
      articleName:
        "Labor Standards Board vetoed by Mayor Frey, St. Paul leaders watching",
      relevance: 0.7,
      date: "2024-11-21",
    },
    {
      relationship: "VETOED",
      target: "Affordable Rental Housing Ordinance",
      evidence:
        "The Minneapolis City Council was unable to override Mayor Jacob Frey's recent veto of an ordinance that would give some organizations first dibs on buying certain rental housing units in an effort to preserve affordable housing.",
      articleID: "601180840",
      articleName:
        "Minneapolis council fails to override affordable Frey rental housing veto",
      relevance: 0.7,
      date: "2024-11-14",
    },
    {
      relationship: "ELECTED",
      target: "Minneapolis Mayor - Second Term",
      evidence:
        "After only two rounds of tabulation, incumbent Mayor Jacob Frey won a second term at the helm of the City of Minneapolis with a total of 70,669 votes.",
      articleID: "600053063",
      articleName:
        "How Jacob Frey won another term in ranked-choice votes, held off Kate Knuth",
      relevance: 0.9,
      date: "2021-11-02",
    },
    {
      relationship: "SUPPORTED",
      target: "Minneapolis 2040 Plan",
      evidence:
        "Mayor Jacob Frey is highlighting a major win for the Minneapolis 2040 Comprehensive Plan, which has been stuck in a years-long court battle. On Sunday night, state lawmakers passed a bill that will resolve the legal challenge under the 2040 Plan that gave rise to the lawsuit.",
      articleID: "600376164",
      articleName: "Mayor Frey Highlights Major Win for Minneapolis 2040 Plan",
      relevance: 0.9,
      date: "2024-05-20",
    },
    {
      relationship: "OPPOSED",
      target: "2021 Minneapolis Question 2",
      evidence:
        "Minneapolis Mayor Jacob Frey opposed the charter amendment to replace the Minneapolis Police Department with a Department of Public Safety.",
      articleID: "600112156",
      articleName:
        "Minneapolis voters reject plan to replace Police Department",
      relevance: 0.8,
      date: "2021-11-02",
    },
    {
      relationship: "PROPOSED",
      target: "Third Precinct Democracy Center",
      evidence:
        "Minneapolis Mayor Jacob Frey is urging the city council to proceed with his plan to repurpose the former 3rd Precinct building, abandoned since it burned during the 2020 riots following George Floyd's murder. Frey wants to transform the site into a 'democracy center' that would include the city's elections division and community space.",
      articleID: "600361110",
      articleName:
        "Minneapolis City Council declines to endorse Frey's Third Precinct plan",
      relevance: 0.7,
      date: "2024-10-15",
    },
    {
      relationship: "ELECTED_TO",
      target: "Minneapolis Mayor - Second Term",
      evidence:
        "After only two rounds of tabulation, incumbent Mayor Jacob Frey won a second term at the helm of the City of Minneapolis with a total of 70,669 votes.",
      articleID: "600053063",
      articleName:
        "How Jacob Frey won another term in ranked-choice votes, held off Kate Knuth",
      relevance: 0.9,
      date: "2021-11-02",
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
function rankRelationshipsByRelevance(paragraph, relationships) {
  return relationships
    .map((rel) => {
      const matchScore = computeRelevanceScore(paragraph, rel);
      return { ...rel, relevance: matchScore };
    })
    .sort((a, b) => b.relevance - a.relevance); // Sort descending by relevance
}

function computeRelevanceScore(paragraph, relationship) {
  const keywords = relationship.evidence.toLowerCase().split(" ");
  let score = 0;

  keywords.forEach((word) => {
    if (paragraph.toLowerCase().includes(word)) {
      score += 1;
    }
  });

  return score / keywords.length; // Normalize by total words in evidence
}
function extractEntities(text) {
  const knownEntities = Object.keys(graphData); // Get all known entities from graph
  const foundEntities = [];

  knownEntities.forEach((entity) => {
    if (text.toLowerCase().includes(entity.toLowerCase())) {
      foundEntities.push(entity);
    }
  });

  return foundEntities;
}

// Initialize graph data
initializeGraphData();

// Track active overlays to prevent duplicates
let activeOverlay = null;

// Add Lucide icons library
const lucideScript = document.createElement("script");
lucideScript.src = "https://unpkg.com/lucide@latest/dist/umd/lucide.js";
document.head.appendChild(lucideScript);

// Define icon constants using Lucide SVG strings
const ICONS = {
  SOURCE:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-link"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>',
  DETAILS:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>',
  QUOTE:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-message-square-quote"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M8 12a2 2 0 0 0 2-2V8H8v2"></path><path d="M14 12a2 2 0 0 0 2-2V8h-2v2"></path></svg>',
  REPORT:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flag"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" x2="4" y1="22" y2="15"></line></svg>',
  ADD: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-plus"><line x1="12" x2="12" y1="5" y2="19"></line><line x1="5" x2="19" y1="12" y2="12"></line></svg> ',
  CLOSE:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><line x1="18" x2="6" y1="6" y2="18"></line><line x1="6" x2="18" y1="6" y2="18"></line></svg>',
  RELEVANCE:
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-target"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
  DATE: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-calendar"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" x2="16" y1="2" y2="6"></line><line x1="8" x2="8" y1="2" y2="6"></line><line x1="3" x2="21" y1="10" y2="10"></line></svg>',
  SORT: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search"><circle cx="11" cy="11" r="8"></circle><line x1="21" x2="16.65" y1="21" y2="16.65"></line></svg>',
  HIDE: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down"><path d="m6 9 6 6 6-6"></path></svg>',
  SEND: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-send"><path d="m22 2-7 20-4-9-9-4Z"></path><path d="M22 2 11 13"></path></svg>',
};

// Helper function to add text to icons when needed
function iconWithText(icon, text) {
  return `<span style="align-items: center; display: flex; gap: 4px;">${icon} ${text}</span>`;
}

// Add CSS for Lucide icons
const iconStyle = document.createElement("style");
iconStyle.textContent = `
  .lucide {
    vertical-align: middle;
    margin-right: 4px;
  }
`;
document.head.appendChild(iconStyle);

// Define common button text combinations
const ICON_TEXT = {
  DETAILS_BTN: ICONS.DETAILS,
  REPORT_BTN: ICONS.REPORT_BTN,
  REPORT_ISSUE: ICONS.REPORT,
  CLOSE_BTN: ICONS.CLOSE,
  CLOSE_FORM: ICONS.CLOSE,
  ADD_RELATIONSHIP: ICONS.ADD,
  REPORT_TITLE: iconWithText(ICONS.REPORT, "Report this relationship:"),
  REPORT_SOMETHING: ICONS.REPORT,
  QUOTE_LABEL: iconWithText(ICONS.QUOTE, "Reference"),
  SOURCE_LABEL: iconWithText(ICONS.SOURCE, "Source URL"),
};

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

// Function to make an element draggable
function makeDraggable(element) {
  let pos1 = 0,
    pos2 = 0,
    pos3 = 0,
    pos4 = 0;

  // Get the header element to use as the drag handle
  const header = element.querySelector(".overlay-header");
  if (!header) return;

  header.style.cursor = "grab";

  header.onmousedown = dragMouseDown;

  function dragMouseDown(e) {
    e.preventDefault();
    // Get the mouse cursor position at startup
    pos3 = e.clientX;
    pos4 = e.clientY;

    // Change cursor style
    header.style.cursor = "grabbing";

    document.onmouseup = closeDragElement;
    // Call a function whenever the cursor moves
    document.onmousemove = elementDrag;
  }

  function elementDrag(e) {
    e.preventDefault();
    // Calculate the new cursor position
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;

    // Set the element's new position
    element.style.top = element.offsetTop - pos2 + "px";
    element.style.left = element.offsetLeft - pos1 + "px";
  }

  function closeDragElement() {
    // Stop moving when mouse button is released
    document.onmouseup = null;
    document.onmousemove = null;

    // Reset cursor style
    header.style.cursor = "grab";
  }
}

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

  // Style overlay - increase size to fit more content
  div.style.background = "#1e1e1e";
  div.style.color = "white";
  div.style.padding = "15px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 4px 15px rgba(0, 0, 0, 0.2)";
  div.style.zIndex = "10000";
  div.style.fontSize = "14px";
  div.style.minWidth = "400px"; // Increased from 300px
  div.style.maxWidth = "550px"; // Increased from 450px
  div.style.maxHeight = "80vh"; // Limit height to 80% of viewport
  div.style.overflowY = "auto"; // Add scrolling for overflow content

  // Add CSS for the overlay
  const style = document.createElement("style");
  style.textContent = `
    #kg-overlay {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      position: absolute;
      z-index: 10000;
    }

    .overlay-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      cursor: grab;
    }
    
    .add-button-container {
      margin-bottom: 15px;
      text-align: center;
    }
    
    .add-btn {
      background: rgba(97, 218, 251, 0.1);
      border: none;
      color: #61dafb;
      cursor: pointer;
      padding: 8px 12px;
      display: flex;
      flex-direction: row;
      align-items: center;
      font-size: 13px;
      border-radius: 4px;
      transition: all 0.2s;
      width: 100%;
    }
    
    .add-btn:hover {
      background: rgba(97, 218, 251, 0.2);
    }
    
    .form-title {
      font-size: 15px;
      font-weight: 500;
      margin-bottom: 5px;
      color: #61dafb;
    }
    
    .form-subtitle {
      font-size: 13px;
      color: #aaa;
      margin-bottom: 15px;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .relationship-inputs {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      gap: 8px;
      align-items: center;
    }
    
    .relationship-inputs select {
      min-width: 120px;
    }
    
    .sorting-controls {
      display: flex;
      justify-content: space-between;
      margin-bottom: 15px;
      padding: 8px;
      background: #2a2a2a;
      border-radius: 6px;
    }
    
    .sort-btn {
      background: none;
      border: none;
      color: #aaa;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      transition: all 0.2s;
    }
    
    .sort-btn:hover {
      color: #61dafb;
      background: rgba(97, 218, 251, 0.1);
    }

    .sort-btn.active {
      color: #61dafb;
      background: rgba(97, 218, 251, 0.1);
      font-weight: bold;
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
      padding: 8px;
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
      flex-direction: column;
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

    .source-btn:hover, .report-btn:hover {
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

    .form-input {
      width: 100%;
      padding: 8px;
      margin-bottom: 10px;
      background: #444;
      border: 1px solid #555;
      border-radius: 4px;
      color: white;
      font-size: 13px;
    }
    
    textarea.form-input {
      resize: vertical;
      min-height: 60px;
      line-height: 1.4;
    }
    
    select.form-input {
      appearance: none;
      background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23FFFFFF%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
      background-repeat: no-repeat;
      background-position: right 8px center;
      background-size: 12px;
      padding-right: 30px;
    }

    .form-submit {
      background: #61dafb;
      color: #1e1e1e;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.2s;
      width: 100%;
    }

    .form-submit:hover {
      background: #4fa8d8;
    }

    .relationship-type {
      display: inline-block;
      margin: 0 8px;
      padding: 2px 4px;
      background: rgba(97, 218, 251, 0.1);
      border-radius: 2px;
      font-size: 12px;
      color: #61dafb;
      font-weight: 500;
    }
    
    .review-badge {
      background-color: #ff9800;
      color: white;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      display: inline-block;
      margin-left: 8px;
      vertical-align: middle;
    }
    
    .recently-added-badge {
      background-color: #4caf50;
      color: white;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      display: inline-block;
      margin-left: 8px;
      vertical-align: middle;
    }
    
    .confirmation-message {
      color: #ff9800;
      padding: 8px;
      margin-top: 10px;
      background: rgba(255, 152, 0, 0.1);
      border-radius: 4px;
      text-align: center;
      font-size: 14px;
      margin-bottom: 10px;
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
    
    .meta-data {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      font-size: 11px;
      color: #aaa;
    }
    
    .meta-info {
      background: rgba(255, 255, 255, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .show-less-btn {
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
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
    }

    .show-less-btn:hover {
      background: #444;
    }
  `;
  document.head.appendChild(style);

  // Sort relationships by relevance (default)
  const sortByRelevance = (a, b) => (b.relevance || 0) - (a.relevance || 0);

  // Sort by recency (date)
  const sortByRecency = (a, b) => {
    const dateA = a.date ? new Date(a.date) : new Date(0);
    const dateB = b.date ? new Date(b.date) : new Date(0);
    return dateB - dateA;
  };

  // Default sort method
  let currentSortMethod = "relevance";
  let sortedRelationships = [...relationships].sort(sortByRelevance);

  // Create content - limit to 3 relationships by default
  const initialRelationships = sortedRelationships.slice(0, 3);
  const hasMoreRelationships = sortedRelationships.length > 3;

  let content = `
    <div class="overlay-header">
      <h3 style="margin: 0; font-size: 16px;">🔍 Relationships for "${selectedText}"</h3>
      <button class="close-btn">${ICONS.CLOSE}</button>
    </div>
    <div class="add-button-container">
      <button class="add-btn" style="justify-content: center; flex-direction: row; align-items: center;">${
        ICONS.ADD
      } <h1>Missing a relationship? Add it here</h1> </button>
       
    </div>
    <div class="add-form" id="add-form">
      <div class="form-title">Think we're missing a relationship?</div>
      <div class="form-subtitle">Help us improve by adding what you know:</div>
      <div class="form-group">
        <label>What's the relationship?</label>
        <div class="relationship-inputs">
          <input type="text" class="form-input subject-input" placeholder="e.g., Mayor Jacob Frey">
          <select class="form-input relationship-input">
            <option value="">-- Select --</option>
            <option value="VETOED">VETOED</option>
            <option value="PROPOSED">PROPOSED</option>
            <option value="SUPPORTED">SUPPORTED</option>
            <option value="OPPOSED">OPPOSED</option>
            <option value="ELECTED">ELECTED</option>
            <option value="OTHER">OTHER</option>
          </select>
          <input type="text" class="form-input target-input" placeholder="e.g., Affordable Housing Bill">
        </div>
      </div>
      <div class="form-group">
        <label>${ICON_TEXT.QUOTE_LABEL}</label>
        <textarea class="form-input quote-input" placeholder="e.g., 'Mayor Frey vetoed the affordable housing bill, citing concerns about implementation costs.' - from Star Tribune article" rows="3"></textarea>
      </div>
      <div class="form-group">
        <label>${ICON_TEXT.SOURCE_LABEL}</label>
        <input type="text" class="form-input url-input" placeholder="e.g., https://startribune.com/article/12345">
      </div>
      <button class="form-submit add-submit">${
        ICONS.SEND
      } Send Relationship</button>
    </div>
    <div class="sorting-controls" style="align-items: center; flex-direction: row; display: flex; gap: 4px;">
      <div style="align-items: center; flex-direction: row; display: flex; gap: 4px;" >
        <span style="font-size: 12px; color: #aaa;"> Sort by:</span>
          <button class="sort-btn active" style="align-items: center; display: flex; gap: 4px;" data-sort="relevance">${
            ICONS.RELEVANCE
          } Relevance</button>
          <button class="sort-btn" style="align-items: center; display: flex; gap: 4px;" data-sort="recency">${
            ICONS.DATE
          } Recency</button>
      </div>
      <div>
        <span style="font-size: 12px; color: #aaa;"> Showing ${
          relationships.length > 3 ? "top 3" : "all"
        } of ${relationships.length}</span>
      </div>
    </div>
    <div class="relationships-container">
  `;

  // Add the first 3 relationships
  initialRelationships.forEach((rel, index) => {
    // Convert article ID to a URL (in a real implementation, you'd use your actual URL pattern)
    const articleUrl = `https://startribune.com/search/${rel.articleID}`;

    // Add "Recently Added" badge to the first relationship
    const recentlyAddedBadge =
      index === null
        ? `<div class="recently-added-badge">Recently Added</div>`
        : "";

    // Add relevance and date info
    const relevanceInfo = rel.relevance
      ? `<div class="meta-info">${ICONS.RELEVANCE} ${(
          rel.relevance * 100
        ).toFixed(0)}%</div>`
      : "";
    const dateInfo = rel.date
      ? `<div class="meta-info">Published: ${new Date(
          rel.date
        ).toLocaleDateString()}</div>`
      : "";

    content += createRelationshipItem(rel, index, articleUrl, true);
  });

  // Add "Show More" button if there are more than 3 relationships
  if (hasMoreRelationships) {
    content += `
      <button class="show-more-btn">Show More Relationships</button>
    `;
  }

  content += `</div>`;

  // Create the overlay div and set its content
  div.innerHTML = content;
  document.body.appendChild(div); // Add div to document first

  // Make the overlay draggable
  makeDraggable(div); // Then make it draggable

  // Add event listeners for sort buttons
  div.querySelectorAll(".sort-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const sortType = this.dataset.sort;

      // Skip if already using this sort method
      if (sortType === currentSortMethod) return;

      // Update active button
      div
        .querySelectorAll(".sort-btn")
        .forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");

      // Update sort method
      currentSortMethod = sortType;

      // Sort relationships
      if (sortType === "relevance") {
        sortedRelationships = [...relationships].sort(sortByRelevance);
      } else if (sortType === "recency") {
        sortedRelationships = [...relationships].sort(sortByRecency);
      }

      // Update displayed relationships
      const relationshipsContainer = div.querySelector(
        ".relationships-container"
      );

      // Clear current relationships
      while (relationshipsContainer.firstChild) {
        if (
          relationshipsContainer.firstChild.classList &&
          relationshipsContainer.firstChild.classList.contains("show-more-btn")
        ) {
          break;
        }
        relationshipsContainer.removeChild(relationshipsContainer.firstChild);
      }

      // Add newly sorted relationships
      const newTopRelationships = sortedRelationships.slice(0, 3);

      newTopRelationships.forEach((rel, index) => {
        // Convert article ID to a URL
        const articleUrl = `https://startribune.com/search/${rel.articleID}`;

        // Add relevance and date info
        const relevanceInfo = rel.relevance
          ? `<div class="meta-info">${ICONS.RELEVANCE} ${(
              rel.relevance * 100
            ).toFixed(0)}%</div>`
          : "";
        const dateInfo = rel.date
          ? `<div class="meta-info">Published: ${new Date(
              rel.date
            ).toLocaleDateString()}</div>`
          : "";

        const relationshipItem = document.createElement("div");
        relationshipItem.className = "relationship-item";
        relationshipItem.dataset.index = index;

        relationshipItem.innerHTML = createRelationshipItem(
          rel,
          index,
          articleUrl,
          true
        );

        // Insert at the beginning of the container (before the Show More button if it exists)
        const showMoreBtn =
          relationshipsContainer.querySelector(".show-more-btn");
        if (showMoreBtn) {
          relationshipsContainer.insertBefore(relationshipItem, showMoreBtn);
        } else {
          relationshipsContainer.appendChild(relationshipItem);
        }
      });

      // Re-add event listeners for the new buttons
      addEventListenersToRelationshipItems(div);
    });
  });

  // Function to add event listeners to relationship items
  function addEventListenersToRelationshipItems(container) {
    // Add event listeners for source buttons
    container.querySelectorAll(".source-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const index = this.dataset.index;
        const sourceContent = document.getElementById(`source-${index}`);

        if (sourceContent.style.display === "block") {
          sourceContent.style.display = "none";
          this.innerHTML = ICON_TEXT.CLOSE_BTN;
        } else {
          // Hide all other forms first
          container
            .querySelectorAll(".report-form, .add-form, .source-content")
            .forEach((el) => {
              if (el.id !== `source-${index}`) {
                el.style.display = "none";
              }
            });

          // Reset button text
          container.querySelectorAll(".source-btn").forEach((btn) => {
            btn.innerHTML = ICON_TEXT.DETAILS_BTN;
          });

          // Reset report button text
          container.querySelectorAll(".report-btn").forEach((btn) => {
            btn.innerHTML = ICON_TEXT.REPORT_ISSUE;
          });

          sourceContent.style.display = "block";
          this.innerHTML = ICON_TEXT.CLOSE_BTN;
        }
      });
    });

    // Add event listeners for report buttons
    container.querySelectorAll(".report-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const index = this.dataset.index;
        const reportForm = document.getElementById(`report-form-${index}`);

        if (reportForm.style.display === "block") {
          reportForm.style.display = "none";
          this.innerHTML = ICON_TEXT.CLOSE_BTN;
        } else {
          // Hide all other forms first
          container
            .querySelectorAll(".report-form, .add-form, .source-content")
            .forEach((el) => {
              if (el.id !== `report-form-${index}`) {
                el.style.display = "none";
              }
            });

          // Reset button text
          container.querySelectorAll(".source-btn").forEach((btn) => {
            btn.innerHTML = ICON_TEXT.DETAILS_BTN;
          });

          // Reset other report button text
          container.querySelectorAll(".report-btn").forEach((btn) => {
            btn.innerHTML = ICON_TEXT.REPORT_ISSUE;
          });

          reportForm.style.display = "block";
          this.innerHTML = ICON_TEXT.CLOSE_BTN;
        }
      });
    });

    // Add event listeners for report submit buttons
    container.querySelectorAll(".report-submit").forEach((button) => {
      button.addEventListener("click", function () {
        const index = this.dataset.index;
        const reportForm = document.getElementById(`report-form-${index}`);
        const relationshipItem = reportForm.closest(".relationship-item");

        // Close the form
        reportForm.style.display = "none";

        // Mark the relationship as under review
        const relationshipText =
          relationshipItem.querySelector(".relationship-text");

        // Add "Under Review" badge if it doesn't exist already
        if (!relationshipItem.querySelector(".review-badge")) {
          const reviewBadge = document.createElement("div");
          reviewBadge.className = "review-badge";
          reviewBadge.textContent = "Under Review";
          reviewBadge.style.cssText = `
            background-color: #ff9800;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
            margin-left: 8px;
            vertical-align: middle;
          `;
          relationshipText.appendChild(reviewBadge);
        }

        // Show confirmation message
        const confirmationMsg = document.createElement("div");
        confirmationMsg.className = "confirmation-message";
        confirmationMsg.textContent =
          "Report sent. Relationship is under review.";
        confirmationMsg.style.cssText = `
          color: #ff9800;
          padding: 8px;
          margin-top: 10px;
          background: rgba(255, 152, 0, 0.1);
          border-radius: 4px;
          text-align: center;
          font-size: 14px;
        `;
        relationshipItem.appendChild(confirmationMsg);

        // Remove confirmation message after 3 seconds
        setTimeout(() => {
          confirmationMsg.remove();
        }, 3000);
      });
    });
  }

  // Initialize event listeners
  addEventListenersToRelationshipItems(div);

  // Add event listeners for close button
  div.querySelector(".close-btn").addEventListener("click", () => {
    div.remove();
    activeOverlay = null;
  });

  // Add event listeners for add relationship buttons
  div.querySelectorAll(".add-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const addForm = document.getElementById("add-form");

      if (!addForm) return;

      // Toggle add form
      if (addForm.style.display === "block") {
        addForm.style.display = "none";
        this.innerHTML = ICON_TEXT.ADD_RELATIONSHIP;
      } else {
        // Hide all other forms first
        div
          .querySelectorAll(".report-form, .add-form, .source-content")
          .forEach((el) => {
            if (el.id !== "add-form") {
              el.style.display = "none";
            }
          });

        // Reset button text
        div.querySelectorAll(".source-btn").forEach((btn) => {
          btn.innerHTML = ICON_TEXT.DETAILS_BTN;
        });

        // Reset report button text
        div.querySelectorAll(".report-btn").forEach((btn) => {
          btn.innerHTML = ICON_TEXT.REPORT_ISSUE;
        });

        addForm.style.display = "block";
        this.innerHTML = ICON_TEXT.CLOSE_FORM;
      }
    });
  });

  // Add event listener for add relationship submit buttons
  div.querySelectorAll(".add-submit").forEach((button) => {
    button.addEventListener("click", function () {
      const form = this.closest(".add-form");
      const subjectInput = form.querySelector(".subject-input");
      const relationshipInput = form.querySelector(".relationship-input");
      const targetInput = form.querySelector(".target-input");
      const quoteInput = form.querySelector(".quote-input");
      const urlInput = form.querySelector(".url-input");

      // Validate inputs
      if (
        !subjectInput.value ||
        !relationshipInput.value ||
        !targetInput.value
      ) {
        alert("Please fill in all required fields");
        return;
      }

      // Create new relationship object
      const newRelationship = {
        source: subjectInput.value,
        relationship: relationshipInput.value,
        target: targetInput.value,
        evidence: quoteInput.value,
        articleID: urlInput.value || window.location.href,
        confidence: 1.0,
        // Add relevance and date for sorting
        relevance: 1.0, // High relevance for user-added relationships
        date: new Date().toISOString().split("T")[0], // Today's date
      };

      try {
        // Clear form
        subjectInput.value = "";
        relationshipInput.value = "";
        targetInput.value = "";
        quoteInput.value = "";
        urlInput.value = "";

        // Hide form
        form.style.display = "none";

        // Reset add button text
        const addBtn = div.querySelector(".add-btn");
        if (addBtn) {
          addBtn.innerHTML = ICON_TEXT.ADD_RELATIONSHIP;
        }

        // Add the new relationship to the display
        const relationshipsContainer = div.querySelector(
          ".relationships-container"
        );
        const newRelationshipItem = document.createElement("div");
        newRelationshipItem.className = "relationship-item";

        // Generate a unique index for this new item
        const newIndex = Date.now().toString();

        // Add relevance and date info
        const relevanceInfo = `<div class="meta-info">${ICONS.RELEVANCE} 100%</div>`;
        const dateInfo = `<div class="meta-info">${
          ICONS.DATE
        } ${new Date().toLocaleDateString()}</div>`;

        newRelationshipItem.innerHTML = createRelationshipItem(
          newRelationship,
          newIndex,
          newRelationship.articleID,
          true
        );

        // Add with a highlight effect
        newRelationshipItem.style.animation = "highlight 2s";

        // Insert at the beginning of the container (before any other relationships)
        if (relationshipsContainer.firstChild) {
          relationshipsContainer.insertBefore(
            newRelationshipItem,
            relationshipsContainer.firstChild
          );
        } else {
          relationshipsContainer.appendChild(newRelationshipItem);
        }

        // Show success message
        const successMsg = document.createElement("div");
        successMsg.className = "success-message";
        successMsg.textContent = "Relationship added successfully!";
        successMsg.style.cssText = `
          color: #4caf50;
          padding: 8px;
          margin-top: 10px;
          background: rgba(76, 175, 80, 0.1);
          border-radius: 4px;
          text-align: center;
          font-size: 14px;
        `;
        div.querySelector(".add-button-container").appendChild(successMsg);

        // Remove success message after 3 seconds
        setTimeout(() => {
          successMsg.remove();
        }, 3000);

        // Add event listeners to the new buttons
        const sourceBtn = newRelationshipItem.querySelector(".source-btn");
        const reportBtn = newRelationshipItem.querySelector(".report-btn");
        const reportSubmitBtn =
          newRelationshipItem.querySelector(".report-submit");

        sourceBtn.addEventListener("click", function () {
          const sourceContent = document.getElementById(`source-${newIndex}`);
          if (sourceContent.style.display === "block") {
            sourceContent.style.display = "none";
            this.innerHTML = ICON_TEXT.DETAILS_BTN;
          } else {
            // Hide all other forms first
            div
              .querySelectorAll(".report-form, .add-form, .source-content")
              .forEach((el) => {
                if (el.id !== `source-${newIndex}`) {
                  el.style.display = "none";
                }
              });

            // Reset button text
            div.querySelectorAll(".source-btn").forEach((btn) => {
              btn.innerHTML = ICON_TEXT.DETAILS_BTN;
            });

            // Reset report button text
            div.querySelectorAll(".report-btn").forEach((btn) => {
              btn.innerHTML = ICON_TEXT.REPORT_ISSUE;
            });

            sourceContent.style.display = "block";
            this.innerHTML = ICON_TEXT.CLOSE_BTN;
          }
        });

        reportBtn.addEventListener("click", function () {
          const reportForm = document.getElementById(`report-form-${newIndex}`);
          if (reportForm.style.display === "block") {
            reportForm.style.display = "none";
            this.innerHTML = ICON_TEXT.REPORT_ISSUE;
          } else {
            // Hide all other forms first
            div
              .querySelectorAll(".report-form, .add-form, .source-content")
              .forEach((el) => {
                if (el.id !== `report-form-${newIndex}`) {
                  el.style.display = "none";
                }
              });

            // Reset button text
            div.querySelectorAll(".source-btn").forEach((btn) => {
              btn.innerHTML = ICON_TEXT.DETAILS_BTN;
            });

            // Reset other report button text
            div.querySelectorAll(".report-btn").forEach((btn) => {
              btn.innerHTML = ICON_TEXT.REPORT_ISSUE;
            });

            reportForm.style.display = "block";
            this.innerHTML = ICON_TEXT.CLOSE_BTN;
          }
        });

        // Add event listener for the report submit button
        reportSubmitBtn.addEventListener("click", function () {
          const reportIndex = this.dataset.index;
          const reportForm = document.getElementById(
            `report-form-${reportIndex}`
          );
          const relationshipItem = reportForm.closest(".relationship-item");

          // Close the form
          reportForm.style.display = "none";

          // Reset report button text
          const reportBtn = relationshipItem.querySelector(".report-btn");
          if (reportBtn) {
            reportBtn.innerHTML = ICON_TEXT.REPORT_ISSUE;
          }

          // Mark the relationship as under review
          const relationshipText =
            relationshipItem.querySelector(".relationship-text");

          // Add "Under Review" badge if it doesn't exist already
          if (!relationshipItem.querySelector(".review-badge")) {
            const reviewBadge = document.createElement("div");
            reviewBadge.className = "review-badge";
            reviewBadge.textContent = "Under Review";
            reviewBadge.style.cssText = `
              background-color: #ff9800;
              color: white;
              padding: 2px 6px;
              border-radius: 4px;
              font-size: 11px;
              font-weight: bold;
              display: inline-block;
              margin-left: 8px;
              vertical-align: middle;
            `;
            relationshipText.appendChild(reviewBadge);
          }

          // Show confirmation message
          const confirmationMsg = document.createElement("div");
          confirmationMsg.className = "confirmation-message";
          confirmationMsg.textContent =
            "Report sent. Relationship is under review.";
          confirmationMsg.style.cssText = `
            color: #ff9800;
            padding: 8px;
            margin-top: 10px;
            background: rgba(255, 152, 0, 0.1);
            border-radius: 4px;
            text-align: center;
            font-size: 14px;
          `;
          relationshipItem.appendChild(confirmationMsg);

          // Remove confirmation message after 3 seconds
          setTimeout(() => {
            confirmationMsg.remove();
          }, 3000);
        });

        // Add highlight animation to CSS
        const style = document.createElement("style");
        style.textContent = `
          @keyframes highlight {
            0% { background-color: #61dafb33; }
            100% { background-color: #2a2a2a; }
          }
        `;
        document.head.appendChild(style);

        // Show success message
        // ... existing code ...

        // Add the new relationship to the sortedRelationships array
        sortedRelationships.unshift(newRelationship);

        // Update the count in the sorting controls
        const countSpan = div.querySelector(
          ".sorting-controls div:last-child span"
        );
        if (countSpan) {
          countSpan.textContent = `Relationships for ${sortedRelationships.length}`;
        }
      } catch (error) {
        console.error("Error adding relationship:", error);
        alert("Failed to add relationship. Please try again.");
      }
    });
  });

  // Add event listener for "Show More" button
  const showMoreBtn = div.querySelector(".show-more-btn");
  if (showMoreBtn) {
    showMoreBtn.addEventListener("click", function () {
      // Get the remaining relationships based on current sort
      const remainingRelationships = sortedRelationships.slice(3);
      const relationshipsContainer = div.querySelector(
        ".relationships-container"
      );

      // Remove the "Show More" button
      this.remove();

      // Add the remaining relationships
      remainingRelationships.forEach((rel, idx) => {
        // Convert article ID to a URL
        const articleUrl = `https://startribune.com/search/${rel.articleID}`;

        // Real index is offset by the initial 3 relationships
        const index = idx + 3;

        // Add relevance and date info
        const relevanceInfo = rel.relevance
          ? `<div class="meta-info">${ICONS.RELEVANCE} ${(
              rel.relevance * 100
            ).toFixed(0)}%</div>`
          : "";
        const dateInfo = rel.date
          ? `<div class="meta-info">Published: ${new Date(
              rel.date
            ).toLocaleDateString()}</div>`
          : "";

        const relationshipItem = document.createElement("div");
        relationshipItem.className = "relationship-item";
        relationshipItem.dataset.index = index;

        relationshipItem.innerHTML = createRelationshipItem(
          rel,
          index,
          articleUrl,
          true
        );

        relationshipsContainer.appendChild(relationshipItem);
      });

      // Add "Show Less" button
      const showLessBtn = document.createElement("button");
      showLessBtn.className = "show-less-btn";
      showLessBtn.innerHTML = `${ICONS.HIDE} Show Less`;
      relationshipsContainer.appendChild(showLessBtn);

      // Update the count in the sorting controls
      const countSpan = div.querySelector(
        ".sorting-controls div:last-child span"
      );
      if (countSpan) {
        countSpan.textContent = `Showing all ${sortedRelationships.length} relationships`;
      }

      // Add event listener to Show Less button
      showLessBtn.addEventListener("click", function () {
        // Remove all but the first 3 relationships
        const items =
          relationshipsContainer.querySelectorAll(".relationship-item");
        items.forEach((item, idx) => {
          if (idx >= 3) {
            item.remove();
          }
        });

        // Remove the Show Less button
        this.remove();

        // Add back the Show More button
        const showMoreBtn = document.createElement("button");
        showMoreBtn.className = "show-more-btn";
        showMoreBtn.innerHTML = "Show More Relationships";
        relationshipsContainer.appendChild(showMoreBtn);

        // Update the count text
        if (countSpan) {
          countSpan.textContent = `Showing top 3 of ${sortedRelationships.length}`;
        }

        // Re-add event listener to new Show More button
        showMoreBtn.addEventListener(
          "click",
          this.parentElement.querySelector(".show-more-btn").onclick
        );
      });

      // Add event listeners to the new items
      addEventListenersToRelationshipItems(div);
    });
  }

  // Set a timeout to remove "Recently Added" badges after 30 seconds
  setTimeout(() => {
    const recentlyAddedBadges = div.querySelectorAll(".recently-added-badge");
    recentlyAddedBadges.forEach((badge) => {
      // Fade out animation
      badge.style.transition = "opacity 1s";
      badge.style.opacity = "0";

      // Remove after animation completes
      setTimeout(() => {
        badge.remove();
      }, 1000);
    });
  }, 30000); // 30 seconds

  // Close overlay when clicking outside
  document.addEventListener("mousedown", function closeOverlay(e) {
    if (activeOverlay && !activeOverlay.contains(e.target)) {
      activeOverlay.remove();
      activeOverlay = null;
      document.removeEventListener("mousedown", closeOverlay);
    }
  });
}

// Update the relationship item template to use the new icon text constants
function createRelationshipItem(rel, index, articleUrl, showRelevance = true) {
  const formattedDate = rel.date
    ? new Date(rel.date).toLocaleDateString()
    : new Date().toLocaleDateString();

  const recentlyAddedBadge = rel.recentlyAdded
    ? '<div class="recently-added-badge">Recently Added by You</div>'
    : "";

  const relevanceInfo =
    showRelevance && rel.relevance
      ? `<div class="meta-info">${ICONS.RELEVANCE} ${(
          rel.relevance * 100
        ).toFixed(0)}%</div>`
      : "";

  const dateInfo = `<div class="meta-info" style="display: flex; align-items: center; gap: 4px;">${ICONS.DATE} Published: ${formattedDate}</div>`;

  return `
    <div class="relationship-item" data-index="${index}">
      <div class="relationship-content">
        <div class="relationship-text">
          <strong>${rel.source || ""}</strong>
          <span class="relationship-type">${rel.relationship}</span>
          <strong>${rel.target || ""}</strong>
          ${recentlyAddedBadge}
        </div>
        <div class="meta-data">
          ${dateInfo}
        </div>
      </div>
      <div class="action-buttons">
        <button class="source-btn" data-index="${index}">${
    ICON_TEXT.DETAILS_BTN
  }</button>
        <button class="report-btn" data-index="${index}">${
    ICON_TEXT.REPORT_ISSUE
  }</button>
      </div>
      <div class="source-content" id="source-${index}" style="display: none;">
        <p style=" align-items: center; display: flex; gap: 4px;"><strong>${
          ICONS.QUOTE
        }</strong> "${rel.evidence || "No supporting quote provided."}"</p>
        <p style=" align-items: center; display: flex; gap: 4px;"><strong>${
          ICONS.SOURCE
        }</strong> <a href="${articleUrl}" target="_blank" class="article-link" >${
    rel.articleID ? `${rel.articleName}` : "Source Link"
  }</a></p>
      </div>
      <div class="report-form" id="report-form-${index}" style="display: none;">
        <div class="form-title">${ICON_TEXT.REPORT_TITLE}</div>
        <textarea class="form-input" placeholder="What's incorrect about this relationship?" rows="3"></textarea>
        <button class="form-submit report-submit" data-index="${index}">Submit Report</button>
      </div>
    </div>
  `;
}
