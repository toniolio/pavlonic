const DEFAULT_STUDY_ID = "0001";

function parseHashRoute(hash) {
  const trimmed = (hash || "").trim();
  if (!trimmed.startsWith("#")) {
    return null;
  }

  const raw = trimmed.slice(1);
  if (!raw) {
    return null;
  }

  const [pathPart, queryPart] = raw.split("?");
  const normalizedPath = pathPart.startsWith("/") ? pathPart : `/${pathPart}`;
  const params = new URLSearchParams(queryPart || "");
  const resultId = (params.get("result") || "").trim() || null;

  if (normalizedPath.startsWith("/techniques/")) {
    const slug = normalizedPath.replace("/techniques/", "").trim();
    if (slug) {
      return { page: "technique", id: slug, resultId: null };
    }
  }

  if (normalizedPath.startsWith("/studies/")) {
    const studyId = normalizedPath.replace("/studies/", "").trim();
    if (studyId) {
      return { page: "study", id: studyId, resultId };
    }
  }

  if (normalizedPath.startsWith("/study/")) {
    const legacyId = normalizedPath.replace("/study/", "").trim();
    if (legacyId) {
      return { page: "study", id: legacyId, resultId };
    }
  }

  return null;
}

export function getRouteFromLocation(location) {
  const hashRoute = parseHashRoute(location.hash);
  if (hashRoute) {
    return hashRoute;
  }

  const searchParams = new URLSearchParams(location.search || "");
  const queryId = (searchParams.get("study") || "").trim();
  if (queryId) {
    return { page: "study", id: queryId, resultId: null };
  }

  return { page: "study", id: DEFAULT_STUDY_ID, resultId: null };
}

export function getStudyIdFromLocation(location) {
  const route = getRouteFromLocation(location);
  if (route.page === "study") {
    return route.id;
  }
  return DEFAULT_STUDY_ID;
}
