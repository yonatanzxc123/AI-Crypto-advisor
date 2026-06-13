import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMyOnboardingPreferences, saveOnboardingPreferences } from "../api/onboardingApi.js";
import ErrorMessage from "../components/ErrorMessage.jsx";
import LoadingMessage from "../components/LoadingMessage.jsx";
import {
  ASSET_OPTIONS,
  CONTENT_TYPE_OPTIONS,
  INVESTOR_TYPES,
} from "../constants/onboardingOptions.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Onboarding() {
  const navigate = useNavigate();
  const { logout, refreshCurrentUser } = useAuth();
  const [assets, setAssets] = useState(["bitcoin", "ethereum"]);
  const [investorType, setInvestorType] = useState("Beginner");
  const [contentTypes, setContentTypes] = useState(["Market News", "Coin Prices"]);
  const [error, setError] = useState("");
  const [hasExistingPreferences, setHasExistingPreferences] = useState(false);
  const [isLoadingPreferences, setIsLoadingPreferences] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadExistingPreferences();
  }, []);

  async function loadExistingPreferences() {
    setError("");
    setIsLoadingPreferences(true);

    try {
      const preferences = await getMyOnboardingPreferences();
      setAssets(preferences.assets);
      setInvestorType(preferences.investor_type);
      setContentTypes(preferences.content_types);
      setHasExistingPreferences(true);
    } catch (apiError) {
      if (apiError.status === 404) {
        setHasExistingPreferences(false);
        return;
      }

      if (apiError.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      setError(apiError.message);
    } finally {
      setIsLoadingPreferences(false);
    }
  }

  function toggleValue(value, selectedValues, setSelectedValues) {
    if (selectedValues.includes(value)) {
      setSelectedValues(selectedValues.filter((selectedValue) => selectedValue !== value));
      return;
    }

    setSelectedValues([...selectedValues, value]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await saveOnboardingPreferences({
        assets,
        investor_type: investorType,
        content_types: contentTypes,
      });
      await refreshCurrentUser();
      navigate("/dashboard");
    } catch (apiError) {
      if (apiError.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      setError(apiError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoadingPreferences) {
    return <LoadingMessage message="Loading preferences..." />;
  }

  const submitButtonText = hasExistingPreferences ? "Update preferences" : "Save preferences";

  return (
    <section className="content-panel">
      <h1>{hasExistingPreferences ? "Edit Preferences" : "Onboarding"}</h1>
      <ErrorMessage message={error} />
      <form className="form-grid" onSubmit={handleSubmit}>
        <fieldset>
          <legend>Crypto assets</legend>
          <div className="option-grid">
            {ASSET_OPTIONS.map((asset) => (
              <label className="checkbox-option" key={asset.value}>
                <input
                  type="checkbox"
                  checked={assets.includes(asset.value)}
                  onChange={() => toggleValue(asset.value, assets, setAssets)}
                />
                {asset.label}
              </label>
            ))}
          </div>
        </fieldset>

        <label>
          Investor type
          <select value={investorType} onChange={(event) => setInvestorType(event.target.value)}>
            {INVESTOR_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <fieldset>
          <legend>Content types</legend>
          <div className="option-grid">
            {CONTENT_TYPE_OPTIONS.map((type) => (
              <label className="checkbox-option" key={type}>
                <input
                  type="checkbox"
                  checked={contentTypes.includes(type)}
                  onChange={() => toggleValue(type, contentTypes, setContentTypes)}
                />
                {type}
              </label>
            ))}
          </div>
        </fieldset>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : submitButtonText}
        </button>
      </form>
    </section>
  );
}
