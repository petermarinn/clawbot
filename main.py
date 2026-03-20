#!/usr/bin/env python3
"""
AUTONOMOUS MAIN LOOP
====================
Continuously runs all agents in a loop
"""

import time
import sys
import logging
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent list - all agents to run each cycle
AGENTS = [
    "Stock",
    "News",
    "Website",
    "Portfolio",
    "Self Upgrade",
    "Tester"
]

# Import agent router
from agents import run_agent


def autonomous_loop(interval: int = 60, cycles: int = None):
    """
    Main autonomous loop
    
    Args:
        interval: Seconds between cycles (default 60)
        cycles: Number of cycles to run (None = infinite)
    """
    cycle_count = 0
    
    logger.info("🚀 Starting Autonomous Agent System")
    logger.info(f"Agents: {', '.join(AGENTS)}")
    logger.info(f"Interval: {interval} seconds")
    print("=" * 60)
    print("🤖 AUTONOMOUS AGENT SYSTEM")
    print("=" * 60)
    
    while True:
        cycle_count += 1
        print(f"\n🔄 CYCLE {cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 40)
        
        # Run each agent
        for agent in AGENTS:
            print(f"\n👉 Running {agent} Agent...")
            try:
                result = run_agent(agent)
                status = "✅ SUCCESS" if result else "⚠️ SKIPPED"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        print("\n" + "=" * 60)
        
        # Check if we should stop
        if cycles and cycle_count >= cycles:
            logger.info(f"Completed {cycles} cycles - stopping")
            break
        
        # Wait for next cycle
        logger.info(f"Sleeping {interval} seconds...")
        time.sleep(interval)


def quick_test():
    """Quick test of all agents"""
    print("🧪 Quick Agent Test")
    print("-" * 30)
    
    for agent in AGENTS:
        try:
            result = run_agent(agent)
            print(f"  {agent}: {'✅' if result else '❌'}")
        except Exception as e:
            print(f"  {agent}: ❌ {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Agent System")
    parser.add_argument("--once", action="store_true", help="Run one cycle only")
    parser.add_argument("--test", action="store_true", help="Quick test")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    parser.add_argument("--cycles", type=int, help="Number of cycles to run")
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    elif args.once:
        autonomous_loop(interval=args.interval, cycles=1)
    else:
        autonomous_loop(interval=args.interval, cycles=args.cycles)
