import { useEffect, useState } from "react";

import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function MemeCard({ meme, onVote }) {
  const [imageFailed, setImageFailed] = useState(false);
  const imageAltText = `${meme.title}: ${meme.caption}`;

  useEffect(() => {
    setImageFailed(false);
  }, [meme.image_url, meme.item_key]);

  return (
    <DashboardCard
      title={meme.title}
      actions={<VoteButtons sectionType="meme" itemKey={meme.item_key} onVote={onVote} />}
    >
      <figure className="meme">
        <div className="meme-frame">
          <span className="meme-badge">Meme break</span>
          {imageFailed ? (
            <div className="meme-fallback" role="img" aria-label={imageAltText}>
              <span>{meme.caption}</span>
            </div>
          ) : (
            <img src={meme.image_url} alt={imageAltText} onError={() => setImageFailed(true)} />
          )}
        </div>
        <figcaption>{meme.caption}</figcaption>
      </figure>
    </DashboardCard>
  );
}
