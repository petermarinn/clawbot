# System monitoring dashboard route - add to web_app.py

@app.route("/system")
def system_dashboard():
    """System monitoring dashboard"""
    import os
    import subprocess
    
    # Get process info
    procs = []
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "python3" in line and ("web_app" in line or "run_system" in line or "agent" in line):
                parts = line.split()
                if len(parts) >= 11:
                    procs.append({
                        "pid": parts[1],
                        "cpu": parts[2],
                        "mem": parts[3],
                        "cmd": " ".join(parts[10:])[:50]
                    })
    except:
        pass
    
    # Read command results for task log
    task_log = []
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            results = mem.get("command_results", [])[-20:]
            for r in results:
                task_log.append({
                    "task": r.get("command", "Unknown"),
                    "status": "completed" if r.get("success") else "failed",
                    "timestamp": r.get("timestamp", "")
                })
    except:
        pass
    
    # System info
    system_info = {
        "status": "running" if procs else "stopped",
        "last_update": datetime.now().isoformat(),
        "active_agents": len(procs),
        "tasks": task_log,
        "processes": procs
    }
    
    html = """<!DOCTYPE html>
<html>
<head>
<title>System Monitor - Clawbot</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #30363d; }
h1 { color: #58a6ff; }
h2 { color: #8b949e; margin: 20px 0 10px; font-size: 16px; text-transform: uppercase; }
.status-badge { padding: 8px 16px; border-radius: 20px; font-weight: bold; }
.running { background: #238636; color: white; }
.stopped { background: #da3633; color: white; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
.card { background: #161b22; border-radius: 12px; padding: 20px; border: 1px solid #30363d; }
.card-title { color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }
.value { font-size: 24px; font-weight: bold; color: #58a6ff; }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }
.row:last-child { border: none; }
.success { color: #3fb950; }
.error { color: #f85149; }
.timestamp { color: #8b949e; font-size: 11px; }
.process { background: #21262d; padding: 10px; margin: 5px 0; border-radius: 6px; font-size: 12px; }
.process span { color: #58a6ff; }
.back-btn { background: #238636; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }
</style>
<meta http-equiv="refresh" content="5">
</head>
<body>
<div class="header">
<a href="/" class="back-btn">Back</a>
<h1>System Monitor</h1>
</div>
<div class="grid">
<div class="card">
<div class="card-title">System Status</div>
<div class="value">
<span class="status-badge running">RUNNING</span>
</div>
</div>
<div class="card">
<div class="card-title">Last Update</div>
<div class="value" style="font-size:16px;">DATETIME</div>
</div>
<div class="card">
<div class="card-title">Active Agents</div>
<div class="value">COUNT</div>
</div>
</div>
<h2>Recent Tasks</h2>
<div class="card">TASKS</div>
<h2>Running Processes</h2>
<div class="card">PROCESSES</div>
<div style="text-align:center; margin-top:30px; color:#8b949e; font-size:12px;">
Auto-refreshing every 5 seconds
</div>
</body>
</html>"""
    
    # Build task rows
    task_rows = ""
    for t in task_log:
        status_class = "success" if t["status"] == "completed" else "error"
        ts = t["timestamp"][:19] if t["timestamp"] else ""
        task_rows += f"<div class='row'><span class='{status_class}'>{t['task']}</span><span class='timestamp'>{ts}</span></div>"
    
    # Build process rows
    proc_rows = ""
    for p in procs:
        proc_rows += f"<div class='process'><span>PID {p['pid']}</span> - CPU {p['cpu']}% - {p['cmd']}</div>"
    if not proc_rows:
        proc_rows = "<div class='row'>No processes running</div>"
    
    html = html.replace("RUNNING", system_info["status"].upper())
    html = html.replace("DATETIME", system_info["last_update"][:19])
    html = html.replace("COUNT", str(system_info["active_agents"]))
    html = html.replace("TASKS", task_rows if task_rows else "<div class='row'>No tasks yet</div>")
    html = html.replace("PROCESSES", proc_rows)
    
    if system_info["status"] != "running":
        html = html.replace('class="status-badge running"', 'class="status-badge stopped"')
    
    return html
