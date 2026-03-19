#!/bin/bash
# pre-push-check.sh - Run this before pushing to catch errors
# Add to git hooks: cp pre-push-check.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push

echo "🔍 Running pre-push checks..."

# Check Python syntax
echo "  📝 Checking Python syntax..."
python3 -m py_compile web_app.py
if [ $? -ne 0 ]; then
    echo "❌ Syntax error in web_app.py"
    exit 1
fi

python3 -m py_compile stock_intel.py
python3 -m py_compile stock_email.py
python3 -m py_compile stock_macro.py
python3 -m py_compile canada_scanner.py

if [ $? -ne 0 ]; then
    echo "❌ Syntax error in one of the modules"
    exit 1
fi

# Import checks disabled - requires dependencies to be installed
# Uncomment below to test imports (requires: pip install flask yfinance requests)
# python3 -c "import web_app" 2>&1 || echo "  ⚠️ Import check skipped (dependencies not installed)"

echo "✅ All checks passed! Ready to push."
