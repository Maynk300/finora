# Finora

**Finora — Your Personal AI Finance Assistant**

A full-stack personal finance application with Django REST backend, React frontend, and Gemini-powered natural-language financial assistance.

## Key Features

- **User authentication** — Secure session-based login with CSRF protection
- **Transaction management** — Create, read, update, delete income and expense transactions
- **Income and expense tracking** — Categorized financial records with date filtering
- **Category management** — Pre-defined and custom categories for income/expense types
- **Budget management** — Set monthly budgets per category with real-time tracking
- **Budget vs actual spending** — Visual progress bars with status indicators (on track, warning, over budget)
- **Monthly financial comparison** — Compare income, expenses, savings rate, and category spending across months
- **Savings-rate calculation** — Automatic calculation of savings percentage
- **Gemini AI financial assistant** — Natural-language queries about your finances
- **AI tool calling** — Four specialized tools for precise financial data retrieval
- **User data isolation** — All data scoped to authenticated user; no cross-user access
- **Responsive modern UI** — Works on desktop, tablet, and mobile
- **Dark mode** — Automatic via `prefers-color-scheme`
- **Animated UI** — Smooth transitions, progress bar animations, hover/focus effects

## AI Assistant

The AI Assistant uses Google Gemini (gemini-3.6-flash) with function calling to answer natural-language questions about your finances. It has access to four tools and automatically selects the appropriate one based on your question:

| Tool | Purpose | Example Questions |
|------|---------|-------------------|
| `get_transactions` | Retrieve filtered transaction lists | "How much did I spend on food this month?" |
| `get_financial_summary` | Calculate totals, net balance, savings rate | "What is my savings rate?" |
| `get_budget_status` | Show budget vs actual per category | "Am I over my food budget?" |
| `compare_months` | Month-to-month financial comparison | "How did I do this month compared to last month?" |

**Security:** The authenticated Django user is passed directly to each tool; Gemini never receives or can specify another user's ID. All tool results are returned to Gemini for natural-language synthesis.

## Tech Stack

**Backend**
- Python 3.11+
- Django 6.1
- Django REST Framework 3.18
- SQLite (development)

**Frontend**
- React 19
- TypeScript 6
- Vite 8
- Tailwind CSS 4 (via CSS custom properties)

**AI**
- Google Gemini API (gemini-3.6-flash)

## Architecture

```
React Frontend (Vite + React 19 + TypeScript)
         │
         ▼ HTTPS + CSRF + Session Auth
Django REST API (Django 6.1 + DRF)
         │
         ▼
Finance Services & Tools (get_transactions, get_financial_summary, get_budget_status, compare_months)
         │
         ▼ Authenticated user context passed securely
Gemini API (gemini-3.6-flash with function calling)
```

**Security notes:**
- Authenticated user passed directly to tools; Gemini never receives user IDs
- CSRF protection on all mutating endpoints
- Session-based authentication with secure cookies
- User data isolation at database query level

## Project Structure

```
finora/
├── .gitignore
├── README.md
├── backend/
│   ├── .env                    # (ignored) Environment variables
│   ├── .env.example            # Template for environment variables
│   ├── manage.py
│   ├── requirements.txt
│   ├── db.sqlite3              # (ignored) Development database
│   ├── config/                 # Django project settings
│   └── finance/                # Main finance app
│       ├── models.py           # Category, Transaction, Budget
│       ├── views.py            # API views (Login, Logout, ViewSets, AI)
│       ├── serializers.py      # DRF serializers
│       ├── urls.py             # API routing
│       ├── tools/transactions.py   # AI tools implementation
│       ├── services/gemini.py      # Gemini service wrapper
│       └── tests.py            # 136 tests
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── index.css           # Design system, animations, dark mode
│       ├── main.tsx
│       ├── App.tsx
│       ├── context/AuthContext.tsx
│       ├── layouts/MainLayout.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Transactions.tsx
│       │   ├── Budgets.tsx
│       │   ├── AIAssistant.tsx
│       │   └── Login.tsx
│       ├── services/           # API client + types
│       └── assets/
└── dist/                       # (generated) Production frontend build
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key (free tier available at [Google AI Studio](https://aistudio.google.com))

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_api_key_here

# Run migrations
python manage.py migrate

# (Optional) Create a superuser for admin access
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

The Django API will be available at `http://localhost:8000/api/`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The React app will be available at `http://localhost:5173` (proxies API calls to Django)

### Production Build

```bash
# Frontend production build
cd frontend && npm run build

# The built files will be in frontend/dist/
# Configure Django to serve static files or use a reverse proxy
```

## Environment Variables

Create `backend/.env` with:

```env
GEMINI_API_KEY=your_api_key_here
```

**Never commit `.env` or any real API keys.** Only `.env.example` is tracked.

## Testing

```bash
# Backend
cd backend
python manage.py check          # Static checks (0 issues expected)
python manage.py test           # 136 tests (131 core + 5 logout)

# Frontend
cd frontend
npm run build                   # TypeScript + Vite production build
```

**Current test results:** 136 tests pass (131 core + 5 logout API tests)

## Security

- `.env` files ignored via `.gitignore`
- Database (`db.sqlite3`) ignored
- `node_modules/` ignored
- Virtual environment (`.venv/`) ignored
- No API keys committed to repository
- Authenticated user isolation: all queries filtered by `request.user`
- CSRF protection on all mutating endpoints
- Session-based authentication with secure cookies
- User data never exposed to other users or Gemini

## AI Quota Note

The Gemini integration uses the Google AI API free tier (20 requests/day per model). If you encounter `429 RESOURCE_EXHAUSTED` errors, this is a Google API quota limitation, not an application bug. Consider:
- Waiting for daily quota reset
- Upgrading to a paid tier on Google AI Studio
- Caching responses for repeated queries

## Screenshots

Screenshots are not currently included in the repository. The application features a modern responsive UI with:
- Gradient stat cards with animated progress bars
- Animated budget progress bars with glow effects
- Dark/light mode support
- Smooth page transitions and hover animations

## Future Improvements

1. **Recurring transactions** — Automate regular income/expenses
2. **Export to CSV/PDF** — Download transaction history and reports
3. **Financial goals** — Set and track savings targets
4. **Multi-currency support** — Handle international accounts
5. **Email notifications** — Budget alerts and monthly summaries

## License

No license specified. This is a personal portfolio project.