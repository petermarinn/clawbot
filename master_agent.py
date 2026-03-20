#!/usr/bin/env python3
"""
master_agent.py - Master agent that orchestrates all other agents
Receives commands from Commander and routes to appropriate agents
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class MasterAgent:
    """Orchestrates all Clawbot agents - receives commands from Commander"""
    
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir)
        self.commands_file = Path(project_dir) / "commander_commands.json"
        
        # Agent routing table
        self.agent_routes = {
            "website_agent": "website_agent.py",
            "news_agent": "news_agent.py", 
            "stock_agent": "stock_agent.py",
            "debugger_agent": "debugger_agent.py",
            "tester_agent": "tester_agent.py",
            "installer_agent": "installer_agent.py",
            "self_upgrade_agent": "self_upgrade_agent.py",
        }
        
    def load_commands(self):
        """Load commands from Commander"""
        if self.commands_file.exists():
            with open(self.commands_file) as f:
                data = json.load(f)
                return data.get("commands", [])
        return []
        
    def route_command(self, command: dict) -> bool:
        """Route a command to the appropriate agent"""
        target = command.get("target_agent", "")
        requirements = command.get("requirements", {})
        
        print(f"\n🎯 Routing command: {command.get('title', 'Unknown')}")
        print(f"   Target agent: {target}")
        
        # Determine which agent to run
        agent_file = self.agent_routes.get(target, f"{target}.py")
        
        # Determine arguments
        args = []
        if isinstance(requirements, dict):
            if "command" in requirements:
                args = requirements["command"].split()
            elif "action" in requirements:
                args = [f"--{requirements['action']}"]
        
        # Execute the agent
        return self.run_agent(agent_file, args)
        
    def run_agent(self, agent_name, args=None):
        """Run a single agent"""
        print(f"\n{'='*50}")
        print(f"Running: {agent_name}")
        print(f"{'='*50}")
        
        # Check if agent exists
        agent_path = self.project_dir / agent_name
        if not agent_path.exists():
            print(f"⚠️ Agent not found: {agent_name}")
            return False
            
        cmd = [sys.executable, agent_name]
        if args:
            cmd.extend(args)
            
        try:
            result = subprocess.run(
                cmd, 
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr[:200]}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"❌ Agent timed out: {agent_name}")
            return False
        except Exception as e:
            print(f"❌ Error running {agent_name}: {e}")
            return False
    
    # ===== STANDARD TASKS =====
    
    def pre_pull_validation(self):
        """Run debugger and tester before git pull"""
        print("=" * 60)
        print("PRE-PULL VALIDATION")
        print("=" * 60)
        
        print("\n[1/2] Running debugger...")
        success1 = self.run_agent("debugger_agent.py", ["--check"])
        
        print("\n[2/2] Running tester...")
        success2 = self.run_agent("tester_agent.py", ["--syntax"])
        
        if success1 and success2:
            print("\n✅ All pre-pull checks passed!")
            return True
        else:
            print("\n❌ Pre-pull validation failed!")
            return False

    def run_all_tests(self):
        """Run full test suite"""
        print("=" * 60)
        print("FULL TEST SUITE")
        print("=" * 60)
        
        return self.run_agent("tester_agent.py", ["--all"])

    def check_dependencies(self):
        """Check and install dependencies"""
        print("=" * 60)
        print("DEPENDENCY CHECK")
        print("=" * 60)
        
        return self.run_agent("installer_agent.py", ["--check"])

    def install_dependencies(self):
        """Install missing dependencies"""
        return self.run_agent("installer_agent.py", ["--install-missing"])

    def analyze_agents(self):
        """Analyze all agents for issues"""
        return self.run_agent("self_upgrade_agent.py", ["--analyze"])

    def auto_upgrade(self):
        """Run self-upgrade agent"""
        return self.run_agent("self_upgrade_agent.py", ["--upgrade"])

    def full_deployment_check(self):
        """Complete pre-deployment validation"""
        print("=" * 60)
        print("FULL DEPLOYMENT CHECK")
        print("=" * 60)
        
        steps = [
            ("Analysis", self.analyze_agents),
            ("Dependencies", self.check_dependencies),
            ("Pre-pull", self.pre_pull_validation),
            ("Tests", self.run_all_tests),
        ]
        
        for name, func in steps:
            print(f"\n>>> {name}...")
            if not func():
                print(f"❌ Failed at: {name}")
                return False
                
        print("\n" + "=" * 60)
        print("✅ READY FOR DEPLOYMENT!")
        print("=" * 60)
        return True
    
    def process_commands(self):
        """Process pending commands from Commander"""
        commands = self.load_commands()
        
        if not commands:
            print("ℹ️  No pending commands")
            return []
            
        results = []
        for cmd in commands:
            success = self.route_command(cmd)
            results.append({
                "command": cmd.get("title"),
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Master Agent")
    parser.add_argument("--pre-pull", action="store_true", help="Run pre-pull validation")
    parser.add_argument("--test", action="store_true", help="Run all tests")
    parser.add_argument("--deps", action="store_true", help="Check dependencies")
    parser.add_argument("--install", action="store_true", help="Install dependencies")
    parser.add_argument("--analyze", action="store_true", help="Analyze agents")
    parser.add_argument("--upgrade", action="store_true", help="Auto-upgrade")
    parser.add_argument("--deploy-check", action="store_true", help="Full deployment check")
    parser.add_argument("--process-commands", action="store_true", help="Process Commander commands")
    
    args = parser.parse_args()
    
    master = MasterAgent()
    
    if args.pre_pull:
        master.pre_pull_validation()
    elif args.test:
        master.run_all_tests()
    elif args.deps:
        master.check_dependencies()
    elif args.install:
        master.install_dependencies()
    elif args.analyze:
        master.analyze_agents()
    elif args.upgrade:
        master.auto_upgrade()
    elif args.deploy_check:
        master.full_deployment_check()
    elif args.process_commands:
        results = master.process_commands()
        print(f"\n📊 Processed {len(results)} commands")
    else:
        print("Clawbot Master Agent")
        print("Usage:")
        print("  python master_agent.py --pre-pull      # Debugger + Tester")
        print("  python master_agent.py --test         # Run all tests")
        print("  python master_agent.py --deps         # Check dependencies")
        print("  python master_agent.py --install      # Install missing deps")
        print("  python master_agent.py --analyze     # Analyze agents")
        print("  python master_agent.py --upgrade      # Auto-upgrade")
        print("  python master_agent.py --deploy-check # Full deployment check")
        print("  python master_agent.py --process-commands  # Process Commander commands")


if __name__ == "__main__":
    main()
