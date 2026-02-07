import { getRouteFromLocation } from "./study_id.js";

const API_BASE_URL = "http://127.0.0.1:8000";

const statusEl = document.getElementById("status");
const studySection = document.getElementById("study");
const techniqueSection = document.getElementById("technique");
const errorSection = document.getElementById("error");
const errorMessageEl = document.getElementById("error-message");

const breadcrumbCurrentEl = document.getElementById("breadcrumb-current");

const titleEl = document.getElementById("study-title");
const citationEl = document.getElementById("study-citation");
const outcomesListEl = document.getElementById("outcomes-list");
const resultsTableBody = document.querySelector("#results-table tbody");

const techniqueTitleEl = document.getElementById("technique-title");
const techniqueSummaryEl = document.getElementById("technique-summary");
const techniqueTablesEl = document.getElementById("technique-tables");

function setPageVisibility({ status = false, study = false, technique = false, error = false } = {}) {
  statusEl.hidden = !status;
  studySection.hidden = !study;
  techniqueSection.hidden = !technique;
  errorSection.hidden = !error;
}

function clearChildren(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

function updateBreadcrumb(route, payload) {
  if (!breadcrumbCurrentEl) {
    return;
  }

  if (route.page === "study") {
    breadcrumbCurrentEl.textContent = `Study ${route.id}`;
    return;
  }

  if (route.page === "technique") {
    const label = payload && payload.title ? payload.title : route.id;
    breadcrumbCurrentEl.textContent = `Technique ${label}`;
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
    row.id = `result-${result.result_id}`;

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

function renderRefs(refs, resolvedResults) {
  const list = document.createElement("ul");
  if (!refs || refs.length === 0) {
    const item = document.createElement("li");
    item.textContent = "No references.";
    list.appendChild(item);
    return list;
  }

  refs.forEach((ref) => {
    const item = document.createElement("li");
    const resolved = resolvedResults ? resolvedResults[ref] : null;
    if (resolved) {
      const link = document.createElement("a");
      link.href =
        resolved.internal_link || `#/studies/${resolved.study_id}?result=${resolved.result_id}`;
      link.textContent = ref;
      item.appendChild(link);
    } else {
      item.textContent = ref;
    }
    list.appendChild(item);
  });

  return list;
}

function renderChannel(label, channel, resolvedResults) {
  const wrapper = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = label;
  wrapper.appendChild(heading);

  const effectLabel = channel && channel.effect_size_label ? channel.effect_size_label : "";
  const reliabilityLabel = channel && channel.reliability_label ? channel.reliability_label : "";
  const summary = document.createElement("p");
  summary.textContent = [effectLabel, reliabilityLabel].filter(Boolean).join(" · ");
  wrapper.appendChild(summary);

  const refs = channel && channel.refs ? channel.refs : [];
  wrapper.appendChild(renderRefs(refs, resolvedResults));

  return wrapper;
}

function renderTechnique(technique) {
  techniqueTitleEl.textContent = technique.title;
  techniqueSummaryEl.textContent = technique.summary;

  clearChildren(techniqueTablesEl);

  const tables = technique.tables || [];
  if (tables.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No evidence tables available.";
    techniqueTablesEl.appendChild(empty);
    return;
  }

  tables.forEach((table) => {
    const tableSection = document.createElement("section");
    const heading = document.createElement("h3");
    heading.textContent = table.table_label || table.table_id || "Evidence table";
    tableSection.appendChild(heading);

    const rows = table.rows || [];
    rows.forEach((row) => {
      const rowBlock = document.createElement("div");
      const rowHeading = document.createElement("h4");
      rowHeading.textContent = row.row_label || row.row_id || "Row";
      rowBlock.appendChild(rowHeading);

      if (row.summary_statement) {
        const summary = document.createElement("p");
        summary.textContent = row.summary_statement;
        rowBlock.appendChild(summary);
      }

      rowBlock.appendChild(renderChannel("Performance", row.performance, technique.resolved_results));
      rowBlock.appendChild(renderChannel("Learning", row.learning, technique.resolved_results));
      tableSection.appendChild(rowBlock);
    });

    techniqueTablesEl.appendChild(tableSection);
  });
}

function scrollToResult(resultId) {
  if (!resultId) {
    return;
  }
  const target = document.getElementById(`result-${resultId}`);
  if (target) {
    target.scrollIntoView({ block: "start" });
  }
}

async function loadStudy(studyId, resultId) {
  const url = `${API_BASE_URL}/v1/studies/${studyId}`;
  statusEl.textContent = `Fetching study ${studyId}…`;
  setPageVisibility({ status: true });
  errorMessageEl.textContent = "";

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
    updateBreadcrumb({ page: "study", id: studyId }, study);

    setPageVisibility({ study: true });
    scrollToResult(resultId);
  } catch (error) {
    setPageVisibility({ error: true });
    errorMessageEl.textContent = `Failed to load ${url}. ${error.message}`;
  }
}

async function loadTechnique(slug) {
  const url = `${API_BASE_URL}/v1/techniques/${slug}`;
  statusEl.textContent = `Fetching technique ${slug}…`;
  setPageVisibility({ status: true });
  errorMessageEl.textContent = "";

  try {
    const response = await fetch(url);
    if (response.status === 404) {
      throw new Error(`Technique not found: ${slug}`);
    }
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const technique = await response.json();
    renderTechnique(technique);
    updateBreadcrumb({ page: "technique", id: slug }, technique);

    setPageVisibility({ technique: true });
  } catch (error) {
    setPageVisibility({ error: true });
    errorMessageEl.textContent = `Failed to load ${url}. ${error.message}`;
  }
}

let lastRouteKey = null;

function handleRouteChange() {
  const route = getRouteFromLocation(window.location);
  const routeKey = `${route.page}:${route.id}`;

  if (route.page === "study") {
    if (routeKey !== lastRouteKey) {
      loadStudy(route.id, route.resultId);
    } else if (route.resultId) {
      scrollToResult(route.resultId);
    }
  }

  if (route.page === "technique" && routeKey !== lastRouteKey) {
    loadTechnique(route.id);
  }

  lastRouteKey = routeKey;
}

window.addEventListener("hashchange", handleRouteChange);
window.addEventListener("popstate", handleRouteChange);

handleRouteChange();
