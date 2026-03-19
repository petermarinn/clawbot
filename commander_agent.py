#!/usr/bin/env python3
"""
COMMANDER AGENT - Autonomous Decision Maker
==========================================
Uses Ollama for AI-powered decision making

Requirements:
- Ollama installed: curl -fsSL https://ollama.com/install.sh | sh
- Model pulled: ollama pull codellama

If Ollama unavailable, falls back to rule-based logic.
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class OllamaClient:
    """Simple Ollama API client"""
    
    def __init__(self, model="codellama:7b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.available = self._check_available()
        
    def _check_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            result = subprocess.run(
                ["curl", "-s", f"{self.base_url}/api/tags"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
            
    def generate(self, prompt: str, system: str = None) -> str:
        """Generate response from Ollama"""
        if not self.available:
            return None
            
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
            
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", f"{self.base_url}/api/generate",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps(payload)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("response", "").strip()
        except Exception as e:
            print(f"Ollama error: {e}")
        return None


class CommanderAgent:
    """
    The Commander decides what needs to be done and outputs structured commands.
    It does NOT execute tasks - it only decides and commands.
    """
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.memory_file = self.project_dir / "memory.json"
        self.commands_file = self.project_dir / "commander_commands.json"
        self.load_memory()
        
    def load_memory(self):
        """Load shared memory"""
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                self.memory = json.load(f)
        else:
            self.memory = {
                "system_state": "initializing",
                "features": [],
                "broken": [],
                "last_updates": {},
                "completed_tasks": [],
                "pending_tasks": []
            }
            
    def save_memory(self):
        """Save shared memory"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
            
    def analyze_state(self) -> Dict:
        """Analyze current system state"""
        print("\n" + "="*60)
        print("🔍 ANALYZING SYSTEM STATE")
        print("="*60)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "recommendations": []
        }
        
        # Check memory for broken items
        broken = self.memory.get("issues", [])
        if broken:
            analysis["issues"].extend(broken)
            analysis["recommendations"].append({
                "priority": "HIGH",
                "action": "fix_broken_items",
                "items": broken
            })
        
        # Check if we have any IMPROVEMENT tasks to do (not just refresh)
        completed = self.memory.get("completed_tasks", [])
        
        # HIGH-VALUE IMPROVEMENTS - check what's NOT done
        improvements_needed = []
        
        # 1. Check if stock detail pages exist
        if not self.has_feature("stock_pages"):
            improvements_needed.append({
                "title": "Add Stock Detail Pages",
                "objective": "Create /stock/[ticker] pages with charts, analysis, company info",
                "target_agent": "website_agent",
                "requirements": {"action": "add_stock_pages"},
                "expected_outcome": "Clickable stock cards lead to detail pages",
                "priority": "HIGH"
            })
        
        # 2. Check if company logos exist
        if not self.has_feature("company_logos"):
            improvements_needed.append({
                "title": "Add Company Logos",
                "objective": "Display company logos on stock cards",
                "target_agent": "website_agent", 
                "requirements": {"action": "add_logos"},
                "expected_outcome": "Logos visible on all stock cards",
                "priority": "MEDIUM"
            })
        
        # 3. Check if news links to stocks
        if not self.has_feature("news_stock_links"):
            improvements_needed.append({
                "title": "Link News to Stocks",
                "objective": "Make news items clickable to relevant stock pages",
                "target_agent": "news_agent",
                "requirements": {"action": "add_stock_links"},
                "expected_outcome": "Click news to see related stock",
                "priority": "MEDIUM"
            })
        
        # 4. Check if portfolio has charts
        if not self.has_feature("portfolio_charts"):
            improvements_needed.append({
                "title": "Add Portfolio Charts",
                "objective": "Visual portfolio performance with charts",
                "target_agent": "website_agent",
                "requirements": {"action": "add_portfolio_charts"},
                "expected_outcome": "Portfolio shows performance chart",
                "priority": "MEDIUM"
            })
        
        # If we have improvements, add ONE priority improvement
        if improvements_needed:
            # Pick the highest priority one
            best = improvements_needed[0]  # Already sorted by priority
            analysis["recommendations"].append({
                "priority": "HIGH",
                "action": "implement_improvement",
                "improvement": best
            })
        else:
            # No improvements needed - just maintenance
            analysis["recommendations"].append({
                "priority": "LOW",
                "action": "maintenance",
                "description": "All features implemented - maintenance mode"
            })
        
        # Check for stale data (only if we're actually doing improvements)
        last_updates = self.memory.get("last_updates", {})
        stale_count = 0
        for feature, timestamp in last_updates.items():
            try:
                last_time = datetime.fromisoformat(timestamp)
                age = (datetime.now() - last_time).total_seconds()
                if age > 3600:
                    stale_count += 1
            except:
                pass
        
        if stale_count > 3 and improvements_needed:
            analysis["recommendations"].append({
                "priority": "MEDIUM",
                "action": "update_timestamps",
                "description": "Update feature timestamps after improvements"
            })
        
        return analysis
    def full_system_scan(self) -> Dict:
        """Perform a comprehensive scan of the entire system"""
        print("\n" + "="*60)
        print("🔍 FULL SYSTEM SCAN")
        print("="*60)
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # Check 1: Is web server running?
        try:
            import requests
            r = requests.get("http://localhost:5000/", timeout=5)
            scan_results["checks"]["web_server"] = "OK" if r.status_code == 200 else "ERROR"
        except:
            scan_results["checks"]["web_server"] = "NOT_RUNNING"
            scan_results["issues_found"].append({"type": "service_down", "target": "web_server"})
        
        # Check 2: Are stock pages working?
        try:
            r = requests.get("http://localhost:5000/stock/AAPL", timeout=5)
            scan_results["checks"]["stock_pages"] = "OK" if r.status_code == 200 else "ERROR"
        except:
            scan_results["checks"]["stock_pages"] = "NOT_TESTED"
        
        # Check 3: Is news page working?
        try:
            r = requests.get("http://localhost:5000/news", timeout=5)
            scan_results["checks"]["news_page"] = "OK" if r.status_code == 200 else "ERROR"
        except:
            scan_results["checks"]["news_page"] = "NOT_TESTED"
        
        # Check 4: Memory state
        mem = self.load_memory()
        scan_results["checks"]["memory"] = "OK"
        scan_results["checks"]["features_count"] = len(mem.get("features", []))
        scan_results["checks"]["command_results"] = len(mem.get("command_results", []))
        
        # Check 5: Data freshness
        last_stock = mem.get("last_updates", {}).get("stocks")
        if last_stock:
            from datetime import datetime
            try:
                last_time = datetime.fromisoformat(last_stock)
                age = (datetime.now() - last_time).total_seconds()
                scan_results["checks"]["data_age_seconds"] = int(age)
                if age > 3600:
                    scan_results["issues_found"].append({"type": "stale_data", "target": "stocks"})
            except:
                pass
        
        # Generate recommendations based on scan
        if scan_results["issues_found"]:
            scan_results["recommendations"].append({
                "priority": "HIGH",
                "action": "fix_issues",
                "issues": scan_results["issues_found"]
            })
        
        # Always recommend data refresh
        scan_results["recommendations"].append({
            "priority": "MEDIUM",
            "action": "refresh_data",
            "description": "Keep data fresh"
        })
        
        print(f"✅ Scan complete: {len(scan_results['issues_found'])} issues found")
        return scan_results


    
    def has_feature(self, feature_name: str) -> bool:
        """Check if a feature has been implemented"""
        features = self.memory.get("features", [])
        return any(f.get("name") == feature_name  for f in features)
        
    def decide_commands(self, analysis: Dict) -> List[Dict]:
        """Decide what commands to issue based on analysis"""
        commands = []
        
        # Process broken items - send fix commands
        for issue in analysis.get("issues", []):
            if isinstance(issue, dict) and "type" in issue:
                commands.append({
                    "title": f"Fix: {issue.get('type', 'Unknown')}",
                    "objective": f"Fix the broken {issue.get('type')} component",
                    "target_agent": issue.get("agent", "debugger_agent"),
                    "requirements": issue,
                    "expected_outcome": "Item fixed and working",
                    "priority": "HIGH"
                })
                
        # Process recommendations
        for rec in analysis.get("recommendations", []):
            action = rec.get("action")
            
            if action == "fix_broken_items":
                commands.append({
                    "title": "Fix Broken Items",
                    "objective": "Analyze and fix any broken components",
                    "target_agent": "debugger_agent",
                    "requirements": {"action": "analyze_and_fix"},
                    "expected_outcome": "All broken items resolved",
                    "priority": rec.get("priority", "MEDIUM")
                })
                
            elif action == "implement_improvement":
                improvement = rec.get("improvement", {})
                commands.append({
                    "title": improvement.get("title", "Implement Improvement"),
                    "objective": improvement.get("objective", ""),
                    "target_agent": improvement.get("target_agent", "website_agent"),
                    "requirements": improvement.get("requirements", {}),
                    "expected_outcome": improvement.get("expected_outcome", ""),
                    "priority": "HIGH"
                })
            elif action == "refresh_data":
                commands.append({
                    "title": "Refresh Data",
                    "objective": f"Refresh stale data for {rec.get('feature')}",
                    "target_agent": "news_agent",
                    "requirements": {"feature": rec.get("feature")},
                    "expected_outcome": "Data refreshed and up to date",
                    "priority": rec.get("priority", "MEDIUM")
                })
                
            elif action == "process_pending_tasks":
                commands.append({
                    "title": "Process Pending Tasks",
                    "objective": "Execute all pending tasks from queue",
                    "target_agent": "master_agent",
                    "requirements": {"task_type": "pending"},
                    "expected_outcome": "All pending tasks completed",
                    "priority": rec.get("priority", "HIGH")
                })
                
        # Always include routine maintenance commands
        commands.append({
            "title": "Run Pre-Pull Validation",
            "objective": "Validate all code before any deployment",
            "target_agent": "master_agent",
            "requirements": {"command": "--pre-pull"},
            "expected_outcome": "All validations pass",
            "priority": "HIGH"
        })
        
        # Check if website needs updates
        if self.needs_website_update():
            commands.append({
                "title": "Update Website",
                "objective": "Ensure website reflects current state",
                "target_agent": "website_agent",
                "requirements": {"action": "sync_with_memory"},
                "expected_outcome": "Website synced with memory",
                "priority": "MEDIUM"
            })
            
        return commands
        
    def needs_website_update(self) -> bool:
        """Check if website needs updating"""
        features = self.memory.get("features", [])
        return len(features) > 0
        
    def output_commands(self, commands: List[Dict]):
        """Output structured commands to file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "command_count": len(commands),
            "commands": commands
        }
        
        with open(self.commands_file, "w") as f:
            json.dump(output, f, indent=2)
            
        print("\n" + "="*60)
        print("📋 COMMANDER COMMANDS OUTPUT")
        print("="*60)
        for i, cmd in enumerate(commands, 1):
            print(f"\n[{i}] {cmd.get('title', 'Untitled')}")
            print(f"    Objective: {cmd.get('objective', 'N/A')}")
            print(f"    Target: {cmd.get('target_agent', 'N/A')}")
            print(f"    Priority: {cmd.get('priority', 'N/A')}")
            
        return output
        
    def run(self) -> List[Dict]:
        """Main execution - analyze and decide commands"""
        print("\n" + "="*60)
        print("🎖️  COMMANDER AGENT")
        print("="*60)
        
        # Step 1: Analyze system state
        analysis = self.analyze_state()
        
        # Step 2: Decide what commands to issue
        commands = self.decide_commands(analysis)
        
        # Step 3: Output commands
        self.output_commands(commands)
        
        return commands
        
    def get_commands(self) -> List[Dict]:
        """Get current commands from file"""
        if self.commands_file.exists():
            with open(self.commands_file) as f:
                data = json.load(f)
                return data.get("commands", [])
        return []
        
    def mark_task_complete(self, task_title: str):
        """Mark a task as completed in memory"""
        if "completed_tasks" not in self.memory:
            self.memory["completed_tasks"] = []
            
        self.memory["completed_tasks"].append({
            "task": task_title,
            "completed_at": datetime.now().isoformat()
        })
        
        # Remove from pending if there
        pending = self.memory.get("pending_tasks", [])
        self.memory["pending_tasks"] = [t for t in pending if t != task_title]
        
        self.save_memory()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Commander Agent - Autonomous Decision Maker")
    parser.add_argument("--run", action="store_true", help="Run analysis and output commands")
    parser.add_argument("--get-commands", action="store_true", help="Get current commands")
    parser.add_argument("--complete", type=str, help="Mark task as complete")
    
    args = parser.parse_args()
    
    commander = CommanderAgent()
    
    if args.run:
        commander.run()
    elif args.get_commands:
        commands = commander.get_commands()
        print(json.dumps(commands, indent=2))
    elif args.complete:
        commander.mark_task_complete(args.complete)
        print(f"Marked '{args.complete}' as complete")
    else:
        print("Commander Agent - Autonomous Decision Maker")
        print("Usage:")
        print("  python commander_agent.py --run              # Analyze and output commands")
        print("  python commander_agent.py --get-commands   # Get current commands")
        print("  python commander_agent.py --complete 'Task' # Mark task complete")


if __name__ == "__main__":
    main()
