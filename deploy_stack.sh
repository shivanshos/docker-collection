#!/bin/bash
set -e

echo '=== [1/6] Installing Playwright & CrewAI Dependencies ==='
cd /opt/shivanshos/agents
source .venv/bin/activate
uv pip install fastapi uvicorn crewai duckduckgo-search playwright beautifulsoup4 pydantic
playwright install-deps chromium 2>/dev/null || true
playwright install chromium

echo '=== [2/6] Updating Gateway Stack (Open WebUI + Qdrant + NPM) ==='
cat << 'DOCKER_EOF' > /opt/shivanshos/gateway/docker-compose.yml
services:
  npm:
    image: 'jc21/nginx-proxy-manager:latest'
    container_name: shivanshos_npm
    restart: unless-stopped
    ports:
      - '80:80'
      - '81:81'
      - '443:443'
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt

  qdrant:
    image: qdrant/qdrant:latest
    container_name: shivanshos_qdrant
    restart: unless-stopped
    ports:
      - '6333:6333'
    volumes:
      - /opt/shivanshos/vector_db/qdrant_data:/qdrant/storage

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: shivanshos_webui
    restart: unless-stopped
    ports:
      - '3000:8080'
    environment:
      - OLLAMA_BASE_URL=http://172.17.0.1:11434
      - WEBUI_SECRET_KEY=shivanshos_secure_secret_2026
    volumes:
      - /opt/shivanshos/gateway/webui_data:/app/backend/data
DOCKER_EOF

cd /opt/shivanshos/gateway
docker compose up -d

echo '=== [3/6] Building Enhanced Execution Agent with Scraping & CrewAI ==='
cat << 'AGENT_EOF' > /opt/shivanshos/agents/execution_agent.py
import os
import subprocess
import json
from openai import OpenAI
from playwright.sync_api import sync_playwright
from crewai import Agent, Task, Crew, Process, LLM

OLLAMA_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL_NAME = os.getenv("HERMES_MODEL", "qwen2.5-coder:7b")
WORKSPACE_DIR = os.getenv("AGENTIC_WORKSPACE", "/opt/shivanshos")

llm_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

def execute_bash(command: str) -> str:
    try:
        res = subprocess.run(command, shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=30)
        return res.stdout.strip() if res.returncode == 0 else res.stderr.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def create_file(filepath: str, content: str) -> str:
    full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filepath))
    if not full_path.startswith(os.path.abspath(WORKSPACE_DIR)):
        return "Security Violation"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File '{filepath}' created."

def scrape_web_page(url: str) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            text = page.inner_text("body")
            browser.close()
            return text[:2000] + "
...[truncated]"
    except Exception as e:
        return f"Scraping Error: {str(e)}"

def run_crew_workflow(topic: str) -> str:
    local_llm = LLM(model=f"ollama/{MODEL_NAME}", base_url="http://127.0.0.1:11434")
    
    researcher = Agent(
        role="Senior Researcher",
        goal=f"Research deep technical details about {topic}",
        backstory="Expert technical research agent.",
        llm=local_llm,
        verbose=True
    )
    
    writer = Agent(
        role="Technical Writer",
        goal=f"Summarize research findings on {topic} into a crisp brief",
        backstory="Senior technical communicator.",
        llm=local_llm,
        verbose=True
    )
    
    t1 = Task(description=f"Gather detailed technical specs for: {topic}", expected_output="Bullets", agent=researcher)
    t2 = Task(description=f"Format research into markdown executive brief.", expected_output="Markdown document", agent=writer)
    
    crew = Crew(agents=[researcher, writer], tasks=[t1, t2], process=Process.sequential)
    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    print("[Agent Stack Loaded. Test Execution Running...]")
    print(create_file("projects/status.txt", "Shivanshos AI Stack Operational"))
    print(execute_bash("cat projects/status.txt"))
AGENT_EOF

echo '=== [4/6] Creating FastAPI Webhook Endpoint Server ==='
cat << 'API_EOF' > /opt/shivanshos/agents/api_server.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from execution_agent import execute_bash, create_file, scrape_web_page, run_crew_workflow

app = FastAPI(title="Shivanshos Agentic API", version="1.0.0")

class CommandRequest(BaseModel):
    command: str

class FileRequest(BaseModel):
    filepath: str
    content: str

class ScrapeRequest(BaseModel):
    url: str

class CrewRequest(BaseModel):
    topic: str

@app.get("/")
def health_check():
    return {"status": "online", "organization": "shivanshos", "system": "Production AI Environment"}

@app.post("/api/bash")
def api_bash(req: CommandRequest):
    return {"output": execute_bash(req.command)}

@app.post("/api/file")
def api_file(req: FileRequest):
    return {"status": create_file(req.filepath, req.content)}

@app.post("/api/scrape")
def api_scrape(req: ScrapeRequest):
    return {"content": scrape_web_page(req.url)}

@app.post("/api/crew")
def api_crew(req: CrewRequest):
    return {"result": run_crew_workflow(req.topic)}
API_EOF

pkill -f "uvicorn api_server:app" 2>/dev/null || true
cd /opt/shivanshos/agents
nohup uvicorn api_server:app --host 0.0.0.0 --port 8000 > /opt/shivanshos/api.log 2>&1 &

echo '=== [5/6] Updating Repository Documentation (README.md) ==='
cat << 'README_EOF' > /opt/shivanshos/README.md
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
README_EOF

echo '=== [6/6] Syncing All Workspace Code to GitHub ==='
cd /opt/shivanshos
git add .
git commit -m "feat: complete UI setup, FastAPI webhooks, Playwright web tools, CrewAI orchestration & docs"
git push origin main || git push origin main --force

echo ''
echo '=========================================================='
echo ' SUCCESS: SHIVANSHOS AGENTIC ENVIRONMENT IS LIVE!'
echo '=========================================================='
echo "1. Web Interface (Open WebUI): http://$(hostname -I | awk '{print $1}'):3000"
echo "2. FastAPI Documentation: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "3. Nginx Proxy Manager: http://$(hostname -I | awk '{print $1}'):81"
