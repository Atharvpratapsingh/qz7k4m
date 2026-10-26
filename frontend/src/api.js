// Backend ko saari calls yahan. Components kabhi khud URL nahi banate.

async function getJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`API ${path} failed with status ${res.status}`);
  }
  return res.json();
}

export function fetchDashboard(cutoff) {
  return getJson(`/api/dashboard?cutoff=${encodeURIComponent(cutoff)}`);
}

export function fetchHorizon() {
  return getJson("/api/horizon");
}