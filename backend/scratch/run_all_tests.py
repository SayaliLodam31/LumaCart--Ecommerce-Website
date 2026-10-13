import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import unittest
from django.test.utils import setup_test_environment, teardown_test_environment
from apps.accounts.tests import AccountsAuthTests

def run_tests():
    print("=" * 60)
    print("RUNNING LUMACART EXISTING TEST SUITE")
    print("=" * 60)
    
    setup_test_environment()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AccountsAuthTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    teardown_test_environment()
    
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    assert result.wasSuccessful(), "Test suite failed!"
    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
