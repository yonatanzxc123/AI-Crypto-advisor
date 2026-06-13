import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function MemeCard({ meme, onVote }) {
  return (
    <DashboardCard
      title={meme.title}
      actions={<VoteButtons sectionType="meme" itemKey={meme.item_key} onVote={onVote} />}
    >
      <figure className="meme">
        <div className="meme-frame">
          <span className="meme-badge">Meme break</span>
          <img src={meme.image_url} alt={meme.caption} />
        </div>
        <figcaption>{meme.caption}</figcaption>
      </figure>
    </DashboardCard>
  );
}
