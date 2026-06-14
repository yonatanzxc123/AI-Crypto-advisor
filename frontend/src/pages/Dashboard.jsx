import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getTodayDashboard } from "../api/dashboardApi.js";
import { submitFeedback } from "../api/feedbackApi.js";
import AiInsightCard from "../components/AiInsightCard.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import LoadingMessage from "../components/LoadingMessage.jsx";
import MemeCard from "../components/MemeCard.jsx";
import NewsList from "../components/NewsList.jsx";
import PriceList from "../components/PriceList.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const CONTENT_TYPES = {
  prices: "Coin Prices",
  news: "Market News",
  aiInsight: "AI Insight",
  fun: "Fun",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadDashboard({ showLoading: true });
  }, []);

  async function loadDashboard({ showLoading = false } = {}) {
    if (showLoading) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }

    setError("");

    try {
      const data = await getTodayDashboard();
      setDashboard(data);
    } catch (apiError) {
      if (apiError.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      if (apiError.status === 400) {
        navigate("/onboarding");
        return;
      }

      setError(apiError.message);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  async function handleVote(feedback) {
    await submitFeedback(feedback);
  }

  if (isLoading || isRefreshing) {
    return <LoadingMessage message={isRefreshing ? "Refreshing dashboard..." : "Loading dashboard..."} />;
  }

  if (!dashboard) {
    return <ErrorMessage message={error || "Dashboard is unavailable."} />;
  }

  const selectedContentTypes = dashboard.profile.content_types || [];
  const showPrices = selectedContentTypes.includes(CONTENT_TYPES.prices);
  const showNews = selectedContentTypes.includes(CONTENT_TYPES.news);
  const showAiInsight = selectedContentTypes.includes(CONTENT_TYPES.aiInsight);
  const showMeme = selectedContentTypes.includes(CONTENT_TYPES.fun);
  const hasVisibleSections = showPrices || showNews || showAiInsight || showMeme;

  return (
    <div className="dashboard-page">
      <section className="dashboard-summary">
        <div>
          <h1>Daily Dashboard</h1>
          <p>{dashboard.profile.name} | {dashboard.profile.investor_type}</p>
        </div>
        <div className="summary-actions">
          <div className="tag-list">
            {dashboard.profile.assets.map((asset) => (
              <span key={asset}>{asset}</span>
            ))}
          </div>
          <div className="button-row">
            <button className="secondary-button" type="button" onClick={() => navigate("/onboarding")}>
              Edit Preferences
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={isRefreshing}
              onClick={() => loadDashboard()}
            >
              {isRefreshing ? "Refreshing..." : "Refresh Dashboard"}
            </button>
          </div>
        </div>
      </section>

      <ErrorMessage message={error} />

      {hasVisibleSections ? (
        <div className="dashboard-grid">
          {showPrices ? <PriceList prices={dashboard.prices} onVote={handleVote} /> : null}
          {showNews ? <NewsList news={dashboard.news} onVote={handleVote} /> : null}
          {showAiInsight ? (
            <AiInsightCard insight={dashboard.ai_insight} onVote={handleVote} />
          ) : null}
          {showMeme ? <MemeCard meme={dashboard.meme} onVote={handleVote} /> : null}
        </div>
      ) : (
        <section className="empty-dashboard">
          <h2>No dashboard sections selected</h2>
          <p>No dashboard sections selected. Edit your preferences to choose content types.</p>
          <button className="primary-button" type="button" onClick={() => navigate("/onboarding")}>
            Edit Preferences
          </button>
        </section>
      )}

      <p className="disclaimer">Educational content only. Not financial advice.</p>
    </div>
  );
}
