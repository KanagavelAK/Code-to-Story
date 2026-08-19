# Code to Story 📖

> Paste any code block → Get a plain English story a junior can follow.

## What it does

Takes any code snippet and turns it into a children's book-style narrative using AI — designed for junior developers who find technical explanations intimidating.

## Tech stack

- **FastAPI** + **Groq API** (`qwen/qwen3.6-27b`) — backend
- **HTML + CSS + JS** — frontend (dark-themed, glassmorphism UI)
- **python-dotenv** — environment management

## Project structure

```
code-to-story/
├── backend/
│   ├── main.py              ← FastAPI app, serves frontend + API
│   ├── story.py             ← Groq API call + prompt + JSON parsing
│   └── requirements.txt
├── frontend/
│   └── index.html           ← Premium dark-themed UI
├── .env                     ← GROQ_API_KEY
└── README.md
```

## How to run

### 1. Clone and set up

```bash
git clone <your-repo-url>
cd code-to-story
```

### 2. Add your Groq API key

```bash
# Edit .env and replace the placeholder
GROQ_API_KEY=your_actual_key_here
```

Get a free key at [console.groq.com](https://console.groq.com)

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Start the app

```bash
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) — both the UI and API run from this single server.

### API endpoints

| Method | Endpoint   | Description              |
|--------|------------|--------------------------|
| GET    | `/`        | Serves the frontend UI   |
| GET    | `/health`  | Returns `{"status":"ok"}`|
| POST   | `/convert` | Converts code to story   |

## Demo

<img width="1919" height="1024" alt="image" src="https://github.com/user-attachments/assets/64fde8a3-a467-4630-bba0-66807134d3c4" />

<img width="808" height="918" alt="image_54" src="https://github.com/user-attachments/assets/3d54af1d-dc01-493f-82f2-aa71645439eb" />

<img width="825" height="884" alt="image" src="https://github.com/user-attachments/assets/35e50c94-3a1c-4d1d-81c8-1b042a7f592b" />




## Design decisions

**Why Groq over OpenAI:** Sub-second latency matters for a learning tool. A student waiting 5 seconds loses focus. Groq delivers responses in under 2 seconds on the free tier.

**Why HTML over Streamlit:** A premium dark-themed UI with typing animations, glassmorphism cards, and copy-to-clipboard makes a stronger impression. The backend is decoupled — any frontend can call `/convert`.

**Why retry mechanism:** LLM output is non-deterministic. The same prompt can return valid JSON on one call and broken JSON on the next. Retrying up to 3 times before falling back is a standard production pattern.

## What AI got wrong

Three real issues hit during development:

1. **Markdown fence wrapping** — The model returned JSON wrapped in ` ```json ``` ` backticks despite the system prompt saying "No markdown." Fixed by stripping fences before `json.loads()`.

2. **Thinking tags** — Qwen3 models wrap responses in `<think>...</think>` chain-of-thought blocks. The actual JSON is buried after thousands of characters of reasoning. Fixed with regex: `re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)`.

3. **Intermittent parse failures** — Even after stripping, ~20% of responses had extra text around the JSON. Fixed with two layers: extracting content between the first `{` and last `}`, plus a retry mechanism (up to 3 attempts).

All three are production patterns — you always sanitize LLM output before processing it.

## Built by

**Kanagavel A K** · AI Native Mentor Sprint
