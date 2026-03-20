#!/usr/bin/env python3
"""
Integration Tests - Validate end-to-end system functionality
"""
import sys
import json
import time
import subprocess
from pathlib import Path

PROJECT_DIR = Path("/workspace/project/clawbot")

class IntegrationTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test(self, name, func):
        """Run a test"""
        print(f"\n🧪 Testing: {name}")
        try:
            result = func()
            if result:
                print(f"   ✅ PASSED")
                self.passed += 1
                self.results.append({"test": name, "status": "PASSED"})
                return True
            else:
                print(f"   ❌ FAILED")
                self.failed += 1
                self.results.append({"test": name, "status": "FAILED"})
                return False
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1
            self.results.append({"test": name, "status": f"ERROR: {e}"})
            return False
    
    def test_supervisor_health_check(self):
        """Test supervisor health check"""
        result = subprocess.run(
            [sys.executable, "supervisor_agent.py", "--check"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0 and "HEALTHY" in result.stdout
    
    def test_orchestrator_loads(self):
        """Test orchestrator loads"""
        result = subprocess.run(
            [sys.executable, "-c", "import orchestrator_agent"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def test_data_intelligence(self):
        """Test data intelligence alignment"""
        result = subprocess.run(
            [sys.executable, "data_intelligence.py", "--picks"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    
    def test_web_server(self):
        """Test web server responds"""
        try:
            import requests
            r = requests.get("http://localhost:5000/", timeout=10)
            return r.status_code == 200
        except:
            return False
    
    def test_stock_page(self):
        """Test stock detail page"""
        try:
            import requests
            r = requests.get("http://localhost:5000/stock/AAPL", timeout=10)
            return r.status_code == 200
        except:
            return False
    
    def test_system_endpoint(self):
        """Test /system endpoint"""
        try:
            import requests
            r = requests.get("http://localhost:5000/system", timeout=10)
            return r.status_code == 200
        except:
            return False
    
    def test_report_generator(self):
        """Test report generation"""
        result = subprocess.run(
            [sys.executable, "report_generator.py", "--text"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    
    def test_github_integration(self):
        """Test GitHub integration"""
        result = subprocess.run(
            [sys.executable, "github_integration.py", "--status"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    
    def test_run_system_once(self):
        """Test single system cycle"""
        result = subprocess.run(
            [sys.executable, "run_system.py", "--once"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("🧪 RUNNING INTEGRATION TESTS")
        print("=" * 60)
        
        # Core tests
        self.test("Supervisor Health Check", self.test_supervisor_health_check)
        self.test("Orchestrator Loads", self.test_orchestrator_loads)
        self.test("Data Intelligence", self.test_data_intelligence)
        
        # Web tests
        self.test("Web Server", self.test_web_server)
        self.test("Stock Detail Page", self.test_stock_page)
        self.test("System Endpoint", self.test_system_endpoint)
        
        # Other tests
        self.test("Report Generator", self.test_report_generator)
        self.test("GitHub Integration", self.test_github_integration)
        
        # System test
        self.test("Run System Once", self.test_run_system_once)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Total:  {self.passed + self.failed}")
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        return self.failed == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Integration Tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--supervisor", action="store_true", help="Test supervisor")
    parser.add_argument("--web", action="store_true", help="Test web server")
    parser.add_argument("--data", action="store_true", help="Test data intelligence")
    
    args = parser.parse_args()
    
    tests = IntegrationTests()
    
    if args.all:
        success = tests.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.supervisor:
        tests.test("Supervisor", tests.test_supervisor_health_check)
    elif args.web:
        tests.test("Web Server", tests.test_web_server)
        tests.test("Stock Page", tests.test_stock_page)
        tests.test("System", tests.test_system_endpoint)
    elif args.data:
        tests.test("Data Intelligence", tests.test_data_intelligence)
    else:
        print("Integration Tests")
        print("  --all          Run all tests")
        print("  --supervisor   Test supervisor")
        print("  --web          Test web server")
        print("  --data         Test data intelligence")


if __name__ == "__main__":
    main()
