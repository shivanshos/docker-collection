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
