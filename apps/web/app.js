import { getRouteFromLocation } from "./study_id.js";
import { renderStudyResultsHtml } from "./results_renderer.js";

const API_BASE_URL = "http://127.0.0.1:8000";
// LOCAL DEV ONLY — DO NOT ENABLE IN HOSTED ENVIRONMENTS
const DEV_ENTITLEMENT_TOGGLE = false;
const DEV_ENTITLEMENT_STORAGE_KEY = "pavlonic_dev_entitlement_mode";

function isLocalHostname(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

const DEV_ENTITLEMENT_ENABLED =
  DEV_ENTITLEMENT_TOGGLE && isLocalHostname(window.location.hostname);
let devEntitlementMode = "public";

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

function readDevEntitlementMode() {
  try {
    const stored = window.localStorage.getItem(DEV_ENTITLEMENT_STORAGE_KEY);
    return stored === "paid" ? "paid" : "public";
  } catch (error) {
    return "public";
  }
}

function persistDevEntitlementMode(mode) {
  try {
    window.localStorage.setItem(DEV_ENTITLEMENT_STORAGE_KEY, mode);
  } catch (error) {
    // Ignore localStorage failures in local dev.
  }
}

function initDevEntitlementToggle() {
  if (!DEV_ENTITLEMENT_ENABLED) {
    return;
  }

  const devNav = document.querySelector("[data-dev-sitemap]");
  if (!devNav) {
    return;
  }

  devEntitlementMode = readDevEntitlementMode();

  const container = document.createElement("span");
  container.setAttribute("data-dev-entitlement-toggle", "true");
  container.innerHTML = `
    <span>|</span>
    <span>Mode:</span>
    <button type="button" data-dev-entitlement="public">Public</button>
    <span>|</span>
    <button type="button" data-dev-entitlement="paid">Paid</button>
    <span data-dev-entitlement-indicator></span>
  `;

  const publicButton = container.querySelector("[data-dev-entitlement='public']");
  const paidButton = container.querySelector("[data-dev-entitlement='paid']");
  const indicator = container.querySelector("[data-dev-entitlement-indicator]");

  if (!publicButton || !paidButton || !indicator) {
    return;
  }

  function updateIndicator() {
    indicator.textContent =
      devEntitlementMode === "paid" ? "DEV MODE: PAID" : "DEV MODE: PUBLIC";
    publicButton.disabled = devEntitlementMode === "public";
    paidButton.disabled = devEntitlementMode === "paid";
  }

  function applyMode(nextMode) {
    if (nextMode !== "public" && nextMode !== "paid") {
      return;
    }
    devEntitlementMode = nextMode;
    persistDevEntitlementMode(nextMode);
    updateIndicator();
    lastRouteKey = null;
    handleRouteChange();
  }

  publicButton.addEventListener("click", () => applyMode("public"));
  paidButton.addEventListener("click", () => applyMode("paid"));

  updateIndicator();
  devNav.appendChild(container);
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

function renderStudy(study, targetResultId = null) {
  titleEl.textContent = study.citation.title;
  citationEl.textContent = formatCitation(study.citation);

  clearChildren(outcomesListEl);

  study.outcomes.forEach((outcome) => {
    const item = document.createElement("li");
    item.textContent = `${outcome.outcome_id}: ${outcome.label} (${outcome.kind})`;
    outcomesListEl.appendChild(item);
  });

  resultsTableBody.innerHTML = renderStudyResultsHtml(study, targetResultId);
  wireResultToggles();
}

function wireResultToggles() {
  const toggles = resultsTableBody.querySelectorAll("[data-result-toggle='true']");
  toggles.forEach((toggle) => {
    const detailId = toggle.getAttribute("aria-controls");
    if (!detailId) {
      return;
    }
    const detailRow = document.getElementById(detailId);
    if (!detailRow) {
      return;
    }

    toggle.addEventListener("click", () => {
      const isExpanded = toggle.getAttribute("aria-expanded") === "true";
      const nextState = !isExpanded;
      toggle.setAttribute("aria-expanded", nextState ? "true" : "false");
      detailRow.hidden = !nextState;
    });
  });
}

function toDomSlug(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function buildRowDomId(tableId, rowId, index) {
  const parts = [toDomSlug(tableId), toDomSlug(rowId || `row-${index}`)].filter(Boolean);
  if (parts.length === 0) {
    return `evidence-row-${index}`;
  }
  return `evidence-${parts.join("-")}`;
}

function formatChannelLabels(channel) {
  const effectLabel = channel && channel.effect_size_label ? channel.effect_size_label : "Not computed";
  const reliabilityLabel = channel && channel.reliability_label ? channel.reliability_label : "Not assessed";
  return { effectLabel, reliabilityLabel };
}

function renderCounts(counts) {
  if (!counts || typeof counts !== "object") {
    return null;
  }

  const entries = [];
  if (counts.studies_count !== undefined) {
    entries.push(`Studies: ${counts.studies_count}`);
  }
  if (counts.subjects_total !== undefined) {
    entries.push(`Subjects: ${counts.subjects_total}`);
  }
  if (counts.meta_analyses_count !== undefined) {
    entries.push(`Meta-analyses: ${counts.meta_analyses_count}`);
  }

  if (entries.length === 0) {
    return null;
  }

  const line = document.createElement("p");
  line.textContent = entries.join(" · ");
  return line;
}

function renderReferenceList(refs, resolvedResults) {
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

      const doi = resolved.doi;
      if (doi) {
        const doiLink = document.createElement("a");
        doiLink.href = doi.startsWith("http") ? doi : `https://doi.org/${doi}`;
        doiLink.textContent = "DOI";
        item.appendChild(document.createTextNode(" "));
        item.appendChild(doiLink);
      }

      const sourceUrl = resolved.source_url;
      if (sourceUrl) {
        const sourceLink = document.createElement("a");
        sourceLink.href = sourceUrl;
        sourceLink.textContent = "Source";
        item.appendChild(document.createTextNode(" "));
        item.appendChild(sourceLink);
      }
    } else {
      item.textContent = ref;
    }
    list.appendChild(item);
  });

  return list;
}

function renderSummaryChannel(label, channel) {
  const wrapper = document.createElement("div");
  wrapper.dataset.evidenceChannel = label.toLowerCase();

  const heading = document.createElement("strong");
  heading.textContent = label;
  wrapper.appendChild(heading);

  const labels = formatChannelLabels(channel);
  const badgeLine = document.createElement("div");
  const effectBadge = document.createElement("span");
  effectBadge.textContent = labels.effectLabel;
  const reliabilityBadge = document.createElement("span");
  reliabilityBadge.textContent = labels.reliabilityLabel;
  badgeLine.appendChild(effectBadge);
  badgeLine.appendChild(document.createTextNode(" · "));
  badgeLine.appendChild(reliabilityBadge);
  wrapper.appendChild(badgeLine);

  return wrapper;
}

function renderExpandedChannel(label, channel, resolvedResults) {
  const wrapper = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = label;
  wrapper.appendChild(heading);

  const labels = formatChannelLabels(channel);
  const summary = document.createElement("p");
  summary.textContent = `${labels.effectLabel} · ${labels.reliabilityLabel}`;
  wrapper.appendChild(summary);

  const countsLine = renderCounts(channel && channel.counts ? channel.counts : null);
  if (countsLine) {
    wrapper.appendChild(countsLine);
  }

  const refs = channel && channel.refs ? channel.refs : [];
  wrapper.appendChild(renderReferenceList(refs, resolvedResults));

  return wrapper;
}

function renderEvidenceRow(row, tableId, rowIndex, resolvedResults) {
  const rowBlock = document.createElement("div");
  rowBlock.dataset.evidenceRow = "true";

  const rowDomId = buildRowDomId(tableId, row.row_id || row.row_label, rowIndex);
  const detailsId = `${rowDomId}-details`;

  const summary = document.createElement("div");
  summary.dataset.evidenceRowSummary = "true";

  const header = document.createElement("div");
  const rowHeading = document.createElement("h4");
  rowHeading.textContent = row.row_label || row.row_id || "Row";
  header.appendChild(rowHeading);

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.dataset.evidenceToggle = "true";
  toggle.setAttribute("aria-expanded", "false");
  toggle.setAttribute("aria-controls", detailsId);
  toggle.textContent = "Details";
  header.appendChild(toggle);
  summary.appendChild(header);

  if (row.summary_statement) {
    const summaryText = document.createElement("p");
    summaryText.textContent = row.summary_statement;
    summary.appendChild(summaryText);
  }

  const badgeRow = document.createElement("div");
  badgeRow.appendChild(renderSummaryChannel("Performance", row.performance));
  badgeRow.appendChild(renderSummaryChannel("Learning", row.learning));
  summary.appendChild(badgeRow);

  const expanded = document.createElement("div");
  expanded.dataset.evidenceExpanded = "true";
  expanded.id = detailsId;
  expanded.hidden = true;

  const canonicalLine = document.createElement("p");
  canonicalLine.textContent = "Canonical effect size: Not available";
  expanded.appendChild(canonicalLine);

  const provenance = document.createElement("p");
  provenance.textContent = "Provenance: not specified";
  expanded.appendChild(provenance);

  expanded.appendChild(
    renderExpandedChannel("Performance", row.performance || {}, resolvedResults)
  );
  expanded.appendChild(
    renderExpandedChannel("Learning", row.learning || {}, resolvedResults)
  );

  toggle.addEventListener("click", () => {
    const isExpanded = toggle.getAttribute("aria-expanded") === "true";
    const nextState = !isExpanded;
    toggle.setAttribute("aria-expanded", nextState ? "true" : "false");
    expanded.hidden = !nextState;
  });

  rowBlock.appendChild(summary);
  rowBlock.appendChild(expanded);
  return rowBlock;
}

function renderEvidenceTable(table, resolvedResults, index) {
  const tableSection = document.createElement("section");
  tableSection.dataset.evidenceTable = "true";

  const heading = document.createElement("h3");
  heading.textContent = table.table_label || table.table_id || "Evidence table";
  tableSection.appendChild(heading);

  const rows = table.rows || [];
  rows.forEach((row, rowIndex) => {
    const tableId = table.table_id || `table-${index}`;
    tableSection.appendChild(
      renderEvidenceRow(row, tableId, rowIndex, resolvedResults)
    );
  });

  return tableSection;
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

  tables.forEach((table, index) => {
    techniqueTablesEl.appendChild(renderEvidenceTable(table, technique.resolved_results, index));
  });
}

function scrollToResult(resultId) {
  if (!resultId) {
    return;
  }
  const targeted = document.querySelector("[data-result-targeted='true']");
  const target = targeted || document.getElementById(`result-${resultId}`);
  if (target) {
    target.scrollIntoView({ block: "start" });
    highlightResultRow(target);
  }
}

let highlightTimer = null;

function highlightResultRow(row) {
  if (!row) {
    return;
  }
  if (highlightTimer) {
    window.clearTimeout(highlightTimer);
    highlightTimer = null;
  }
  row.style.outline = "2px solid #f2b705";
  row.style.backgroundColor = "#fff8d1";
  highlightTimer = window.setTimeout(() => {
    row.style.outline = "";
    row.style.backgroundColor = "";
    highlightTimer = null;
  }, 1500);
}

function buildApiRequestOptions() {
  if (!DEV_ENTITLEMENT_ENABLED || devEntitlementMode !== "paid") {
    return {};
  }
  return {
    headers: {
      "X-Pavlonic-Entitlement": "paid",
    },
  };
}

async function fetchApi(url) {
  const options = buildApiRequestOptions();
  return fetch(url, options);
}

async function loadStudy(studyId, resultId) {
  const url = `${API_BASE_URL}/v1/studies/${studyId}`;
  statusEl.textContent = `Fetching study ${studyId}…`;
  setPageVisibility({ status: true });
  errorMessageEl.textContent = "";

  try {
    const response = await fetchApi(url);
    if (response.status === 404) {
      throw new Error(`Study not found: ${studyId}`);
    }
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const study = await response.json();
    renderStudy(study, resultId);
    lastStudyPayload = study;
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
    const response = await fetchApi(url);
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
let lastStudyPayload = null;

function handleRouteChange() {
  const route = getRouteFromLocation(window.location);
  const routeKey = `${route.page}:${route.id}`;

  if (route.page === "study") {
    if (routeKey !== lastRouteKey) {
      loadStudy(route.id, route.resultId);
    } else if (route.resultId) {
      if (lastStudyPayload) {
        renderStudy(lastStudyPayload, route.resultId);
      }
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

initDevEntitlementToggle();
handleRouteChange();
