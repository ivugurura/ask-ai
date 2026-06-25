# ASK-AI Chatbot Service

## Setup
```bash
pipenv install
cp .env.example .env
```

## Ollama (Required For Summaries)
```bash
# Install/start Ollama on the server, then pull the configured model.
ollama serve
ollama pull qwen2.5:0.5b

# Optional checks
curl http://127.0.0.1:11434/api/tags
curl http://127.0.0.1:11434/api/generate -H "Content-Type: application/json" -d '{"model":"qwen2.5:0.5b","prompt":"hello","stream":false}'
```

Set these in `.env`:
```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:0.5b
```

## Run
```bash
pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```