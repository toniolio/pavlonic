export function getStudyIdFromLocation(location) {
  const hash = (location.hash || "").trim();
  if (hash.startsWith("#/study/")) {
    const hashId = hash.replace("#/study/", "").trim();
    if (hashId) {
      return hashId;
    }
  }

  const searchParams = new URLSearchParams(location.search || "");
  const queryId = searchParams.get("study");
  if (queryId) {
    return queryId.trim();
  }

  return "0001";
}
