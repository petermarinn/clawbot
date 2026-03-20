#!/usr/bin/env python3
"""
RUN SYSTEM - Main Loop
=====================
This is the main orchestration loop that:
1. Supervisor health check
2. Runs Commander
3. Gets commands
4. Orchestrator executes tasks via Master
5. Updates memory/state
6. Repeats
"""

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.resolve()

# Import supervisor for health checks
def run_supervisor_check():
    """Run supervisor health check"""
    try:
        result = subprocess.run(
            [sys.executable, "supervisor_agent.py", "--check"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except:
        return False


class SystemRunner:
    """Main system orchestration loop"""
    
    def __init__(self):
        self.running = True
        self.memory_file = PROJECT_DIR / "memory.json"
        self.commands_file = PROJECT_DIR / "commander_commands.json"
        self.load_state()
        
    def load_state(self):
        """Load memory state"""
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                self.memory = json.load(f)
        else:
            self.memory = {}
            
    def save_state(self):
        """Save memory state"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
            
    def run_commander(self):
        """Step 1: Run Commander to get commands"""
        print("\n" + "="*60)
        print("STEP 1: RUN COMMANDER")
        print("="*60)
        
        result = subprocess.run(
            [sys.executable, "commander_agent.py", "--run"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Commander executed successfully")
            return True
        else:
            print(f"❌ Commander failed: {result.stderr}")
            return False
            
    def get_commands(self):
        """Step 2: Get commands from Commander"""
        print("\n" + "="*60)
        print("STEP 2: GET COMMANDS")
        print("="*60)
        
        if self.commands_file.exists():
            with open(self.commands_file) as f:
                data = json.load(f)
                commands = data.get("commands", [])
                print(f"📋 Found {len(commands)} commands")
                return commands
        return []
        
    def execute_command(self, command: dict) -> bool:
        """Step 3: Execute a single command via Orchestrator"""
        print(f"
🔧 Executing: {command.get('title', 'Unknown')}")
        
        # Import orchestrator dynamically to avoid circular imports
        from orchestrator_agent import OrchestratorAgent
        
        agent_name = command.get("target_agent", "master_agent")
        
        # Use orchestrator to route to the correct agent
        orch = OrchestratorAgent()
        result = orch.route_to_agent(agent_name, command)
        
        success = result.get("success", False) if isinstance(result, dict) else False

        if success:
            print(f"✅ Command executed: {command.get('title')}")
        else:
            error = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            print(f"❌ Command failed: {error[:200]}")

        return success
        
    def execute_commands(self, commands: list):
        """Step 4: Execute all commands"""
        print("\n" + "="*60)
        print("STEP 3-4: EXECUTE COMMANDS VIA MASTER")
        print("="*60)
        
        results = []
        for cmd in commands:
            success = self.execute_command(cmd)
            results.append({
                "command": cmd.get("title"),
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update memory with result
            if "command_results" not in self.memory:
                self.memory["command_results"] = []
            self.memory["command_results"] = self.memory["command_results"][-20:] + [results[-1]]
            
        return results
        
    def update_memory(self, results: list):
        """Step 5: Update memory with results"""
        print("\n" + "="*60)
        print("STEP 5: UPDATE MEMORY")
        print("="*60)
        
        # Update last run timestamp
        self.memory["last_system_run"] = datetime.now().isoformat()
        
        # Count successes/failures
        successes = sum(1 for r in results if r.get("success"))
        self.memory["last_run_success"] = successes == len(results)
        self.memory["last_run_stats"] = {
            "total": len(results),
            "success": successes,
            "failed": len(results) - successes
        }
        
        self.save_state()
        print(f"✅ Memory updated - {successes}/{len(results)} successful")
        
    def run_cycle(self, iterations=1):
        """Run one complete cycle"""
        print("\n" + "="*70)
        print("🚀 STARTING AUTONOMOUS SYSTEM CYCLE")
        print("="*70)
        
        # Step 1: Run Commander
        if not self.run_commander():
            print("❌ Commander failed, aborting cycle")
            return False
            
        # Step 2: Get commands
        commands = self.get_commands()
        
        if not commands:
            print("ℹ️  No commands to execute")
            return True
            
        # Step 3-4: Execute commands
        results = self.execute_commands(commands)
        
        # Step 5: Update memory
        self.update_memory(results)
        
        print("\n" + "="*70)
        print("✅ CYCLE COMPLETE")
        print("="*70)
        
        return True
        
    def run_continuous(self, interval=60, max_iterations=None):
        """Run continuously"""
        print(f"\n🔄 Starting continuous mode (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        while self.running:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"ITERATION #{iteration}")
            print(f"{'='*70}")
            
            self.run_cycle()
            
            if max_iterations and iteration >= max_iterations:
                print(f"\n✅ Reached max iterations: {max_iterations}")
                break
                
            print(f"\n💤 Sleeping for {interval}s...")
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted by user")
                break
                
        print("\n🛑 System stopped")
        
    def stop(self):
        """Stop the system"""
        self.running = False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run System - Autonomous Multi-Agent Coordinator")
    parser.add_argument("--once", action="store_true", help="Run one cycle only")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=60, help="Interval between cycles (seconds)")
    parser.add_argument("--max", type=int, help="Max iterations (for testing)")
    
    args = parser.parse_args()
    
    runner = SystemRunner()
    
    if args.once:
        runner.run_cycle()
    elif args.continuous:
        runner.run_continuous(args.interval, args.max)
    else:
        print("Run System - Autonomous Multi-Agent Coordinator")
        print("Usage:")
        print("  python run_system.py --once              # Run one cycle")
        print("  python run_system.py --continuous        # Run continuously")
        print("  python run_system.py --continuous --interval 30  # Every 30s")


if __name__ == "__main__":
    main()
