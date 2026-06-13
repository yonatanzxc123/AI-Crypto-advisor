import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";

export default function VoteButtons({ sectionType, itemKey, onVote }) {
  const [status, setStatus] = useState("");
  const [statusType, setStatusType] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleVote(vote) {
    setIsSubmitting(true);
    setStatus("");
    setStatusType("");

    try {
      await onVote({ section_type: sectionType, item_key: itemKey, vote });
      setStatus("Saved");
      setStatusType("success");
    } catch (error) {
      setStatus(error.message || "Vote failed");
      setStatusType("error");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="vote-control" aria-busy={isSubmitting}>
      <button
        className="icon-button"
        type="button"
        aria-label="Vote up"
        title="Vote up"
        disabled={isSubmitting}
        onClick={() => handleVote("up")}
      >
        <ThumbsUp size={17} aria-hidden="true" />
      </button>
      <button
        className="icon-button"
        type="button"
        aria-label="Vote down"
        title="Vote down"
        disabled={isSubmitting}
        onClick={() => handleVote("down")}
      >
        <ThumbsDown size={17} aria-hidden="true" />
      </button>
      {status ? (
        <span className={`vote-status ${statusType}`} role="status" aria-live="polite">
          {status}
        </span>
      ) : null}
    </div>
  );
}
