import { apiFetch } from "./client.js";

export function saveOnboardingPreferences(preferences) {
  return apiFetch("/onboarding", {
    method: "POST",
    body: JSON.stringify(preferences),
  });
}

export function getMyOnboardingPreferences() {
  return apiFetch("/onboarding/me");
}
