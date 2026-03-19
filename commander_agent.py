from datetime import datetime
from pathlib import Path
from threading import Thread, Event
import json
import logging
import os
import subprocess
import sys
import time
#!/usr/bin/env python3
"""
commander_agent.py - Autonomous commander that runs master agent automatically
Schedules and executes tasks without manual intervention
"""


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommanderAgent:
    """Autonomous agent that commands other agents automatically"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.running = False
        self.stop_event = Event()
        self.last_results = {}
        self.schedule = {
            "pre_pull": {"interval": 300, "last_run": 0, "enabled": True},      # 5 min
            "analyze": {"interval": 1800, "last_run": 0, "enabled": True},      # 30 min
            "upgrade": {"interval": 3600, "last_run": 0, "enabled": True},        # 1 hour
            "test": {"interval": 600, "last_run": 0, "enabled": True},         # 10 min
            "deploy_check": {"interval": 1800, "last_run": 0, "enabled": True},  # 30 min
        }
        
    def log(self, message, level="info"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {message}"
        if level == "info":
            logger.info(msg)
        elif level == "error":
            logger.error(msg)
        elif level == "warning":
            logger.warning(msg)
        print(msg)
        
    def run_command(self, command, timeout=120):
        """Run a shell command and return output"""
        self.log(f"Executing: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout[:3000],
                "error": result.stderr[:500] if result.stderr else None,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out", "timeout": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_master(self, args):
        """Run master_agent.py with arguments"""
        cmd = f"{sys.executable} master_agent.py {args}"
        return self.run_command(cmd)
    
    def execute_pre_pull(self):
        """Run pre-pull validation"""
        self.log("🎯 Running PRE-PULL validation...")
        result = self.run_master("--pre-pull")
        self.last_results["pre_pull"] = result
        if result.get("success"):
            self.log("✅ Pre-pull check PASSED")
        else:
            self.log(f"❌ Pre-pull check FAILED: {result.get('error', 'Unknown')}", "error")
        return result
    
    def execute_analyze(self):
        """Analyze all agents"""
        self.log("🔍 Running agent analysis...")
        result = self.run_master("--analyze")
        self.last_results["analyze"] = result
        if result.get("success"):
            self.log("✅ Analysis complete")
        else:
            self.log(f"❌ Analysis failed: {result.get('error')}", "error")
        return result
    
    def execute_upgrade(self):
        """Auto-upgrade agents"""
        self.log("🚀 Running auto-upgrade...")
        result = self.run_master("--upgrade")
        self.last_results["upgrade"] = result
        if result.get("success"):
            self.log("✅ Upgrade complete")
        else:
            self.log(f"❌ Upgrade failed: {result.get('error')}", "error")
        return result
    
    def execute_test(self):
        """Run tests"""
        self.log("🧪 Running tests...")
        result = self.run_master("--test")
        self.last_results["test"] = result
        if result.get("success"):
            self.log("✅ Tests passed")
        else:
            self.log(f"❌ Tests failed: {result.get('error')}", "error")
        return result
    
    def execute_deploy_check(self):
        """Full deployment check"""
        self.log("🚀 Running deployment check...")
        result = self.run_master("--deploy-check")
        self.last_results["deploy_check"] = result
        if result.get("success"):
            self.log("✅ Deployment ready!")
        else:
            self.log(f"❌ Deployment check failed: {result.get('error')}", "error")
        return result
    
    def execute_full_cycle(self):
        """Run complete command cycle"""
        self.log("=" * 60)
        self.log("🚀 STARTING AUTONOMOUS COMMAND CYCLE")
        self.log("=" * 60)
        
        # Always run pre-pull first (safety)
        self.execute_pre_pull()
        
        # Run periodic tasks
        current_time = time.time()
        
        if current_time - self.schedule["analyze"]["last_run"] > self.schedule["analyze"]["interval"]:
            self.execute_analyze()
            self.schedule["analyze"]["last_run"] = current_time
            
        if current_time - self.schedule["test"]["last_run"] > self.schedule["test"]["interval"]:
            self.execute_test()
            self.schedule["test"]["last_run"] = current_time
            
        if current_time - self.schedule["upgrade"]["last_run"] > self.schedule["upgrade"]["interval"]:
            self.execute_upgrade()
            self.schedule["upgrade"]["last_run"] = current_time
            
        if current_time - self.schedule["deploy_check"]["last_run"] > self.schedule["deploy_check"]["interval"]:
            self.execute_deploy_check()
            self.schedule["deploy_check"]["last_run"] = current_time
        
        self.log("=" * 60)
        self.log("✅ Command cycle complete")
        self.log("=" * 60)
        
    def continuous_mode(self, interval=300):
        """Run continuously on interval"""
        self.running = True
        self.log(f"🔄 Starting continuous mode (interval: {interval}s)")
        
        while self.running and not self.stop_event.is_set():
            try:
                self.execute_full_cycle()
                self.log(f"💤 Sleeping for {interval}s...")
                self.stop_event.wait(interval)
            except KeyboardInterrupt:
                self.log("⚠️ Interrupted by user")
                break
            except Exception as e:
                self.log(f"❌ Error in continuous mode: {e}", "error")
                time.sleep(60)
                
        self.log("🛑 Continuous mode stopped")
        
    def status_report(self):
        """Generate status report"""
        report = {
            "commander_status": "running" if self.running else "stopped",
            "last_run": datetime.now().isoformat(),
            "schedule": {k: {"interval": v["interval"], "last_run": datetime.fromtimestamp(v["last_run"]).isoformat() if v["last_run"] else "never"} for k, v in self.schedule.items()},
            "last_results": {k: {"success": v.get("success"), "error": v.get("error")[:100] if v.get("error") else None} for k, v in self.last_results.items()}
        }
        return report
    
    def save_state(self, filepath="commander_state.json"):
        """Save state to file"""
        state = {
            "last_results": self.last_results,
            "schedule": {k: {"last_run": v["last_run"], "enabled": v["enabled"]} for k, v in self.schedule.items()}
        }
        with open(self.project_dir / filepath, "w") as f:
            json.dump(state, f, indent=2)
        self.log(f"💾 State saved to {filepath}")
        
    def load_state(self, filepath="commander_state.json"):
        """Load state from file"""
        state_file = self.project_dir / filepath
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            if "schedule" in state:
                for k, v in state["schedule"].items():
                    if k in self.schedule:
                        self.schedule[k]["last_run"] = v.get("last_run", 0)
            self.log(f"📂 State loaded from {filepath}")
    
    def start_daemon(self, interval=300):
        """Start as daemon in background"""
        self.log(f"🚀 Starting commander daemon (interval: {interval}s)")
        thread = Thread(target=self.continuous_mode, args=(interval,))
        thread.daemon = True
        thread.start()
        return thread
    
    def stop(self):
        """Stop the commander"""
        self.running = False
        self.stop_event.set()
        self.save_state()
        self.log("🛑 Commander stopped")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Commander Agent")
    parser.add_argument("--run", action="store_true", help="Run full command cycle once")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as daemon")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval in seconds")
    parser.add_argument("--pre-pull", action="store_true", help="Run pre-pull only")
    parser.add_argument("--analyze", action="store_true", help="Run analyze only")
    parser.add_argument("--upgrade", action="store_true", help="Run upgrade only")
    parser.add_argument("--test", action="store_true", help="Run test only")
    parser.add_argument("--deploy-check", action="store_true", help="Run deploy check")
    parser.add_argument("--status", action="store_true", help="Show status")
    
    args = parser.parse_args()
    
    commander = CommanderAgent()
    commander.load_state()
    
    if args.status:
        print(json.dumps(commander.status_report(), indent=2))
        
    elif args.daemon:
        commander.start_daemon(args.interval)
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            commander.stop()
            
    elif args.run:
        commander.execute_full_cycle()
        
    elif args.pre_pull:
        commander.execute_pre_pull()
        
    elif args.analyze:
        commander.execute_analyze()
        
    elif args.upgrade:
        commander.execute_upgrade()
        
    elif args.test:
        commander.execute_test()
        
    elif args.deploy_check:
        commander.execute_deploy_check()
        
    else:
        print("Commander Agent - Autonomous task runner")
        print("Usage:")
        print("  python commander_agent.py --run           # Run full cycle once")
        print("  python commander_agent.py --daemon       # Run continuously")
        print("  python commander_agent.py --daemon --interval 60  # Every 60s")
        print("  python commander_agent.py --pre-pull     # Pre-pull only")
        print("  python commander_agent.py --analyze      # Analyze only")
        print("  python commander_agent.py --upgrade      # Upgrade only")
        print("  python commander_agent.py --status       # Show status")


if __name__ == "__main__":
    main()
