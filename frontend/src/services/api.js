// En production, VITE_API_URL pointe vers le backend Railway (ex: https://xxx.railway.app/api)
// En développement, le proxy Vite redirige /api vers localhost:8000
const BASE_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * Récupère les biens immobiliers avec filtres.
 * @param {Object} filters
 */
export async function fetchProperties(filters = {}) {
  const params = new URLSearchParams();

  if (filters.minPrice != null) params.set("min_price", filters.minPrice);
  if (filters.maxPrice != null) params.set("max_price", filters.maxPrice);
  if (filters.minSurface != null) params.set("min_surface", filters.minSurface);
  if (filters.maxSurface != null) params.set("max_surface", filters.maxSurface);
  if (filters.minExterior != null) params.set("min_exterior", filters.minExterior);
  if (filters.maxExterior != null) params.set("max_exterior", filters.maxExterior);
  if (filters.maxTrainWalk != null) params.set("max_train_walk", filters.maxTrainWalk);
  if (filters.maxBusWalk != null) params.set("max_bus_walk", filters.maxBusWalk);
  if (filters.maxTramWalk != null) params.set("max_tram_walk", filters.maxTramWalk);
  if (filters.department && filters.department !== "all") params.set("department", filters.department);
  if (filters.propertyType) params.set("property_type", filters.propertyType);
  if (filters.source) params.set("source", filters.source);
  params.set("page", filters.page || 1);
  params.set("limit", filters.limit || 200);

  const resp = await fetch(`${BASE_URL}/properties?${params}`);
  if (!resp.ok) throw new Error(`Erreur API: ${resp.status}`);
  return resp.json();
}

/**
 * Déclenche un scraping.
 * @param {string} source - "all" | "leboncoin" | "pap"
 */
export async function startScrape(source = "all") {
  const resp = await fetch(`${BASE_URL}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  if (!resp.ok) throw new Error(`Erreur scrape: ${resp.status}`);
  return resp.json();
}

/**
 * Récupère le statut du job de scraping en cours.
 */
export async function fetchScrapeStatus() {
  const resp = await fetch(`${BASE_URL}/scrape/status`);
  if (!resp.ok) throw new Error(`Erreur status: ${resp.status}`);
  return resp.json();
}

/**
 * Récupère les statistiques globales.
 */
export async function fetchStats() {
  const resp = await fetch(`${BASE_URL}/properties/stats/summary`);
  if (!resp.ok) throw new Error(`Erreur stats: ${resp.status}`);
  return resp.json();
}
