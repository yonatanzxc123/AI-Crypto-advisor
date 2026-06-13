import { apiFetch } from "./client.js";

export function submitFeedback(feedback) {
  return apiFetch("/feedback", {
    method: "POST",
    body: JSON.stringify(feedback),
  });
}
