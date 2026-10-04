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
