import os
import subprocess
import json
import re
from openai import OpenAI

OLLAMA_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL_NAME = os.getenv("HERMES_MODEL", "qwen2.5-coder:7b")
WORKSPACE_DIR = os.getenv("AGENTIC_WORKSPACE", "/opt/shivanshos")

llm = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

def execute_bash(command: str) -> str:
    print(f"\n[Tool Execution] Running Bash Command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return output.strip() if output else "Command executed successfully with no output."
    except Exception as e:
        return f"Execution Error: {str(e)}"

def create_file(filepath: str, content: str) -> str:
    full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filepath))
    if not full_path.startswith(os.path.abspath(WORKSPACE_DIR)):
        return "Security Violation: Cannot write outside workspace."
        
    print(f"\n[Tool Execution] Creating File: {full_path}")
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filepath}' successfully created."
    except Exception as e:
        return f"File Creation Error: {str(e)}"

def dispatch_tool(name: str, args: dict):
    if name == "create_file":
        res = create_file(args.get("filepath", ""), args.get("content", ""))
        print(f"[Tool Result]: {res}")
    elif name == "execute_bash":
        res = execute_bash(args.get("command", ""))
        print(f"[Tool Result]: {res}")
    else:
        print(f"[Unknown Tool]: {name}")

def parse_and_execute_raw_json(content: str) -> bool:
    """Fallback parser for models outputting JSON tool calls in text."""
    lines = content.strip().split("\n")
    executed = False
    for line in lines:
        line = line.strip().strip("`")
        if line.startswith("json"):
            line = line[4:].strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict) and "name" in data and "arguments" in data:
                dispatch_tool(data["name"], data["arguments"])
                executed = True
        except json.JSONDecodeError:
            continue
    return executed

def run_agent_task(prompt: str):
    print(f"\n=======================================================")
    print(f"[User Goal]: {prompt}")
    print(f"=======================================================")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Create a file in workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["filepath", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_bash",
                "description": "Execute bash command in workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }
        }
    ]

    response = llm.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an autonomous execution agent. Perform tool actions to fulfill user goals."},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message
    
    # Path 1: Native API Tool Calls
    if msg.tool_calls:
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            dispatch_tool(tool_call.function.name, args)
    # Path 2: Text JSON Fallback Parser
    elif msg.content:
        success = parse_and_execute_raw_json(msg.content)
        if not success:
            print(f"[Agent Response]: {msg.content}")

if __name__ == "__main__":
    run_agent_task("Create a python script at 'projects/sys_check.py' that prints system memory usage using psutil or os module, then execute it with python3.")
