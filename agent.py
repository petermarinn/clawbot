import requests
import subprocess
import os
import time

MODEL = "qwen2.5:0.5b"
OLLAMA = "http://localhost:11434/api/generate"

WORKSPACE = os.getcwd()

SYSTEM_PROMPT = f"""
You are an autonomous software engineer.

You can:
- write code
- edit files
- delete files
- run Linux commands
- improve your own code

Workspace: {WORKSPACE}

Respond with bash commands or code blocks.
"""


def ask_llm(prompt):
    r = requests.post(
        OLLAMA,
        json={
            "model": MODEL,
            "prompt": SYSTEM_PROMPT + "\nTask:\n" + prompt,
            "stream": False
        }
    )
    return r.json()["response"]


def run_command(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=WORKSPACE
    )
    return result.stdout + result.stderr


def agent_loop():
    goal = """
Continuously improve the software in this folder.
Create tools, scripts, and improvements.
"""

    while True:
        response = ask_llm(goal)

        print("\nAgent output:\n", response)

        if "```bash" in response:
            cmd = response.split("```bash")[1].split("```")[0]
            print("\nRunning:", cmd)
            print(run_command(cmd))

        time.sleep(10)


if __name__ == "__main__":
    agent_loop()
