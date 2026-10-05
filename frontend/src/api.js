const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8002/api/v1';

async function apiFetch(path, params = {}) {
  const url = new URL(BASE_URL + path, window.location.origin);
  Object.entries(params).forEach(([k, v]) => v !== undefined && url.searchParams.set(k, v));
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

export const getStats = () => apiFetch('/statistics');

export const getRandomArticle = () => apiFetch('/articles/random', { include_text: true });

export const getArticle = (title) =>
  apiFetch(`/articles/${encodeURIComponent(title)}`, { include_text: true });

export const searchArticles = (q, { searchType = 'title', limit = 20, offset = 0 } = {}) =>
  apiFetch('/articles/search', { q, search_type: searchType, limit, offset, include_text: false });
