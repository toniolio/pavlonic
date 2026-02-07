function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatEffectSummary(effect) {
  if (!effect) {
    return "Not reported";
  }
  const type = effect.type || "effect";
  const value = effect.value ?? "n/a";
  const direction = effect.direction || "unknown";
  const provenance = effect.provenance || "unknown";
  return `${type} ${value} (${direction}, ${provenance})`;
}

function formatSignificanceSummary(significance) {
  if (!significance) {
    return "Not reported";
  }
  const type = significance.type || "stat";
  const value = significance.value ?? "n/a";
  const provenance = significance.provenance || "unknown";
  return `${type} ${value} (${provenance})`;
}

function formatReliabilitySummary(reliability) {
  if (!reliability) {
    return "Not assessed";
  }
  const rating = reliability.rating || "Not assessed";
  const provenance = reliability.provenance || "unknown";
  return `${rating} (${provenance})`;
}

function selectResultTarget(results, targetResultId) {
  const normalized = String(targetResultId || "").trim();
  if (!normalized) {
    return { targetId: null, targetMiss: false };
  }

  const found = results.find((result) => result.result_id === normalized);
  if (found) {
    return { targetId: normalized, targetMiss: false };
  }

  if (results.length > 0) {
    return { targetId: results[0].result_id, targetMiss: true };
  }

  return { targetId: null, targetMiss: true };
}

function renderDetailSection(title, bodyHtml) {
  return `
    <div>
      <strong>${escapeHtml(title)}</strong>
      ${bodyHtml}
    </div>
  `;
}

function renderResultDetailHtml(result, outcome) {
  const sections = [];
  const comparisonBits = [];

  if (result.result_label) {
    comparisonBits.push(result.result_label);
  }

  if (outcome && outcome.label) {
    const kind = outcome.kind ? ` (${outcome.kind})` : "";
    comparisonBits.push(`Outcome: ${outcome.label}${kind}`);
  }

  if (comparisonBits.length > 0) {
    sections.push(
      renderDetailSection(
        "What was compared",
        `<p>${escapeHtml(comparisonBits.join(" - "))}</p>`
      )
    );
  }

  if (result.result_description) {
    sections.push(
      renderDetailSection(
        "What happened",
        `<p>${escapeHtml(result.result_description)}</p>`
      )
    );
  }

  const statsLines = [];
  if (result.effect) {
    statsLines.push(`Effect: ${formatEffectSummary(result.effect)}`);
  }
  if (result.significance) {
    statsLines.push(`Significance: ${formatSignificanceSummary(result.significance)}`);
  }
  if (result.reliability) {
    statsLines.push(`Reliability: ${formatReliabilitySummary(result.reliability)}`);
  }

  if (statsLines.length > 0) {
    sections.push(
      renderDetailSection(
        "Stats & reporting",
        `<ul>${statsLines
          .map((line) => `<li>${escapeHtml(line)}</li>`)
          .join("")}</ul>`
      )
    );
  }

  if (result.notes) {
    sections.push(renderDetailSection("Notes", `<p>${escapeHtml(result.notes)}</p>`));
  }

  return sections.join("");
}

export function renderStudyResultsHtml(study, targetResultId) {
  const results = Array.isArray(study && study.results) ? study.results : [];
  const outcomes = Array.isArray(study && study.outcomes) ? study.outcomes : [];
  const outcomeById = new Map(
    outcomes.map((outcome) => [outcome.outcome_id, outcome])
  );

  const shouldTarget = Boolean(targetResultId);
  const targeting = shouldTarget
    ? selectResultTarget(results, targetResultId)
    : { targetId: null, targetMiss: false };

  const columnCount = 7;

  return results
    .map((result) => {
      const outcome = outcomeById.get(result.outcome_id) || null;
      const outcomeKind = outcome && outcome.kind ? outcome.kind : "unknown";
      const effectSummary = formatEffectSummary(result.effect);
      const significanceSummary = formatSignificanceSummary(result.significance);
      const reliabilitySummary = formatReliabilitySummary(result.reliability);
      const detailId = `result-${result.result_id}-detail`;

      const isTarget = targeting.targetId && result.result_id === targeting.targetId;
      const targetAttrs = isTarget
        ? ` data-result-targeted="true"${
            targeting.targetMiss ? " data-result-target-miss=\"true\"" : ""
          }`
        : "";

      const detailHtml = renderResultDetailHtml(result, outcome);

      return `
        <tr id="result-${escapeHtml(result.result_id)}" data-result-row="true"${targetAttrs}>
          <td>${escapeHtml(result.result_id)}</td>
          <td>${escapeHtml(result.result_label)}</td>
          <td>${escapeHtml(outcomeKind)}</td>
          <td>${escapeHtml(effectSummary)}</td>
          <td>${escapeHtml(significanceSummary)}</td>
          <td>${escapeHtml(reliabilitySummary)}</td>
          <td>
            <button
              type="button"
              data-result-toggle="true"
              aria-expanded="false"
              aria-controls="${escapeHtml(detailId)}"
            >
              Details
            </button>
          </td>
        </tr>
        <tr id="${escapeHtml(detailId)}" data-result-detail="true" hidden>
          <td colspan="${columnCount}">
            ${detailHtml}
          </td>
        </tr>
      `;
    })
    .join("");
}
