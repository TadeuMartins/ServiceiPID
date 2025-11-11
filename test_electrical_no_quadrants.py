#!/usr/bin/env python3
"""
Test to verify that quadrant processing is disabled for electrical diagrams
to prevent duplicate equipment detection.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# This test just verifies the logic in the code
# We can't easily run a full integration test without a real PDF and OpenAI API key


def test_quadrant_logic_in_code():
    """Test that the analyze endpoint has logic to skip quadrants for electrical diagrams"""
    print("Testing quadrant processing logic in backend.py...\n")
    
    # Read the backend.py file
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend.py')
    with open(backend_path, 'r') as f:
        backend_code = f.read()
    
    tests = [
        ("Check for electrical quadrant skip condition", 
         'diagram_type.lower() != "electrical"' in backend_code or 
         'diagram_type.lower() == "electrical"' in backend_code),
        ("Log message about skipping quadrants for electrical",
         "usando apenas análise global (sem quadrantes) para evitar duplicatas" in backend_code or
         "sem quadrantes" in backend_code.lower()),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


def test_electrical_deduplication_exists():
    """Test that the deduplication function has electrical diagram support"""
    print("\nTesting that deduplication has electrical diagram support...\n")
    
    from backend import dedup_items
    
    # Test that the function accepts is_electrical parameter
    import inspect
    sig = inspect.signature(dedup_items)
    
    tests = [
        ("dedup_items has is_electrical parameter", 'is_electrical' in sig.parameters),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


def test_code_structure():
    """Test the code structure for quadrant handling"""
    print("\nTesting code structure for quadrant processing...\n")
    
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend.py')
    with open(backend_path, 'r') as f:
        lines = f.readlines()
    
    # Find the line with quadrant processing
    quadrant_check_found = False
    electrical_log_found = False
    
    for i, line in enumerate(lines):
        if 'if grid > 1 and diagram_type.lower() != "electrical"' in line:
            quadrant_check_found = True
        if 'Modo elétrico: usando apenas análise global' in line:
            electrical_log_found = True
    
    tests = [
        ("Quadrant processing checks diagram type", quadrant_check_found),
        ("Log message for electrical mode exists", electrical_log_found),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("Testing Electrical Diagram Quadrant Processing")
    print("="*70)
    
    results = []
    
    results.append(("Quadrant logic in code", test_quadrant_logic_in_code()))
    results.append(("Electrical deduplication exists", test_electrical_deduplication_exists()))
    results.append(("Code structure", test_code_structure()))
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Electrical diagrams will be analyzed without quadrant processing.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        sys.exit(1)
