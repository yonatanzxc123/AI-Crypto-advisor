import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function PriceList({ prices, onVote }) {
  return (
    <DashboardCard title="Coin Prices" subtitle="USD market snapshot">
      <div className="price-list">
        {prices.map((price) => (
          <div className="price-row" key={price.item_key}>
            <div>
              <strong>{price.symbol}</strong>
              <span>{price.coin_id}</span>
            </div>
            <div className="price-values">
              <strong>${formatPrice(price.price_usd)}</strong>
              <span className={price.change_24h >= 0 ? "positive" : "negative"}>
                {formatChange(price.change_24h)}
              </span>
            </div>
            <VoteButtons sectionType="price" itemKey={price.item_key} onVote={onVote} />
          </div>
        ))}
      </div>
      <p className="helper-note">Prices may be delayed or cached by the data provider.</p>
    </DashboardCard>
  );
}

function formatPrice(value) {
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: value < 1 ? 4 : 2,
    maximumFractionDigits: value < 1 ? 4 : 2,
  });
}

function formatChange(value) {
  if (value === null || value === undefined) {
    return "24h n/a";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${Number(value).toFixed(2)}% 24h`;
}
