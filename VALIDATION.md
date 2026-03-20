# Validation Criteria

## Success Metrics

### 1. Supervisor Watchdog
- ✅ System detects freeze and auto-restarts within 60 seconds
- ✅ Health check returns "HEALTHY" when system is running
- ✅ Crash detection increments crash counter
- ✅ Auto-restart triggers when frozen

### 2. Orchestrator
- ✅ Tasks execute in lifecycle order: pending → running → completed/failed
- ✅ Failed tasks retry once (max 1 retry)
- ✅ Duplicate tasks are rejected
- ✅ No task runs twice if completed

### 3. Data Intelligence
- ✅ Stock recommendations include aligned DATA + NEWS + SENTIMENT proof
- ✅ Confidence scores calculated correctly
- ✅ Top picks sorted by alignment score
- ✅ Market data fetched via yfinance

### 4. Website
- ✅ Dashboard loads at http://localhost:5000/
- ✅ Stock detail pages work at /stock/{symbol}
- ✅ System monitor at /system shows agent status
- ✅ Clickable stock cards navigate to detail pages

### 5. Reports
- ✅ Email sent with stock picks
- ✅ Price targets included with mathematical justification
- ✅ Source citations in reports
- ✅ HTML format professional

### 6. Self-Improvement
- ✅ Self-upgrade agent detects and creates improvement tasks
- ✅ Cannot modify core files directly
- ✅ All changes go through orchestrator

### 7. GitHub
- ✅ Changes backed up to repository
- ✅ Commits with descriptive messages
- ✅ Push to remote works

## Validation Tests

### Run Commands

```bash
# 1. Single system cycle
python run_system.py --once

# 2. 3 iterations
python run_system.py --continuous --max 3

# 3. Dashboard loads
curl http://localhost:5000/

# 4. Stock detail page
curl http://localhost:5000/stock/AAPL

# 5. Supervisor health
python supervisor_agent.py --check

# 6. Data intelligence
python data_intelligence.py --analyze NANO

# 7. Top picks
python data_intelligence.py --picks

# 8. Generate report
python report_generator.py --text

# 9. GitHub status
python github_integration.py --status

# 10. Run all tests
python test_integration.py --all
```

## Expected Results

- **HEALTHY** status from supervisor
- Stock picks with alignment scores > 0.6
- Web pages return 200 OK
- Test suite passes all tests
- GitHub shows recent commits
