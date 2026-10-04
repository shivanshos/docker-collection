# Shivanshos Production Agentic Workspace

Production-grade Agentic AI environment hosted on Ubuntu 24.04 VPS for shivanshos.

## Architecture Overview
- **Domain Gateway:** Nginx Proxy Manager (http://<VPS_IP>:81)
- **Web Interface:** Open WebUI connected to agent.aio3.cloud (Port 3000)
- **Local LLM Engine:** Ollama running qwen2.5-coder:7b (http://127.0.0.1:11434)
- **Vector Memory:** Qdrant (http://127.0.0.1:6333)
- **API Endpoint Server:** FastAPI (http://127.0.0.1:8000)
- **Multi-Agent Orchestration:** CrewAI + Playwright Web Scraper

## Fast Management Commands
```bash
# Activate Virtual Environment
source /opt/shivanshos/agents/.venv/bin/activate

# Check API Server Status
curl http://127.0.0.1:8000/

# Restart Gateway Services
cd /opt/shivanshos/gateway && docker compose restart
```

## API Routes
- `POST /api/bash` - Run bash commands in workspace
- `POST /api/file` - Create or edit workspace files
- `POST /api/scrape` - Headless Playwright page extraction
- `POST /api/crew` - Kickoff CrewAI multi-agent tasks
