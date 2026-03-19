#!/usr/bin/env python3
"""
COMMANDER AGENT - Autonomous Decision Maker
==========================================
Responsibilities:
- Analyze system state
- Decide what tasks should be executed
- Assign tasks to master_agent
- Coordinate all other agents

Commander MUST NOT:
- Write code
- Modify files directly
- Execute tasks

Commander ONLY outputs structured commands.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


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
        broken = self.memory.get("broken", [])
        if broken:
            analysis["issues"].extend(broken)
            analysis["recommendations"].append({
                "priority": "HIGH",
                "action": "fix_broken_items",
                "items": broken
            })
            
        # Check for stale data
        last_updates = self.memory.get("last_updates", {})
        for feature, timestamp in last_updates.items():
            try:
                last_time = datetime.fromisoformat(timestamp)
                age = (datetime.now() - last_time).total_seconds()
                if age > 3600:  # Older than 1 hour
                    analysis["recommendations"].append({
                        "priority": "MEDIUM",
                        "action": "refresh_data",
                        "feature": feature
                    })
            except:
                pass
                
        # Check pending tasks
        pending = self.memory.get("pending_tasks", [])
        if pending:
            analysis["recommendations"].append({
                "priority": "HIGH",
                "action": "process_pending_tasks",
                "count": len(pending)
            })
            
        return analysis
        
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
