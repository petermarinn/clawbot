#!/usr/bin/env python3
"""
Orchestrator Agent - Execution Control Layer
Manages task lifecycle: pending → running → completed/failed
Prevents duplicate execution, handles retries
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

COMMANDS_FILE = "commander_commands.json"
MEMORY_FILE = "memory.json"
LOG_FILE = "logs.json"

# Get project directory dynamically
PROJECT_DIR = Path(__file__).parent.resolve()


class OrchestratorAgent:
    def __init__(self):
        self.commands_file = COMMANDS_FILE
        self.memory_file = MEMORY_FILE
        self.log_file = LOG_FILE
        self.max_retries = 1  # Max 1 retry per failed task
        self.max_running_time = 300  # 5 minutes max per task
        
    def load_commands(self):
        """Load commands from file"""
        try:
            with open(self.commands_file) as f:
                return json.load(f)
        except:
            return {"commands": [], "timestamp": datetime.now().isoformat()}
    
    def save_commands(self, commands):
        """Save commands to file"""
        commands["timestamp"] = datetime.now().isoformat()
        with open(self.commands_file, 'w') as f:
            json.dump(commands, f, indent=2)
    
    def load_memory(self):
        """Load memory.json"""
        try:
            with open(self.memory_file) as f:
                return json.load(f)
        except:
            return {}
    
    def save_memory(self, memory):
        """Save memory.json"""
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
    
    def log(self, event_type, message, details=None):
        """Log event"""
        try:
            with open(self.log_file) as f:
                logs = json.load(f)
        except:
            logs = {"events": []}
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "source": "orchestrator",
            "message": message,
            "details": details or {}
        }
        logs.setdefault("events", []).append(event)
        
        # Keep last 1000 events
        if len(logs["events"]) > 1000:
            logs["events"] = logs["events"][-1000:]
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def get_pending_tasks(self):
        """Get all pending tasks (not running, completed, or failed)"""
        commands = self.load_commands()
        pending = []
        
        for cmd in commands.get("commands", []):
            status = cmd.get("status", "pending")
            if status == "pending":
                # Check retry count
                retry_count = cmd.get("retry_count", 0)
                if retry_count <= self.max_retries:
                    pending.append(cmd)
        
        return pending
    
    def get_running_tasks(self):
        """Get all running tasks"""
        commands = self.load_commands()
        return [cmd for cmd in commands.get("commands", []) if cmd.get("status") == "running"]
    
    def update_task_status(self, task_id, status, result=None, error=None):
        """Update task status"""
        commands = self.load_commands()
        
        for cmd in commands.get("commands", []):
            if cmd.get("id") == task_id or cmd.get("title") == task_id:
                cmd["status"] = status
                cmd["updated_at"] = datetime.now().isoformat()
                
                if status == "running":
                    cmd["started_at"] = datetime.now().isoformat()
                elif status == "completed":
                    cmd["completed_at"] = datetime.now().isoformat()
                    cmd["result"] = result
                elif status == "failed":
                    cmd["retry_count"] = cmd.get("retry_count", 0) + 1
                    cmd["error"] = error
                    cmd["last_attempt"] = datetime.now().isoformat()
                
                break
        
        self.save_commands(commands)
    
    def check_stuck_tasks(self):
        """Check for stuck running tasks"""
        commands = self.load_commands()
        stuck_tasks = []
        
        for cmd in commands.get("commands", []):
            if cmd.get("status") == "running":
                started = cmd.get("started_at")
                if started:
                    try:
                        start_time = datetime.fromisoformat(started)
                        runtime = (datetime.now() - start_time).total_seconds()
                        
                        if runtime > self.max_running_time:
                            stuck_tasks.append(cmd)
                    except:
                        pass
        
        # Mark stuck tasks as failed
        for task in stuck_tasks:
            self.log("WARNING", f"Task stuck - marking as failed: {task.get('title')}")
            self.update_task_status(task.get("title"), "failed", error="Task timed out")
        
        return stuck_tasks
    
    def execute_task(self, task):
        """Execute a single task by routing to appropriate agent"""
        task_id = task.get("id") or task.get("title")
        target_agent = task.get("target_agent", "unknown")
        
        print(f"\n{'='*50}")
        print(f"⚡ ORCHESTRATOR EXECUTING: {task_id}")
        print(f"🎯 Target Agent: {target_agent}")
        print(f"{'='*50}")
        
        self.log("TASK_START", f"Starting task: {task_id}", {"agent": target_agent})
        
        # Update status to running
        self.update_task_status(task_id, "running")
        
        try:
            # Route to appropriate agent
            result = self.route_to_agent(target_agent, task)
            
            # Task completed successfully
            self.update_task_status(task_id, "completed", result=result)
            self.log("TASK_COMPLETE", f"Task completed: {task_id}", {"result": result})
            
            print(f"\n✅ Task completed: {task_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Task failed: {task_id}")
            print(f"   Error: {error_msg}")
            
            self.update_task_status(task_id, "failed", error=error_msg)
            self.log("TASK_FAILED", f"Task failed: {task_id}", {"error": error_msg})
            
            return False
    
    def route_to_agent(self, agent_name, task):
        """Route task to the appropriate agent for execution"""

        # Map agent names to their files/modules
        agent_map = {
            "master_agent": "master_agent.py",
            "website_agent": "website_agent.py",
            "news_agent": "news_agent.py",
            "stock_agent": "stock_agent.py",
            "portfolio_agent": "portfolio_agent.py",
            "debugger_agent": "debugger_agent.py",
            "tester_agent": "tester_agent.py",
            "installer_agent": "installer_agent.py",
            "self_upgrade_agent": "self_upgrade_agent.py",
            "alert_agent": "alert_agent.py",
            "data_intelligence": "data_intelligence.py",
        }

        # Get the agent file
        agent_file = agent_map.get(agent_name)
        if not agent_file:
            print(f"   ⚠️ Unknown agent: {agent_name}")
            return {"success": False, "error": f"Unknown agent: {agent_name}"}

        # Build command arguments from requirements
        task_req = task.get("requirements", {})
        args = []

        # Handle different requirement formats
        if "command" in task_req:
            args = task_req["command"].split()
        elif "action" in task_req:
            args = ["--action", task_req["action"]]

        # Add any additional requirements as args
        for key, value in task_req.items():
            if key not in ["command", "action"]:
                args.extend([f"--{key}", str(value)])

        # Execute the agent as a subprocess
        print(f"\n{'='*50}")
        print(f"Running: {agent_name} ({agent_file})")
        print(f"Args: {args}")
        print(f"{'='*50}")

        agent_path = PROJECT_DIR / agent_file
        if not agent_path.exists():
            print(f"   ⚠️ Agent file not found: {agent_file}")
            return {"success": False, "error": f"Agent file not found: {agent_file}"}

        cmd = [sys.executable, agent_file]
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr[:500]}")

            success = result.returncode == 0
            return {
                "success": success,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            print(f"   ❌ Agent timed out: {agent_name}")
            return {"success": False, "error": "Task timed out"}
        except Exception as e:
            print(f"   ❌ Error running {agent_name}: {e}")
            return {"success": False, "error": str(e)}

    def execute_debugger_task(self, task):
        """Execute a debugger/fix task"""
        task_req = task.get("requirements", {})
        issue_type = task_req.get("type", "unknown")
        
        print(f"   🔧 Debugger handling: {issue_type}")
        
        # Simulate fix
        return f"Fixed issue: {issue_type}"
    
    def run(self):
        """Main orchestrator loop - execute pending tasks"""
        print("\n" + "="*60)
        print("⚡ ORCHESTRATOR AGENT - TASK EXECUTION")
        print("="*60)
        
        # Step 1: Check for stuck tasks
        stuck = self.check_stuck_tasks()
        if stuck:
            print(f"\n⚠️  Found {len(stuck)} stuck tasks - marked as failed")
        
        # Step 2: Get pending tasks
        pending = self.get_pending_tasks()
        
        if not pending:
            print("\n✅ No pending tasks")
            return {"executed": 0, "status": "idle"}
        
        print(f"\n📋 Found {len(pending)} pending tasks")
        
        # Step 3: Execute each pending task
        executed = 0
        failed = 0
        
        for task in pending:
            task_id = task.get("title", "unknown")
            
            success = self.execute_task(task)
            
            if success:
                executed += 1
            else:
                failed += 1
        
        # Step 4: Update memory
        memory = self.load_memory()
        memory["orchestrator"] = {
            "last_run": datetime.now().isoformat(),
            "tasks_executed": executed,
            "tasks_failed": failed,
            "pending_count": len(self.get_pending_tasks())
        }
        self.save_memory(memory)
        
        result = {
            "executed": executed,
            "failed": failed,
            "status": "complete" if executed > 0 else "idle"
        }
        
        print(f"\n{'='*50}")
        print(f"📊 ORCHESTRATOR RESULT: {executed} executed, {failed} failed")
        print(f"{'='*50}")
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Orchestrator Agent - Task Execution")
    parser.add_argument("--execute", action="store_true", help="Execute pending tasks")
    parser.add_argument("--status", action="store_true", help="Show task status")
    parser.add_argument("--clear-failed", action="store_true", help="Clear failed tasks")
    
    args = parser.parse_args()
    
    orchestrator = OrchestratorAgent()
    
    if args.status:
        # Show status
        commands = orchestrator.load_commands()
        print("\n📋 Task Status:")
        print("-" * 40)
        
        pending = orchestrator.get_pending_tasks()
        running = orchestrator.get_running_tasks()
        
        print(f"Pending: {len(pending)}")
        print(f"Running: {len(running)}")
        
        for cmd in commands.get("commands", [])[-10:]:
            status = cmd.get("status", "unknown")
            title = cmd.get("title", "unknown")
            print(f"  [{status}] {title}")
    
    elif args.clear_failed:
        # Clear failed tasks
        commands = orchestrator.load_commands()
        commands["commands"] = [c for c in commands.get("commands", []) 
                             if c.get("status") != "failed"]
        orchestrator.save_commands(commands)
        print("✅ Cleared failed tasks")
    
    else:
        # Execute tasks
        result = orchestrator.run()
        print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
