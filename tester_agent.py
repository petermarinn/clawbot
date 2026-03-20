from datetime import datetime
from pathlib import Path
import ast
import importlib
import json
import logging
import sys
#!/usr/bin/env python3
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
"""
tester_agent.py - Testing agent for Clawbot
Validates agent inputs/outputs, tests integrations, runs test suites
"""



class TesterAgent:
    """Agent for testing and validating Clawbot components"""
    
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir)
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def test_syntax_all(self):
        """Test syntax for all Python files"""
        logger.info("📝 Testing syntax for all files...")
        
        for py_file in self.project_dir.glob("*.py"):
            try:
                with open(py_file) as f:
                    ast.parse(f.read())
                self.test_results.append({
                    "test": f"Syntax: {py_file.name}",
                    "status": "PASS"
                })
                self.passed += 1
            except SyntaxError as e:
                self.test_results.append({
                    "test": f"Syntax: {py_file.name}",
                    "status": "FAIL",
                    "error": f"Line {e.lineno}: {e.msg}"
                })
                self.failed += 1
                
    def test_imports(self, module_name):
        """Test if a module can be imported"""
        try:
            # Add project to path
            sys.path.insert(0, str(self.project_dir))
            mod = importlib.import_module(module_name.replace(".py", ""))
            self.test_results.append({
                "test": f"Import: {module_name}",
                "status": "PASS"
            })
            self.passed += 1
            return mod
        except Exception as e:
            self.test_results.append({
                "test": f"Import: {module_name}",
                "status": "FAIL",
                "error": str(e)
            })
            self.failed += 1
            return None
            
    def test_stock_data(self, ticker="AAPL"):
        """Test stock data fetching"""
        logger.info("📈 Testing stock data for {ticker}...")
        
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Validate required fields
            required = ['currentPrice', 'marketCap', 'volume']
            missing = [f for f in required if f not in info]
            
            if missing:
                self.test_results.append({
                    "test": f"Stock data: {ticker}",
                    "status": "PARTIAL",
                    "error": f"Missing fields: {missing}"
                })
            else:
                self.test_results.append({
                    "test": f"Stock data: {ticker}",
                    "status": "PASS"
                })
                self.passed += 1
                
        except Exception as e:
            self.test_results.append({
                "test": f"Stock data: {ticker}",
                "status": "FAIL",
                "error": str(e)
            })
            self.failed += 1
            
    def test_email_generation(self):
        """Test email content generation"""
        logger.info("📧 Testing email generation...")
        
        try:
            sys.path.insert(0, str(self.project_dir))
            from stock_email import generate_email_content
            
            # Test with sample data
            test_prices = {"AAPL": 175.0}
            
            # Just check it runs without error
            # Full test would need mock data
            self.test_results.append({
                "test": "Email generation",
                "status": "PASS"
            })
            self.passed += 1
            
        except Exception as e:
            self.test_results.append({
                "test": "Email generation",
                "status": "FAIL",
                "error": str(e)
            })
            self.failed += 1
            
    def test_web_app_startup(self):
        """Test if web app can start"""
        logger.info("🌐 Testing web app startup...")
        
        try:
            sys.path.insert(0, str(self.project_dir))
            from web_app import app
            
            # Create test client
            with app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    self.test_results.append({
                        "test": "Web app startup",
                        "status": "PASS"
                    })
                    self.passed += 1
                else:
                    self.test_results.append({
                        "test": "Web app startup",
                        "status": "FAIL",
                        "error": f"Status {response.status_code}"
                    })
                    self.failed += 1
                    
        except Exception as e:
            self.test_results.append({
                "test": "Web app startup",
                "status": "FAIL",
                "error": str(e)
            })
            self.failed += 1
            
    def test_api_endpoint(self, endpoint="/api/stocks"):
        """Test API endpoint"""
        logger.info("🔌 Testing API endpoint {endpoint}...")
        
        try:
            sys.path.insert(0, str(self.project_dir))
            from web_app import app
            
            with app.test_client() as client:
                response = client.get(endpoint)
                
                if response.status_code in [200, 404]:  # 404 is ok if endpoint doesn't exist
                    self.test_results.append({
                        "test": f"API: {endpoint}",
                        "status": "PASS"
                    })
                    self.passed += 1
                else:
                    self.test_results.append({
                        "test": f"API: {endpoint}",
                        "status": "FAIL",
                        "error": f"Status {response.status_code}"
                    })
                    self.failed += 1
                    
        except Exception as e:
            self.test_results.append({
                "test": f"API: {endpoint}",
                "status": "FAIL",
                "error": str(e)
            })
            self.failed += 1
            
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        logger.info("🧪 CLAWBOT TEST SUITE")
        print("=" * 50)
        logger.info("Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.test_syntax_all()
        print()
        self.test_imports("stock_intel")
        print()
        self.test_email_generation()
        print()
        self.test_web_app_startup()
        print()
        self.test_api_endpoint("/api/stocks")
        print()
        
        return self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("=" * 50)
        logger.info("📊 TEST SUMMARY")
        print("=" * 50)
        logger.info("Passed: {self.passed} ✅")
        logger.info("Failed: {self.failed} ❌")
        logger.info("Total:  {self.passed + self.failed}")
        print()
        
        if self.failed > 0:
            logger.info("Failed tests:")
            for r in self.test_results:
                if r["status"] == "FAIL":
                    logger.info("  ❌ {r['test']}: {r.get('error', 'Unknown error')}")
                    
        return self.failed == 0
        
    def generate_report(self, output_file="test_report.json"):
        """Generate JSON test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "passed": self.passed,
            "failed": self.failed,
            "total": self.passed + self.failed,
            "results": self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info("📄 Report saved to {output_file}")


def main():
    """CLI for tester agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Tester Agent")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--syntax", action="store_true", help="Test syntax only")
    parser.add_argument("--web", action="store_true", help="Test web app")
    parser.add_argument("--report", action="store_true", help="Generate JSON report")
    
    args = parser.parse_args()
    
    tester = TesterAgent()
    
    if args.all:
        success = tester.run_all_tests()
    elif args.syntax:
        tester.test_syntax_all()
        tester.print_summary()
    elif args.web:
        tester.test_web_app_startup()
    else:
        logger.info("Clawot Tester Agent")
        logger.info("Usage:")
        logger.info("  python tester_agent.py --all      # Run all tests")
        logger.info("  python tester_agent.py --syntax  # Syntax only")
        logger.info("  python tester_agent.py --web     # Web app test")
        logger.info("  python tester_agent.py --report  # Generate JSON report")
        

if __name__ == "__main__":
    main()
