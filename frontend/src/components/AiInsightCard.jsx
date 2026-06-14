import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function AiInsightCard({ insight, onVote }) {
  return (
    <DashboardCard
      title={insight.title}
      subtitle={formatInsightDate(insight.generated_for_date)}
      actions={<VoteButtons sectionType="ai_insight" itemKey={insight.item_key} onVote={onVote} />}
    >
      <div className="insight-meta">
        <span className={`source-badge ${getSourceClassName(insight.source)}`}>
          {formatSourceLabel(insight.source)}
        </span>
        {insight.source === "openrouter" ? <span>Model: {insight.model}</span> : null}
      </div>
      <p className="insight-text">{insight.content}</p>
    </DashboardCard>
  );
}

function formatInsightDate(value) {
  if (!value) {
    return "Today";
  }

  return `For ${value}`;
}

function formatSourceLabel(source) {
  if (source === "openrouter") {
    return "OpenRouter";
  }

  if (source === "cached-openrouter") {
    return "OpenRouter";
  }

  return "Static fallback";
}

function getSourceClassName(source) {
  if (source === "openrouter") {
    return "live";
  }

  if (source === "cached-openrouter") {
    return "live";
  }

  return "fallback";
}
