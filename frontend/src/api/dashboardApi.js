import { apiFetch } from "./client.js";

export function getTodayDashboard() {
  return apiFetch("/dashboard/today");
}
