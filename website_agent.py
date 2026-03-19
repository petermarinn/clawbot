#!/usr/bin/env python3
"""
website_agent.py - Website management agent for Clawbot
Manages web_app.py, frontend, API endpoints, templates, and serving
"""

import subprocess
import sys
import os
import signal
from pathlib import Path
from datetime import datetime


class WebsiteAgent:
    """Agent for managing Clawbot web presence"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.web_app = self.project_dir / "web_app.py"
        self.port = 5000
        self.process = None
        
    def check_web_app_exists(self):
        """Check if web_app.py exists"""
        return self.web_app.exists()
    
    def check_syntax(self):
        """Check web_app.py syntax"""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(self.web_app)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        required = ["flask", "flask_cors", "yfinance", "requests"]
        missing = []
        
        for pkg in required:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg],
                capture_output=True
            )
            if result.returncode != 0:
                missing.append(pkg)
                
        return missing
    
    def start_server(self, port=None, debug=False):
        """Start the web server"""
        if port:
            self.port = port
            
        missing = self.check_dependencies()
        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            print("   Run: pip install " + " ".join(missing))
            return False
            
        if not self.check_syntax():
            print("❌ web_app.py has syntax errors!")
            return False
            
        print(f"🌐 Starting web server on port {self.port}...")
        
        # Start in background
        env = os.environ.copy()
        env["FLASK_ENV"] = "development" if debug else "production"
        
        self.process = subprocess.Popen(
            [sys.executable, str(self.web_app)],
            cwd=str(self.project_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ Server running! Open http://localhost:{self.port}")
        return True
    
    def stop_server(self):
        """Stop the web server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("🛑 Server stopped")
        else:
            # Try to kill by port
            subprocess.run(["pkill", "-f", "web_app.py"])
            print("🛑 Server stopped")
    
    def restart_server(self, port=None):
        """Restart the web server"""
        self.stop_server()
        return self.start_server(port)
    
    def get_status(self):
        """Get server status"""
        result = subprocess.run(
            ["pgrep", "-f", "web_app.py"],
            capture_output=True
        )
        
        if result.returncode == 0:
            pid = result.stdout.decode().strip()
            return {"status": "running", "pid": pid}
        return {"status": "stopped"}
    
    def get_logs(self, lines=50):
        """Get recent server logs"""
        try:
            result = subprocess.run(
                ["tail", f"-n{lines}", "/var/log/clawbot*"],
                capture_output=True,
                text=True
            )
            return result.stdout or "No logs found"
        except:
            return "Logs not available"
    
    def add_api_endpoint(self, endpoint_name, handler_code):
        """Add a new API endpoint to web_app.py"""
        # This is a placeholder - would need to parse and modify web_app.py
        print(f"📝 Would add endpoint: {endpoint_name}")
        print(f"   Code: {handler_code[:50]}...")
        
    def list_routes(self):
        """List all API routes"""
        print("📡 Available routes:")
        print("   GET /                    - Main dashboard")
        print("   GET /api/stocks          - Get all stocks")
        print("   GET /api/stock/<symbol>  - Get specific stock")
        print("   POST /api/refresh        - Refresh data")
        print("   GET /api/alerts          - Get alerts")
        print("   POST /api/alerts         - Create alert")
        
    def check_port(self, port=None):
        """Check if port is available"""
        import socket
        if port is None:
            port = self.port
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        return result != 0  # True if port is free
    
    def get_external_url(self):
        """Get external URL (for penguin server)"""
        # Try to get external IP
        result = subprocess.run(
            ["curl", "-s", "ifconfig.me"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ip = result.stdout.strip() if result.stdout else "localhost"
        return f"http://{ip}:{self.port}"
    
    def deploy_to_production(self):
        """Deploy to production (penguin)"""
        print("🚀 Deploying to production...")
        
        # Check if on penguin
        result = subprocess.run(
            ["hostname"],
            capture_output=True,
            text=True
        )
        
        if "penguin" in result.stdout.lower():
            # We're on penguin, just restart
            return self.restart_server()
        else:
            # Need to push to git
            print("   Committing changes...")
            subprocess.run(["git", "add", "-A"], cwd=self.project_dir)
            subprocess.run(["git", "commit", "-m", "Website updates"], cwd=self.project_dir)
            subprocess.run(["git", "push"], cwd=self.project_dir)
            print("   ✅ Changes pushed to GitHub")
            print("   ℹ️  Penguin will auto-pull in 15 minutes")
            return True


def main():
    """CLI for website agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Website Agent")
    parser.add_argument("--start", action="store_true", help="Start web server")
    parser.add_argument("--stop", action="store_true", help="Stop web server")
    parser.add_argument("--restart", action="store_true", help="Restart web server")
    parser.add_argument("--status", action="store_true", help="Get server status")
    parser.add_argument("--routes", action="store_true", help="List routes")
    parser.add_argument("--deploy", action="store_true", help="Deploy to production")
    parser.add_argument("--port", type=int, default=5000, help="Port to use")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    
    args = parser.parse_args()
    
    agent = WebsiteAgent()
    
    if args.start:
        agent.start_server(port=args.port)
    elif args.stop:
        agent.stop_server()
    elif args.restart:
        agent.restart_server(port=args.port)
    elif args.status:
        status = agent.get_status()
        print(f"Status: {status['status']}")
        if 'pid' in status:
            print(f"PID: {status['pid']}")
    elif args.routes:
        agent.list_routes()
    elif args.deploy:
        agent.deploy_to_production()
    elif args.check:
        missing = agent.check_dependencies()
        if missing:
            print(f"Missing: {missing}")
        else:
            print("All dependencies OK!")
    else:
        print("Clawbot Website Agent")
        print("Usage:")
        print("  python website_agent.py --start          # Start server")
        print("  python website_agent.py --stop          # Stop server")
        print("  python website_agent.py --restart        # Restart server")
        print("  python website_agent.py --status        # Check status")
        print("  python website_agent.py --routes         # List routes")
        print("  python website_agent.py --deploy        # Deploy to production")


if __name__ == "__main__":
    main()
