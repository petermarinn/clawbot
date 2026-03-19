#!/bin/bash
# pre-pull-hook.sh - Run before git pull to validate code
# Install: cp pre-pull-hook.sh .git/hooks/pre-pull && chmod +x .git/hooks/pre-pull

echo "🔄 Running pre-pull validation..."

# Change to project directory
cd "$(dirname "$0")"

# Run debugger syntax check
echo "🔧 Running debugger..."
python3 debugger_agent.py --check
if [ $? -ne 0 ]; then
    echo "❌ Debugger check failed!"
    exit 1
fi

# Run tester 
echo "🧪 Running tests..."
python3 tester_agent.py --syntax
if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ All pre-pull checks passed!"
exit 0
