import DashboardCard from "./DashboardCard.jsx";
import VoteButtons from "./VoteButtons.jsx";

export default function PriceList({ prices, onVote }) {
  const sourceNote = getSourceNote(prices);

  return (
    <DashboardCard title="Coin Prices" subtitle="USD market snapshot">
      <div className="price-list">
        {prices.map((price) => (
          <div className="price-row" key={price.item_key}>
            <div>
              <strong>{price.symbol}</strong>
              <span>{price.coin_id}</span>
              <span className={`source-pill ${getSourceClassName(price.source)}`}>
                {formatSource(price.source)}
              </span>
            </div>
            <div className="price-values">
              <strong>{formatPriceLabel(price)}</strong>
              <span className={getChangeClassName(price.change_24h)}>
                {formatChange(price.change_24h)}
              </span>
              {price.last_updated_at ? (
                <span className="source-time">Updated {formatUpdatedAt(price.last_updated_at)}</span>
              ) : null}
            </div>
            <VoteButtons sectionType="price" itemKey={price.item_key} onVote={onVote} />
          </div>
        ))}
      </div>
      {sourceNote ? <p className="helper-note warning-note">{sourceNote}</p> : null}
      <p className="helper-note">Prices may be delayed or cached by the data provider.</p>
    </DashboardCard>
  );
}

function formatPriceLabel(price) {
  if (price.source === "unavailable" || price.price_usd === null || price.price_usd === undefined) {
    return "Price temporarily unavailable";
  }

  return `$${formatPrice(price.price_usd)}`;
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

function getChangeClassName(value) {
  if (value === null || value === undefined) {
    return "neutral";
  }

  return value >= 0 ? "positive" : "negative";
}

function formatSource(source) {
  if (source === "coingecko") {
    return "CoinGecko";
  }

  if (source === "coingecko-cached") {
    return "Cached";
  }

  if (source === "unavailable") {
    return "Unavailable";
  }

  return "Source unknown";
}

function getSourceClassName(source) {
  if (source === "coingecko") {
    return "live";
  }

  if (source === "coingecko-cached") {
    return "cached";
  }

  return "unavailable";
}

function formatUpdatedAt(value) {
  return new Date(value).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getSourceNote(prices) {
  if (prices.some((price) => price.source === "unavailable")) {
    return "Live CoinGecko data is temporarily unavailable for some assets. Try Refresh Dashboard.";
  }

  if (prices.some((price) => price.source === "coingecko-cached")) {
    return "Using recently cached CoinGecko prices because live data is temporarily unavailable. Try Refresh Dashboard for live data.";
  }

  return "";
}
