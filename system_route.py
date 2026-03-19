# System monitoring dashboard route - add to web_app.py

@app.route("/system")
def system_dashboard():
    """System monitoring dashboard - tracks logical agents"""
    from datetime import datetime
    
    # Read agent tracking from memory
    agents = {}
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            agents = mem.get("agents", {})
            # Update commander/master as "running" since they're active
            if "commander_agent" in agents:
                agents["commander_agent"]["status"] = "running"
            if "master_agent" in agents:
                agents["master_agent"]["status"] = "running"
    except:
        pass
    
    # Count statuses
    running = sum(1 for a in agents.values() if a.get("status") == "running")
    idle = sum(1 for a in agents.values() if a.get("status") == "idle")
    
    # Build agent rows
    agent_rows = ""
    for name, info in agents.items():
        status = info.get("status", "unknown")
        last = info.get("last_active", "Never")
        if last and len(str(last)) > 19:
            last = str(last)[:19]
        
        # Color based on status
        if status == "running":
            color = "#3fb950"
            icon = "🟢"
        elif status == "idle":
            color = "#d29922"
            icon = "🟡"
        else:
            color = "#f85149"
            icon = "🔴"
        
        display_name = name.replace("_agent", "").replace("_", " ").title()
        agent_rows += f"""<div class='agent-row'>
            <span class='agent-icon'>{icon}</span>
            <span class='agent-name'>{display_name}</span>
            <span class='agent-status' style='color:{color}'>{status.upper()}</span>
            <span class='agent-time'>{last}</span>
        </div>"""
    
    # Read task log from memory
    task_log = []
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            results = mem.get("command_results", [])[-10:]
            for r in results:
                task_log.append({
                    "task": r.get("command", "Unknown"),
                    "status": "completed" if r.get("success") else "failed",
                    "timestamp": r.get("timestamp", "")
                })
    except:
        pass
    
    # Build task rows
    task_rows = ""
    for t in task_log:
        status_class = "success" if t["status"] == "completed" else "error"
        ts = t["timestamp"][:19] if t["timestamp"] else ""
        task_rows += f"<div class='task-row'><span class='{status_class}'>{t['task']}</span><span class='timestamp'>{ts}</span></div>"
    
    # System status
    system_status = "RUNNING" if agents else "STOPPED"
    status_class = "running" if agents else "stopped"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<title>System Monitor - Clawbot</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #30363d; }}
h1 {{ color: #58a6ff; }}
h2 {{ color: #8b949e; margin: 20px 0 10px; font-size: 16px; text-transform: uppercase; }}
.status-badge {{ padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
.running {{ background: #238636; color: white; }}
.stopped {{ background: #da3633; color: white; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.card {{ background: #161b22; border-radius: 12px; padding: 20px; border: 1px solid #30363d; }}
.card-title {{ color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
.value {{ font-size: 28px; font-weight: bold; color: #58a6ff; }}
.row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }}
.row:last-child {{ border: none; }}
.success {{ color: #3fb950; }}
.error {{ color: #f85149; }}
.timestamp {{ color: #8b949e; font-size: 11px; }}
.agent-row {{ display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #30363d; }}
.agent-icon {{ font-size: 16px; }}
.agent-name {{ flex: 1; color: #c9d1d9; }}
.agent-status {{ font-weight: bold; font-size: 12px; }}
.agent-time {{ color: #8b949e; font-size: 11px; }}
.task-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }}
.back-btn {{ background: #238636; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }}
.summary {{ display: flex; gap: 20px; margin-bottom: 20px; }}
.summary-item {{ background: #21262d; padding: 10px 20px; border-radius: 8px; }}
.summary-num {{ font-size: 24px; font-weight: bold; color: #58a6ff; }}
.summary-label {{ font-size: 11px; color: #8b949e; }}
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
<span class="status-badge {status_class}">{system_status}</span>
</div>
</div>
<div class="card">
<div class="card-title">Last Update</div>
<div class="value" style="font-size:16px;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
</div>
</div>

<div class="summary">
<div class="summary-item">
<div class="summary-num">{running}</div>
<div class="summary-label">Running</div>
</div>
<div class="summary-item">
<div class="summary-num">{idle}</div>
<div class="summary-label">Idle</div>
</div>
<div class="summary-item">
<div class="summary-num">{len(agents)}</div>
<div class="summary-label">Total Agents</div>
</div>
</div>

<h2>Agent Status</h2>
<div class="card">
{agent_rows if agent_rows else '<div class="row">No agents tracked</div>'}
</div>

<h2>Recent Tasks</h2>
<div class="card">
{task_rows if task_rows else '<div class="row">No tasks yet</div>'}
</div>

<div style="text-align:center; margin-top:30px; color:#8b949e; font-size:12px;">
Auto-refreshing every 5 seconds
</div>
</body>
</html>"""
    return html
