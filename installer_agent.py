#!/usr/bin/env python3
"""
installer_agent.py - Dependency management agent for Clawbot
Checks, installs, and manages required packages and dependencies
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


class InstallerAgent:
    """Agent for managing Clawbot dependencies"""
    
    def __init__(self, project_dir="/workspace/project/clawbot"):
        self.project_dir = Path(project_dir)
        self.installed = []
        self.failed = []
        
    def get_requirements(self):
        """Get list of required packages"""
        req_file = self.project_dir / "requirements.txt"
        
        if req_file.exists():
            with open(req_file) as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        # Infer from imports if no requirements.txt
        packages = set()
        for py_file in self.project_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
                
                # Common package mappings
                import_map = {
                    "yfinance": "yfinance",
                    "flask": "flask",
                    "flask_cors": "flask-cors",
                    "requests": "requests",
                    "pandas": "pandas",
                    "numpy": "numpy",
                    "beautifulsoup": "beautifulsoup4",
                    "bs4": "beautifulsoup4",
                    "selenium": "selenium",
                    "webdriver": "webdriver-manager",
                    "praw": "praw",
                    "tweepy": "tweepy",
                    "twilio": "twilio",
                }
                
                for imp, pkg in import_map.items():
                    if f"import {imp}" in content or f"from {imp}" in content:
                        packages.add(pkg)
                        
        return sorted(list(packages))
    
    def check_installed(self, package):
        """Check if a package is installed"""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def install_package(self, package):
        """Install a single package"""
        print(f"  Installing {package}...")
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "-q"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.installed.append(package)
            print(f"    ✅ {package} installed")
            return True
        else:
            self.failed.append(package)
            print(f"    ❌ {package} failed: {result.stderr[:100]}")
            return False
    
    def install_all(self, packages=None):
        """Install all required packages"""
        if packages is None:
            packages = self.get_requirements()
            
        print("=" * 50)
        print("📦 INSTALLING DEPENDENCIES")
        print("=" * 50)
        print(f"Found {len(packages)} packages to check\n")
        
        for pkg in packages:
            if self.check_installed(pkg):
                print(f"  ✅ {pkg} already installed")
            else:
                self.install_package(pkg)
                
        return self.print_summary()
    
    def check_all(self):
        """Check which packages are missing"""
        packages = self.get_requirements()
        
        print("=" * 50)
        print("🔍 CHECKING DEPENDENCIES")
        print("=" * 50)
        
        missing = []
        for pkg in packages:
            if self.check_installed(pkg):
                print(f"  ✅ {pkg}")
            else:
                print(f"  ❌ {pkg} (missing)")
                missing.append(pkg)
                
        print(f"\n{len(missing)} packages missing")
        
        return missing
    
    def install_missing(self):
        """Install only missing packages"""
        missing = self.check_all()
        if missing:
            print("\nInstalling missing packages...")
            for pkg in missing:
                self.install_package(pkg)
        else:
            print("\n✅ All dependencies already installed!")
            
        return self.print_summary()
    
    def print_summary(self):
        """Print installation summary"""
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"Installed: {len(self.installed)}")
        print(f"Failed: {len(self.failed)}")
        
        if self.failed:
            print(f"\n❌ Failed packages: {', '.join(self.failed)}")
            
        return len(self.failed) == 0
    
    def create_requirements_txt(self):
        """Create requirements.txt from current state"""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True
        )
        
        packages = result.stdout.split("\n")
        # Filter to just our packages
        needed = [p for p in packages if p and not p.startswith("#")]
        
        req_file = self.project_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write("# Clawbot Dependencies\n")
            f.write("# Auto-generated by installer_agent.py\n\n")
            f.write("\n".join(sorted(needed)))
            
        print(f"✅ requirements.txt created with {len(needed)} packages")


def main():
    """CLI for installer agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawot Installer Agent")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    parser.add_argument("--install", action="store_true", help="Install all")
    parser.add_argument("--install-missing", action="store_true", help="Install missing only")
    parser.add_argument("--generate", action="store_true", help="Generate requirements.txt")
    
    args = parser.parse_args()
    
    installer = InstallerAgent()
    
    if args.check:
        installer.check_all()
    elif args.install:
        installer.install_all()
    elif args.install_missing:
        installer.install_missing()
    elif args.generate:
        installer.create_requirements_txt()
    else:
        print("Clawbot Installer Agent")
        print("Usage:")
        print("  python installer_agent.py --check           # Check what's installed")
        print("  python installer_agent.py --install        # Install all deps")
        print("  python installer_agent.py --install-missing # Install only missing")
        print("  python installer_agent.py --generate       # Create requirements.txt")


if __name__ == "__main__":
    main()
