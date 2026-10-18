const DEFAULT_API_URL = "http://localhost:8000";

// Environment values are easy to enter with a trailing slash in hosting
// dashboards. Remove it once so joining endpoint paths never produces `//`.
export const API_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(
  /\/+$/,
  "",
);
