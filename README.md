# AI-First CRM — HCP Module: Log Interaction Screen

An AI-first CRM module that lets a pharma field representative log an
interaction with a Healthcare Professional (HCP) either through a
**structured form** or a **conversational chat interface**, backed by a
**LangGraph agent** running on **Groq (gemma2-9b-it)**.

---

## 1. What this is

Field reps visit doctors all day and hate filling out forms afterward. This
module gives them two ways to log the same visit:

- **Structured Form** — type type/channel + free-text notes → the agent
  summarizes, extracts entities, and stores a clean record.
- **Conversational Chat** — just describe the visit like you'd tell a
  colleague ("Met Dr. Rao, discussed CardioX trial data, she was positive,
  dropped 2 samples, follow up next week") and the LangGraph agent figures
  out what to do (log it, edit an old entry, pull history, schedule a
  follow-up, or run a compliance check).

Both paths write to the **same database** and go through the **same 5
tools**, so the data model never forks.

---

## 2. Tech stack

| Layer          | Choice                                          |
|-----------------|--------------------------------------------------|
| Frontend        | React 18 + Redux Toolkit, Vite, Google Inter font |
| Backend         | Python + FastAPI                                |
| AI Agent        | LangGraph                                       |
| LLM             | Groq — `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (fallback) |
| Database        | PostgreSQL (SQLite fallback for instant local runs) |
| ORM             | SQLAlchemy                                       |

---

## 3. Architecture

```
frontend (React/Redux)  ──HTTP──▶  FastAPI
                                     ├── /api/hcps          (list/create HCPs)
                                     ├── /api/interactions  (form path → tools directly)
                                     └── /api/chat          (chat path → LangGraph agent)
                                            │
                                      LangGraph agent
                                            │
                              ┌─────────────┼─────────────────────┐
                         classify_intent          route()
                                            │
        ┌──────────────┬─────────────┬──────────────┬──────────────┐
        ▼              ▼             ▼              ▼              ▼
  log_interaction edit_interaction fetch_hcp_history schedule_followup compliance_check
        │              │             │              │              │
        └──────────────┴─────────────┴──────────────┴──────────────┘
                                 │
                            Postgres / SQLite
```

The **structured form** calls `log_interaction` / `edit_interaction` /
`compliance_check` directly via REST endpoints (no need to run the full
graph for a deterministic form submit).

The **chat interface** always goes through the LangGraph agent
(`app/agent/graph.py`), which:
1. Classifies the rep's message intent using Groq (gemma2-9b-it).
2. Routes to the matching tool node.
3. Runs the tool against the live DB session.
4. Generates a natural-language confirmation reply.

---

## 4. LangGraph Agent & the 5 Tools

The agent's role is to be the single intelligent layer between "what the rep
typed" and "what gets written to the CRM database" — it removes the need for
reps to fill rigid forms while still producing clean, structured, compliant
records for managers and analytics.

| # | Tool | Purpose |
|---|------|---------|
| 1 | **`log_interaction`** | Creates a new interaction. Sends the rep's raw notes to Groq (gemma2-9b-it) with a structured-extraction prompt that returns a JSON summary, topics discussed, products discussed, HCP sentiment, samples dropped, and an implied follow-up action. The result + raw notes are saved, and a compliance check is run automatically before saving. |
| 2 | **`edit_interaction`** | Updates an existing interaction. If the rep edits the raw notes, the tool **re-runs the LLM extraction** so summary/topics/sentiment/samples stay consistent with the new notes (so a stale AI summary can never sit next to updated text). |
| 3 | **`fetch_hcp_history`** | Retrieves an HCP's profile (name, specialty, segment) and their last 5 interactions. Used so the agent (and rep) has context — e.g. "what did we discuss last time?" — before logging something new. |
| 4 | **`schedule_followup`** | Sets/updates the follow-up action and date on a specific interaction (e.g. "send updated study data next week", "drop samples on next visit"). |
| 5 | **`compliance_check`** | Runs the interaction summary through a compliance-reviewer prompt that flags off-label promotion claims, unapproved efficacy/safety claims, or payment-for-prescribing language, storing a `flag` (`OK`/`REVIEW`) + `reason`. Can be triggered automatically (on log/edit) or manually from the UI ("Recheck Compliance" button / chat command). |

All 5 tools are implemented in `backend/app/agent/tools.py` and wired into
the graph in `backend/app/agent/graph.py`.

---

## 5. Data model

- **HCP**: name, specialty, hospital, email, phone, segment (A/B/C tiering).
- **Interaction**: type, channel, date, raw_notes, AI summary, topics,
  products, sentiment, samples_dropped, follow_up_action/date,
  compliance_flag/reason, created_via (`form` or `chat`).

---

## 6. Running it locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free Groq API key: https://console.groq.com/keys
- (Optional) PostgreSQL — SQLite is used automatically if `DATABASE_URL`
  isn't set to a Postgres URL, so you can run this with **zero DB setup**.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your GROQ_API_KEY

uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`). Three demo HCPs are seeded automatically on
first run.

To use Postgres instead of the SQLite default, create a database and set:
```
DATABASE_URL=postgresql://user:password@localhost:5432/hcp_crm
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env       # defaults to http://localhost:8000, edit if needed
npm run dev
```

Open `http://localhost:5173`.

---

## 7. Trying out all 5 tools quickly

Once both servers are running, select an HCP in the sidebar, switch to
**Conversational Chat**, and try:

1. `"Met Dr. Rao today, discussed CardioX trial results, she was very
   positive and I dropped 2 samples."` → **log_interaction**
2. `"Actually change interaction 1 — she was neutral, not positive."` →
   **edit_interaction**
3. `"What's Dr. Rao's history with us?"` → **fetch_hcp_history**
4. `"Schedule a follow-up for interaction 1 — send updated study data next
   Monday."` → **schedule_followup**
5. `"Recheck compliance on interaction 1."` → **compliance_check**

Or use the **Structured Form** tab, which calls `log_interaction` /
`edit_interaction` / `compliance_check` directly via REST, and the
**Interaction History** panel below it, which has Edit / Recheck Compliance
buttons per record.

---

## 8. Project structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py       # LangGraph StateGraph definition
│   │   │   └── tools.py       # the 5 tools
│   │   ├── routers/
│   │   │   ├── hcps.py
│   │   │   ├── interactions.py
│   │   │   └── chat.py
│   │   ├── database.py
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── llm.py             # Groq client + JSON helper
│   │   └── main.py            # FastAPI app + seed data
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LogInteractionScreen.jsx
│   │   │   ├── InteractionForm.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   └── InteractionHistory.jsx
│   │   ├── store/              # Redux Toolkit slices
│   │   ├── api/api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html               # loads Google Inter font
│   └── package.json
└── README.md
```

---

## 9. Notes / assumptions

- SQLite is used as a local dev fallback for zero-setup review; swap in the
  Postgres `DATABASE_URL` for a "production" run — no code changes needed.
- Groq's `gemma2-9b-it` is the primary model per the task spec; `llama-3.3-70b-versatile`
  is used as an automatic fallback if the primary call fails.
- This is a scoped assignment build: auth, multi-tenant reps, and pagination
  were intentionally left out to keep the focus on the LangGraph agent + the
  dual form/chat logging experience.
