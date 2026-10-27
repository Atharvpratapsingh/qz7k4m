// Backend ka base URL.
// Laptop pe khali hota hai (Vite proxy sambhalta hai).
// Vercel pe VITE_API_BASE environment variable mein backend ka link hota hai.
const API_BASE = import.meta.env.VITE_API_BASE || "";

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
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