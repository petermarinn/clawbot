import os
import json
import re
import time
import requests
import subprocess
from duckduckgo_search import DDGS

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

API_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:3b"

BASE_DIR = os.path.expanduser("~/clawbot")
WORKSPACE = os.path.join(BASE_DIR, "workspace")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
QUEUE_FILE = os.path.join(BASE_DIR, "task_queue.json")

os.makedirs(WORKSPACE, exist_ok=True)

# --------------------------------------------------
# MEMORY
# --------------------------------------------------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"completed_tasks": []}
    with open(MEMORY_FILE) as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# --------------------------------------------------
# TASK QUEUE
# --------------------------------------------------

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

# --------------------------------------------------
# MODEL CALL
# --------------------------------------------------

def ask_model(prompt):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=900)
        data = r.json()
    except Exception as e:
        print("Model connection error:", e)
        return ""

    if "response" in data:
        return data["response"]

    if "message" in data:
        return data["message"].get("content", "")

    return ""

# --------------------------------------------------
# JSON PARSER
# --------------------------------------------------

def parse_json(text):

    if not text:
        return None

    text = text.replace("```json", "").replace("```", "")

    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        return None

    try:
        return json.loads(match.group())
    except:
        return None

# --------------------------------------------------
# WORKSPACE FILES
# --------------------------------------------------

def get_workspace_files():

    files = []

    for root, dirs, filenames in os.walk(WORKSPACE):
        for f in filenames:
            files.append(os.path.relpath(os.path.join(root, f), WORKSPACE))

    return files

# --------------------------------------------------
# FILE OPERATIONS
# --------------------------------------------------

def write_file(path, content):

    full_path = os.path.join(WORKSPACE, path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as f:
        f.write(content)

    print("Created file:", path)

def edit_file(path, content):

    full_path = os.path.join(WORKSPACE, path)

    if not os.path.exists(full_path):
        print("File not found for edit:", path)
        return

    with open(full_path, "w") as f:
        f.write(content)

    print("Edited file:", path)

# --------------------------------------------------
# COMMAND RUNNER
# --------------------------------------------------

def run_command(command):

    print("Running:", command)

    subprocess.run(command, shell=True, cwd=WORKSPACE)

# --------------------------------------------------
# TESTER
# --------------------------------------------------

def tester(file_path):

    if not file_path.endswith(".py"):
        return

    print("Testing:", file_path)

    subprocess.run(f"python {file_path}", shell=True, cwd=WORKSPACE)

# --------------------------------------------------
# DEPENDENCY DETECTOR
# --------------------------------------------------

def detect_dependencies(code):

    imports = re.findall(r"import (\w+)", code)

    for lib in imports:
        if lib not in ["os", "sys", "json", "re", "time"]:
            subprocess.run(f"pip install {lib}", shell=True)

# --------------------------------------------------
# DEBUGGER
# --------------------------------------------------

def debugger(error):

    prompt = f"""
You are a debugging AI.

Error:
{error}

Explain briefly what went wrong and how to fix it.
"""

    return ask_model(prompt)

# --------------------------------------------------
# WEB SEARCH
# --------------------------------------------------

def web_search(query):

    results = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(r["title"] + " - " + r["href"])
    except:
        pass

    return "\n".join(results)

# --------------------------------------------------
# GITHUB SEARCH
# --------------------------------------------------

def github_search(query):

    try:
        r = requests.get(
            f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        )

        data = r.json()

        repos = []

        for item in data.get("items", [])[:3]:
            repos.append(item["html_url"])

        return "\n".join(repos)

    except:
        return ""

# --------------------------------------------------
# GIT COMMIT
# --------------------------------------------------

def git_commit():

    try:
        subprocess.run("git add .", shell=True, cwd=WORKSPACE)
        subprocess.run('git commit -m "AI update"', shell=True, cwd=WORKSPACE)
    except:
        pass

# --------------------------------------------------
# AGENTS
# --------------------------------------------------

def manager(queue):

    if queue:
        task = queue.pop(0)
        save_queue(queue)
        print("\nManager (from queue):", task)
        return task

    files = get_workspace_files()

    prompt = f"""
You are the CEO of an autonomous AI software development system.

Existing workspace files:
{files}

Choose the next useful Python project or tool.

Focus on:
- automation scripts
- CLI tools
- web scrapers
- developer tools
- data processors

Never create coding exercises.

Return one project idea.
"""

    task = ask_model(prompt)

    print("\nManager:", task)

    return task

def researcher(task):

    web = web_search(task)
    github = github_search(task)

    prompt = f"""
You are a research agent.

Task:
{task}

Web research:
{web}

GitHub projects:
{github}

Explain briefly how to implement this in Python.
"""

    research = ask_model(prompt)

    print("Research:", research)

    return research

def planner(task, research):

    prompt = f"""
You are a software planner.

Task:
{task}

Research:
{research}

Create ONE actionable development step.
"""

    step = ask_model(prompt)

    print("Planner:", step)

    return step

def coder(step):

    prompt = f"""
You are a coding AI.

Convert the step into JSON.

Allowed actions:

write_file
edit_file
run_command

Example:

{{
 "action":"write_file",
 "path":"tool.py",
 "content":"print('hello')"
}}

Step:
{step}
"""

    code = ask_model(prompt)

    print("Coder:", code)

    return code

# --------------------------------------------------
# EXECUTOR
# --------------------------------------------------

def execute(action):

    if not action:
        print("No valid action returned")
        return

    if action.get("action") == "write_file":

        path = action["path"]
        content = action["content"]

        detect_dependencies(content)

        write_file(path, content)

        tester(path)

        git_commit()

    elif action.get("action") == "edit_file":

        edit_file(action["path"], action["content"])

        tester(action["path"])

        git_commit()

    elif action.get("action") == "run_command":

        run_command(action["command"])

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

def loop():

    print("Autonomous developer system started\n")

    memory = load_memory()
    queue = load_queue()

    while True:

        try:

            task = manager(queue)

            research = researcher(task)

            step = planner(task, research)

            code = coder(step)

            action = parse_json(code)

            execute(action)

            memory["completed_tasks"].append(task)

            save_memory(memory)

        except Exception as e:

            print("Execution error:", e)

            debug = debugger(str(e))

            print("Debugger:", debug)

        time.sleep(5)

# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":
    loop()
