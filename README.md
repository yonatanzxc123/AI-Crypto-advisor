# AI Crypto Advisor

A personalized crypto investor dashboard.

## Links

- Live App: https://ai-crypto-advisor-orcin.vercel.app
- Backend API: https://ai-crypto-advisor-3s8x.onrender.com
- Swagger Docs: https://ai-crypto-advisor-3s8x.onrender.com/docs
- Assignment Overview: [docs/ASSIGNMENT_OVERVIEW.md](docs/ASSIGNMENT_OVERVIEW.md)
- AI Usage Summary: [docs/AI_USAGE_SUMMARY.md](docs/AI_USAGE_SUMMARY.md)

## Short Concept

Users register, complete onboarding preferences, and receive a personalized daily dashboard with coin prices, market news, AI insight, meme content, and feedback voting.

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI
- Database: PostgreSQL
- Deployment: Vercel + Render
- APIs/Tools: CoinGecko, OpenRouter, static JSON meme catalog

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```


Render free-tier services may cold start, and free external APIs such as CoinGecko/OpenRouter may occasionally be delayed or rate-limited , so please take this into consideration.
