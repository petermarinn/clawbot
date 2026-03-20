#!/usr/bin/env python3
"""
Supervisor Agent (Watchdog) - Keeps the system running 24/7
Monitors health, detects crashes/freeze, auto-restarts
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_FILE = "memory.json"
LOG_FILE = "logs.json"
SYSTEM_PID_FILE = "/tmp/clawbot_system.pid"

class SupervisorAgent:
    def __init__(self):
        self.memory = self.load_memory()
        self.logs = self.load_logs()
        self.health_check_interval = 30  # seconds
        self.freeze_threshold = 120  # seconds - considered frozen if no update
        self.crash_threshold = 3  # max crashes before alert
        
    def load_memory(self):
        """Load memory.json"""
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except:
            return {"supervisor": {}, "agents": {}}
    
    def load_logs(self):
        """Load logs.json"""
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except:
            return {"events": []}
    
    def save_memory(self):
        """Save memory.json"""
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def log(self, event_type, message, details=None):
        """Log an event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "details": details or {}
        }
        self.logs.setdefault("events", []).append(event)
        # Keep only last 1000 events
        if len(self.logs["events"]) > 1000:
            self.logs["events"] = self.logs["events"][-1000:]
        
        with open(LOG_FILE, 'w') as f:
            json.dump(self.logs, f, indent=2)
        
        print(f"[{event_type}] {message}")
    
    def check_system_health(self):
        """Check if system components are healthy"""
        health = {
            "status": "healthy",
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check 1: Last system cycle
        last_cycle = self.memory.get("last_system_run")
        if last_cycle:
            try:
                last_time = datetime.fromisoformat(last_cycle)
                age = (datetime.now() - last_time).total_seconds()
                
                if age > self.freeze_threshold:
                    health["status"] = "frozen"
                    health["issues"].append(f"No cycle for {int(age)}s (threshold: {self.freeze_threshold}s)")
                elif age > 60:
                    health["issues"].append(f"Slow cycle: {int(age)}s")
            except:
                pass
        
        # Check 2: Memory file integrity
        try:
            with open(MEMORY_FILE) as f:
                json.load(f)
        except json.JSONDecodeError:
            health["status"] = "corrupted"
            health["issues"].append("memory.json corrupted")
        
        # Check 3: Command file issues
        try:
            with open("commander_commands.json") as f:
                commands = json.load(f)
                # Check for stuck running tasks
                for cmd in commands.get("commands", []):
                    if cmd.get("status") == "running":
                        # Check if running too long
                        started = cmd.get("started_at")
                        if started:
                            try:
                                start_time = datetime.fromisoformat(started)
                                runtime = (datetime.now() - start_time).total_seconds()
                                if runtime > 300:  # 5 min max
                                    health["issues"].append(f"Task stuck: {cmd.get('title')}")
                            except:
                                pass
        except:
            pass
        
        # Check 4: Crash count
        crash_count = self.memory.get("supervisor", {}).get("crash_count", 0)
        if crash_count >= self.crash_threshold:
            health["status"] = "critical"
            health["issues"].append(f"Multiple crashes: {crash_count}")
        
        return health
    
    def restart_component(self, component):
        """Restart a specific component"""
        self.log("RESTART", f"Attempting to restart {component}")
        
        if component == "system":
            # Kill and restart run_system.py
            os.system("pkill -f 'run_system.py'")
            time.sleep(2)
            proj_dir = Path(__file__).parent
os.system(f"cd {proj_dir} && python3 run_system.py --continuous os.system("cd /workspace/project/clawbot && python3 run_system.py --continuous &")")
            
            # Update crash count
            self.memory.setdefault("supervisor", {})
            self.memory["supervisor"]["crash_count"] = self.memory["supervisor"].get("crash_count", 0) + 1
            self.save_memory()
            
            self.log("RESTART", f"System restarted (crash #{self.memory['supervisor']['crash_count']})")
        
        elif component == "web":
            os.system("pkill -f 'web_app.py'")
            time.sleep(2)
            proj_dir = Path(__file__).parent
os.system(f"cd {proj_dir} && python3 web_app.py os.system("cd /workspace/project/clawbot && python3 web_app.py &")")
            self.log("RESTART", "Web server restarted")
    
    def run_health_check(self):
        """Run a single health check"""
        print("\n" + "="*50)
        print("🏥 SUPERVISOR HEALTH CHECK")
        print("="*50)
        
        health = self.check_system_health()
        
        print(f"\nStatus: {health['status'].upper()}")
        
        if health['issues']:
            print("\nIssues found:")
            for issue in health['issues']:
                print(f"  ⚠️  {issue}")
        
        # Update memory with health status
        self.memory.setdefault("supervisor", {})["last_health_check"] = health["timestamp"]
        self.memory["supervisor"]["last_health_status"] = health["status"]
        self.save_memory()
        
        # Take action if needed
        if health["status"] == "frozen" or health["status"] == "critical":
            self.log("ALERT", f"System {health['status']} - attempting recovery")
            self.restart_component("system")
            return False
        
        return len(health['issues']) == 0
    
    def continuous_monitoring(self, interval=30):
        """Run continuous monitoring loop"""
        print("\n" + "="*60)
        print("👁️  SUPERVISOR AGENT - CONTINUOUS MONITORING")
        print("="*60)
        print(f"Health check every {interval} seconds")
        print(f"Freeze threshold: {self.freeze_threshold}s")
        print(f"Crash threshold: {self.crash_threshold}")
        print("="*60 + "\n")
        
        self.log("START", "Supervisor agent started")
        
        while True:
            try:
                self.run_health_check()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("STOP", "Supervisor agent stopped")
                break
            except Exception as e:
                print(f"Error in health check: {e}")
                self.log("ERROR", f"Health check failed: {e}")
                time.sleep(interval)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Supervisor Agent - System Watchdog")
    parser.add_argument("--check", action="store_true", help="Run single health check")
    parser.add_argument("--interval", type=int, default=30, help="Health check interval (seconds)")
    parser.add_argument("--freeze-threshold", type=int, default=120, help="Freeze threshold (seconds)")
    
    args = parser.parse_args()
    
    supervisor = SupervisorAgent()
    supervisor.freeze_threshold = args.freeze_threshold
    
    if args.check:
        # Single health check
        supervisor.run_health_check()
    else:
        # Continuous monitoring
        supervisor.continuous_monitoring(args.interval)


if __name__ == "__main__":
    main()
