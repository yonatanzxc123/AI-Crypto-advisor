# AI Crypto Advisor - Assignment Overview

**Repository:** https://github.com/yonatanzxc123/AI-Crypto-advisor  
**Frontend:** https://ai-crypto-advisor-orcin.vercel.app  
**Backend API:** https://ai-crypto-advisor-3s8x.onrender.com  
**Health Check:** https://ai-crypto-advisor-3s8x.onrender.com/health  
**Swagger Docs:** https://ai-crypto-advisor-3s8x.onrender.com/docs

AI Crypto Advisor is a personalized crypto investor dashboard. The application lets users create an account, log in, complete onboarding preferences, and view a daily dashboard tailored to their crypto interests. The dashboard combines market-oriented content, live coin prices, an AI-generated educational insight, and a fun crypto meme, with feedback voting on each visible section.

## User Flow

Users sign up and log in using JWT-based authentication. After logging in for the first time, they complete an onboarding quiz that asks which crypto assets they are interested in, what type of investor they are, and what content types they want to see. The supported content sections are Coin Prices, Market News, AI Insight, and Fun.

Once onboarding is complete, the user sees a daily dashboard with selected coin prices, asset-aware market news, an AI Insight of the Day, and a crypto meme. The dashboard respects the user's selected content preferences, so sections that were not selected are hidden. Each dashboard item or section supports thumbs up/down feedback.

## Architecture and Frameworks

The frontend is built with React + Vite and deployed on Vercel. It is organized into pages, reusable components, API client modules, an authentication context, constants, and plain CSS styling. The frontend stores the JWT in localStorage for this assignment and uses fetch-based API calls.

The backend is built with FastAPI and deployed on Render. PostgreSQL is used as the production database through Render PostgreSQL. SQLAlchemy is used for database models and persistence, and Pydantic schemas are used as DTOs. The backend follows a clean layered structure: routers handle HTTP concerns, services contain business logic, repositories handle database access, SQLAlchemy models represent tables, and mappers/schemas keep API responses separate from raw database models.

## APIs and Data Sources

Coin prices use the CoinGecko API. The backend includes retry, caching, and unavailable-state handling so fake static prices are not shown as live data.

Market News currently uses an asset-aware static fallback. The assignment allowed CryptoPanic API or static fallback, and the service is structured so CryptoPanic can be added later without changing the dashboard contract.

AI Insight uses OpenRouter when an API key is configured. The backend cleans AI output, rejects empty or prompt-like responses, caches successful daily insights per user/preferences, retries safely, and falls back without exposing internal errors. The content is educational and avoids direct buy/sell or price prediction recommendations.

Crypto Meme uses a static JSON meme catalog referencing local original SVG assets. Reddit scraping was not enabled by default because static JSON is safer and more reliable for deployment demos. A future enhancement could add Reddit-based sourcing behind a controlled integration.

## Feedback and Future Recommendation Improvement

Each dashboard section supports thumbs up/down voting. Feedback is stored in PostgreSQL in the `feedback` table with the authenticated user id, section type, item key, vote, and timestamp. The current application does not automatically train a model, but the stored feedback can later be used to rank content, adjust AI prompts, prioritize preferred assets or content types, and improve recommendation quality over time.

## Database Access

The production database is hosted on Render PostgreSQL. Database credentials are not stored in GitHub and are not included in this document. Access will be provided privately in the submission email using Render's External Database URL or PSQL command. The main tables are `users`, `preferences`, `feedback`, and `daily_ai_insights`.

## Notes

The project is deployed publicly using Vercel for the frontend and Render for the backend/database. Render free-tier services may cold start, so the first backend request after inactivity can take longer. The app also relies on free-tier external APIs, so CoinGecko or OpenRouter may occasionally be delayed, rate-limited, or unavailable. The backend uses caching and safe fallbacks so the dashboard remains usable. If live data does not appear immediately, use the dashboard refresh button once or twice.
