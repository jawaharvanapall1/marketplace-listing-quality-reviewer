# Marketplace Listing Quality Reviewer (React + Flask + MySQL)

```
React Frontend (Vite)
      ↓  /api
Flask REST API
      ↓
 ┌──────────────────┬──────────────────────┐
 │ Deterministic    │ AI Policy Review     │
 │ Validation       │ + RAG                │
 └──────────────────┴──────────────────────┘
      ↓                        ↓
   MySQL DB          Policy/Guide Documents (backend/docs/*.md)
      ↓
 Review + Approval History
```

## Run
**1. MySQL** (or skip: with no `DATABASE_URL` the backend uses SQLite for local dev)
```bash
docker compose up -d
```
**2. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # set DATABASE_URL (MySQL) and optionally ANTHROPIC_API_KEY
python run.py            # http://localhost:5000
python -m unittest discover -s tests
```
**3. Frontend**
```bash
cd frontend
npm install
npm run dev              # http://localhost:5173 (proxies /api to Flask)
```
No `ANTHROPIC_API_KEY`? The AI step falls back to offline pattern rules; the UI shows which mode ran.

## Flow
1. **Deterministic validation** (`app/validation.py`): required fields, price format, title/description length, supported category, attributes, tag count, duplicates (same seller + ≥80% title overlap).
2. **RAG** (`app/rag.py`): policy and brand-guide markdown in `backend/docs/` is chunked by `## <ID> <Title>` headings and ranked with BM25 against the listing; core sections P1/P3/B1 are always included.
3. **AI policy review** (`app/ai_review.py`): the model sees the listing + only the retrieved sections and returns findings (severity, kind, assumption/unverifiable note, cited policy id) and improved wording. Findings that cite a section that wasn't retrieved are discarded and counted.
4. **Human review**: per-field approve / edit / reject / reset, original-vs-revised diff, original-vs-final comparison, batch import.
5. **History** (`history_events`, append-only): every add, review and decision with before/after text. Reviews and revisions are kept per run, so re-reviewing never erases earlier results.

## API
`GET /api/meta` · `GET /api/sample` · `GET /api/listings` · `POST /api/listings {listings:[…]}` ·
`POST /api/listings/:id/review` · `POST /api/revisions/:id {action: approve|reject|reset|edit, text?}` · `GET /api/history[?listing_id=]`

## Notes
- `price` is stored as text so invalid input (e.g. `12,99`) can be saved and reported instead of rejected at insert.
- Add the real policy documents by dropping `.md` files with `## <ID> <Title>` sections into `backend/docs/`; restart Flask.
- Policy text included here is placeholder content.
- Next steps: embeddings for retrieval, async batch jobs, auth + reviewer identity on history events, eval set for finding precision/recall.
