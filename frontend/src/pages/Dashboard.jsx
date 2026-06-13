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

  if (isLoading) {
    return <LoadingMessage message="Loading dashboard..." />;
  }

  if (!dashboard) {
    return <ErrorMessage message={error || "Dashboard is unavailable."} />;
  }

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

      <div className="dashboard-grid">
        <PriceList prices={dashboard.prices} onVote={handleVote} />
        <NewsList news={dashboard.news} onVote={handleVote} />
        <AiInsightCard insight={dashboard.ai_insight} onVote={handleVote} />
        <MemeCard meme={dashboard.meme} onVote={handleVote} />
      </div>

      <p className="disclaimer">Educational content only. Not financial advice.</p>
    </div>
  );
}
