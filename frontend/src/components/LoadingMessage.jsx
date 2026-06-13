export default function LoadingMessage({ message = "Loading..." }) {
  return (
    <div className="state-message" role="status" aria-live="polite">
      {message}
    </div>
  );
}
