import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function AiInsightCard({ insight, onVote }) {
  return (
    <DashboardCard
      title={insight.title}
      subtitle={`Model: ${insight.model}`}
      actions={<VoteButtons sectionType="ai_insight" itemKey={insight.item_key} onVote={onVote} />}
    >
      <p className="insight-text">{insight.content}</p>
    </DashboardCard>
  );
}
