from pathlib import Path
import ast
import logging
import os
import subprocess
import sys
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
debugger_agent.py - Debugging and troubleshooting agent for Clawbot
Helps identify syntax errors, trace issues, analyze logs, and diagnose problems
"""



class DebuggerAgent:
    """Agent for debugging and troubleshooting Clawbot"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.results = []
        
    def check_syntax(self, filepath=None):
        """Check Python syntax for files"""
        results = []
        
        if filepath:
            files = [self.project_dir / filepath]
        else:
            files = list(self.project_dir.glob("*.py"))
            
        for f in files:
            try:
                with open(f) as code:
                    ast.parse(code.read())
                results.append({"file": f.name, "status": "OK", "error": None})
            except SyntaxError as e:
                results.append({
                    "file": f.name,
                    "status": "ERROR",
                    "error": f"Line {e.lineno}: {e.msg}",
                    "context": self._get_error_context(f, e.lineno)
                })
                
        return results
    
    def _get_error_context(self, filepath, lineno, context=3):
        """Get lines around the error"""
        with open(filepath) as f:
            lines = f.readlines()
            
        start = max(0, lineno - context - 1)
        end = min(len(lines), lineno + context)
        
        return "".join(f"{i+1}: {lines[i]}" for i in range(start, end))
    
    def check_imports(self, filepath):
        """Check if all imports are available"""
        results = []
        full_path = self.project_dir / filepath
        
        try:
            with open(full_path) as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        results.append(self._check_import(alias.name, filepath))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        results.append(self._check_import(node.module, filepath))
                        
        except Exception as e:
            results.append({"import": "N/A", "status": "ERROR", "message": str(e)})
            
        return results
    
    def _check_import(self, module_name, filepath):
        """Check if a single import is available"""
        try:
            __import__(module_name)
            return {"import": module_name, "status": "OK"}
        except ImportError:
            return {"import": module_name, "status": "MISSING"}
    
    def run_pre_push_checks(self):
        """Run pre-push validation"""
        logger.info("🔍 Running pre-push checks...")
        
        # Syntax check
        logger.info("  📝 Checking Python syntax...")
        syntax_results = self.check_syntax()
        
        errors = [r for r in syntax_results if r["status"] == "ERROR"]
        
        if errors:
            logger.info(f"  ❌ Found {len(errors)} syntax errors:")
            for e in errors:
                logger.info(f"     - {e['file']}: {e['error']}")
            return False
        else:
            logger.info(f"  ✅ All {len(syntax_results)} files pass syntax check")
            
        return True
    
    def diagnose_file(self, filepath):
        """Full diagnostic for a file"""
        logger.info(f"\n🔧 Diagnosing {filepath}...")
        
        # Syntax
        syntax = self.check_syntax(filepath)
        logger.info(f"  Syntax: {syntax[0]['status']}")
        
        # Imports
        imports = self.check_imports(filepath)
        missing = [i for i in imports if i["status"] == "MISSING"]
        
        if missing:
            logger.info(f"  Missing imports: {', '.join(m['import'] for m in missing)}")
        else:
            logger.info("  Imports: All OK")
            
        return {
            "syntax": syntax,
            "imports": imports,
            "errors": errors if (errors := [r for r in syntax if r["status"] == "ERROR"]) else []
        }
    
    def analyze_logs(self, log_pattern="/var/log/clawbot*"):
        """Analyze logs for errors"""
        try:
            result = subprocess.run(
                ["grep", "-r", "ERROR", self.project_dir.parent / ".agent_tmp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout[:2000] if result.stdout else "No errors found"
        except Exception as e:
            return f"Could not analyze logs: {e}"


def main():
    """CLI for debugger agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Debugger Agent")
    parser.add_argument("--check", action="store_true", help="Run pre-push checks")
    parser.add_argument("--diagnose", type=str, help="Diagnose specific file")
    parser.add_argument("--syntax", action="store_true", help="Check all syntax")
    
    args = parser.parse_args()
    
    debugger = DebuggerAgent()
    
    if args.check or args.syntax:
        debugger.run_pre_push_checks()
    elif args.diagnose:
        debugger.diagnose_file(args.diagnose)
    else:
        logger.info("Clawbot Debugger Agent")
        logger.info("Usage:")
        logger.info("  python debugger_agent.py --check       # Pre-push validation")
        logger.info("  python debugger_agent.py --diagnose FILE  # Full diagnostic")


if __name__ == "__main__":
    main()
