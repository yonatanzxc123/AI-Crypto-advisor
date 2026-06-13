import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMyOnboardingPreferences, saveOnboardingPreferences } from "../api/onboardingApi.js";
import CheckboxGroup from "../components/CheckboxGroup.jsx";
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

  function validateSelections() {
    if (assets.length === 0) {
      return "Choose at least one crypto asset.";
    }

    if (!investorType) {
      return "Choose an investor type.";
    }

    if (contentTypes.length === 0) {
      return "Choose at least one content type.";
    }

    return "";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const validationError = validateSelections();

    if (validationError) {
      setError(validationError);
      return;
    }

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
      <p className="page-intro">
        These preferences personalize your daily prices, news, insight, and meme.
      </p>
      <ErrorMessage message={error} />
      <form className="form-grid" onSubmit={handleSubmit}>
        <CheckboxGroup
          legend="Crypto assets"
          options={ASSET_OPTIONS}
          selectedValues={assets}
          onToggle={(value) => toggleValue(value, assets, setAssets)}
        />

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

        <CheckboxGroup
          legend="Content types"
          options={CONTENT_TYPE_OPTIONS}
          selectedValues={contentTypes}
          onToggle={(value) => toggleValue(value, contentTypes, setContentTypes)}
        />

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : submitButtonText}
        </button>
      </form>
    </section>
  );
}
