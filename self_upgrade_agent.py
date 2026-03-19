from datetime import datetime
from pathlib import Path
import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
#!/usr/bin/env python3
"""
self_upgrade_agent.py - Self-upgrading agent for Clawbot
Researches web/GitHub for improvements and auto-updates other agents
"""


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SelfUpgradeAgent:
    """Agent that researches and upgrades other agents automatically"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.upgrades_made = []
        self.research_results = []
        
    def check_github_trends(self):
        """Check GitHub trending repos for relevant improvements"""
        print("Checking GitHub trends for stock/fintech...")
        
        try:
            url = "https://api.github.com/search/repositories?q=stocks+trading+bot&sort=stars&order=desc"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read())
            
            trends = []
            for repo in data.get("items", [])[:5]:
                trends.append({
                    "name": repo["full_name"],
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                })
                
            self.research_results.append({"type": "github_trends", "data": trends})
            return trends
            
        except Exception as e:
            print(f"Could not fetch trends: {e}")
            return []
    
    def check_latest_libraries(self):
        """Check for latest versions of key libraries"""
        print("Checking latest library versions...")
        
        libraries = ["yfinance", "flask", "pandas", "numpy", "requests"]
        updates = []
        
        for lib in libraries:
            try:
                url = f"https://pypi.org/pypi/{lib}/json"
                response = urllib.request.urlopen(url, timeout=10)
                data = json.loads(response.read())
                version = data["info"]["version"]
                updates.append({"library": lib, "latest": version})
            except Exception:
                pass
                
        self.research_results.append({"type": "libraries", "data": updates})
        return updates
    
    def analyze_agent_code(self, agent_file):
        """Analyze an agent for potential improvements"""
        print(f"Analyzing {agent_file}...")
        
        filepath = self.project_dir / agent_file
        if not filepath.exists():
            return {"error": "File not found"}
            
        with open(filepath) as f:
            content = f.read()
            
        issues = []
        
        if "except:" in content:
            issues.append("Bare except clause - should specify exception type")
            
        if "print(" in content and "logging" not in content:
            issues.append("Uses print() instead of logging module")
            
        if "time.sleep(" in content:
            issues.append("Uses time.sleep() - consider async")
            
        if "TODO" in content or "FIXME" in content:
            issues.append("Contains TODO/FIXME comments")
            
        return {"file": agent_file, "issues": issues, "line_count": len(content.split("\n"))}
    
    def analyze_all_agents(self):
        """Analyze all agent files"""
        print("Analyzing all agents...")
        
        agents = list(self.project_dir.glob("*_agent.py"))
        results = []
        
        for agent in agents:
            result = self.analyze_agent_code(agent.name)
            results.append(result)
            
        return results
    
    def apply_security_fix(self, filepath):
        """Apply security improvements"""
        print(f"Applying security fixes to {filepath}...")
        
        full_path = self.project_dir / filepath
        with open(full_path) as f:
            content = f.read()
            
        original = content
        
        if "import os" not in content:
            content = "import os\n" + content
            
        if "password" in content.lower() or "api_key" in content.lower():
            if "# SECURITY" not in content:
                content = content.replace(
                    "import os",
                    "import os\nimport logging\n\n# SECURITY: Never hardcode secrets"
                )
                
        if content != original:
            with open(full_path, "w") as f:
                f.write(content)
            self.upgrades_made.append(f"Security fix: {filepath}")
            return True
            
        return False
    
    def optimize_imports(self, filepath):
        """Optimize imports"""
        print(f"Optimizing imports in {filepath}...")
        
        full_path = self.project_dir / filepath
        with open(full_path) as f:
            lines = f.readlines()
            
        imports = []
        other = []
        
        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)
            else:
                other.append(line)
                
        imports.sort()
        
        new_content = "".join(imports + other)
        
        if new_content != "".join(lines):
            with open(full_path, "w") as f:
                f.write(new_content)
            self.upgrades_made.append(f"Optimized imports: {filepath}")
            return True
            
        return False
    
    def auto_upgrade_agents(self):
        """Automatically upgrade all agents"""
        print("Running auto-upgrade...")
        
        results = self.analyze_all_agents()
        
        for result in results:
            if "error" in result:
                continue
                
            filepath = result["file"]
            self.apply_security_fix(filepath)
            self.optimize_imports(filepath)
            
        return self.upgrades_made
    
    def research_and_upgrade(self):
        """Full research and upgrade cycle"""
        print("=" * 50)
        print("SELF-UPGRADE AGENT")
        print("=" * 50)
        
        print("\n[1/3] Researching...")
        self.check_github_trends()
        self.check_latest_libraries()
        
        print("\n[2/3] Analyzing agents...")
        results = self.analyze_all_agents()
        
        print("\n[3/3] Applying upgrades...")
        upgrades = self.auto_upgrade_agents()
        
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Research items: {len(self.research_results)}")
        print(f"Upgrades made: {len(upgrades)}")
        
        if upgrades:
            print("\nApplied upgrades:")
            for u in upgrades:
                print(f"   - {u}")
        else:
            print("\nNo upgrades needed!")
            
        return upgrades
    
    def create_report(self, output_file="upgrade_report.md"):
        """Create upgrade report"""
        print(f"Creating upgrade report...")
        
        report = f"""# Clawbot Self-Upgrade Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Upgrades Applied

"""
        for upgrade in self.upgrades_made:
            report += f"- {upgrade}\n"
            
        report += "\n## Recommendations\n\n1. Keep yfinance updated\n2. Add unit tests\n3. Set up CI/CD\n\n---\n*Generated by SelfUpgradeAgent*\n"
        
        with open(self.project_dir / output_file, "w") as f:
            f.write(report)
            
        print(f"Report saved to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Self-Upgrade Agent")
    parser.add_argument("--analyze", action="store_true", help="Analyze agents only")
    parser.add_argument("--upgrade", action="store_true", help="Run full upgrade")
    parser.add_argument("--report", action="store_true", help="Generate report")
    
    args = parser.parse_args()
    
    agent = SelfUpgradeAgent()
    
    if args.analyze:
        results = agent.analyze_all_agents()
        for r in results:
            print(f"{r['file']}: {len(r.get('issues', []))} issues")
    elif args.upgrade:
        agent.research_and_upgrade()
    elif args.report:
        agent.research_and_upgrade()
        agent.create_report()
    else:
        print("Usage:")
        print("  python self_upgrade_agent.py --analyze")
        print("  python self_upgrade_agent.py --upgrade")
        print("  python self_upgrade_agent.py --report")


if __name__ == "__main__":
    main()
