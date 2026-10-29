# AFTERIMAGE.EXE

AFTERIMAGE.EXE is a local-first AI memory-reconstruction experience for the Hacktoberfest 2026 Week 4 theme, “Ghost in the Machine.” Enter a handful of fragments, choose a mood, and ask a local Gemma model to weave them into a short afterimage.

The app sends bounded input to Ollama running on the same machine. It does not use a cloud AI API, accounts, analytics, or a database.

## Features

- CRT-inspired terminal interface with responsive and reduced-motion styles.
- Up to 15 memory fragments, with per-fragment and total length limits.
- Nostalgic, eerie, and hopeful reconstruction tones.
- Local Gemma generation through Ollama.
- Clear model availability status and honest failure states when Ollama is unavailable.
- Recovered-memory artifact view with copy and `.txt` download actions.
- Input is displayed as text, not injected as HTML.

## Requirements

- Python 3.10 or newer
- Ollama, if you want real local generation
- The Gemma 3 1B model, installed with `ollama pull gemma3:1b`

## Run on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

For local Gemma generation, start Ollama and install the default model:

```powershell
ollama pull gemma3:1b
$env:OLLAMA_MODEL="gemma3:1b"
python app.py
```

`OLLAMA_URL` defaults to `http://127.0.0.1:11434`. Set `PORT` to use a different Flask port.

## Project structure

```text
app.py                    Flask routes, validation, and Ollama integration
templates/index.html      Single-page terminal interface
static/afterimage.js      Form, health status, loading, result, copy, and download behavior
static/style.css          Active CRT/pixel visual system
tests/test_afterimage.py  Backend API tests with mocked Ollama responses
QA_CHECKLIST.md           Manual and automated QA status
docs/SUBMISSION_FIELDS.md Publishing checklist for owner-provided links and claims
```

`afterimage_ui_reference.html` is a standalone visual design reference. It is not loaded by Flask and is not required to run the application. The production page uses only `static/style.css` for its active styling.

## API behavior

- `GET /` serves the application.
- `GET /api/health` reports whether Ollama and the configured model are available.
- `POST /api/reconstruct` accepts `{ "fragments": [...], "tone": "nostalgic|eerie|hopeful" }` and returns model-generated memory text.

The backend accepts at most 15 fragments, 160 characters per fragment, and 2,200 characters in total. Generated output is bounded before it is returned.

## Testing

Run the backend tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Run the JavaScript syntax check:

```powershell
node --check static/afterimage.js
```

Compile-check the Flask application:

```powershell
python -m py_compile app.py
```

## Honest limitations

Real Gemma generation requires a running local Ollama service and installed model. Browser clipboard permissions vary by browser. No real browser automation or hosted demo is included in this repository.

Review Gemma, Ollama, and project licensing terms before publishing or redistributing the application.

## Git hygiene

Commit the application source, tests, documentation, and `requirements.txt`. Do not commit `.venv/`, `__pycache__/`, compiled Python files, `.env`, or other machine-local data; these are excluded by `.gitignore`.
