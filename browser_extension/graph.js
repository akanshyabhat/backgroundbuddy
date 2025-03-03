// The goal is to replace this with the real graph shown in Neo4j
export const fakeGraph = {
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
