"""
Ledge Test Suite — pytest configuration

All tests use pytest. No custom test runners.
Structure:
  tests/unit/           — unit tests per module
  tests/integration/    — cross-module integration
  tests/conformance/    — language conformance (normative)
  tests/differential/   — tree-walker vs VM equivalence
  tests/fuzz_suite/     — fuzzer (deterministic)
  tests/examples/       — all example files must run green
"""

import sys
import os

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(__file__))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit test")
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "conformance: Conformance test (normative)")
    config.addinivalue_line("markers", "differential: Tree-walker vs VM equivalence")
    config.addinivalue_line("markers", "slow: May take > 5s")
    config.addinivalue_line("markers", "ai_native: Tests AI-native features")
    config.addinivalue_line("markers", "examples: Official example files")
