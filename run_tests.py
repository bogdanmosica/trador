"""
Test Runner for Trador Strategy Module

Runs tests for the strategy module from the project root directory.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from strategy.test_strategy_module import main as run_strategy_tests

if __name__ == "__main__":
    print("Trador Strategy Module Test Runner")
    print("=" * 50)
    
    # Run strategy module tests
    run_strategy_tests()