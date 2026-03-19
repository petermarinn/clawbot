import json
import os
import requests
import subprocess
import time

MODEL = "qwen2.5:0.5b"
OLLAMA = "http://localhost:11434/api/generate"
WORKSPACE = os.getcwd()

SYSTEM_PROMPT = f"""
You are an autonomous software engineer.

You can:
- write and modify code
- create/delete files
- run shell commands
- refactor and improve your own programs
- create new tools and scripts

Workspace: {WORKSPACE}

Respond ONLY in JSON:

{{
 "action": "write_file | run_command | delete_file",
 "path": "file if needed",
 "content": "code if writing",
 "command": "shell command if running"
}}
"""


def ask_llm(prompt):
    try:
        r = requests.post(
            OLLAMA,
            json={
                "model": MODEL,
                "prompt": SYSTEM_PROMPT + "\nTask:\n" + prompt,
                "stream": False
            },
            timeout=60
        )
        logger.info("Status: {r.status_code}")
        logger.info("Response: {r.text[:200]}")
        data = r.json()
        return data.get("response", "") or data.get("message", {}).get("content", "")
    except Exception as e:
        logger.info("LLM Error: {e}")
        return ""


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def delete_file(path):
    if os.path.exists(path):
        os.remove(path)


def run_command(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=WORKSPACE
    )
    return result.stdout + result.stderr


def execute(action_json):
    try:
        action = json.loads(action_json)

        if action["action"] == "write_file":
            write_file(action["path"], action["content"])
            print("Wrote:", action["path"])

        elif action["action"] == "delete_file":
            delete_file(action["path"])
            print("Deleted:", action["path"])

        elif action["action"] == "run_command":
            print(run_command(action["command"]))

    except Exception as e:
        print("Agent error:", e)


def agent_loop():
    goal = """
Continuously improve the software in this folder.
Build useful developer tools and enhance your own code.
"""

    while True:
        response = ask_llm(goal)
        print("\nAgent decision:\n", response)
        execute(response)
        time.sleep(5)


if __name__ == "__main__":
    agent_loop()
