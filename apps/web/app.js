import { getStudyIdFromLocation } from "./study_id.js";

const API_BASE_URL = "http://127.0.0.1:8000";

const statusEl = document.getElementById("status");
const studySection = document.getElementById("study");
const errorSection = document.getElementById("error");
const errorMessageEl = document.getElementById("error-message");

const titleEl = document.getElementById("study-title");
const citationEl = document.getElementById("study-citation");
const outcomesListEl = document.getElementById("outcomes-list");
const resultsTableBody = document.querySelector("#results-table tbody");

function clearChildren(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

function formatCitation(citation) {
  const authors = citation.authors.join(", ");
  return `${authors} (${citation.year}). ${citation.title}. ${citation.venue}.`;
}

function renderStudy(study) {
  titleEl.textContent = study.citation.title;
  citationEl.textContent = formatCitation(study.citation);

  clearChildren(outcomesListEl);
  const outcomeKindById = new Map();

  study.outcomes.forEach((outcome) => {
    outcomeKindById.set(outcome.outcome_id, outcome.kind);

    const item = document.createElement("li");
    item.textContent = `${outcome.outcome_id}: ${outcome.label} (${outcome.kind})`;
    outcomesListEl.appendChild(item);
  });

  clearChildren(resultsTableBody);
  study.results.forEach((result) => {
    const row = document.createElement("tr");
    const outcomeKind = outcomeKindById.get(result.outcome_id) || "unknown";

    row.innerHTML = `
      <td>${result.result_id}</td>
      <td>${result.result_label}</td>
      <td>${outcomeKind}</td>
      <td>${result.effect.type} ${result.effect.value} (${result.effect.direction}, ${result.effect.provenance})</td>
      <td>${result.significance.type} ${result.significance.value} (${result.significance.provenance})</td>
      <td>${result.reliability.rating} (${result.reliability.provenance})</td>
    `;

    resultsTableBody.appendChild(row);
  });
}

async function loadStudy() {
  const studyId = getStudyIdFromLocation(window.location);
  const url = `${API_BASE_URL}/v1/studies/${studyId}`;

  statusEl.textContent = `Fetching study ${studyId}…`;

  try {
    const response = await fetch(url);
    if (response.status === 404) {
      throw new Error(`Study not found: ${studyId}`);
    }
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const study = await response.json();
    renderStudy(study);

    statusEl.hidden = true;
    errorSection.hidden = true;
    studySection.hidden = false;
  } catch (error) {
    statusEl.hidden = true;
    studySection.hidden = true;
    errorSection.hidden = false;
    errorMessageEl.textContent = `Failed to load ${url}. ${error.message}`;
  }
}

loadStudy();
