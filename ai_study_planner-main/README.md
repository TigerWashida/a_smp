# StudyMate

StudyMate is a local-first study planner that recommends real calendar sessions, lets the student adjust them in 30-minute steps, and saves the plan only after explicit acceptance.

## What changed

- AI recommendation -> draggable preview -> whole-plan acceptance
- Real dates and 24-hour times, with 30-minute snapping and two-hour session caps
- Atomic JSON persistence in `data/study_data.json`
- Conflict, past-time, deadline, duration, and duplicate-accept validation
- Month, week, and day calendar views, with editable weekly timing after acceptance
- Dynamic Ollama context with a clear deterministic fallback
- Safe text rendering and consistent network error handling
- API and scheduler tests

See `application-overview.html` for the product explanation and `implementation-changes.html` for the implementation report.

## Clean start

Requirements: Python 3.11+, Ollama, and a modern browser.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2:3b
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>.

### Fastest way to open it

Do **not** open `frontend/index.html` directly; that file needs the local server for its styling, calendar, and planner API. In Finder, double-click `Start StudyMate.command` in the project folder. It creates the virtual environment if needed, starts the app, and opens the correct address.

If Ollama is stopped or takes longer than 12 seconds, StudyMate still creates a valid schedule and labels its explanation as **Fallback**.

## Data and recovery

Study goals and tasks are saved to `data/study_data.json`. Each update is written to a temporary file and atomically replaced. IDs use `max(existing_ids) + 1`.

If the JSON is corrupt, startup fails with the data path and a recovery message. Copy the corrupt file before restoring a known-good backup; the app never silently resets it.

For isolated runs:

```bash
STUDYMATE_DATA_FILE=/tmp/studymate-demo.json uvicorn main:app
```

## Three-minute demo

1. Enter a subject, hours, difficulty, preferred slot, and deadline.
2. Select **Get AI Recommendation**.
3. Drag a dashed preview session in the weekly calendar.
4. Select **Accept Plan**.
5. Reload; the accepted session remains.
6. Drag the accepted session. A conflicting or invalid move reverts with a reason.
7. Stop Ollama and repeat to show the visible fallback mode.

## Test

```bash
pytest -q
```

The suite covers scheduling capacity, preview non-persistence, atomic acceptance, reload persistence, double acceptance, invalid moves, fallback behavior, and corrupt-data handling.

## API

- `POST /plan-previews`: create a 30-minute in-memory recommendation
- `POST /plan-previews/{preview_id}/accept`: validate and atomically save the adjusted plan
- `PATCH /tasks/{task_id}/schedule`: move a saved session without changing duration
- `PATCH /tasks/{task_id}`: update pending/completed status
- `POST /chat`: returns `response`, `mode`, and `warning`
- `POST /generate-plan`: deprecated compatibility endpoint

No external calendar integration or timezone conversion is performed in this version.
