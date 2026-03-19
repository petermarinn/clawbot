from pathlib import Path
import os
import subprocess
import sys
#!/usr/bin/env python3
"""
master_agent.py - Master agent that orchestrates all other agents
Runs debugger, tester, installer, website_agent, and self_upgrade_agent
"""



class MasterAgent:
    """Orchestrates all Clawbot agents"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.agents = [
            "debugger_agent.py",
            "tester_agent.py", 
            "installer_agent.py",
            "website_agent.py",
            "self_upgrade_agent.py"
        ]
        
    def run_agent(self, agent_name, args=None):
        """Run a single agent"""
        print(f"\n{'='*50}")
        print(f"Running: {agent_name}")
        print(f"{'='*50}")
        
        cmd = [sys.executable, agent_name]
        if args:
            cmd.extend(args)
            
        result = subprocess.run(cmd, cwd=self.project_dir)
        return result.returncode == 0
    
    def pre_pull_validation(self):
        """Run debugger and tester before git pull"""
        print("=" * 60)
        print("PRE-PULL VALIDATION")
        print("=" * 60)
        
        # Run debugger
        print("\n[1/2] Running debugger...")
        success1 = self.run_agent("debugger_agent.py", ["--check"])
        
        # Run tester
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
    else:
        print("Clawbot Master Agent")
        print("Usage:")
        print("  python master_agent.py --pre-pull      # Debugger + Tester")
        print("  python master_agent.py --test         # Run all tests")
        print("  python master_agent.py --deps         # Check dependencies")
        print("  python master_agent.py --install      # Install missing deps")
        print("  python master_agent.py --analyze      # Analyze agents")
        print("  python master_agent.py --upgrade       # Auto-upgrade")
        print("  python master_agent.py --deploy-check  # Full deployment check")


if __name__ == "__main__":
    main()
