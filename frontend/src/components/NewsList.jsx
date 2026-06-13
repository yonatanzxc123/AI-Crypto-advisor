import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function NewsList({ news, onVote }) {
  return (
    <DashboardCard title="Market News" subtitle="Asset-aware headlines">
      <div className="stack-list">
        {news.map((item) => (
          <article className="list-item" key={item.item_key}>
            <div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <span className="source-badge">{item.source}</span>
            </div>
            <VoteButtons sectionType="news" itemKey={item.item_key} onVote={onVote} />
          </article>
        ))}
      </div>
    </DashboardCard>
  );
}
